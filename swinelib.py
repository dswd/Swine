# -*- coding: utf-8 -*-
############################################################################
#    Copyright (C) 2007-2012 by Dennis Schwerdel, Thomas Schmidt           #
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

import sys

reload(sys)
sys.setdefaultencoding("utf-8")

from config import *
import os, shutil, ConfigParser, array, pipes, urllib, subprocess, codecs, shlex
import shortcutlib, winetricks
from tarfile import TarFile
from subprocess import Popen

def tr(s):
  return s

class SwineException(Exception):
  pass

class Shortcut:
  def __init__(self, name, slot, data={}):
    if not name:
      raise SwineException(tr("Shortcut name cannot be empty"))
    self.name = unicode(name)
    if not data:
      self.data = {}
    else:
      self.data = data
    assert slot and isinstance(slot, Slot)
    self.slot = slot
    if self["program"] and self["program"].startswith("["):
      #code for old program format
      import ast
      args = ast.literal_eval(self["program"])
      self.setProgram(args[0], args[1:])
  def __str__(self):
    return self.name
  def getSlot(self):
    return self.slot
  def getName(self):
    return self.name
  def __setitem__(self, key, value):
    self.data[key]=value
    self.save()
  def __getitem__(self, key):
    return self.data.get(key, None)
  def __delitem__(self, key):
    del self.data[key]
  def _storeData(self):
    self.slot._storeShortcutData(self.name, self.data)
  def _removeData(self):
    self.slot._removeShortcutData(self.name)
  def save(self):
    self._storeData()
  def delete(self):
    self._removeData()
    self.removeMenuEntry()
  def rename(self, newname):
    if not newname:
      raise SwineException (tr("Shortcut name cannot be empty"))
    if newname == self.name:
      return
    self._removeData()
    hasMenuEntry = self.hasMenuEntry()
    if hasMenuEntry:
      self.removeMenuEntry()
    self.name = newname
    self._storeData()
    if hasMenuEntry:
      self.createMenuEntry()
  def clone(self, newname):
    if not newname:
      raise SwineException(tr("Shortcut name cannot be empty"))
    if self.slot.hasShortcut(newname):
      raise SwineException(tr("Shortcut already exists"))
    shortcut = Shortcut(newname, self.slot, self.data.copy())
    shortcut.save()
    return shortcut
  def isDefault(self):
    return self.slot.getDefaultShortcutName() == self.name
  def setDefault(self):
    self.slot.setDefaultShortcut(self)
  def getProgram(self):
    if not self['program']:
      return []
    return map(lambda s: s.rstrip('\0'), shlex.split(self['program']))
  def setProgram(self, exePath, args):
    assert isinstance(exePath, str)
    if isinstance(args, str):
      args = shlex.split(args)
    assert isinstance(args, list)
    self['program'] = " ".join(map(repr, [exePath]+args))
  def getIcon(self):
    return os.path.join(self.slot.getPath(), self["icon"]) if self["icon"] else None
  def setIcon(self, icon):
    if not os.path.exists(icon):
      self['icon'] = None
    else:
      self['icon'] = relpath(icon, self.slot.getPath())
  def getWorkingDirectory(self):
    return self["working_directory"]
  def setWorkingDirectory(self, path):
    assert isinstance(path, str)
    self["working_directory"] = path
  def getDesktop(self):
    return self["desktop"]
  def setDesktop(self, desktop):
    assert isinstance(desktop, str)
    self["desktop"] = desktop
  def _iconsDir(self):
    if self["iconsdir"]:
      return os.path.join(self.slot.getPath(), self["iconsdir"])
    return None
  def _exePath(self):
    path = self.slot.winPathToUnix(self.getProgram()[0])
    if not os.path.exists(path) and os.path.exists(path+".exe"):
      path += ".exe"
    return path
  def extractIcons(self):
    path = self._exePath()
    if os.path.splitext(path)[1].lower() == '.exe':
      self['iconsdir'] = os.path.join("icons", os.path.basename(path))
      self.slot.extractExeIcons(path, self._iconsDir())
  def _menuEntryPath(self):
    return os.path.join(DESKTOP_MENU_DIR, "%s-%s.desktop" % (self.slot.getName(), self.name))
  def hasMenuEntry(self):
    return os.path.exists(self._menuEntryPath())
  def createMenuEntry(self):
    if not os.path.exists(DESKTOP_MENU_DIR):
      os.mkdir(DESKTOP_MENU_DIR)
    with open(self._menuEntryPath(), "w") as fp:
      fp.write("[Desktop Entry]\nEncoding=UTF-8\nVersion=1.0\n")
      fp.write("Name=%s: %s\n" % (self.slot.getName(), self.name))
      fp.write("Type=Application\n")
      fp.write("Exec=swinecli --slot %r --shortcut %r --translate-paths --run %U\n" % (self.slot.getName(), self.name))
      fp.write("Icon=%s\n" % self["icon"])
      fp.write("Categories=Wine;\n")
  def removeMenuEntry(self):
    if self.hasMenuEntry():
      os.remove(self._menuEntryPath())
  def run(self, wait=False, args=[]):
    prog = self.getProgram()
    workingDirectory = self['working_directory']
    runInTerminal = self["interminal"] and int(self["interminal"]) == 1
    desktop = self["desktop"]
    return self.slot.runWin(prog=prog+args, wait=wait, workingDirectory=workingDirectory, runInTerminal=runInTerminal, desktop=desktop)
  def readFromLnk(self, path):
    if not os.path.exists(path):
      path = self.slot.winPathToUnix(path)
    if not os.path.exists(path):
      raise Exception(tr("File does not exist"))
    lnk = shortcutlib.readlnk(path)
    name = os.path.splitext(os.path.basename(path))[0]
    self.setProgram(lnk['target'], lnk['command_line_arguments'])
    self.setWorkingDirectory(lnk['working_directory'])
    if lnk['custom_icon']:
      iconPath = self.slot.winPathToUnix(lnk['custom_icon'],"c:\windows")
    else:
      iconPath = self.slot.winPathToUnix(lnk['target'])
    iconsdir = os.path.join(self.slot.getPath(), "icons", os.path.basename(iconPath))
    self['iconsdir'] = os.path.join("icons", os.path.basename(iconPath))
    if os.path.splitext(iconPath)[1].lower() == '.exe':
      self.slot.extractExeIcons(iconPath, iconsdir)
      icons = os.listdir(iconsdir)
      self.setIcon(os.path.join(iconsdir, self.slot.bestIco(icons, lnk['icon_number'])))
    else:
      self.setIcon(self.slot.winPathToUnix(iconPath))

    
    
class Slot:
  def __init__(self, name):
    if not name:
      raise SwineException(tr("Slot name cannot be empty."))
    assert isinstance(name, str)
    self.name = name
    self.config = None
    self.settings = None
  def __setitem__(self, key, value):
    self.settings[key]=value
  def __getitem__(self, key):
    return self.settings.get(key, None)
  def __delitem__(self, key):
    del self.settings[key]
  def __str__(self):
    return self.name
  def getName(self):
    return self.name
  def _storeShortcutData(self, shortcut, data):
    if not shortcut:
      raise SwineException(tr("Shortcut name cannot be empty"))
    assert isinstance(data, dict)
    if not self.config.has_section(shortcut):
      self.config.add_section(shortcut)
    for o in self.config.options(shortcut):
      self.config.remove_option(shortcut, o)
    for k, v in data.iteritems():
      self.config.set(shortcut, k, v)
    self.saveConfig()
  def _removeShortcutData(self, shortcut):
    if not shortcut:
      raise SwineException(tr("Shortcut name cannot be empty"))
    if self.config.has_section(shortcut):
      self.config.remove_section(shortcut)
    if self.getDefaultShortcutName() == shortcut:
      self.setDefaultShortcutName(shortcut)
    self.saveConfig()
  def getPath(self):
    return os.path.join(SWINE_SLOT_PATH, self.name)
  def getDosDrivesPath(self):
    return os.path.join(self.getPath(), "dosdevices")
  def getDrivePath(self, drive):
    drive = drive.lower()
    if not drive.endswith(":"):
      drive += ":"
    path = os.path.join(self.getDosDrivesPath(), drive)
    if not os.path.exists(path):
      raise SwineException(tr("%s does not exist") % drive)
    return path
  def getConfigFile(self):
    return os.path.join(self.getPath(), "swine.ini")
  def loadConfig(self):
    self.config = ConfigParser.ConfigParser()
    if os.path.exists(self.getConfigFile()):
      with codecs.open(self.getConfigFile(), "r", "utf8") as fp:
        self.config.readfp(fp)
    if not self.config.has_section(SWINE_DEFAULT_SECTION):
      self.config.add_section(SWINE_DEFAULT_SECTION)
    self.settings = dict(self.config.items(SWINE_DEFAULT_SECTION))
  def saveConfig(self):
    for k, v in self.settings.iteritems():
      self.config.set(SWINE_DEFAULT_SECTION, k, v)
    with open(self.getConfigFile(), "w") as fp:
      self.config.write(fp)
  def exists(self):
    return os.path.exists(self.getPath())
  def create(self):
    if self.exists():
      raise SwineException(tr("Slot already exists: %s") % self.name)
    os.mkdir(self.getPath())
    self.runWineboot()
    self.loadConfig()
    self.saveConfig()
  def delete(self):
    if self.name == SWINE_DEFAULT_SLOT_NAME:
      raise SwineException(tr("Default slot cannot be deleted"))
    if not self.exists():
      raise SwineException(tr("Slot does not exist: %s") % self.name)
    for s in self.getAllShortcuts():
      s.delete()
    shutil.rmtree(self.getPath())
  def clone(self, newname):
    if not newname:
      raise SwineException(tr("Slot name cannot be empty"))
    if not self.exists():
      raise SwineException(tr("Slot does not exist: %s") % self.name)
    assert isinstance(newname, str)
    slot = Slot(newname)
    if slot.exists():
      raise SwineException(tr("Slot does already exist: %s") % newname)
    shutil.copytree(self.getPath(), slot.getPath(), True)
    slot.loadConfig()
    return slot
  def rename(self, newname):
    if not newname:
      raise SwineException(tr("Slot name cannot be empty"))
    if self.name == SWINE_DEFAULT_SLOT_NAME:
      raise SwineException(tr("Default slot cannot be renamed"))
    if not self.exists():
      raise SwineException(tr("Slot does not exist: %s") % self.name)
    dummySlot = Slot(newname)
    if dummySlot.exists():
      raise SwineException(tr("Slot does already exist: %s") % newname)
    shortcutMenus = []
    for s in self.getAllShortcuts():
      if s.hasMenuEntry():
        shortcutMenus.append(s)
        s.removeMenuEntry()
    shutil.move(self.getPath(), dummySlot.getPath())
    self.name = newname
    for s in shortcutMenus:
      s.createMenuEntry()
  def getAllShortcuts(self):
    shortcuts = []
    for section in self.config.sections():
      if not section == SWINE_DEFAULT_SECTION:
        shortcuts.append(self.loadShortcut(section))
    return shortcuts
  def hasShortcut(self, name):
    assert name
    return self.config.has_section(name)
  def loadShortcut(self,name):
    assert name
    if not self.hasShortcut(name):
      return None
    return Shortcut(name, self, dict(self.config.items(name)))
  def getDefaultShortcutName(self):
    return self['default_shortcut']
  def setDefaultShortcutName(self, name):
    self['default_shortcut'] = name
    self.saveConfig()
  def setDefaultShortcut(self, shortcut):
    assert shortcut
    self.setDefaultShortcutName(shortcut.getName())
  def unsetDefaultShortcut(self):
    self.setDefaultShortcutName(None)
  def loadDefaultShortcut(self):
    try:
      return self.loadShortcut(self.getDefaultShortcutName())
    except:
      return None
  def extractExeIcons(self, path, iconsdir, onlyNr=None):
    if not os.path.exists(iconsdir):
      os.makedirs(iconsdir)
    if onlyNr == None:
      self.runNative(["wrestool", "-x", "-t14", "--output", iconsdir, path], wait=True)
    else:
      self.runNative(["wrestool", "-x", "-t14", "-n%d" % onlyNr, "--output", iconsdir, path], wait=True)
    files = os.listdir(iconsdir)
    for icon in files:
      if os.path.splitext(icon)[1].lower() == '.ico':
        iconPath = os.path.join(iconsdir, icon)
        self.runNative(["icotool", "-x", "-o", iconsdir, iconPath], wait=True)
        os.remove(iconPath)
    return self.bestIco(os.listdir(iconsdir))
  def bestIco(self, icons, nr=0):
    def parseIcoName(name):
      import re
      f = re.match(".*_([0-9]+)_(.*)_([0-9]+)x([0-9]+)x([0-9]+).png", name)
      if not f:
        return (0, 0, 0, 0)
      return (int(f.group(1)), f.group(2), int(f.group(3)), int(f.group(5)))
    def icoCmp(x,y):
      x_nr1, x_nr2, x_size, x_color = parseIcoName(x)
      y_nr1, y_nr2, y_size, y_color = parseIcoName(y)
      if x_size != y_size:
        if x_size == 32:
          return -1
        if y_size == 32:
          return 1
        return -cmp(x_size,y_size)
      if x_color != y_color:
        return -cmp(x_color,y_color)
      return cmp(x_nr2,y_nr2)
    def icoCmpNr(x,y):
      x_nr1, x_nr2, x_size, x_color = parseIcoName(x)
      y_nr1, y_nr2, y_size, y_color = parseIcoName(y)
      if x_nr1 != y_nr1:
        return cmp(x_nr1,y_nr1)
      return cmp(x_nr2,y_nr2)
    def icoFilter(l, nr1, nr2):
      def icoFilterName(n, nr1, nr2):
        n_nr1, n_nr2, n_size, n_color = parseIcoName(n)
        return n_nr1 == nr1 and n_nr2 == nr2
      return filter(lambda n: icoFilterName(n, nr1, nr2), l)
    if len(icons) >= nr and nr >= 0:
      icons.sort(icoCmpNr)
      nr1, nr2, size, color = parseIcoName(icons[nr])
      icons = icoFilter(icons, nr1, nr2)
    icons.sort(icoCmp)
    if not icons:
      return ""
    else:
      return icons[0]
  def createShortcutFromFile(self, path):
    name = os.path.splitext(os.path.basename(path))[0]
    shortcut = Shortcut(name, self)
    shortcut.readFromLnk(path)
    shortcut.save()
    return shortcut
  def findShortcutsCallback(self, shortcuts, dirname, fnames):
    for fname in fnames:
      if os.path.splitext(fname)[1].lower() == ".lnk":
        try:
          shortcuts.append(self.createShortcutFromFile(os.path.join(dirname,fname)))
        except Exception, inst:
          print os.path.join(dirname,fname) + ": " + str(inst)
  def findShortcuts(self, exeonly=False):
    shortcuts = []
    os.path.walk(os.path.join(self.getPath(), "drive_c"), self.findShortcutsCallback, shortcuts)
    if exeonly:
      for shortcut in shortcuts:
        if not os.path.splitext(shortcut.getProgram()[0])[1].lower() == '.exe':
          shortcuts.remove(shortcut)
    return shortcuts
  def runNative(self, prog, cwd=None, wait=False, env=None, stdin=None, stdout=None, stderr=None):
    """Run any native program (no windows binaries)
    Parameters:
      prog: this is the program with all paramters as a list
      cwd: the working directory (unix-path)
      wait: wait until the process terminates
      env: custom environment, NOTE: this overwrites the normal environment
      stdin, stdout, stderr: if this is set to "subprocess.PIPE" a new pipe is created to be accessed later
                             if this is set to a file descriptor, the file is used as input/output
    """
    if not cwd and self.exists():
      cwd = self.getPath()
    proc = Popen(prog, stdin=stdin, stderr=stderr, stdout=stdout, cwd=cwd, env=env)
    (proc.stdout_data, proc.stderr_data) = proc.communicate() if wait else (None, None)
    return proc
  def runWineTool(self, prog, cwd=None, wait=False, stdin=None, stdout=None, stderr=None, debug=None):
    """Run a wine tool (eg wine itself) with prefix and debug environment set
    This is only a wrapper for runNative
    """
    env = os.environ.copy()
    env["WINEPREFIX"] = self.getPath()
    env["WINEDEBUG"] = "err+all,warn-all,fixme-all,trace-all"
    #env["WINEDLLOVERRIDES"] = "winemenubuilder.exe=d" #do not add shortcuts to desktop or menu
    global WINE_WRAPPER
    if WINE_WRAPPER and os.path.exists(self.getPath()):
      open(os.path.join(self.getPath(), ".no_prelaunch_window_flag"),"wc").close()
    if debug:
      env["WINEDEBUG"] = debug
    return self.runNative(prog, cwd, wait, env, stdin, stdout, stderr)
  def runWis(self, wisFile):
    env = os.environ
    env["WINEPREFIX"] = self.getPath()
    env["SLOT"] = self.name
    return self.runNative(["xterm", "-T", "WIS", "-hold", "-e", WISRUN, wisFile], cwd=".", wait=True, env=env)
  def runWinetricks(self, prog):
    """Run a winetricks command
    This is only a wrapper for runNative
    """
    return self.runWineTool(["xterm", "-T", "Winetricks %s" % prog, "-hold", "-e", WINETRICKS, str(prog)])
  def runWin(self, prog, workingDirectory=".", wait=False, runInTerminal=False, desktop=None, debug=None, log=None):
    """Run a windows program
    Parameters:
      prog: this is the program with all paramters as a list
      workingDirectory: the working directory, unix- and windows-paths will work
      wait: wait until the process terminates
      runInTerminal: if this is set the wine call is done with wineconsole instead of wine
      debug: user-defined WINEDEBUG-String (see wine manpage)
      log: if this is set, wine stderr output will be written to that file
      desktop: if this is set, program will be run in a window
    """
    if not os.path.splitext(prog[0])[1].lower() == ".exe":
      prog.insert(0, "start")
      if os.path.exists(prog[1]): #Path is unix path
        prog.insert(1, "/UNIX")
      if wait:
        prog.insert(1, "/W")
    if desktop:
      prog.insert(0, "explorer")
      prog.insert(1, "/desktop=%s" % desktop)
    if runInTerminal:
      prog.insert(0, "wineconsole")
      prog.insert(1, "--backend=user")
    else:
      prog.insert(0, "wine")
    cwd = None
    if os.path.exists(workingDirectory):
      cwd = workingDirectory
    if os.path.exists(self.winPathToUnix(workingDirectory)):
      cwd = self.winPathToUnix(workingDirectory)
    res = self.runWineTool(prog, cwd, wait=wait, stderr=subprocess.PIPE, debug=debug)
    if log:
      with open(log, "w") as fp:
        fp.write(res.stderr_data)
    return res
  def runWinecfg(self):
    return self.runWineTool(["wine", "winecfg"], wait=False)
  def runRegedit(self):
    return self.runWineTool(["wine", "regedit"], wait=False)
  def runWineboot(self):
    return self.runWineTool(["wine", "wineboot"], wait=False)
  def runWinefile(self, directory="C:"):
    return self.runWineTool(["wine", "winefile", directory], wait=False)
  def runUninstaller(self):
    return self.runWineTool(["wine", "uninstaller"], wait=False)
  def runWineControl(self):
    return self.runWineTool(["wine", "control"], wait=False)
  def runEject(self):
    return self.runWin(["wine", "eject"], wait=False)
  def winPathToUnix(self, path, basedir=None):
    if basedir:
      basedir = self.winPathToUnix(basedir)
    return self.runWinePath(["wine", "winepath", "-u", path], basedir)
  def unixPathToWin(self, path, basedir=None):
    return self.runWinePath(["wine", "winepath", "-w", path], basedir)
  def runWinePath(self, prog, basedir):
    proc = self.runWineTool(prog, wait=True, stdout=subprocess.PIPE, cwd=basedir)
    return proc.stdout_data.splitlines()[-1]
  def exportData(self, archive):
    if not archive:
      raise SwineException(tr("File name cannot be empty"))
    os.chdir(self.getPath())
    with TarFile.gzopen(archive, "w") as tar:
      tar.add(".") #recursive
  def importData(self, archive):
    if not archive:
      raise SwineException(tr("File name cannot be empty"))
    os.chdir(self.getPath())
    with TarFile.gzopen(archive, "r") as tar:
      tar.extractall(".")
    self.loadConfig()

    
def importSlot(name, archive):
  if not archive:
    raise SwineException(tr("File name cannot be empty"))
  slot = Slot(name)
  slot.create()
  slot.importData(archive)
  return slot

def relpath(target, base=os.curdir):
  if not os.path.exists(target):
    return target
  base_list = (os.path.abspath(base)).split(os.sep)
  target_list = (os.path.abspath(target)).split(os.sep)
  for i in range(min(len(base_list), len(target_list))):
    if base_list[i] <> target_list[i]:
      break
    else:
      i+=1
  rel_list = [os.pardir] * (len(base_list)-i) + target_list[i:]
  return os.path.join(*rel_list)

def init():
  if not os.path.exists(SWINE_PATH):
    os.mkdir(SWINE_PATH)
    print tr("created %s") % SWINE_PATH
  if not os.path.exists(SWINE_SLOT_PATH):
    os.mkdir(SWINE_SLOT_PATH)
    print tr("created %s") % SWINE_SLOT_PATH
  if not os.path.exists(SWINE_DEFAULT_SLOT_PATH) and os.path.exists(WINE_PATH):
    os.symlink(WINE_PATH, SWINE_DEFAULT_SLOT_PATH)
    print tr("symlinked %s to %s") % (SWINE_DEFAULT_SLOT_PATH, WINE_PATH)
  global WINE_WRAPPER
  WINE_WRAPPER = "text" in os.popen('file `which wine`', 'r').read()

def getAllSlots():
  slist = os.listdir(SWINE_SLOT_PATH)
  slist.sort()
  slots = []
  for slot in slist:
    if os.path.isdir(os.path.join(SWINE_SLOT_PATH, slot)):
      slots.append(loadSlot(slot))
  return slots

def loadSlot(name):
  slot = Slot(name)
  if not slot.exists():
    raise SwineException(tr("Slot does not exist: %s") % name)
  slot.loadConfig()
  return slot

def loadDefaultSlot():
  return loadSlot(SWINE_DEFAULT_SLOT_NAME)

try:
  init()
except Exception, data:
  print data
  sys.exit(-1)
