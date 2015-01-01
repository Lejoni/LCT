#! /usr/bin/env python3
# LCT2

import sys, re, os, string, logging
try:
	os.chdir(os.path.expanduser("~/.LCT"))
except:
	os.makedirs(os.path.expanduser("~/.LCT"))
	os.chdir(os.path.expanduser("~/.LCT"))
logging.basicConfig(filename=os.path.expanduser('~/.LCT/LCT2.log'),level=logging.DEBUG)
from time import sleep
from collections import OrderedDict
from threading import Thread, Event
from os.path import exists
from xml.etree.ElementTree import ElementTree, fromstring
from urllib.request import urlretrieve as DownLoad

try:
	from gi.repository import Gtk, Gdk, GObject
except:
	logging.critical("CRITICAL: PyGI is not available. Please install.\n")

class Handler:
	def onDeleteWindow(self, *args):
		Gtk.main_quit(*args)
	

class LCTWindow(Gtk.Window):
	def __init__(self):
		builder = Gtk.Builder()
		builder.add_from_file("LCT.glade")
		builder.connect_signals(Handler())
		
		MainWindow = builder.get_object("MainWindow")
		MainWindow.show_all()
		
		Gtk.main()

if __name__ == "__main__":
	#Startup main Window
	LCTWindow()

