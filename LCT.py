#! /usr/bin/env python3
# LCT2
import sys, re, os, string, logging
logging.basicConfig(filename=os.path.expanduser('~/LCT.log'),level=logging.DEBUG)
from time import sleep
from collections import OrderedDict
from threading import Thread, Event
from os.path import exists
from xml.etree.ElementTree import ElementTree, fromstring
from urllib.request import urlretrieve as DownLoad

#GUI imports need PyGI / GTK+
try:
	from gi.repository import Gtk, Gdk, GObject
except:
	logging.critical("CRITICAL: PyGI is not available. Please install.\n")

class Parser(Thread):
	def GetYOUName(self, name):
		name = name.replace('YOUR',  self.YOU)
		name = name.replace('YOU',  self.YOU)
		name = name.replace('\'s',  '')
		name = name.replace('\'',  '')
		return name
	
	def CheckFiles(self, path): #Check log files, return last modifyed.
		filelist = os.listdir(path)
		filedict = dict({})
		for file in filelist:
			filedict[file] = os.stat(path+'/'+file).st_mtime
		sortdict = OrderedDict(sorted(filedict.items(), key=lambda t: t[1],  reverse=True))
		last_mod_file = sortdict.popitem(last=False)
		print(last_mod_file[0] + " loaded!")
		return path + '/' + last_mod_file[0]
		
	def ScanLogFile(self): #Scan the Logfile for Current zone.
		currentzone = "Unknown"
		
		while True:
			line = self.logfile.readline()
			#GObject.idle_add(self.Statusbar.pulse)
			if line == "":
				return currentzone
			elif self.checkforunixtime.search(line):
				splited = self.checkforunixtime.split(line)
				splited2 = self.checkfortimestamp.split(splited[1])
				words = splited2[1].split(" ")
				if len(words) > 2 and words[2] == 'entered':
					currentzone = ""
					zone = words[3:len(words)]
					for word in zone:
						currentzone += word+" "
	
	def AddTrigger(self, trigger):
		who = trigger[0]
		trigger = self.ListToString(trigger[1:]).replace('\n',  '')
		self.Triggers[who] = trigger
		logging.info("Added trigger: "+trigger+" for: "+who)
		logging.info(self.Triggers)
		return
	
	def AddDamage(self,  words):
		player = self.GetYOUName(words[0])
		self.StopFightTime = self.timestamp
		damage = words[words.index('damage.\n')-2]
		damagetype = words[words.index('damage.\n')-1]
		logging.info(str(words))
		self.TotalPlayerDamage[player] += int(damage)
		self.TotalPlayerDamage['Group'] += int(damage)
		logging.info(player+" hit for: "+str(damage)+" "+damagetype+" Now Total damage: "+str(self.TotalPlayerDamage[player]))
	
	def StopDPS(self):
		time = int(self.StopFightTime) - int(self.StartFightTime)
		logging.info("Stopping Fight Parse after 6 second idle")
		clipboardtext = ""
		sortdict = OrderedDict(sorted(self.TotalPlayerDamage.items(), key=lambda t: t[1],  reverse=True))
		for player in sortdict:
			logging.info(player)
			logging.info(sortdict[player])
			if sortdict[player]:
				if time > 0:
					dps = sortdict[player]/time
				else:
					dps = sortdict[player]
				logging.info(str(dps))
				clipboardtext += player+": "+str(sortdict[player])+" / "+str(int(dps))+"\n"
			else:
				logging.info(player+" did no damage.")
		self.CopyToClipBoard(clipboardtext)
		GObject.idle_add(self.Statusbar.set_text, "Fight ended.")
		try:
			GObject.idle_add(self.StatusIcon.set_from_file, "LCT-running.png")
		except:
			pass
				
		for player in self.TotalPlayerDamage:
			self.TotalPlayerDamage[player] = 0
			logging.info("TotalPlayerDamage dict is reset: "+str(self.TotalPlayerDamage))

	def ParseDPS(self):
		logging.info("Starting Fight Parse")
		GObject.idle_add(self.Statusbar.set_text, "Fighting!")
		try:
			GObject.idle_add(self.StatusIcon.set_from_file, "LCT-fighting.png")
		except:
			pass
		
		stoptimer = 0
		while True:
			line = self.logfile.readline()
			if line == "":
				if stoptimer > 5:
					self.StopDPS()
					return
				else:
					print("Sleeping...")
					stoptimer += 1
					sleep(1.0)
			elif self.checkforunixtime.search(line):
				if self.checkforweakness.search(line):
					os.system('espeak \"weakness\"')
					logging.info(str(line))
				self.timestamp = self.checkforunixtime.findall(line)[0].replace('(',  '').replace(')',  '')
				splited = self.checkforunixtime.split(line)
				splited2 = self.checkfortimestamp.split(splited[1])
				words = splited2[1].split(" ")
				if words[0] == 'Unknown' and words[1] == 'command:':
					if words[2].replace('\'',  '') == 'lct':
						command = words[3].replace('\'',  '').replace('\n',  '')
						logging.info("LCT Command: "+command)
					if command == 'stopdps':
						self.StopDPS()
						return
					else:
						logging.info("Unknown command")
				elif words.count('fail'):
					logging.info("Miss!")
				elif words.count('fails'):
					logging.info("Miss!")
				elif self.GetYOUName(words[0]) in self.TotalPlayerDamage and words[1] == 'are' and words[2] == 'hit':
					logging.info("Environmental damage on: "+self.GetYOUName(words[0]))
				# Autoattacks
				elif self.GetYOUName(words[0]) in self.TotalPlayerDamage and words[-1] == 'damage.\n':
					logging.info(words[0]+ " did something:")
					if words.count('hit') or words.count('hits') or words.count('attack') or words.count('attacks') or words.count('flurry') or words.count('flurries'):
						logging.info(words[0]+ " it was a autoattack.")
						self.AddDamage(words)
						stoptimer = 0
				#My Spells
				elif self.GetYOUName(words[0]) in self.TotalPlayerDamage and words[-1] == 'damage.\n':
					logging.info(words[0]+ " did something:")
					if words.count('hit') or words.count('hits') or words.count('attack') or words.count('attacks') or words.count('flurry') or words.count('flurries'):
						logging.info(words[0]+ " it was a spell.")
						self.AddDamage(words)
						stoptimer = 0
				#Other's spells.
				elif self.GetYOUName(words[0]) in self.TotalPlayerDamage and words[-1] == 'damage.\n':
					logging.info(words[0]+ " did something:")
					if words.count('hit') or words.count('hits') or words.count('attack') or words.count('attacks') or words.count('flurry') or words.count('flurries'):
						logging.info(words[0]+ " it was a spell.")
						self.AddDamage(words)
						stoptimer = 0
                
				#Check for triggers.
				if words[0] == '\\aPC':
					name = words[2].split(':')[0]
					if name in self.Triggers:
						message = self.ListToString(words[3:]).replace('\"',  '')
						message = message.lower()
						logging.info("Name for Trigger match: "+name+" is saying: "+str(message))
						[event,  speak] = self.Triggers[name].split('=')
						event = event.lower()
						if event in message:
							os.system('espeak \"'+speak+'\"')
						else:
							logging.info(event+" not in: "+str(message))
			else:
				logging.info("UNHANDLED log line: "+line)
	def ListToString(self, list):
		retstring = ""
		for word in list:
			retstring += word+" "
		retstring.rstrip()
		return retstring
	
	def __init__(self,  path, ctc, statusbar, statusicon):
		Thread.__init__(self)
		
		#CheckFiles test
		filepath = self.CheckFiles(path)
		
		self.stoprequest = Event()
		logging.info("Opening file: "+filepath)
		self.logfile = open(filepath,  "r")
		self.parsing = 1
		(directory,  filename) = os.path.split(filepath)
		
		#CopyToClipBoard
		self.CopyToClipBoard = ctc
		
		#Statusbar
		self.Statusbar = statusbar
		
		#StatusIcon
		self.StatusIcon = statusicon
		try:
			GObject.idle_add(self.StatusIcon.set_from_file, "LCT-running.png")
		except:
			pass
		
		#Variables
		self.StartFightTime = 0
		self.StopFightTime = 0
		self.CurrentZone = None
		self.YOU = filename.split('_')[1].replace('.txt',  '')
		logging.info("YOU = "+self.YOU)
		GObject.idle_add(self.Statusbar.set_text, 'Playing as: '+self.YOU)
			
		#regex programs.
		logging.info("Compiling regex programs")
		self.checkforunixtime = re.compile("^[(]\d{10}[)]")
		self.checkfortimestamp = re.compile("^[[].+\d{4}[]]\s")
		self.checkforweakness = re.compile(r"FF9900You can see a weakness in your enemy*")
		
		#Dictionarys
		self.TotalPlayerDamage = dict({'Group': 0,  self.YOU: 0})
		self.Triggers = dict({})
		#Scan Logfile for Current zone aswell as ittirate it to EOF.
		self.CurrentZone = self.ScanLogFile()
		logging.info("Scan Logfile complete. Current zone: "+self.CurrentZone)
		
		
	def stop(self):
		logging.info("Stopping Parser")
		self.stoprequest.set()
		self.alive = False
		self.join()
	
	def run(self):
		self.alive = True
		
		while not self.stoprequest.isSet():
			line = self.logfile.readline()
            
			if line == "":
				#print("sleeping...")
				sleep(1.0)
			
			elif self.checkforunixtime.search(line):
				self.timestamp = self.checkforunixtime.findall(line)[0].replace('(',  '').replace(')',  '')
				splited = self.checkforunixtime.split(line)
				splited2 = self.checkfortimestamp.split(splited[1])
				words = splited2[1].split(" ")
				#print(str(words))
				if words[0] == 'Unknown' and words[1] == 'command:':
					if words[2].replace('\'',  '') == 'lct':
						command = words[3].replace('\'',  '').replace('\n',  '')
						#for word in commandline:
						#   command += word.replace('\'',  '')
						logging.info("LCT Command: "+command+".")
						if command == 'startdps':
							self.StartFightTime = self.timestamp
							self.ParseDPS()
						elif command == 'onlogoff':
							pass
						elif command == 'addpc':
							player = words[4].replace('\n',  '').replace('\'',  '')
							logging.info("Adding Player: "+player)
							self.TotalPlayerDamage[player] = 0
							logging.info(self.TotalPlayerDamage)
						elif command == 'rmpc':
							pass
						elif command == 'trigger':
							self.AddTrigger(words[4:])
						elif command == 'tesp':
							os.system('espeak \"Testing ESpeak\"')
						else:
							logging.info("Unknown command: /lct "+command)
				elif len(words) > 1 and words[1] == 'Lvl' and len(words) > 3:
					player = words[0]
					logging.info("Adding Player: "+player)
					self.TotalPlayerDamage[player] = 0
					logging.info(self.TotalPlayerDamage)
				#Check if a fight has started.
				elif self.GetYOUName(words[0]) in self.TotalPlayerDamage and words.count('fail'):
					logging.info("Miss!")
					self.StartFightTime = self.timestamp
					self.ParseDPS()
				elif self.GetYOUName(words[0]) in self.TotalPlayerDamage and words.count('fails'):
					logging.info("Miss!")
					self.StartFightTime = self.timestamp
					self.ParseDPS()
				elif self.GetYOUName(words[0]) in self.TotalPlayerDamage and words.count('fail'):
					logging.info("Miss!")
					self.StartFightTime = self.timestamp
					self.ParseDPS()
				elif self.GetYOUName(words[0]) in self.TotalPlayerDamage and words.count('fails'):
					logging.info("Miss!")
					self.StartFightTime = self.timestamp
					self.ParseDPS()
				elif self.GetYOUName(words[0]) in self.TotalPlayerDamage and words[1] == 'are' and words[2] == 'hit':
					logging.info("Environmental damage on: "+self.GetYOUName(words[0]))
				# Autoattacks
				elif self.GetYOUName(words[0]) in self.TotalPlayerDamage and words[-1] == 'damage.\n':
					logging.info(words[0]+ " it was a autoattack.")
					if words.count('hit'):
						self.AddDamage(words)
						self.StartFightTime = self.timestamp
						self.ParseDPS()
					elif words.count('hits'):
						self.AddDamage(words)
						self.StartFightTime = self.timestamp
						self.ParseDPS()
					elif words.count('attack'):
						self.AddDamage(words)
						self.StartFightTime = self.timestamp
						self.ParseDPS()
					elif words.count('attacks'):
						self.AddDamage(words)
						self.StartFightTime = self.timestamp
						self.ParseDPS()
					elif words.count('flurry'):
						self.AddDamage(words)
						self.StartFightTime = self.timestamp
						self.ParseDPS()
					elif words.count('flurries'):
						self.AddDamage(words)
						self.StartFightTime = self.timestamp
						self.ParseDPS()
				
				#My Spells
				elif self.GetYOUName(words[0]) in self.TotalPlayerDamage and words[-1] == 'damage.\n':
					if words.count('hit'):
						self.AddDamage(words)
						self.StartFightTime = self.timestamp
						self.ParseDPS()
					elif words.count('hits'):
						self.AddDamage(words)
						self.StartFightTime = self.timestamp
						self.ParseDPS()
					elif words.count('attack'):
						self.AddDamage(words)
						self.StartFightTime = self.timestamp
						self.ParseDPS()
					elif  words.count('attacks'):
						self.AddDamage(words)
						self.StartFightTime = self.timestamp
						self.ParseDPS()
					elif words.count('flurry'):
						self.AddDamage(words)
						self.StartFightTime = self.timestamp
						self.ParseDPS()
					elif words.count('flurries'):
						self.AddDamage(words)
						self.StartFightTime = self.timestamp
						self.ParseDPS()
				
				#Other's spells.
				elif self.GetYOUName(words[0]) in self.TotalPlayerDamage and words[-1] == 'damage.\n':
					if words.count('hit'):
						self.AddDamage(words)
						self.StartFightTime = self.timestamp
						self.ParseDPS()
					elif words.count('hits'):
						self.AddDamage(words)
						self.StartFightTime = self.timestamp
						self.ParseDPS()
					elif words.count('attack'):
						self.AddDamage(words)
						self.StartFightTime = self.timestamp
						self.ParseDPS()
					elif  words.count('attacks'):
						self.AddDamage(words)
						self.StartFightTime = self.timestamp
						self.ParseDPS()
					elif words.count('flurry'):
						self.AddDamage(words)
						self.StartFightTime = self.timestamp
						self.ParseDPS()
					elif words.count('flurries'):
						self.AddDamage(words)
						self.StartFightTime = self.timestamp
						self.ParseDPS()
				
				#Check for new zone.
				elif len(words) > 3 and words[2] == 'entered':
					currentzone = ""
					zone = words[3:len(words)]
					for word in zone:
						currentzone += word+" "
					self.CurrentZone = currentzone
					logging.info("Current zone: "+currentzone)
				#Check for triggers.
				if words[0] == '\\aPC':
					name = words[2].split(':')[0]
					if name in self.Triggers:
						message = self.ListToString(words[3:]).replace('\"',  '')
						message = message.lower()
						logging.info("Name for Trigger match: "+name+" is saying: "+str(message))
						[event,  speak] = self.Triggers[name].split('=')
						event = event.lower()
						if event in message:
							os.system('espeak \"'+speak+'\"')
						else:
							logging.info(event+" not in: "+str(message))
                
			else:
				logging.info("UNHANDLED log line: "+str(line))

class LCTWindow(Gtk.Window):
	def __init__(self):
		self.parserrunning = False
		self.LogFolder = ""
		self.settings = ElementTree()
		self.LoadSettings()
		Gtk.Window.__init__(self, title="Lazy Combat Tracker")
		self.set_keep_above(True)
		self.connect("delete-event", Gtk.main_quit)
		self.VBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
		self.add(self.VBox)
		self.HBox = Gtk.Box(spacing=6)
		if self.LogFolder == "":
			self.LogLable = Gtk.Label("No log file selected!")
		else:
			self.LogLable = Gtk.Label(self.GetServer())
		
		self.HBox.pack_start(self.LogLable, True, True, 0)
		self.button = Gtk.Button(label="Change")
		self.button.connect("clicked", self.on_file_select)
		self.HBox.pack_start(self.button, True, True, 0)
		self.runButton = Gtk.Button(label="Start Parser!")
		self.VBox.pack_start(self.HBox, True, True, 0)
		self.runButton.connect("clicked", self.toggle_parser)
		self.VBox.pack_start(self.runButton, True, True, 0)
		self.Statusbar = Gtk.ProgressBar()
		self.Statusbar.set_text("Please select a log file directory.")
		self.Statusbar.set_show_text(True)
		self.Statusbar.set_pulse_step(0.01)
		self.VBox.pack_start(self.Statusbar, True, True, 0)
		
		#StatusIcon
		self.StatusIcon = Gtk.StatusIcon()
		try:
			self.StatusIcon.set_from_file("LCT.png")
			self.StatusIcon.set_visible(True)
		except:
			pass
		
	def GetServer(self):
		server = self.LogFolder.split('/')
		server = server[len(server)-1]
		return server
	
	def toggle_parser(self, widget):
		if (self.parserrunning):
			self.Statusbar.set_text("Stopping parser...")
			Gtk.main_iteration()
			self.parser_thread.stop()
			self.parserrunning = False
			self.Statusbar.set_text("Done!")
			self.Statusbar.set_fraction(0.0)
			try:
				self.StatusIcon.set_from_file("LCT.png")
			except:
				pass
			
			self.runButton.set_label("Start Parser!")
		else:
			self.Statusbar.set_text("Scanning log file, please wait...")
			Gtk.main_iteration()
			self.parser_thread = Parser(self.LogFolder, self.CopyToClipBoard, self.Statusbar, self.StatusIcon)
			self.parser_thread.name = 0
			self.parser_thread.start()
			self.parserrunning = True
			self.Statusbar.set_text("Parser is running...")
			self.Statusbar.set_fraction(1.0)
			self.runButton.set_label("Stop Parser!")
			
	
	def on_file_select(self, widget):
		dialog = Gtk.FileChooserDialog("Please choose a folder", self,
						Gtk.FileChooserAction.SELECT_FOLDER,
						(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
							"Select", Gtk.ResponseType.OK))
		
		dialog.set_default_size(800, 400)
		response = dialog.run()
		if response == Gtk.ResponseType.OK:
			logging.info("Open clicked")
			logging.info("File selected: " + dialog.get_filename())
			self.LogFolder = dialog.get_filename()
			self.SaveSettings()
			self.LogLable.set_text(self.GetServer())
			self.Statusbar.set_text("Log directory set!")
		elif response == Gtk.ResponseType.CANCEL:
			logging.info("Cancel clicked")
		
		dialog.destroy()	
	
	
	def CopyToClipBoard(self, text):
		self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
		GObject.idle_add(self.clipboard.set_text, text, -1)
	
	def LoadSettings(self):
		try:
			os.chdir(os.path.expanduser("~/.LCT"))
		except:
			os.makedirs(os.path.expanduser("~/.LCT"))
			os.chdir(os.path.expanduser("~/.LCT"))
		try:
			self.settings.parse(os.path.expanduser("~/.LCT/Settings.xml"))
		except:
			file = open(os.path.expanduser("~/.LCT/Settings.xml"), 'w+')
			file.write('<LCT><LOGFOLDER></LOGFOLDER></LCT>')
			file.close()
			self.settings.parse(os.path.expanduser("~/.LCT/Settings.xml"))
		
		if not exists("LCT.png"):
			print("Downloading: LCT.png")
			DownLoad("http://www.lejoni.com/lct/LCT.png", "LCT.png")
		if not exists("LCT-running.png"):
			print("Downloading: LCT-running.png")
			DownLoad("http://www.lejoni.com/lct/LCT-running.png", "LCT-running.png")
		if not exists("LCT-fighting.png"):
			print("Downloading: LCT-fighting.png")
			DownLoad("http://www.lejoni.com/lct/LCT-fighting.png", "LCT-fighting.png")
		
		self.LogFolder = self.settings.findtext("LOGFOLDER")
		
	
	def SaveSettings(self):
		self.settings.find("LOGFOLDER").text = self.LogFolder
		self.settings.write(os.path.expanduser("~/.LCT/Settings.xml"))

if __name__ == "__main__":
	#Startup main Window
	GObject.threads_init()
	rootWindow = LCTWindow()
	rootWindow.show_all()
	Gtk.main()
