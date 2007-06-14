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

import sys, os, shutil, signal, time, ConfigParser, stat, array, pipes
from tarfile import TarFile


DWORD=4
QWORD=8

def bytes2long(bytes):
	return bytes[3]*256+bytes[2]*256+bytes[1]*256+bytes[0]

def getbit(value,number):
	return (value>>number) & 1

def readlnk(filename):
	fileobj = open(filename, mode='rb')
	size = os.lstat(filename)[stat.ST_SIZE]
	data = array.array("B")
	data.read ( fileobj, size )
	shortcut = {}
	shortcut['magic_number'] = bytes2long(data[0x0:0x0+DWORD])
	if not shortcut['magic_number'] == ord("L"):
		raise Exception("Magic number must be 76 ('L')")
	shortcut['GUID'] = data[0x4:0x4+16]
	if not shortcut['GUID'] == array.array ("B", [0x1, 0x14, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0xC0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x46 ] ):
		raise Exception("GUID must be 0114 0200 0000 0000 C000 0000 0000 0046")
	flags = bytes2long(data[0x14:0x14+DWORD])
	shortcut['flags'] = {
		"shell_item_id_present": getbit(flags,0),
		"file_or_directory": getbit(flags,1),
		"description": getbit(flags,2),
		"relative_path": getbit(flags,3),
		"working_directory": getbit(flags,4),
		"command_line_arguments": getbit(flags,5),
		"custom_icon": getbit(flags,6)
	}
	file_attr = bytes2long(data[0x18:0x18+DWORD])
	shortcut['file_attr'] = {
		"read_only": getbit(file_attr,0),
		"hidden": getbit(file_attr,1),
		"system_file": getbit(file_attr,2),
		"volume_label": getbit(file_attr,3),
		"directory": getbit(file_attr,4),
		"archive": getbit(file_attr,5),
		"encrypted": getbit(file_attr,6),
		"normal": getbit(file_attr,7),
		"temporary": getbit(file_attr,8),
		"sparse_file": getbit(file_attr,9),
		"reparse_point_data": getbit(file_attr,10),
		"compressed": getbit(file_attr,11),
		"offline": getbit(file_attr,12),
	}
	shortcut['creation_time'] = data[0x1C:0x1C+QWORD]
	shortcut['modification_time'] = data[0x24:0x24+QWORD]
	shortcut['access_time'] = data[0x2C:0x2C+QWORD]
	shortcut['file_length'] = bytes2long(data[0x34:0x34+DWORD])
	shortcut['icon_number'] = bytes2long(data[0x38:0x38+DWORD])
	shortcut['show_wnd'] = bytes2long(data[0x3C:0x3C+DWORD])
	shortcut['hot_key'] = bytes2long(data[0x40:0x40+DWORD])
	if not data[0x44:0x44+2*DWORD] == array.array("B",[0,0,0,0,0,0,0,0]):
		raise Exception("0x44-0x4C must be 00 00 00 00 00 00 00 00")
	start = 0x4C
	if shortcut['flags']['shell_item_id_present']:
		start += data[0x4C]+data[0x4D]*256+2	
	file_location = {}
	file_location['total_length'] = bytes2long(data[start+0x0:start+0x0+DWORD])
	if not bytes2long(data[start+0x4:start+0x4+DWORD]) == 0x1C:
		raise Exception("0x04-0x08 of file_location must be 0x1C")
	flags = bytes2long(data[start+0x08:start+0x08+DWORD])
	file_location['flags'] = {
		'on_local_volume': getbit ( flags, 0 ),
		'on_network_drive': getbit ( flags, 1 )
	}
	file_location['local_volume_info_offset'] = bytes2long(data[start+0xC:start+0xC+DWORD])
	file_location['base_pathname_offset'] = bytes2long(data[start+0x10:start+0x10+DWORD])
	file_location['network_volume_info_offset'] = bytes2long(data[start+0x14:start+0x14+DWORD])
	file_location['remainig_pathname_offset'] = bytes2long(data[start+0x18:start+0x18+DWORD])
	local_volume = {}
	
	if file_location['flags']['on_local_volume']:
		block = start + file_location['local_volume_info_offset']
		local_volume['length'] = bytes2long(data[block+0x0:block+0x0+DWORD])
		local_volume['type'] = bytes2long(data[block+0x4:block+0x4+DWORD])
		local_volume['serial_number'] = bytes2long(data[block+0x8:block+0x8+DWORD])
		if not bytes2long(data[block+0xC:block+0xC+DWORD]) == 0x10:
			raise Exception("0x0C-0x10 of local_volume_info must be 0x10")
		index = block + 0x10
		name = ""
		while not data[index] == 0:
			name += chr(data[index])
			index = index + 1
		local_volume['volume_label'] = name
		index = start + file_location['base_pathname_offset']
		name = ""
		while not data[index] == 0:
			name += chr(data[index])
			index = index + 1
		local_volume['base_pathname'] = name
	
	network_volume = {}
	if file_location['flags']['on_network_drive']:
		block = start + file_location['network_volume_info_offset']
		network_volume['length'] = bytes2long(data[block+0x0:block+0x0+DWORD])
		index = block + 0x14
		name = ""
		while not data[index] == 0:
			name += chr(data[index])
			index = index + 1
		network_volume['volume_label'] = name
	
	index = start + file_location['remainig_pathname_offset']
	name = ""
	while not data[index] == 0:
		name += chr(data[index])
		index = index + 1
	file_location['remainig_pathname'] = name
	
	start += file_location['total_length']
	
	if shortcut['flags']['description']:
		name = ""
		for i in range(0,2*(data[start]+256*data[start+1])):
			if i % 2 == 0:
				name += chr(data[start+2+i]+data[start+2+i+1]*256)
		start += i + 2 + 1
		shortcut['description']=str(name[:-1])
	else:
		shortcut['description']=""

	if shortcut['flags']['relative_path']:
		name = ""
		for i in range(0,2*(data[start]+256*data[start+1])):
			if i % 2 == 0:
				name += chr(data[start+2+i]+data[start+2+i+1]*256)
		start += i + 2 + 1
		shortcut['relative_path']=name
	else:
		shortcut['relative_path']=""
		
	if shortcut['flags']['working_directory']:
		name = ""
		for i in range(0,2*(data[start]+256*data[start+1])):
			if i % 2 == 0:
				name += chr(data[start+2+i]+data[start+2+i+1]*256)
		start += i + 2 + 1
		shortcut['working_directory']=str(name[:-1])
	else:
		shortcut['working_directory']=""
		
	if shortcut['flags']['command_line_arguments']:
		name = ""
		for i in range(0,2*(data[start]+256*data[start+1])):
			if i % 2 == 0:
				name += chr(data[start+2+i]+data[start+2+i+1]*256)
		start += i + 2 + 1
		shortcut['command_line_arguments']=str(name[:-1])
	else:
		shortcut['command_line_arguments']=""
	
	if shortcut['flags']['custom_icon']:
		name = ""
		for i in range(0,2*(data[start]+256*data[start+1])):
			if i % 2 == 0:
				name += chr(data[start+2+i]+data[start+2+i+1]*256)
		start += i + 2 + 1
		shortcut['custom_icon']=name
	else:
		shortcut['custom_icon']=""

	file_location['network_volume'] = network_volume
	file_location['local_volume'] = local_volume
	shortcut['file_location'] = file_location
	
	if shortcut['file_location']['flags']['on_local_volume']:
		shortcut['target'] = shortcut['file_location']['local_volume']['base_pathname']
	elif shortcut['file_location']['flags']['on_network_drive']:
		shortcut['target'] = shortcut['file_location']['network_volume']['volume_label']
	shortcut['target'] += shortcut['file_location']['remainig_pathname']
	return shortcut

def lnkinfo ( filename ):
	print "Filename: " + filename
	lnk = readlnk ( filename )
	print "Target: " + lnk['target']
	print "Arguments: " + str(lnk['command_line_arguments'])
	print "Working directory: " + str(lnk['working_directory'])
	print "Relative path: " + str(lnk['relative_path'])
	print "Description: " + str(lnk['description'])
	print "Icon ID: " + str(lnk['icon_number'])
	print "Custom Icon: " + str(lnk['custom_icon'])




VERSION = "0.2 beta"

os.environ['PATH'] += ":" + os.path.dirname(__file__)

SWINE_PATH = os.getenv("HOME") + "/.swine"
SWINE_SLOT_PATH = SWINE_PATH
SWINE_DEFAULT_SLOT_NAME = "DEFAULT"
SWINE_DEFAULT_SLOT_PATH = SWINE_PATH + "/" + SWINE_DEFAULT_SLOT_NAME
SWINE_DEFAULT_SECTION = "__SYSTEM__"
WINE_PATH = os.getenv("HOME") + "/.wine"

BIN = {}


class Shortcut:
	def __init__(self,name,slot,data={}):
		if len(name) == 0:
			raise Exception ("Shortcut name cannot be empty.")
		self.name = name
		if len(data) == 0:
			self.data = {}
		else:
			self.data = data
		self.slot = slot
	
	def __str__(self):
		return self.name
	
	def save (self):
		if not self.slot.config.has_section ( self.name ):
			self.slot.config.add_section ( self.name )
		for k, v in self.data.iteritems():
			self.slot.config.set(self.name,k,v)
		
	def delete (self):
		self.slot.config.remove_section (self.name)
		
	def rename (self, newname):
		if len(newname) == 0:
			raise Exception ("Shortcut name cannot be empty.")
		if newname == self.name:
			return None
		self.delete ()
		self.name = newname
		self.save ()
		
	def clone (self, newname):
		if len(newname) == 0:
			raise Exception ("Shortcut name cannot be empty.")
		shortcut = Shortcut(newname,self.slot,self.data)
		shortcut.save ()

	def run (self,mode=os.P_NOWAIT):
		return self.slot.run (str2args(self.data['program']),mode,self.data['working_directory'])

	def isDefault (self):
		return ( not self.slot.loadDefaultShortcut() == None ) and self.name == self.slot.loadDefaultShortcut().name
	
	def setDefault (self):
		self.slot.setDefaultShortcut(self)

	def iconsDir (self):
		if self.data.has_key("iconsdir"):
			return self.slot.getPath() + "/" + self.data["iconsdir"]
		return None

class Slot:
	def __init__(self, name):
		if len(name) == 0:
			raise Exception ("Slot name cannot be empty.")
		self.name = name
		self.config = None
		self.settings = None
		
	def __str__(self):
		return self.name
		
	def getPath(self):
		return SWINE_SLOT_PATH + "/" + self.name

	def getConfigFile(self):
		return SWINE_SLOT_PATH + "/" + self.name + "/swine.ini"

	def loadConfig(self):
		self.config = ConfigParser.ConfigParser()
		self.config.read(self.getConfigFile())
		if not self.config.has_section ( SWINE_DEFAULT_SECTION ):
			self.config.add_section ( SWINE_DEFAULT_SECTION )
		self.settings = dict(self.config.items(SWINE_DEFAULT_SECTION))

	def saveConfig(self):
		for k, v in self.settings.iteritems():
			self.config.set(SWINE_DEFAULT_SECTION,k,v)
		self.config.write ( open ( self.getConfigFile(), "w" ) )

	def setWinePrefix(self):
		os.environ['WINEPREFIX'] = self.getPath()

	def setWinePrefixCheck (self):
		if not self.exists():
			raise Exception ("Slot does not exist: " + self.name)
		self.setWinePrefix()

	def exists (self):
		return os.path.exists ( self.getPath() )
	
	def create (self):
		if self.exists():
			raise Exception ("Slot already exists: " + self.name)
		self.setWinePrefix()
		os.system (BIN["wineprefixcreate"])
		self.loadConfig()
		self.saveConfig()
	
	def delete (self):
		if self.name == SWINE_DEFAULT_SLOT_NAME:
			raise Exception ("Default slot cannot be deleted")
		if not self.exists ():
			raise Exception ("Slot does not exist: " + self.name)
		shutil.rmtree ( self.getPath() )

	def clone (self,newname):
		if len(newname) == 0:
			raise Exception ("Slot name cannot be empty.")
		if not self.exists():
			raise Exception ("Slot does not exist: " + self.name)
		if Slot(newname).exists():
			raise Exception ("Slot does already exist: " + newname)
		shutil.copytree ( self.getPath(), Slot(newname).getPath(), True )

	def rename (self,newname):
		if len(newname) == 0:
			raise Exception ("Slot name cannot be empty.")
		if self.name == SWINE_DEFAULT_SLOT_NAME:
			raise Exception ("Default slot cannot be renamed")
		if not self.exists():
			raise Exception ("Slot does not exist: " + self.name)
		if Slot(newname).exists():
			raise Exception ("Slot does already exist: " + newname)
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
		self.settings['default_shortcut'] = shortcut.name
	
	def extractExeIcons (self, file, iconsdir):
		if not os.path.exists ( iconsdir ):
			os.makedirs ( iconsdir )
		self._run ([BIN["winresdump"],file],os.P_WAIT,iconsdir)
	
	def createShortcutFromFile (self, file):
		lnk = readlnk ( file )
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
		print self.winPathToUnix(workingDirectory)
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
		
	def runUninstaller (self,mode=os.P_WAIT):
		return self._run ([BIN["uninstaller"]],mode)
		
	def runWineControl (self,mode=os.P_WAIT):
		return self._run ([BIN["wine"],"control"],mode)
	
	def winPathToUnix (self,path):
		self.setWinePrefixCheck()
		return readCommandOutput("winepath -u " + pipes.quote(path))[:-1]
	
	def unixPathToWin (self,path):
		self.setWinePrefixCheck()
		return readCommandOutput("winepath -w " + pipes.quote(path))[:-1]

	def exportData (self,file):
		if len(file) == 0:
			raise Exception ("File name cannot be empty.")
		os.chdir(self.getPath ())
		tar = TarFile.gzopen ( file, "w" )
		tar.add ( "." )
		tar.close ()

	def importData (self, file):
		if len(file) == 0:
			raise Exception ("File name cannot be empty.")
		os.chdir(self.getPath ())
		tar = TarFile.gzopen ( file, "r" )
		for file in tar:
			tar.extract(file)
		tar.close ()
		self.loadConfig()


def importSlot (name, file):
	if len(file) == 0:
		raise Exception ("File name cannot be empty.")
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
    raise Exception("Can't find file %s" % name)

def init ():
	for file in ["wine", "wineconsole", "wineprefixcreate", "winecfg", "wineboot", "winepath", "regedit", "uninstaller", "winresdump"]:
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
		raise Exception ("Slot does not exist: " + name)
	slot.loadConfig()
	return slot

try:
	init()
except Exception, data:
	print data
	sys.exit(-1)