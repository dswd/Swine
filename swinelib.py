############################################################################
#    Copyright (C) 2007 by Dennis Schwerdel, Thomas Schmidt                #
#                                                                          #
#                                                                          #
#    This program is free software; you can redistribute it and or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
#                                                                          #
#    This program is distributed in the hope that it will be useful,       #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#    GNU General Public License for more details.                          #
#                                                                          #
#    You should have received a copy of the GNU General Public License     #
#    along with this program; if not, write to the                         #
#    Free Software Foundation, Inc.,                                       #
#    59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             #
############################################################################

import sys, os, shutil, ConfigParser, array, pipes
import shortcutlib
from tarfile import TarFile

VERSION = "0.3 beta"

os.environ['PATH'] += ":" + os.path.dirname(__file__)

SWINE_PATH = os.getenv("HOME") + "/.swine"
SWINE_SLOT_PATH = SWINE_PATH
SWINE_DEFAULT_SLOT_NAME = "DEFAULT"
SWINE_DEFAULT_SLOT_PATH = SWINE_PATH + "/" + SWINE_DEFAULT_SLOT_NAME
SWINE_DEFAULT_SECTION = "__SYSTEM__"
WINE_PATH = os.getenv("HOME") + "/.wine"

BIN = {}


class SwineException(Exception):
	pass

class Shortcut:
	def __init__(self,name,slot,data={}):
		if len(name) == 0:
			raise SwineException ("Shortcut name cannot be empty.")
		self.name = name
		if len(data) == 0:
			self.data = {}
		else:
			self.data = data
		self.slot = slot
	
	def __str__(self):
		return self.name
	
	def save (self):
		# NOTE: Slot.saveConfig needs to be called to make this permanent
		if not self.slot.config.has_section ( self.name ):
			self.slot.config.add_section ( self.name )
		for k, v in self.data.iteritems():
			self.slot.config.set(self.name,k,v)
		
	def delete (self):
		# NOTE: Slot.saveConfig needs to be called to make this permanent
		self.slot.config.remove_section (self.name)
		
	def rename (self, newname):
		# NOTE: Slot.saveConfig needs to be called to make this permanent
		if len(newname) == 0:
			raise SwineException ("Shortcut name cannot be empty.")
		if newname == self.name:
			return None
		self.delete ()
		self.name = newname
		self.save ()
		
	def clone (self, newname):
		# NOTE: Slot.saveConfig needs to be called to make this permanent
		if len(newname) == 0:
			raise SwineException ("Shortcut name cannot be empty.")
		shortcut = Shortcut(newname,self.slot,self.data)
		shortcut.save ()

	def run (self,mode=os.P_NOWAIT):
		return self.slot.run (str2args(self.data['program']),mode,self.data['working_directory'])

	def isDefault (self):
		return ( not self.slot.loadDefaultShortcut() == None ) and self.name == self.slot.loadDefaultShortcut().name
	
	def setDefault (self):
		# NOTE: Slot.saveConfig needs to be called to make this permanent
		self.slot.setDefaultShortcut(self)

	def iconsDir (self):
		if self.data.has_key("iconsdir"):
			return self.slot.getPath() + "/" + self.data["iconsdir"]
		return None

class Slot:
	def __init__(self, name):
		if len(name) == 0:
			raise SwineException ("Slot name cannot be empty.")
		self.name = name
		self.config = None
		self.settings = None
		
	def __str__(self):
		return self.name
		
	def getPath(self):
		return SWINE_SLOT_PATH + "/" + self.name

	def getDrivePath(self, drive):
		drive = drive.lower()
		if len(drive) == 1:
			drive = drive + ":"
		if not len(drive) == 2:
			raise SwineException (drive + " is not a valid drive")
		if not os.path.exists ( self.getPath() + "/dosdevices/" + drive ):
			raise SwineException (drive + " does not exist")
		return self.getPath() + "/dosdevices/" + drive
	
	def getConfigFile(self):
		return SWINE_SLOT_PATH + "/" + self.name + "/swine.ini"

	def loadConfig(self):
		self.config = ConfigParser.ConfigParser()
		self.config.read(self.getConfigFile())
		if not self.config.has_section ( SWINE_DEFAULT_SECTION ):
			self.config.add_section ( SWINE_DEFAULT_SECTION )
		self.settings = dict(self.config.items(SWINE_DEFAULT_SECTION))

	def saveConfig(self):
		# NOTE: This needs to be called after any Shortcut changes to make them permanent
		for k, v in self.settings.iteritems():
			self.config.set(SWINE_DEFAULT_SECTION,k,v)
		self.config.write ( open ( self.getConfigFile(), "w" ) )

	def setWinePrefix(self):
		os.environ['WINEPREFIX'] = self.getPath()

	def setWinePrefixCheck (self):
		if not self.exists():
			raise SwineException ("Slot does not exist: " + self.name)
		self.setWinePrefix()

	def exists (self):
		return os.path.exists ( self.getPath() )
	
	def create (self):
		if self.exists():
			raise SwineException ("Slot already exists: " + self.name)
		self.setWinePrefix()
		os.system (BIN["wineprefixcreate"])
		self.loadConfig()
		self.saveConfig()
	
	def delete (self):
		if self.name == SWINE_DEFAULT_SLOT_NAME:
			raise SwineException ("Default slot cannot be deleted")
		if not self.exists ():
			raise SwineException ("Slot does not exist: " + self.name)
		shutil.rmtree ( self.getPath() )

	def clone (self,newname):
		if len(newname) == 0:
			raise SwineException ("Slot name cannot be empty.")
		if not self.exists():
			raise SwineException ("Slot does not exist: " + self.name)
		if Slot(newname).exists():
			raise SwineException ("Slot does already exist: " + newname)
		shutil.copytree ( self.getPath(), Slot(newname).getPath(), True )

	def rename (self,newname):
		if len(newname) == 0:
			raise SwineException ("Slot name cannot be empty.")
		if self.name == SWINE_DEFAULT_SLOT_NAME:
			raise SwineException ("Default slot cannot be renamed")
		if not self.exists():
			raise SwineException ("Slot does not exist: " + self.name)
		if Slot(newname).exists():
			raise SwineException ("Slot does already exist: " + newname)
		shutil.move ( self.getPath(), Slot(newname).getPath() )
		self.name = newname

	def getAllShortcuts (self):
		shortcuts = []
		for section in self.config.sections():
			if not section == SWINE_DEFAULT_SECTION:
				shortcuts.append ( self.loadShortcut ( section ) )
		return shortcuts
		
	def loadShortcut (self,name):
		return Shortcut ( name, self, dict(self.config.items(name)))
	
	def loadDefaultShortcut (self):
		try:
			return self.loadShortcut ( self.settings['default_shortcut'] )
		except:
			return None
	
	def setDefaultShortcut (self,shortcut):
		# NOTE: saveConfig needs to be called to make this permanent
		self.settings['default_shortcut'] = shortcut.name
	
	def extractExeIcons (self, file, iconsdir):
		if not os.path.exists ( iconsdir ):
			os.makedirs ( iconsdir )
		self._run ([BIN["winresdump"],file],os.P_WAIT,iconsdir)
	
	def createShortcutFromFile (self, file):
		lnk = shortcutlib.readlnk ( file )
		name = os.path.splitext(os.path.basename(file))[0]
		shortcut = Shortcut(name,self)
		prg = [lnk['target']]
		prg.extend ( str2args ( lnk['command_line_arguments'] ) )
		shortcut.data['program']=str(prg)
		shortcut.data['working_directory']=lnk['working_directory']
		shortcut.data['description']=lnk['description']
		file = self.winPathToUnix(lnk['target'])
		iconsdir = self.getPath() + "/icons/" + os.path.basename(file)
		shortcut.data['iconsdir']="icons/" + os.path.basename(file)
		if os.path.splitext(file)[1].lower() == '.exe':
			self.extractExeIcons ( file, iconsdir )
			if len(str(lnk['custom_icon'])) > 0:
				shortcut.data['icon'] = self.winPathToUnix ( lnk['custom_icon'] )
			if len(str(lnk['icon_number'])) > 0:
				shortcut.data['icon'] = iconsdir + "/icon" + str(lnk['icon_number']) + ".bmp"
		return shortcut

	def findShortcutsCallback ( self, shortcuts, dirname, fnames ):
		for file in fnames:
			if os.path.splitext(file)[1] == ".lnk":
				try:
					shortcuts.append(self.createShortcutFromFile(os.path.join(dirname,file)))
				except Exception, inst:
					print os.path.join(dirname,file) + ": " + str(inst)
	
	def findShortcuts (self,exeonly=False):
		shortcuts = []
		os.path.walk(self.getPath()+"/drive_c",self.findShortcutsCallback,shortcuts)
		if exeonly:
			for shortcut in shortcuts:
				if not os.path.splitext(str2args(shortcut.data['program'])[0])[1].lower() == '.exe':
					shortcuts.remove ( shortcut )
		return shortcuts

	def _run (self,prog,mode=os.P_WAIT,workingDirectory="."):
		self.setWinePrefixCheck()
		if os.path.exists(workingDirectory):
			os.chdir ( workingDirectory )
		if os.path.exists(self.winPathToUnix(workingDirectory)):
			os.chdir ( self.winPathToUnix(workingDirectory) )
		return os.spawnv(mode, prog[0], prog)
	
	def run (self,prog,mode=os.P_WAIT,workingDirectory=".",runInTerminal=False):
		if runInTerminal:
			prog.insert(0,BIN["wineconsole"])
			prog.insert(1,"--backend=user")
		else:
			prog.insert(0,BIN["wine"])
		return self._run(prog,mode,workingDirectory)
		
	def runWinecfg (self,mode=os.P_WAIT):
		return self._run ([BIN["winecfg"]],mode)

	def runRegedit (self,mode=os.P_WAIT):
		return self._run ([BIN["regedit"]],mode)
	
	def runWineboot (self,mode=os.P_WAIT):
		return self._run ([BIN["wineboot"]],mode)
		
	def runWinefile (self,mode=os.P_WAIT,directory="C:"):
		return self._run ([BIN["winefile"],directory],mode)
	
	def runUninstaller (self,mode=os.P_WAIT):
		return self._run ([BIN["uninstaller"]],mode)
		
	def runWineControl (self,mode=os.P_WAIT):
		return self._run ([BIN["wine"],"control"],mode)
	
	def installCorefonts (self):
		from urllib import urlopen
		fonts = ["andale","arial","arialb","comic","courie","georgi","impact","times","trebuc","verdan","webdin"]
		path = self.getPath() + "/corefonts"
		cabextract = which ("cabextract")
		if not os.path.exists ( path ):
			os.mkdir ( path )
		os.chdir ( path )
		for font in fonts:
			file = font + "32.exe"
			if not os.path.exists ( file ):
				instream=urlopen("http://downloads.sourceforge.net/corefonts/" + file + "?use_mirror=switch")
				outfile=open(file, "wb")
				outfile.write(instream.read())
				outfile.close()
			self._run([cabextract,file])
		for file in os.listdir ( path ):
			if os.path.splitext(file)[1].lower() == ".ttf":
				shutil.move ( file, self.getDrivePath("c:") + "/windows/fonts/" + file )
	
	def winPathToUnix (self,path):
		self.setWinePrefixCheck()
		return readCommandOutput("winepath -u " + pipes.quote(path))[:-1]
	
	def unixPathToWin (self,path):
		self.setWinePrefixCheck()
		return readCommandOutput("winepath -w " + pipes.quote(path))[:-1]

	def exportData (self,file):
		if len(file) == 0:
			raise SwineException ("File name cannot be empty.")
		os.chdir(self.getPath ())
		tar = TarFile.gzopen ( file, "w" )
		tar.add ( "." )
		tar.close ()

	def importData (self, file):
		if len(file) == 0:
			raise SwineException ("File name cannot be empty.")
		os.chdir(self.getPath ())
		tar = TarFile.gzopen ( file, "r" )
		for file in tar:
			tar.extract(file)
		tar.close ()
		self.loadConfig()


def importSlot (name, file):
	if len(file) == 0:
		raise SwineException ("File name cannot be empty.")
	slot = Slot ( name )
	slot.create()
	os.chdir(slot.getPath ())
	tar = TarFile.gzopen ( file, "r" )
	for file in tar:
		tar.extract(file)
	tar.close ()
	slot.loadConfig()
	return slot


def readCommandOutput (command):
	# this definetly needs a rewrite
	stdin, stdout = os.popen2(command)
	output = ""
	while True:
		try:
			data = array.array("B")
			data.read ( stdout, 1 )
		except Exception:
			break
		else:
			output += chr ( data[0] )
	return output

def str2args ( s ):
	if len(s) == 0:
		return []
	if s[0] == "[":
		try:
			return eval ( s )
		except Exception:
			pass
	return s.split ( " " )

def which(name, matchFunc=os.path.isfile):
    for dirname in os.environ["PATH"].split(os.pathsep):
        candidate = os.path.join(dirname, name)
        if matchFunc(candidate):
            return candidate
    raise SwineException("Can't find file %s" % name)



def init ():
	for file in ["wine", "wineconsole", "wineprefixcreate", "winecfg", "wineboot", "winefile", "winepath", "regedit", "uninstaller", "winresdump"]:
		BIN[file]=which(file)
	os.environ['WINEDEBUG'] = "warn"
	if not os.path.exists ( SWINE_PATH ):
		os.mkdir ( SWINE_PATH )
		print "created " + SWINE_PATH
	if not os.path.exists ( SWINE_SLOT_PATH ):
		os.mkdir ( SWINE_SLOT_PATH )
		print "created " + SWINE_SLOT_PATH
	if not os.path.exists ( SWINE_DEFAULT_SLOT_PATH ) and os.path.exists ( WINE_PATH ):
		os.symlink ( WINE_PATH, SWINE_DEFAULT_SLOT_PATH )
		print "symlinked " + SWINE_DEFAULT_SLOT_PATH + " to " + WINE_PATH

def getAllSlots ():
	slist = os.listdir ( SWINE_SLOT_PATH )
	slist.sort()
	slots = []
	for slot in slist:
		slots.append ( loadSlot(slot) )
	return slots

def loadSlot (name):
	slot = Slot(name)
	if not slot.exists():
		raise SwineException ("Slot does not exist: " + name)
	slot.loadConfig()
	return slot

try:
	init()
except Exception, data:
	print data
	sys.exit(-1)
