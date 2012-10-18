# -*- coding: utf-8 -*-
############################################################################
#    Copyright (C) 2012 by Dennis Schwerdel, Thomas Schmidt                #
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

import os 

os.environ['PATH'] += ":" + os.path.dirname(__file__)

VERSION="1.0.3" #no spaces here, line is interpreted by bash

HOME_PATH = os.getenv("HOME")
SWINE_PATH = os.path.join(HOME_PATH, ".swine")
SWINE_CONFIG = os.path.join(SWINE_PATH, "swine.conf")
SWINE_SLOT_PATH = SWINE_PATH
SWINE_DEFAULT_SLOT_NAME = "DEFAULT"
SWINE_DEFAULT_SLOT_PATH = os.path.join(SWINE_PATH, SWINE_DEFAULT_SLOT_NAME)
WINE_PATH = os.path.join(HOME_PATH, ".wine")
REAL_PATH = os.path.dirname(os.path.realpath(__file__))
DESKTOP_MENU_DIR = os.path.join(HOME_PATH, ".local/share/applications/swine")
TRANSLATION_DIRS = ["translations", "/usr/share/swine/translations", "/usr/local/share/swine/translations"]
SWINE_WEBSITE = "http://dswd.github.com/Swine"
APPDB_WEBSITE = "http://appdb.winehq.org"
WINE_PATH_CANDIDATES = ["/opt/*[wW]ine*", "/opt/*[wW]ine*/*", "/usr/local", "/usr/local/*[wW]ine*", "/usr/local/*[wW]ine*/*", "/home/*/.PlayOnLinux/wine/*", "/home/*/.PlayOnLinux/wine/*/*"]

def tr(s, context="@default"):
  return unicode(s)

import json
try:
  from collections import OrderedDict
  def json_load(fp):
    return json.load(fp, object_pairs_hook=OrderedDict)
except: #Python 2.6
  OrderedDict = dict
  json_load = json.load

_config = {}
  
def load():
  if not os.path.exists(SWINE_CONFIG):
    return
  with open(SWINE_CONFIG, "r") as fp:
    global _config
    _config = json_load(fp)

def save():
  with open(SWINE_CONFIG, "w") as fp:
    json.dump(_config, fp, indent=2)

_defaults = {
  "wine_paths": {},
  "default_wine_path": None,
  "allow_menu_entry_creation": False,
  "auto_import_shortcuts": True,
  "debug_line": "err+all,warn-all,fixme-all,trace-all",
  "architecture": "win32",
}
    
def setValue(key, value):
  _config[key]=value
  
def getValue(key):
  return _config.get(key, _defaults.get(key, None))

def delete(key):
  del _config[key]
