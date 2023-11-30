# DeepStream LPR python test 1
# make hbesthee@naver.com
# date 2023-11-22

from os import path
import sys
sys.path.append("../")
from common.bus_call import bus_call
from common.is_aarch_64 import is_aarch64
from typing import Any, Final
import pyds
import platform
import math
import time
from ctypes import *
import gi
gi.require_version("Gst", "1.0")
gi.require_version("GstRtspServer", "1.0")
from gi.repository import Gst, GstRtspServer, GLib
import configparser
import datetime

import argparse



MAX_DISPLAY_LEN: Final								= 64
MEASURE_ENABLE: Final								= 1
PGIE_CLASS_ID_VEHICLE: Final						= 0
PGIE_CLASS_ID_PERSON: Final							= 2
SGIE_CLASS_ID_LPD: Final							= 0 

""" The muxer output resolution must be set if the input streams will be of
different resolution. The muxer will scale all the input frames to this
resolution. """
MUXER_OUTPUT_WIDTH: Final							= 1280
MUXER_OUTPUT_HEIGHT: Final							= 720

""" Muxer batch formation timeout, for e.g. 40 millisec. Should ideally be set
based on the fastest source's framerate. """
MUXER_BATCH_TIMEOUT_USEC: Final						= 4000000

CONFIG_GROUP_TRACKER: Final							= "tracker"
CONFIG_GROUP_TRACKER_WIDTH: Final					= "tracker-width"
CONFIG_GROUP_TRACKER_HEIGHT: Final					= "tracker-height"
CONFIG_GROUP_TRACKER_LL_CONFIG_FILE: Final			= "ll-config-file"
CONFIG_GROUP_TRACKER_LL_LIB_FILE: Final				= "ll-lib-file"
CONFIG_GROUP_TRACKER_ENABLE_BATCH_PROCESS: Final	= "enable-batch-process"
CONFIG_GPU_ID: Final								= "gpu-id"
TRITON: Final										= "triton"
NVINFER_LPD_CH_CFG: Final							= "lpd_yolov4-tiny_ch.txt"
NVINFER_LDP_US_CFG: Final							= "lpd_yolov4-tiny_us.txt"

frame_number = 0
total_plate_number = 0
pgie_classes_str = [ "Vehicle", "TwoWheeler", "Person",	"Roadsign" ]

#def parse_nvdsanalytics_meta_data (NvDsBatchMeta *batch_meta) -> Any:

PRIMARY_DETECTOR_UID: Final							= 1
SECONDARY_DETECTOR_UID: Final						= 2
SECONDARY_CLASSIFIER_UID: Final						= 3


#def get_absolute_file_path(cfg_file_path: str, file_path: str) -> str:
#	gchar abs_cfg_path[PATH_MAX + 1]
#	gchar *abs_file_path
#	gchar *delim

#	if (file_path and file_path[0] == '/'):
#		return file_path

#	if (!realpath (cfg_file_path, abs_cfg_path)) {
#		g_free (file_path)
#		return NULL
#	}

#	# Return absolute path of config file if file_path is NULL.
#	if (not file_path):
#		abs_file_path = g_strdup (abs_cfg_path)
#		return abs_file_path
#	}

#	delim = g_strrstr (abs_cfg_path, "/")
#	*(delim + 1) = '\0'

#	abs_file_path = g_strconcat (abs_cfg_path, file_path, NULL)
#	g_free (file_path)

#	return abs_file_path
#}


def osd_sink_pad_buffer_probe (pad, info, u_data) -> Any:
	""" osd_sink_pad_buffer_probe  will extract metadata received on OSD sink pad
	and update params for drawing rectangle, object information etc.
	static GstPadProbeReturn
	osd_sink_pad_buffer_probe (GstPad * pad, GstPadProbeInfo * info,
			gpointer u_data) """

	obj_meta = None
	lp_count, person_count, vehicle_count = 0, 0, 0
	label_i, total_plate_number = 0, 0
	l_frame = None
	l_obj = None
	l_class = None
	l_label = None
	display_meta = None
	class_meta = None
	label_info = None

	"""
	perf_measure * perf = (perf_measure *)(u_data)
	now = g_get_monotonic_time()

	if (perf->pre_time == GST_CLOCK_TIME_NONE) {
		perf->pre_time = now
		perf->total_time = GST_CLOCK_TIME_NONE
	} else {
		if (perf->total_time == GST_CLOCK_TIME_NONE) {
			perf->total_time = (now - perf->pre_time)
		} else {
			perf->total_time += (now - perf->pre_time)
		}
		perf->pre_time = now
		perf->count++
	}
	"""

	gst_buffer = info.get_buffer()
	if (not gst_buffer):
		print("Unable to get GstBuffer!")
		return None

	# Retrieve batch metadata from the gst_buffer
	# Note that pyds.gst_buffer_get_nvds_batch_meta() expects the
	# C address of gst_buffer as input, which is obtained with hash(gst_buffer)
	# NvDsBatchMeta *batch_meta = gst_buffer_get_nvds_batch_meta (buf)
	batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))


	#for (l_frame = batch_meta->frame_meta_list l_frame != NULL
	#		 l_frame = l_frame->next) {
	#	NvDsFrameMeta *frame_meta = (NvDsFrameMeta *) (l_frame->data)
	l_frame = batch_meta.frame_meta_list
	while l_frame is not None:
		try:
			# Note that l_frame.data needs a cast to pyds.NvDsFrameMeta
			# The casting is done by pyds.NvDsFrameMeta.cast()
			# The casting also keeps ownership of the underlying memory
			# in the C code, so the Python garbage collector will leave
			# it alone.
			frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
		except StopIteration:
			break

		if (not frame_meta):
			continue

		offset = 0
		#for (l_obj = frame_meta->obj_meta_list l_obj != NULL
		#		 l_obj = l_obj->next) {
		#	obj_meta = (NvDsObjectMeta *) (l_obj->data)
		#	if (!obj_meta)
		#		continue;
		frame_number = frame_meta.frame_num
		num_rects = frame_meta.num_obj_meta
		l_obj = frame_meta.obj_meta_list
		while l_obj is not None:
			try:
				# Casting l_obj.data to pyds.NvDsObjectMeta
				obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
			except StopIteration:
				break
			#obj_counter[obj_meta.class_id] += 1
			try: 
				l_obj=l_obj.next
			except StopIteration:
				break

			if (not obj_meta):
				continue

			""" Check that the object has been detected by the primary detector
			and that the class id is that of vehicles/persons. """
			if (obj_meta.unique_component_id == PRIMARY_DETECTOR_UID):
				if (obj_meta.class_id == PGIE_CLASS_ID_VEHICLE):
					vehicle_count += 1
				if (obj_meta.class_id == PGIE_CLASS_ID_PERSON):
					person_count += 1

			if (obj_meta.unique_component_id == SECONDARY_DETECTOR_UID):
				if (obj_meta.class_id == SGIE_CLASS_ID_LPD):
					lp_count += 1
					# Print this info only when operating in secondary model.
					#if (obj_meta.parent)
					#	print("License plate found for parent object %p (type=%s)\n",
					#		obj_meta->parent, pgie_classes_str[obj_meta->parent->class_id])
					if (obj_meta.parent):
						print(f"License plate found for parent object {obj_meta.parent} (type={pgie_classes_str[obj_meta.parent.class_id]})\n")

					obj_meta.text_params.set_bg_clr = 1
					obj_meta.text_params.text_bg_clr.red = 0.0
					obj_meta.text_params.text_bg_clr.green = 0.0
					obj_meta.text_params.text_bg_clr.blue = 0.0
					obj_meta.text_params.text_bg_clr.alpha = 0.0

					obj_meta.text_params.font_params.font_color.red = 1.0
					obj_meta.text_params.font_params.font_color.green = 1.0
					obj_meta.text_params.font_params.font_color.blue = 0.0
					obj_meta.text_params.font_params.font_color.alpha = 1.0
					obj_meta.text_params.font_params.font_size = 12

			#for (l_class = obj_meta->classifier_meta_list l_class != NULL
			#		l_class = l_class->next) {
			#	class_meta = (NvDsClassifierMeta *)(l_class->data)
			#	if (!class_meta)
			#		continue
			#	if (class_meta->unique_component_id == SECONDARY_CLASSIFIER_UID) {
			#		for ( label_i = 0, l_label = class_meta->label_info_list
			#					label_i < class_meta->num_labels && l_label label_i++,
			#					l_label = l_label->next) {
			#			label_info = (NvDsLabelInfo *)(l_label->data)
			#			if (label_info) {
			#				if (label_info->label_id == 0 && label_info->result_class_id == 1) {
			#					g_print ("Plate License %s\n",label_info->result_label)
			#				}
			#			}
			l_class = obj_meta.classifier_meta_list
			while l_class is not None:
				try:
					class_meta = pyds.NvDsClassifierMeta.cast(l_class.data)
				except StopIteration:
					break
				if (not class_meta):
					continue
				if (class_meta.unique_component_id == SECONDARY_CLASSIFIER_UID):
					l_label = class_meta.label_info_list
					while l_label is not None:
						try:
							label_info = pyds.NvDsLabelInfo.cast(l_label.data)
						except StopIteration:
							break

						if ( (label_info) and (label_info.label_id == 0) and (label_info.result_class_id == 1) ):
							print(f"Plate License: {label_info.result_label}")

						try:
							l_label = l_label.next
						except StopIteration:
							break
				try:
					l_class = l_class.next
				except StopIteration:
					break

		#display_meta = nvds_acquire_display_meta_from_pool(batch_meta)
		#NvOSD_TextParams *txt_params  = &display_meta->text_params[0]
		#display_meta->num_labels = 1
		#txt_params->display_text = (char*) g_malloc0 (MAX_DISPLAY_LEN)
		#offset = snprintf(txt_params->display_text, MAX_DISPLAY_LEN,
		#					"Person = %d ", person_count)
		#offset += snprintf(txt_params->display_text + offset , MAX_DISPLAY_LEN,
		#					"Vehicle = %d ", vehicle_count)
		# Acquiring a display meta object. The memory ownership remains in
		# the C code so downstream plugins can still access it. Otherwise
		# the garbage collector will claim it when this probe function exits.
		display_meta = pyds.nvds_acquire_display_meta_from_pool(batch_meta)
		display_meta.num_labels = 1
		txt_params = display_meta.text_params[0]
		txt_params.display_text = f"{person_count=} / {vehicle_count=}"

		# Now set the offsets where the string should appear
		txt_params.x_offset = 10
		txt_params.y_offset = 12

		# Font , font-color and font-size
		#char font_n[6]
		#snprintf(font_n, 6, "Serif")
		#txt_params.font_params.font_name = font_n
		txt_params.font_params.font_name = "Serif"
		txt_params.font_params.font_size = 10
		txt_params.font_params.font_color.red = 1.0
		txt_params.font_params.font_color.green = 1.0
		txt_params.font_params.font_color.blue = 1.0
		txt_params.font_params.font_color.alpha = 1.0

		# Text background color
		txt_params.set_bg_clr = 1
		txt_params.text_bg_clr.red = 0.0
		txt_params.text_bg_clr.green = 0.0
		txt_params.text_bg_clr.blue = 0.0
		txt_params.text_bg_clr.alpha = 1.0

		print(pyds.get_string(txt_params.display_text))
		pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)

		try:
			l_frame = l_frame.next
		except StopIteration:
			break

	print(f"{frame_number=} / {vehicle_count=} / {person_count=} / {lp_count=}")
	frame_number += 1
	total_plate_number += lp_count
	return Gst.PadProbeReturn.OK


#static gboolean
#bus_call (GstBus * bus, GstMessage * msg, gpointer data)
#{
#	GMainLoop *loop = (GMainLoop *) data
#	switch (GST_MESSAGE_TYPE (msg)) {
#		case GST_MESSAGE_EOS:
#			g_print ("End of stream\n")
#			g_main_loop_quit (loop)
#			break
#		case GST_MESSAGE_ERROR:{
#			gchar *debug
#			GError *error
#			gst_message_parse_error (msg, &error, &debug)
#			g_printerr ("ERROR from element %s: %s\n",
#					GST_OBJECT_NAME (msg->src), error->message)
#			if (debug)
#				g_printerr ("Error details: %s\n", debug)
#			g_free (debug)
#			g_error_free (error)
#			g_main_loop_quit (loop)
#			break
#		}
#		default:
#			break
#	}
#	return TRUE
#}
# >> bus_call.bus_call() 로 대체됨





"""
static void
cb_new_pad (GstElement *element,
				GstPad     *pad,
				GstElement *data)
{
	GstCaps *new_pad_caps = NULL
	GstStructure *new_pad_struct = NULL
	const gchar *new_pad_type = NULL
	GstPadLinkReturn ret

	GstPad *sink_pad = gst_element_get_static_pad (data, "sink")
	if (gst_pad_is_linked (sink_pad)) {
		g_print ("h264parser already linked. Ignoring.\n")
		goto exit
	}

	new_pad_caps = gst_pad_get_current_caps (pad)
	new_pad_struct = gst_caps_get_structure (new_pad_caps, 0)
	new_pad_type = gst_structure_get_name (new_pad_struct)
	g_print("qtdemux pad %s\n",new_pad_type)
	
	if (g_str_has_prefix (new_pad_type, "video/x-h264")) {
		ret = gst_pad_link (pad, sink_pad)
		if(GST_PAD_LINK_FAILED (ret))
			g_print ("fail to link parser and mp4 demux.\n")
	} else {
		g_print ("%s output, not 264 stream\n",new_pad_type)
	}

exit:
	gst_object_unref (sink_pad)
}
"""





"""
static gboolean
set_tracker_properties (GstElement *nvtracker, char * config_file_name)

	if (!g_key_file_load_from_file (key_file, config_file_name, G_KEY_FILE_NONE, &error)) {
		g_printerr ("Failed to load config file: %s\n", error->message)
		return FALSE
	}

	keys = g_key_file_get_keys (key_file, CONFIG_GROUP_TRACKER, NULL, &error)
	CHECK_ERROR (error)

	for (key = keys *key key++) {
		if (!g_strcmp0 (*key, CONFIG_GROUP_TRACKER_WIDTH)) {
			gint width =
					g_key_file_get_integer (key_file, CONFIG_GROUP_TRACKER,
					CONFIG_GROUP_TRACKER_WIDTH, &error)
			CHECK_ERROR (error)
			g_object_set (G_OBJECT (nvtracker), "tracker-width", width, NULL)
		} else if (!g_strcmp0 (*key, CONFIG_GROUP_TRACKER_HEIGHT)) {
			gint height =
					g_key_file_get_integer (key_file, CONFIG_GROUP_TRACKER,
					CONFIG_GROUP_TRACKER_HEIGHT, &error)
			CHECK_ERROR (error)
			g_object_set (G_OBJECT (nvtracker), "tracker-height", height, NULL)
		} else if (!g_strcmp0 (*key, CONFIG_GPU_ID)) {
			guint gpu_id =
					g_key_file_get_integer (key_file, CONFIG_GROUP_TRACKER,
					CONFIG_GPU_ID, &error)
			CHECK_ERROR (error)
			g_object_set (G_OBJECT (nvtracker), "gpu_id", gpu_id, NULL)
		} else if (!g_strcmp0 (*key, CONFIG_GROUP_TRACKER_LL_CONFIG_FILE)) {
			char* ll_config_file = get_absolute_file_path (config_file_name,
					g_key_file_get_string (key_file,
					CONFIG_GROUP_TRACKER,
					CONFIG_GROUP_TRACKER_LL_CONFIG_FILE, &error))
			CHECK_ERROR (error)
			g_object_set (G_OBJECT (nvtracker), "ll-config-file",
					ll_config_file, NULL)
		} else if (!g_strcmp0 (*key, CONFIG_GROUP_TRACKER_LL_LIB_FILE)) {
			char* ll_lib_file = get_absolute_file_path (config_file_name,
						g_key_file_get_string (key_file,
							CONFIG_GROUP_TRACKER,
							CONFIG_GROUP_TRACKER_LL_LIB_FILE, &error))
			CHECK_ERROR (error)
			g_object_set (G_OBJECT (nvtracker), "ll-lib-file", ll_lib_file, NULL)
		} else if (!g_strcmp0 (*key, CONFIG_GROUP_TRACKER_ENABLE_BATCH_PROCESS)) {
			gboolean enable_batch_process =
					g_key_file_get_integer (key_file, CONFIG_GROUP_TRACKER,
					CONFIG_GROUP_TRACKER_ENABLE_BATCH_PROCESS, &error)
			CHECK_ERROR (error)
			g_object_set (G_OBJECT (nvtracker), "enable_batch_process",
					enable_batch_process, NULL)
		} else {
			g_printerr ("Unknown key '%s' for group [%s]", *key,
					CONFIG_GROUP_TRACKER)
		}
	}

	ret = TRUE
done:
	if (error) {
		g_error_free (error)
	}
	if (keys) {
		g_strfreev (keys)
	}
	if (!ret) {
		g_printerr ("%s failed", __func__)
	}
	return ret
}
"""
def set_tracker_properties(nvtracker, config_file_name: str = 'lpr_sample_tracker_config.txt') -> bool:
	""" Tracker config parsing 

	Args:
		nvtracker (GstElement): Tracker 객체
		config_file_name (str, optional): Tracker 설정 파일명. Defaults to 'lpr_sample_tracker_config.txt'.

	Returns:
		bool: Tracker 설정 성공 여뷰
	"""
	config = configparser.ConfigParser()
	config.read(config_file_name)
	config.sections()

	for key in config['tracker']:
		if key == 'tracker-width':
			tracker_width = config.getint('tracker', key)
			nvtracker.set_property('tracker-width', tracker_width)
		if key == 'tracker-height':
			tracker_height = config.getint('tracker', key)
			nvtracker.set_property('tracker-height', tracker_height)
		if key == 'gpu-id':
			tracker_gpu_id = config.getint('tracker', key)
			nvtracker.set_property('gpu_id', tracker_gpu_id)
		if key == 'll-lib-file':
			tracker_ll_lib_file = config.get('tracker', key)
			nvtracker.set_property('ll-lib-file', tracker_ll_lib_file)
		if key == 'll-config-file':
			tracker_ll_config_file = config.get('tracker', key)
			nvtracker.set_property('ll-config-file', tracker_ll_config_file)
		if key == 'enable-batch-process':
			tracker_enable_batch_process = config.getint('tracker', key)
			nvtracker.set_property('enable_batch_process',
								tracker_enable_batch_process)



"""
/* nvdsanalytics_src_pad_buffer_probe  will extract metadata received on
 * nvdsanalytics src pad and extract nvanalytics metadata etc. */
static GstPadProbeReturn
nvdsanalytics_src_pad_buffer_probe (GstPad * pad, GstPadProbeInfo * info,
		gpointer u_data)
{
	GstBuffer *buf = (GstBuffer *) info->data
	NvDsBatchMeta *batch_meta = gst_buffer_get_nvds_batch_meta (buf)

	parse_nvdsanalytics_meta_data (batch_meta)

	return GST_PAD_PROBE_OK
}
"""
""" nvdsanalytics_src_pad_buffer_probe  will extract metadata received on
	nvdsanalytics src pad and extract nvanalytics metadata etc. """
def nvdsanalytics_src_pad_buffer_probe(pad, info, u_data):
	buf = info.get_buffer()
	batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(buf))

	# ROI 등 분석 정보를 활용함 ; 예제에서는 분석결과를 출력만 함
	# 세부적인 내용은 deepstream_nvdsanalytics_meta.cpp 소스 참조
	#parse_nvdsanalytics_meta_data (batch_meta)

	return Gst.PadProbeReturn.OK


def print_help(command: str = "") -> None:
	""" 간단한 사용법을 출력합니다. """
	print(f"Usage: {command} [1:us model|2: ch_model] [1:file sink|2:fakesink|3:display sink]"
			, "[0:ROI disable|0:ROI enable] [infer|triton|tritongrpc] <In mp4 filename> <in mp4 filename> ..."
			, "<out H264 filename>\n")




"""
int
main (int argc, char *argv[])
{
	GMainLoop *loop = NULL
	GstElement *pipeline = NULL,*streammux = NULL, *sink = NULL, 
				     *primary_detector = NULL, *secondary_detector = NULL,
				     *nvvidconv = NULL, *nvosd = NULL, *nvvidconv1 = NULL,
				     *nvh264enc = NULL, *capfilt = NULL,
				     *secondary_classifier = NULL, *nvtile=NULL
	GstElement *tracker = NULL, *nvdsanalytics = NULL
	GstElement *queue1 = NULL, *queue2 = NULL, *queue3 = NULL, *queue4 = NULL,
				     *queue5 = NULL, *queue6 = NULL, *queue7 = NULL, *queue8 = NULL,
				     *queue9 = NULL, *queue10 = NULL
	GstElement *h264parser[128], *source[128], *decoder[128], *mp4demux[128],
				     *parsequeue[128]
	char pgie_cfg_file_path[256] = {0}
	char lpd_cfg_file_path[256] = {0}
	char lpr_cfg_file_path[256] = {0}
#ifdef PLATFORM_TEGRA
	GstElement *transform = NULL
#endif
	GstBus *bus = NULL
	guint bus_watch_id
	GstPad *osd_sink_pad = NULL
	GstCaps *caps = NULL
	GstCapsFeatures *feature = NULL
	//int i
	static guint src_cnt = 0
	guint tiler_rows, tiler_columns
	perf_measure perf_measure

	gchar ele_name[64]
	GstPad *sinkpad, *srcpad
	gchar pad_name_sink[16] = "sink_0"
	gchar pad_name_src[16] = "src"

	bool isYAML=false
	bool isH264=true
	GList* g_list = NULL
	GList* iterator = NULL
		
	const char*  ptriton = "triton"
	const char*  ptriton_grpc = "tritongrpc"
	const char *infer_plugin = "nvinfer"
	gboolean use_nvinfer_server = false
	gboolean use_triton_grpc = false
	guint car_mode = 1
"""
def main (argv) -> int:
	""" 메인 함수 """

	# 변수 초기화 부분
	loop = None
	pipeline, streammux, sink = None, None, None
	primary_detector, secondary_detector, nvvidconv = None, None, None
	nvosd, nvvidconv1, nvh264enc = None, None, None
	secondary_classifier, capfilt, nvtile = None, None, None
	tracker, nvdsanalytics, nvtile = None, None, None
	queue1, queue2, queue3, queue4, queue5, queue6, queue7, queue8, queue9, queue10 = None, None, None, None, None, None, None, None, None, None
	h264parser, source, decoder, mp4demux, parsequeue = list(128), list(128), list(128), list(128), list(128)
	pgie_cfg_file_path, lpd_cfg_file_path, lpr_cfg_file_path = '', '', ''

	if(is_aarch64()):
		transform = None

	bus, osd_sink_pad, caps, feature = None
	bus_watch_id, tiler_rows, tiler_columns = 0, 0, 0
	src_cnt = 0
	
	perf_measure = None # perf_measure

	ele_name = ''
	sinkpad, srcpad = None, None
	pad_name_sink, pad_name_src = "sink_0", "src"

	isYAML, isH264 = False, True
	g_list, iterator = None, None
	arg_lang_mode, arg_sink_mode, arg_is_roi, arg_mode = 0, 0, 0, "infer"
		
	ptriton, ptriton_grpc, infer_plugin = "triton", "tritongrpc", "nvinfer"
	use_nvinfer_server, use_triton_grpc = False, False
	car_mode = 1

	# Check input arguments
	argc = len(argv)
	if (argc == 2):
		config_ext: str = path.splitext(argv[1])
		if ( (config_ext.lower() == ".yml") or (config_ext.lower() == ".yaml")):
			isYAML = True
	else:
		if ( (argc < 6) or (argc > 13) ):
			print_help()
			return -1
		try:
			arg_lang_mode = int(argv[1])
			arg_sink_mode = int(argv[2])
			arg_is_roi = int(argv[3])
			arg_mode = str(argv[4])
		except Exception as e:
			print_help()
			return -1
		
		if ( (arg_lang_mode not in [1, 2]) 
				or (arg_sink_mode not in [1, 2, 3])
				or (arg_is_roi not in [0, 1])
				or (arg_mode.lower() not in ["infer", "triton", "tritongrpc"])
				):
			print_help(argv[0])
			return -1

	# For Chinese language supporting
	#setlocale(LC_CTYPE, "")
	if (isYAML):
		#if(ds_parse_group_enable(argv[1], TRITON)) {
		#	use_nvinfer_server = true
		#	infer_plugin = "nvinferserver"

		#	if(ds_parse_group_type(argv[1], TRITON) == 1){
		#		use_triton_grpc = true
		#	}
		#}
		pass
	else:
		if (arg_mode.lower() in ["triton", "tritongrpc"]):
			use_nvinfer_server = True
			infer_plugin = "nvinferserver"
			if(arg_mode.lower() == "tritongrpc"):
				use_triton_grpc = True

	print(f"use_nvinfer_server: {use_nvinfer_server}, use_triton_grpc: {use_triton_grpc}\n")

	# Standard GStreamer initialization
	#gst_init (&argc, &argv)
	GObject.threads_init()
	Gst.init(None)
	#loop = g_main_loop_new (NULL, FALSE)
	# create an event loop and feed gstreamer bus mesages to it
	loop = GLib.MainLoop()
	
	#perf_measure.pre_time = GST_CLOCK_TIME_NONE
	#perf_measure.total_time = GST_CLOCK_TIME_NONE
	#perf_measure.count = 0  

	# Create gstreamer elements
	# Create Pipeline element that will form a connection of other elements
	#pipeline = gst_pipeline_new ("pipeline") 
	pipeline = Gst.Pipeline()
	if not pipeline:
		Gst.error(" Unable to create Pipeline")

	# Create nvstreammux instance to form batches from one or more sources.
	#streammux = gst_element_factory_make ("nvstreammux", "stream-muxer")
	streammux = Gst.ElementFactory.make("nvstreammux", "stream-muxer")
	if (not streammux):
			print("nvstreammux element could not be created. Exiting.\n")
			return -1

	#gst_bin_add (GST_BIN(pipeline), streammux)
	pipeline.add(streammux)

	#if(!isYAML) {
	#	for (src_cnt=0 src_cnt<(guint)argc-6 src_cnt++) {
	#		g_list = g_list_append(g_list, argv[src_cnt + 5])
	#	}
	#} else {
	#		if (NVDS_YAML_PARSER_SUCCESS != nvds_parse_source_list(&g_list, argv[1], "source-list")) {
	#			g_printerr ("No source is found. Exiting.\n")
	#			return -1
	#		}
	#}
	if(not isYAML):
		src_cnt = 0
		g_list = list()
		for src_cnt in range (argc - 6):
			g_list = g_list.append(argv[src_cnt + 5])
	else:
		g_list = list()
		#if (NVDS_YAML_PARSER_SUCCESS != nvds_parse_source_list(&g_list, argv[1], "source-list")) {
		#	g_printerr ("No source is found. Exiting.\n")
		#	return -1
	
	# Multiple source files
	#for (iterator = g_list, src_cnt=0 iterator iterator = iterator->next,src_cnt++) {
	for source_index in range(src_cnt):
		# Only h264 element stream with mp4 container is supported.
		#g_snprintf (ele_name, 64, "file_src_%d", src_cnt)

		# Source element for reading from the file
		#source[src_cnt] = gst_element_factory_make ("filesrc", ele_name)
		source[source_index] = Gst.ElementFactory.make("filesrc", f"file_src_{source_index}")

		#g_snprintf (ele_name, 64, "mp4demux_%d", src_cnt)
		#mp4demux[src_cnt] = gst_element_factory_make ("qtdemux", ele_name)
		mp4demux[src_cnt] = Gst.ElementFactory.make("qtdemux", f"mp4demux_{source_index}")

		#g_snprintf (ele_name, 64, "h264parser_%d", src_cnt)
		#h264parser[src_cnt] = gst_element_factory_make ("h264parse", ele_name)
		h264parser[src_cnt] = gst_element_factory_make ("h264parse", ele_name)
			
		#g_snprintf (ele_name, 64, "parsequeue_%d", src_cnt)
		#parsequeue[src_cnt] = gst_element_factory_make ("queue", ele_name)
		parsequeue[src_cnt] = gst_element_factory_make ("queue", ele_name)

		# Use nvdec_h264 for hardware accelerated decode on GPU
		#g_snprintf (ele_name, 64, "decoder_%d", src_cnt)
		#decoder[src_cnt] = gst_element_factory_make ("nvv4l2decoder", ele_name)
		decoder[src_cnt] = gst_element_factory_make ("nvv4l2decoder", ele_name)
			
		#if(!source[src_cnt] || !h264parser[src_cnt] || !decoder[src_cnt] ||
		#		!mp4demux[src_cnt]) {
		#	g_printerr ("One element could not be created. Exiting.\n")
		#	return -1
		#}
		if (!source[src_cnt] || !h264parser[src_cnt] || !decoder[src_cnt] || !mp4demux[src_cnt]):
			g_printerr ("One element could not be created. Exiting.\n")
			return -1
			
		gst_bin_add_many (GST_BIN (pipeline), source[src_cnt], mp4demux[src_cnt],
				h264parser[src_cnt], parsequeue[src_cnt], decoder[src_cnt], NULL)
			
		g_snprintf (pad_name_sink, 64, "sink_%d", src_cnt)
		sinkpad = gst_element_get_request_pad (streammux, pad_name_sink)
		g_print("Request %s pad from streammux\n",pad_name_sink)
		if (!sinkpad) {
			g_printerr ("Streammux request sink pad failed. Exiting.\n")
			return -1
		}

		srcpad = gst_element_get_static_pad (decoder[src_cnt], pad_name_src)
		if (!srcpad) {
			g_printerr ("Decoder request src pad failed. Exiting.\n")
			return -1
		}

		if (gst_pad_link (srcpad, sinkpad) != GST_PAD_LINK_OK) {
			g_printerr ("Failed to link decoder to stream muxer. Exiting.\n")
			return -1
		}

		if(!gst_element_link_pads (source[src_cnt], "src", mp4demux[src_cnt],
					"sink")) {
			g_printerr ("Elements could not be linked: 0. Exiting.\n")
			return -1
		}

		g_signal_connect (mp4demux[src_cnt], "pad-added", G_CALLBACK (cb_new_pad),
					h264parser[src_cnt])

		if (!gst_element_link_many (h264parser[src_cnt], parsequeue[src_cnt],
					decoder[src_cnt], NULL)) {
			g_printerr ("Elements could not be linked: 1. Exiting.\n")
		}

		/* we set the input filename to the source element */
		g_object_set (G_OBJECT (source[src_cnt]), "location",
				(gchar *)iterator->data, NULL)

		gst_object_unref (sinkpad)
		gst_object_unref (srcpad)
	}
	g_list_free(g_list)

	# Create three nvinfer instances for two detectors and one classifier
	#primary_detector = gst_element_factory_make (infer_plugin, "primary-infer-engine1")
	#secondary_detector = gst_element_factory_make (infer_plugin, "secondary-infer-engine1")
	#secondary_classifier = gst_element_factory_make (infer_plugin, "secondary-infer-engine2")
	primary_detector = Gst.ElementFactory.make(infer_plugin, "primary-infer-engine1")
	secondary_detector = Gst.ElementFactory.make(infer_plugin, "secondary-infer-engine1")
	secondary_classifier = Gst.ElementFactory.make(infer_plugin, "secondary-infer-engine2")

	# Use convertor to convert from NV12 to RGBA as required by nvosd
	#nvvidconv = gst_element_factory_make ("nvvideoconvert", "nvvid-converter")
	nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "nvvid-converter")

	# Create OSD to draw on the converted RGBA buffer
	#nvosd = gst_element_factory_make ("nvdsosd", "nv-onscreendisplay")
	#nvvidconv1 = gst_element_factory_make ("nvvideoconvert", "nvvid-converter1")
	nvosd = Gst.ElementFactory.make("nvdsosd", "nv-onscreendisplay")
	nvvidconv1 = Gst.ElementFactory.make("nvvideoconvert", "nvvid-converter1")

	#if (isYAML) {
	#	if (!ds_parse_enc_type(argv[1], "output"))
	#		isH264 = true
	#	else
	#		isH264 = false
	#}
	if (isYAML):
		if (!ds_parse_enc_type(argv[1], "output")):
			isH264 = True
		else:
			isH264 = False

	#if (isH264)
	#	nvh264enc = gst_element_factory_make ("nvv4l2h264enc" ,"nvvideo-h264enc")
	#else:
	#	nvh264enc = gst_element_factory_make ("nvv4l2h265enc" ,"nvvideo-h265enc")
	if (isH264)
		nvh264enc = Gst.ElementFactory.make("nvv4l2h264enc" ,"nvvideo-h264enc")
	else:
		nvh264enc = Gst.ElementFactory.make("nvv4l2h265enc" ,"nvvideo-h265enc")

	#capfilt = gst_element_factory_make ("capsfilter", "nvvideo-caps")
	#nvtile = gst_element_factory_make ("nvmultistreamtiler", "nvtiler")
	#tracker = gst_element_factory_make ("nvtracker", "nvtracker")
	capfilt = Gst.ElementFactory.make("capsfilter", "nvvideo-caps")
	nvtile  = Gst.ElementFactory.make("nvmultistreamtiler", "nvtiler")
	tracker = Gst.ElementFactory.make("nvtracker", "nvtracker")

	# Use nvdsanalytics to perform analytics on object
	#nvdsanalytics = gst_element_factory_make ("nvdsanalytics", "nvdsanalytics")
	nvdsanalytics = Gst.ElementFactory.make("nvdsanalytics", "nvdsanalytics")
	
	#queue1 = gst_element_factory_make ("queue", "queue1")
	#queue2 = gst_element_factory_make ("queue", "queue2")
	#queue3 = gst_element_factory_make ("queue", "queue3")
	#queue4 = gst_element_factory_make ("queue", "queue4")
	#queue5 = gst_element_factory_make ("queue", "queue5")
	#queue6 = gst_element_factory_make ("queue", "queue6")
	#queue7 = gst_element_factory_make ("queue", "queue7")
	#queue8 = gst_element_factory_make ("queue", "queue8")
	#queue9 = gst_element_factory_make ("queue", "queue9")
	#queue10 = gst_element_factory_make ("queue", "queue10")
	queue1  = Gst.ElementFactory.make("queue","queue1")
	queue2  = Gst.ElementFactory.make("queue","queue2")
	queue3  = Gst.ElementFactory.make("queue","queue3")
	queue4  = Gst.ElementFactory.make("queue","queue4")
	queue5  = Gst.ElementFactory.make("queue","queue5")
	queue6  = Gst.ElementFactory.make("queue","queue6")
	queue7  = Gst.ElementFactory.make("queue","queue7")
	queue8  = Gst.ElementFactory.make("queue","queue8")
	queue9  = Gst.ElementFactory.make("queue","queue9")
	queue10 = Gst.ElementFactory.make("queue","queue10")

	guint output_type = 2

	#if (isYAML)
	#	output_type = ds_parse_group_type(argv[1], "output")
	#else
	#	output_type = atoi(argv[2])
	if (isYAML):
		output_type = ds_parse_group_type(argv[1], "output")
	else:
		output_type = arg_sink_mode

#	if (output_type == 1)
#		sink = gst_element_factory_make ("filesink", "nvvideo-renderer")
#	else if (output_type == 2)
#		sink = gst_element_factory_make ("fakesink", "fake-renderer")
#	else if (output_type == 3) {
##ifdef PLATFORM_TEGRA
#		transform = gst_element_factory_make ("nvegltransform", "nvegltransform")
#		if(!transform) {
#			g_printerr ("nvegltransform element could not be created. Exiting.\n")
#			return -1
#		}
##endif
#		sink = gst_element_factory_make ("nveglglessink", "nvvideo-renderer")
#	}
	if (output_type == 1)
		sink = gst_element_factory_make ("filesink", "nvvideo-renderer")
	else if (output_type == 2)
		sink = gst_element_factory_make ("fakesink", "fake-renderer")
	else if (output_type == 3) {
#ifdef PLATFORM_TEGRA
		transform = gst_element_factory_make ("nvegltransform", "nvegltransform")
		if(!transform) {
			g_printerr ("nvegltransform element could not be created. Exiting.\n")
			return -1
		}
#endif
		sink = gst_element_factory_make ("nveglglessink", "nvvideo-renderer")
	}

	if (!primary_detector || !secondary_detector || !nvvidconv
			|| !nvosd || !sink  || !capfilt || !nvh264enc) {
		g_printerr ("One element could not be created. Exiting.\n")
		return -1
	}

	g_object_set (G_OBJECT (streammux), "width", MUXER_OUTPUT_WIDTH, "height",
			MUXER_OUTPUT_HEIGHT, "batch-size", src_cnt,
			"batched-push-timeout", MUXER_BATCH_TIMEOUT_USEC, NULL)

	tiler_rows = (guint) sqrt (src_cnt)
	tiler_columns = (guint) ceil (1.0 * src_cnt / tiler_rows)
	g_object_set (G_OBJECT (nvtile), "rows", tiler_rows, "columns",
			tiler_columns, "width", 1280, "height", 720, NULL)

	g_object_set (G_OBJECT (nvdsanalytics), "config-file",
			"config_nvdsanalytics.txt", NULL)

	/* Set the config files for the two detectors and one classifier. The PGIE
	 * detects the cars. The first SGIE detects car plates from the cars and the
	 * second SGIE classifies the caracters in the car plate to identify the car
	 * plate string. */
	if (isYAML) {
		if(!use_nvinfer_server){
				nvds_parse_gie (primary_detector, argv[1], "primary-gie")
				nvds_parse_gie (secondary_detector, argv[1], "secondary-gie-0")
				nvds_parse_gie (secondary_classifier, argv[1], "secondary-gie-1")
		} else {
				car_mode = ds_parse_group_car_mode(argv[1], "triton")
				get_triton_yml(car_mode, use_triton_grpc, pgie_cfg_file_path, lpd_cfg_file_path, lpr_cfg_file_path, 256)
				g_object_set (G_OBJECT (primary_detector), "config-file-path", pgie_cfg_file_path, "unique-id",
					PRIMARY_DETECTOR_UID, "batch-size", 1, NULL)
				g_object_set (G_OBJECT (secondary_detector), "config-file-path", lpd_cfg_file_path, "unique-id",
					SECONDARY_DETECTOR_UID, "process-mode", 2, NULL)
				g_object_set (G_OBJECT (secondary_classifier), "config-file-path", lpr_cfg_file_path, "unique-id",
					SECONDARY_CLASSIFIER_UID, "process-mode", 2, NULL)
		}
	} else {
		if(!use_nvinfer_server){
				g_object_set (G_OBJECT (primary_detector), "config-file-path",
					"trafficamnet_config.txt",
					"unique-id", PRIMARY_DETECTOR_UID, NULL)

				if (atoi(argv[1]) == 1) {
					g_object_set (G_OBJECT (secondary_detector), "config-file-path",
						NVINFER_LDP_US_CFG, "unique-id",
						SECONDARY_DETECTOR_UID, "process-mode", 2, NULL)
					g_object_set (G_OBJECT (secondary_classifier), "config-file-path",
						"lpr_config_sgie_us.txt", "unique-id", SECONDARY_CLASSIFIER_UID,
						"process-mode", 2, NULL)
				} else if (atoi(argv[1]) == 2) {
					g_object_set (G_OBJECT (secondary_detector), "config-file-path",
						NVINFER_LPD_CH_CFG, "unique-id",
						SECONDARY_DETECTOR_UID, "process-mode", 2, NULL)
					g_object_set (G_OBJECT (secondary_classifier), "config-file-path",
						"lpr_config_sgie_ch.txt", "unique-id", SECONDARY_CLASSIFIER_UID,
						"process-mode", 2, NULL)
				}
		} else{
				car_mode = atoi(argv[1])
				get_triton_yml(car_mode, use_triton_grpc, pgie_cfg_file_path, lpd_cfg_file_path, lpr_cfg_file_path, 256)
				g_object_set (G_OBJECT (primary_detector), "config-file-path", pgie_cfg_file_path,
							"unique-id", PRIMARY_DETECTOR_UID,"batch-size", 1, NULL)
					g_object_set (G_OBJECT (secondary_detector), "config-file-path",
							lpd_cfg_file_path, "unique-id",
							SECONDARY_DETECTOR_UID, NULL)
					g_object_set (G_OBJECT (secondary_classifier), "config-file-path",
							lpr_cfg_file_path, "unique-id", SECONDARY_CLASSIFIER_UID, NULL)
		}
	}

"""
	if (isYAML) {
			nvds_parse_tracker(tracker, argv[1], "tracker")
	} else {
		char name[300]
		snprintf(name, 300, "lpr_sample_tracker_config.txt")
		if (!set_tracker_properties(tracker, name)) {
			g_printerr ("Failed to set tracker1 properties. Exiting.\n")
			return -1
		}
	}
"""
	if (isYAML):
			pyds.nvds_parse_tracker(tracker, argv[1], "tracker")
	else:
		config_file_name = "lpr_sample_tracker_config.txt"
		if (not set_tracker_properties(tracker, config_file_name)):
			print(f"Failed to set tracker1 properties. Exiting.\n")
			return -1


	caps =
			gst_caps_new_simple ("video/x-raw", "format", G_TYPE_STRING, "I420", NULL)
	feature = gst_caps_features_new ("memory:NVMM", NULL)
	gst_caps_set_features (caps, 0, feature)
	g_object_set (G_OBJECT (capfilt), "caps", caps, NULL)

	/* we add a bus message handler */
	bus = gst_pipeline_get_bus (GST_PIPELINE (pipeline))
	bus_watch_id = gst_bus_add_watch (bus, bus_call, loop)
	gst_object_unref (bus)

	/* Set up the pipeline */
	/* we add all elements into the pipeline */
	gst_bin_add_many (GST_BIN (pipeline), primary_detector, secondary_detector,
			tracker, nvdsanalytics, queue1, queue2, queue3, queue4, queue5, queue6,
			queue7, queue8, secondary_classifier, nvvidconv, nvosd, nvtile, sink,
			NULL)
	if (isYAML) {
			g_print("set analy config\n")
			if (!ds_parse_file_name(argv[1], "analytics-config"))
					g_object_set (G_OBJECT (nvdsanalytics), "enable", FALSE, NULL)
	} else {
		if (atoi(argv[3]) == 0) {
			g_object_set (G_OBJECT (nvdsanalytics), "enable", FALSE, NULL)
		} else {
			g_object_set (G_OBJECT (nvdsanalytics), "enable", TRUE, NULL)
		}
	}
	if (!gst_element_link_many (streammux, queue1, primary_detector, queue2,
			tracker, queue3, nvdsanalytics, queue4, secondary_detector, queue5,
			secondary_classifier, queue6, nvtile, queue7, nvvidconv, queue8,
			nvosd, NULL)) {
			g_printerr ("Inferring and tracking elements link failure.\n")
			return -1
	}

	if (output_type == 1) {
		gchar *filepath = NULL
		if (isYAML) {
				GString * output_file =
				  ds_parse_file_name(argv[1], "output")
				if (isH264)
				    filepath = g_strconcat(output_file->str,".264",NULL)
				else
				    filepath = g_strconcat(output_file->str,".265",NULL)
				ds_parse_enc_config(nvh264enc, argv[1], "output")
		} else {
				filepath = g_strconcat(argv[argc-1],".264",NULL)
		}
		if(use_nvinfer_server){
				g_object_set (G_OBJECT (sink), "async", FALSE, NULL)
				g_object_set (G_OBJECT (sink), "sync", TRUE, NULL)
		}
		g_object_set (G_OBJECT (sink), "location", filepath, NULL)
		gst_bin_add_many (GST_BIN (pipeline), nvvidconv1, nvh264enc, capfilt, 
				queue9, queue10, NULL)

		if (!gst_element_link_many (nvosd, queue9, nvvidconv1, capfilt, queue10,
				   nvh264enc, sink, NULL)) {
			g_printerr ("OSD and sink elements link failure.\n")
			return -1
		}
	} else if (output_type == 2) {
		g_object_set (G_OBJECT (sink), "sync", 0, "async", false,NULL)
		if (!gst_element_link (nvosd, sink)) {
			g_printerr ("OSD and sink elements link failure.\n")
			return -1
		}
	} else if (output_type == 3) {
#ifdef PLATFORM_TEGRA
		gst_bin_add_many (GST_BIN (pipeline), transform, queue9, NULL)
		if (!gst_element_link_many (nvosd, queue9, transform, sink, NULL)) {
			g_printerr ("OSD and sink elements link failure.\n")
			return -1
		}
#else
		gst_bin_add (GST_BIN (pipeline), queue9)
		if (!gst_element_link_many (nvosd, queue9, sink, NULL)) {
			g_printerr ("OSD and sink elements link failure.\n")
			return -1
		}
#endif
	}

	/* Lets add probe to get informed of the meta data generated, we add probe to
	 * the sink pad of the osd element, since by that time, the buffer would have
	 * had got all the metadata. */
	osd_sink_pad = gst_element_get_static_pad (nvosd, "sink")
	if (!osd_sink_pad)
		g_print ("Unable to get sink pad\n")
	else
		gst_pad_add_probe (osd_sink_pad, GST_PAD_PROBE_TYPE_BUFFER,
				osd_sink_pad_buffer_probe, &perf_measure, NULL)
	gst_object_unref (osd_sink_pad)

	osd_sink_pad = gst_element_get_static_pad (nvdsanalytics, "src")
	if (!osd_sink_pad)
		g_print ("Unable to get src pad\n")
	else
		gst_pad_add_probe (osd_sink_pad, GST_PAD_PROBE_TYPE_BUFFER,
				nvdsanalytics_src_pad_buffer_probe, NULL, NULL)
	gst_object_unref (osd_sink_pad)

	/* Set the pipeline to "playing" state */
	g_print ("Now playing: %s\n", argv[1])
	gst_element_set_state (pipeline, GST_STATE_PLAYING)

	/* Wait till pipeline encounters an error or EOS */
	g_print ("Running...\n")
	g_main_loop_run (loop)

	/* Out of the main loop, clean up nicely */
	g_print ("Returned, stopping playback\n")
	gst_element_set_state (pipeline, GST_STATE_NULL)
	
	g_print ("Average fps %f\n",
			((perf_measure.count-1)*src_cnt*1000000.0)/perf_measure.total_time)
	g_print ("Totally %d plates are inferred\n",total_plate_number)
	g_print ("Deleting pipeline\n")
	gst_object_unref (GST_OBJECT (pipeline))
	g_source_remove (bus_watch_id)
	g_main_loop_unref (loop)
	return 0


if __name__ == '__main__':
	sys.exit(main(sys.argv))
