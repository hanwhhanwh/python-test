#!/usr/bin/env python3
# reference: https://github.com/gkralik/python-gst-tutorial/blob/master/basic-tutorial-3.py

import sys
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst

# https://gstreamer.freedesktop.org/documentation/tutorials/basic/dynamic-pipelines.html


class Player(object):

	def __init__(self):
		# initialize GStreamer
		Gst.init(None)

		# create the elements
		self.source = Gst.ElementFactory.make("uridecodebin", "source")
		self.convert = Gst.ElementFactory.make("audioconvert", "convert")
		self.sink = Gst.ElementFactory.make("autoaudiosink", "sink")

		# create empty pipeline
		self.pipeline = Gst.Pipeline.new("test-pipeline")

		if not self.pipeline or not self.source or not self.convert or not self.sink:
			print("ERROR: Could not create all elements")
			sys.exit(1)

		# build the pipeline. we are NOT linking the source at this point.
		# will do it later
		self.pipeline.add(self.source, self.convert, self.sink)
		if not self.convert.link(self.sink):
			print("ERROR: Could not link 'convert' to 'sink'")
			sys.exit(1)

		# set the URI to play
		self.source.set_property(
			"uri", "http://docs.gstreamer.com/media/sintel_trailer-480p.webm")

		# connect to the pad-added signal
		self.source.connect("pad-added", self.on_pad_added)

		# start playing
		ret = self.pipeline.set_state(Gst.State.PLAYING)
		if ret == Gst.StateChangeReturn.FAILURE:
			print("ERROR: Unable to set the pipeline to the playing state")
			sys.exit(1)

		# listen to the bus
		bus = self.pipeline.get_bus()
		terminate = False
		while True:
			msg = bus.timed_pop_filtered(
				Gst.CLOCK_TIME_NONE,
				Gst.MessageType.STATE_CHANGED | Gst.MessageType.EOS | Gst.MessageType.ERROR)

			if not msg:
				continue

			t = msg.type
			if t == Gst.MessageType.ERROR:
				err, dbg = msg.parse_error()
				print("ERROR:", msg.src.get_name(), " ", err.message)
				if dbg:
					print("debugging info:", dbg)
				terminate = True
			elif t == Gst.MessageType.EOS:
				print("End-Of-Stream reached")
				terminate = True
			elif t == Gst.MessageType.STATE_CHANGED:
				# we are only interested in STATE_CHANGED messages from
				# the pipeline
				if msg.src == self.pipeline:
					old_state, new_state, pending_state = msg.parse_state_changed()
					print("Pipeline state changed from {0:s} to {1:s}".format(
						Gst.Element.state_get_name(old_state),
						Gst.Element.state_get_name(new_state)))
			else:
				# should not get here
				print("ERROR: Unexpected message received")
				break

			if terminate:
				break

		self.pipeline.set_state(Gst.State.NULL)

	# handler for the pad-added signal
	def on_pad_added(self, src, new_pad):
		sink_pad = self.convert.get_static_pad("sink")
		print(
			"Received new pad '{0:s}' from '{1:s}'".format(
				new_pad.get_name(),
				src.get_name()))

		# if our converter is already linked, we have nothing to do here
		if(sink_pad.is_linked()):
			print("We are already linked. Ignoring.")
			return

		# check the new pad's type
		new_pad_caps = new_pad.get_current_caps()
		new_pad_struct = new_pad_caps.get_structure(0)
		new_pad_type = new_pad_struct.get_name()

		if not new_pad_type.startswith("audio/x-raw"):
			print("It has type '{0:s}' which is not raw audio. Ignoring.".format(
				new_pad_type))
			return

		# attempt the link
		ret = new_pad.link(sink_pad)
		if not ret == Gst.PadLinkReturn.OK:
			print("Type is '{0:s}}' but link failed".format(new_pad_type))
		else:
			print("Link succeeded (type '{0:s}')".format(new_pad_type))

		return

if __name__ == '__main__':
	p = Player()