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
import config
import os, shutil, array, pipes, urllib, subprocess, codecs, shlex, json, glob, base64
import shortcutlib, winetricks, icolib
from tarfile import TarFile
from subprocess import Popen

U_SEP = '/'
W_SEP = '\\'
D_SEP = ':'
DIR_UP = '..'
DIR_CUR = '.'

class SwineException(Exception):
  pass

class Shortcut:
  def __init__(self, name, slot, data={}, virtual=False):
    if not name:
      raise SwineException(self.tr("Shortcut name cannot be empty"))
    self.name = unicode(name)
    if not data:
      self.data = {}
    else:
      self.data = data
    assert slot and isinstance(slot, Slot)
    self.slot = slot
    self.virtual = virtual
  def tr(self, s):
    return tr(s, self.__class__.__name__)
  def __str__(self):
    return self.name
  def getSlot(self):
    return self.slot
  def getName(self):
    return self.name
  def __setitem__(self, key, value):
    self.data[key]=value
    if not self.virtual:
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
    self.virtual = False
    self._storeData()
  def delete(self):
    self._removeData()
    self.removeMenuEntry()
  def rename(self, newname):
    if not newname:
      raise SwineException(self.tr("Shortcut name cannot be empty"))
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
      raise SwineException(self.tr("Shortcut name cannot be empty"))
    if self.slot.hasShortcut(newname):
      raise SwineException(self.tr("Shortcut already exists"))
    shortcut = Shortcut(newname, self.slot, self.data.copy())
    shortcut.save()
    return shortcut
  def isDefault(self):
    return self.slot.getDefaultShortcutName() == self.name
  def setDefault(self):
    self.slot.setDefaultShortcut(self)
  def getProgram(self):
    return self['program']
  def setProgram(self, prog):
    assert isinstance(prog, (str, unicode))
    self["program"] = prog
  def getArguments(self):
    return self["arguments"] if self["arguments"] else []
  def setArguments(self, args):
    assert isinstance(args, (str, unicode, list))
    if isinstance(args, (str, unicode)):
      args = shlex.split(args)
    self['arguments'] = args
  def getIcon(self):
    if self["icon"]:
      try:
        return base64.b64decode(self["icon"])
      except:
        pass
      path = os.path.join(self.slot.getPath(), self["icon"])
      if os.path.exists(path):
        with open(path, "r") as fp:
          data = fp.read()
          self.setIcon(data)
          return data
    return None
  def setIcon(self, icon):
    self['icon'] = base64.b64encode(icon) if icon else None
  def getWorkingDirectory(self):
    return self["working_directory"]
  def setWorkingDirectory(self, path):
    assert isinstance(path, (str, unicode))
    self["working_directory"] = path
  def getDesktop(self):
    return self["desktop"]
  def setDesktop(self, desktop):
    assert isinstance(desktop, (str, unicode))
    self["desktop"] = desktop
  def _exePath(self):
    path = self.slot.winPathToUnix(self.getProgram())
    if not os.path.exists(path) and os.path.exists(path+".exe"):
      path += ".exe"
    return path
  def _menuEntryPath(self):
    return os.path.join(DESKTOP_MENU_DIR, "%s-%s.desktop" % (self.slot.getName(), self.name))
  def _menuEntryIconPath(self):
    return os.path.join(DESKTOP_MENU_DIR, "%s-%s.png" % (self.slot.getName(), self.name))
  def hasMenuEntry(self):
    return os.path.exists(self._menuEntryPath())
  def createMenuEntry(self):
    if not os.path.exists(DESKTOP_MENU_DIR):
      os.mkdir(DESKTOP_MENU_DIR)
    if self.getIcon():
      with open(self._menuEntryIconPath(), "wb") as fp:
        fp.write(self.getIcon())
    with open(self._menuEntryPath(), "w") as fp:
      fp.write("[Desktop Entry]\nEncoding=UTF-8\nVersion=1.0\n")
      fp.write("Name=%s: %s\n" % (self.slot.getName(), self.name))
      fp.write("Type=Application\n")
      fp.write("Exec=swinecli --slot %r --shortcut %r --translate-paths --run %%U\n" % (str(self.slot.getName()), str(self.name)))
      if self.getIcon():
        fp.write("Icon=%s\n" % self._menuEntryIconPath())
      fp.write("Categories=Wine;\n")
  def removeMenuEntry(self):
    if self.hasMenuEntry():
      os.remove(self._menuEntryPath())
      os.remove(self._menuEntryIconPath())
  def run(self, wait=True, args=[]):
    prog = [self.getProgram()]+self.getArguments()
    workingDirectory = self['working_directory']
    runInTerminal = self["interminal"] and int(self["interminal"]) == 1
    desktop = self["desktop"]
    return self.slot.runWin(prog=prog+args, wait=wait, workingDirectory=workingDirectory, runInTerminal=runInTerminal, desktop=desktop)
  def readFromLnk(self, path):
    if not os.path.exists(path):
      path = self.slot.winPathToUnix(path)
    if not os.path.exists(path):
      raise Exception(self.tr("File does not exist"))
    try:
      lnk = shortcutlib.readLnk(path)
    except:
      print >>sys.stderr, "Failed to read %s" % path
      raise
    name = os.path.splitext(os.path.basename(path))[0]
    self.setProgram(lnk.target)
    self.setArguments(str(lnk.commandLineArgs) if lnk.commandLineArgs else "")
    self.setWorkingDirectory(str(lnk.workingDirectory) if lnk.workingDirectory else "")
    if lnk.description:
      self["description"] = lnk.description
    if lnk.customIcon:
      iconPath = self.slot.winPathToUnix(str(lnk.customIcon), "c:\windows")
    else:
      iconPath = self.slot.winPathToUnix(lnk.target)
    if os.path.splitext(iconPath)[1].lower() == '.exe':
      icons = icolib.readExeIcons(iconPath, lnk.iconIndex)
      if not icons:
        icons = icolib.readExeIcons(iconPath)
    else:
      icons = icolib.readIcoIcons(iconPath)
    bestIco = icolib.bestIcon(icons)
    if bestIco:
      self.setIcon(bestIco.data)

    
    
class Slot:
  def __init__(self, name):
    if not name:
      raise SwineException(self.tr("Slot name cannot be empty."))
    assert isinstance(name, (str, unicode))
    self.name = name
    self.settings = {}
    self.shortcutData = {}
  def tr(self, s):
    return tr(s, self.__class__.__name__)
  def __setitem__(self, key, value):
    self.settings[key]=value
  def __getitem__(self, key):
    return self.settings.get(key, config.getValue(key))
  def __delitem__(self, key):
    del self.settings[key]
  def __str__(self):
    return self.name
  def getName(self):
    return self.name
  def _storeShortcutData(self, shortcut, data):
    if not shortcut:
      raise SwineException(self.tr("Shortcut name cannot be empty"))
    assert isinstance(data, dict)
    self.shortcutData[shortcut] = data
    self.saveConfig()
  def _removeShortcutData(self, shortcut):
    if not shortcut:
      raise SwineException(self.tr("Shortcut name cannot be empty"))
    if shortcut in self.shortcutData:
      del self.shortcutData[shortcut]
    if self.getDefaultShortcutName() == shortcut:
      self.setDefaultShortcutName(None)
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
      raise SwineException(self.tr("%s does not exist") % drive)
    return path
  def getOldConfigFile(self):
    return os.path.join(self.getPath(), "swine.ini")
  def getConfigFile(self):
    return os.path.join(self.getPath(), "swine_slot.conf")
  def migrateOldConfig(self):
    import ConfigParser, ast
    config = ConfigParser.ConfigParser()
    if os.path.exists(self.getOldConfigFile()):
      with codecs.open(self.getOldConfigFile(), "r", "utf8") as fp:
        config.readfp(fp)
    if not config.has_section("__SYSTEM__"):
      config.add_section("__SYSTEM__")
    self.settings = dict(config.items("__SYSTEM__"))
    for name in config.sections():
      if name != "__SYSTEM__":
        dat = dict(config.items(name))
        if dat["program"] and dat["program"].startswith("["):
          args = ast.literal_eval(dat["program"])
        else:
          args = shlex.split(str(dat["program"]))
        dat["program"] = args[0]
        if "\\\\" in dat["program"]:
          dat["program"] = ast.literal_eval('"'+dat["program"]+'"')
        dat["arguments"] = args[1:]
        self.shortcutData[name] = dat 
  def loadConfig(self):
    if os.path.exists(self.getOldConfigFile()):
      self.migrateOldConfig()
      self.saveConfig()
      os.rename(self.getOldConfigFile(), self.getOldConfigFile()+".old")
    if not os.path.exists(self.getConfigFile()):
      return
    with open(self.getConfigFile(), "r") as fp:
      self.config = json_load(fp)
      self.settings = self.config.get("settings", {})
      self.shortcutData = self.config.get("shortcuts", {})
  def saveConfig(self):
    with open(self.getConfigFile(), "w") as fp:
      json.dump({"settings": self.settings, "shortcuts": self.shortcutData}, fp, indent=2)
  def exists(self):
    return os.path.exists(self.getPath())
  def create(self):
    if self.exists():
      raise SwineException(self.tr("Slot already exists: %s") % self.name)
    self.runWineboot()
    self.loadConfig()
    self.saveConfig()
  def delete(self):
    if self.name == SWINE_DEFAULT_SLOT_NAME:
      raise SwineException(self.tr("Default slot cannot be deleted"))
    if not self.exists():
      raise SwineException(self.tr("Slot does not exist: %s") % self.name)
    for s in self.getAllShortcuts():
      s.delete()
    shutil.rmtree(self.getPath())
  def clone(self, newname):
    if not newname:
      raise SwineException(self.tr("Slot name cannot be empty"))
    if not self.exists():
      raise SwineException(self.tr("Slot does not exist: %s") % self.name)
    assert isinstance(newname, (str, unicode))
    slot = Slot(newname)
    if slot.exists():
      raise SwineException(self.tr("Slot does already exist: %s") % newname)
    shutil.copytree(self.getPath(), slot.getPath(), True)
    slot.loadConfig()
    return slot
  def rename(self, newname):
    if not newname:
      raise SwineException(self.tr("Slot name cannot be empty"))
    if self.name == SWINE_DEFAULT_SLOT_NAME:
      raise SwineException(self.tr("Default slot cannot be renamed"))
    if not self.exists():
      raise SwineException(self.tr("Slot does not exist: %s") % self.name)
    dummySlot = Slot(newname)
    if dummySlot.exists():
      raise SwineException(self.tr("Slot does already exist: %s") % newname)
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
    for name in self.shortcutData:
      shortcuts.append(self.loadShortcut(name))
    return shortcuts
  def hasShortcut(self, name):
    assert name
    return name in self.shortcutData
  def loadShortcut(self,name):
    assert name
    if not self.hasShortcut(name):
      return None
    return Shortcut(name, self, dict(self.shortcutData[name]))
  def getWinePath(self):
    return self["wine_path"]
  def setWinePath(self, path):
    self["wine_path"] = path
    self.saveConfig()
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
  def createShortcutFromFile(self, path):
    name = os.path.splitext(os.path.basename(path))[0]
    shortcut = Shortcut(name, self, virtual=True)
    shortcut.readFromLnk(path)
    return shortcut
  def findLnkFiles(self, onlyNew=False):
    files = []
    for root, dnames, fnames in os.walk(os.path.join(self.getPath(), "drive_c")):
      for fname in fnames:
        if os.path.splitext(fname)[1].lower() == ".lnk":
          files.append(self.unixPathToWin(os.path.join(root,fname)))
    oldfiles = self["known_lnk_files"]
    self["known_lnk_files"] = files
    self.saveConfig()
    if oldfiles and onlyNew:
      files = list(set(files) - set(oldfiles))
    return files
  def runNative(self, prog, cwd=None, wait=True, env=None, stdin=None, stdout=None, stderr=None):
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
  def runWineTool(self, prog, cwd=None, wait=True, stdin=None, stdout=None, stderr=None, debug=None, winePath=False):
    """Run a wine tool (eg wine itself) with prefix and debug environment set
    This is only a wrapper for runNative
    """
    env = os.environ.copy()
    env["WINEPREFIX"] = self.getPath()
    env["WINEARCH"] = self["architecture"]
    env["WINEDEBUG"] = debug if debug else self["debug_line"]
    if not self["allow_menu_entry_creation"]:
      env["WINEDLLOVERRIDES"] = "winemenubuilder.exe=d" #do not add shortcuts to desktop or menu
    global WINE_WRAPPER
    if WINE_WRAPPER and os.path.exists(self.getPath()):
      open(os.path.join(self.getPath(), ".no_prelaunch_window_flag"),"wc").close()
    if winePath is False:
      winePath = self.getWinePath()
    if winePath:
      binPaths = filter(os.path.exists, (os.path.join(winePath, binDir) for binDir in ["bin", "usr/bin"]))
      if binPaths:
        env["PATH"] = os.pathsep.join(binPaths+[os.environ["PATH"]])
        env["WINE"] = filter(os.path.exists, [os.path.join(p, "wine") for p in env["PATH"].split(os.pathsep)])[0]
      libPaths = filter(os.path.exists, (os.path.join(winePath, binDir) for binDir in ["lib", "usr/lib", "lib64", "usr/lib64"]))
      if libPaths:
        env["LD_LIBRARY_PATH"] = os.pathsep.join(libPaths+[os.environ.get("LD_LIBRARY_PATH", os.pathsep.join(["/usr/lib","/lib","/usr/lib64","/lib64"]))])
    return self.runNative(prog, cwd, wait, env, stdin, stdout, stderr)
  def runVerb(self, verbFile):
    return self.runWineTool(["xterm", "-T", "Verb %s" % verbFile, "-hold", "-e", winetricks.WINETRICKS, "--gui", "--no-isolate", verbFile])
  def runWinetricks(self, prog):
    """Run a winetricks command
    This is only a wrapper for runNative
    """
    return self.runWineTool(["xterm", "-T", "Winetricks %s" % prog, "-hold", "-e", winetricks.WINETRICKS, unicode(prog)])
  def runWin(self, prog, workingDirectory=".", wait=True, runInTerminal=False, desktop=None, debug=None, log=None, winePath=False):
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
    if "." in prog[0] and not prog[0].lower().endswith(".exe"):
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
    res = self.runWineTool(prog, cwd, wait=wait, stderr=subprocess.PIPE, debug=debug, winePath=winePath)
    if log:
      with open(log, "w") as fp:
        fp.write(res.stderr_data)
    return res
  def runWinecfg(self, winePath=False):
    return self.runWineTool(["wine", "winecfg"], wait=True, winePath=winePath)
  def runRegedit(self, winePath=False):
    return self.runWineTool(["wine", "regedit"], wait=True, winePath=winePath)
  def runWineboot(self, winePath=False):
    return self.runWineTool(["wine", "wineboot"], wait=True, winePath=winePath)
  def runWinefile(self, directory="C:", winePath=False):
    return self.runWineTool(["wine", "winefile", directory], wait=True, winePath=winePath)
  def runUninstaller(self, winePath=False):
    return self.runWineTool(["wine", "uninstaller"], wait=True, winePath=winePath)
  def runWineControl(self, winePath=False):
    return self.runWineTool(["wine", "control"], wait=True, winePath=winePath)
  def runEject(self, winePath=False):
    return self.runWin(["wine", "eject"], wait=True, winePath=winePath)
  def isWindowsPath(path):
    return W_SEP in path
  def _normalizePath(self, path, sep):
    res = []
    for el in path.split(sep):
      if el == DIR_CUR:
        continue
      elif el == DIR_UP:
        if res:
          res.pop()
      else:
        res.append(el)
    return sep.join(res)
  def winPathToUnix(self, winPath, basedir=None):
    #Handle case-sensitive ambiguities by using existing files/folders when possible
    if (D_SEP + W_SEP) in winPath: #path is absolute
      drive, rest = winPath.split(D_SEP + W_SEP)
      drive = drive.lower()
      unixPath = self.getDosDrivesPath() + U_SEP + drive + D_SEP
    else:
      rest = winPath.replace(W_SEP, U_SEP)
      unixPath = self.winPathToUnix(basedir) if basedir else os.path.curdir
    winEls = rest.split(W_SEP)
    for el in winEls:
      if not os.path.exists(unixPath) or os.path.exists(unixPath + U_SEP + el):
        unixPath += U_SEP + el
      else:
        if "~" in el:
          globStr = "".join([char if char.upper() == char.lower() else "[%s%s]" % (char.upper(), char.lower()) for char in el.split("~")[0]]) + "*"
        else:
          globStr = "".join([char if char.upper() == char.lower() else "[%s%s]" % (char.upper(), char.lower()) for char in el])
        cands = glob.glob(unixPath + U_SEP + globStr)
        if len(cands) == 1:
          unixPath = cands[0]
        else:
          unixPath += U_SEP + el
    return os.path.realpath(unixPath)
  def unixPathToWin(self, unixPath, basedir=None, drive=None):
    if not os.path.isabs(unixPath) and basedir:
      unixPath = basedir + U_SEP + unixPath
    if drive:
      unixPath = os.path.realpath(unixPath)
      drivePath = os.path.realpath(self.getDosDrivesPath() + U_SEP + drive + D_SEP)
      rel = os.path.relpath(unixPath, drivePath)
      if not rel.startswith(DIR_UP):
        rel = rel.replace(U_SEP, W_SEP)
        return drive + D_SEP + W_SEP + rel
    else:
      path = None
      for drive in os.listdir(self.getDosDrivesPath()):
        driveName = drive.replace(D_SEP, '')
        p = self.unixPathToWin(unixPath, drive=driveName)
        if not p:
          continue
        if not path or len(p) < len(path):
          path = p
      return path
  def exportData(self, archive):
    if not archive:
      raise SwineException(self.tr("File name cannot be empty"))
    os.chdir(self.getPath())
    with TarFile.gzopen(archive, "w") as tar:
      tar.add(".") #recursive
  def importData(self, archive):
    if not archive:
      raise SwineException(self.tr("File name cannot be empty"))
    os.chdir(self.getPath())
    with TarFile.gzopen(archive, "r") as tar:
      tar.extractall(".")
    self.loadConfig()

    
def importSlot(name, archive):
  if not archive:
    raise SwineException(self.tr("File name cannot be empty"))
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
  try:
    config.load()
  except:
    import traceback
    traceback.print_exc()
    print >>sys.stderr, tr("Config could not be loaded")
  for path in [WINE_PATH, SWINE_PATH, SWINE_SLOT_PATH]:
    if not os.path.exists(path):
      os.mkdir(path)
      print tr("created %s") % path
  if not os.path.exists(SWINE_DEFAULT_SLOT_PATH):
    os.symlink(WINE_PATH, SWINE_DEFAULT_SLOT_PATH)
    print tr("symlinked %s to %s") % (SWINE_DEFAULT_SLOT_PATH, WINE_PATH)
  global WINE_WRAPPER
  WINE_WRAPPER = "text" in os.popen('file `which wine`', 'r').read()
  global defaultSlot
  defaultSlot = loadDefaultSlot()
  winetricks.init()

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
  
def getWineVersion(path):
  if path:
    valid = True
    for f in ["bin/wine", "lib/wine/fakedlls"]:
      valid = valid and os.path.exists(os.path.join(path, f))
    if not valid:
      return None
  proc = defaultSlot.runWineTool(["wine", "--version"], winePath=path, stdout=subprocess.PIPE, wait=True)
  return proc.stdout_data.strip() if proc.stdout_data else None
    
def findWinePaths():
  return filter(getWineVersion, sum(map(glob.glob, config.WINE_PATH_CANDIDATES), []))
  
try:
  init()
except Exception, data:
  print data
  sys.exit(-1)
