# to rknn converter (Python-3.8 tested)
# date	2023-02-15
# author	hbesthee@naver.com

from argparse import ArgumentParser
from os import path
from rknn.api import RKNN

DATASET = './dataset.txt'
QUANTIZE_ON = True


def make_parser():
	""" 실행 파라미터 분석 """
	parser = ArgumentParser("onnx2rknn-converter")

	#setting args
	parser.add_argument(
		"-d", "--device"
		, type = str
		, default = "rk3588"
		, help = "target device : rk3588, rk3566, ..."
	)
	parser.add_argument(
		"-i", "--model_path"
		, type = str
		, default = None
		, required = True
		, help = "변환할 원본 모델(*.pt, *.onnx, *.weights 등)의 경로를 입력해주세요."
	)
	parser.add_argument(
		"-o","--rknn_path"
		, type = str
		, default = None
		, required = True
		, help = "변환하여 저장될 rknn 모델의 경로를 입력해주세요."
	)
	parser.add_argument(
		"-v", "--verbose"
		, action = 'count'
		, default = 0
		, help="Make the operation more talkative"
	)
	parser.add_argument(
		"-V", "--version"
		, action = 'store_true'
		, help="Show version number and quit"
	)

	return parser


def convert2rknn(args):
	# Create RKNN object
	rknn = RKNN(args.verbose > 0)

	if (args.version):
		sdk_version = rknn.get_sdk_version()
		print(sdk_version)
		rknn.release()
		return

	# pre-process config
	if (args.verbose > 0):
		print('Config model')
	rknn.config(mean_values = [[0, 0, 0]], std_values = [[255, 255, 255]]
		, target_platform = args.device)
	if (args.verbose > 0):
		print('--> Config done')

	# Load source model
	if (args.verbose > 0):
		print('Loading model...')

	filepath = path.splitext(args.model_path)[0]
	ext = path.splitext(args.model_path)[1]
	if (ext == ''):
		print('model file name fail. extension not found! (*.pt, *.onnx, *.cfg, *pb, *.tflite, *.prototxt )')
		exit(ret)

	ret = 0
	if (ext == '.onnx'):
		ret = rknn.load_onnx(model = args.model_path)
	elif (ext == '.cfg'):
		ret = rknn.load_darknet(model = args.model_path, weight = f'{filepath}.weights')
	elif (ext == '.tflite'):
		ret = rknn.load_tflite(model = args.model_path)
	elif (ext == '.pt'):
		ret = rknn.load_pytorch(model = args.model_path)
	elif (ext == '.pb'):
		ret = rknn.load_tensorflow(model = args.model_path)
	elif (ext == '.prototxt'):
		ret = rknn.load_caffe(model = args.model_path, blobs = f'{filepath}.caffemodel')
	if ret != 0:
		print(f'Load model failed! result = {ret}')
		exit(ret)
	if (args.verbose > 0):
		print('--> Loading done')

	# Build model
	if (args.verbose > 0):
		print('Building model')
	ret = rknn.build(do_quantization = QUANTIZE_ON, dataset = DATASET)
	if ret != 0:
		print('Build model failed!')
		exit(ret)
	if (args.verbose > 0):
		print('--> Building done')

	# Export RKNN model
	if (args.verbose > 0):
		print('Export rknn model')
	ret = rknn.export_rknn(args.rknn_path)
	if ret != 0:
		print('Export rknn model failed!')
		exit(ret)
	if (args.verbose > 0):
		print('--> Export done')

	rknn.release()


if __name__ == '__main__':
	args = make_parser().parse_args()

	convert2rknn(args)

