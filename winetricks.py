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

import sys, os, json, subprocess
from config import *

try:
  from collections import OrderedDict
  def json_load(fp):
    return json.load(fp, object_pairs_hook=OrderedDict)
except: #Python 2.6
  OrderedDict = dict
  json_load = json.load

CACHEFILE = os.path.join(SWINE_PATH, "winetricks.cache")
VERSION_FIELD = "_version"
WINETRICKS = "winetricks"

def discover():
  global WINETRICKS
  for path in [SWINE_PATH] + os.environ['PATH'].split(":"):
    path = os.path.join(path, "winetricks")
    if os.path.exists(path):
      WINETRICKS = path
      break
      
def loadCache():
  cache = {}
  if os.path.exists(CACHEFILE):
    with open(CACHEFILE, "r") as fp:
      cache = json_load(fp)
  return cache
  
def saveCache():
  cache[VERSION_FIELD] = version
  with open(CACHEFILE, "w") as fp:
    json.dump(cache, fp, indent=2)
  
def call(args, plain=False, shell=False):
  if isinstance(args, str):
    args = [args]
  if not plain:
    args = [WINETRICKS]+args
  proc = subprocess.Popen(args, stdout=subprocess.PIPE, shell=shell)
  (stdout, stderr) = proc.communicate()
  if proc.returncode:
    raise Exception(tr("Command failed: %s") % stderr)
  return stdout

def showHelp():
  call("help")

def download():
  dst = os.path.join(SWINE_PATH, "winetricks")
  call("wget http://winetricks.org/winetricks --quiet -O %(path)s && chmod +x %(path)s" % {"path": dst}, plain=True, shell=True)
  init()
  
def getCacheVersion():
  return cache.get(VERSION_FIELD, None)
    
def loadOptions():
  global cache
  cache = OrderedDict()
  sections = call("list").splitlines()
  for sec in sections:
    cache[sec] = OrderedDict()
    items = call([sec, "list"]).splitlines()
    for item in items:
      (name, desc) = item.split(" ", 1)
      cache[sec][name] = desc.strip()
  
def sections():
  return filter(lambda s: s != VERSION_FIELD, cache.keys())
  
def options(section):
  return cache[section].iteritems()

def init():
  global cache, version
  cache = loadCache()
  discover()
  try:
    version = call("--version").strip()
  except:
    version = None
  if version:
    if getCacheVersion() != version:
      print >>sys.stderr, tr("Loading winetricks entries...")
      loadOptions()
      saveCache()
  else:
    print >>sys.stderr, tr("WARNING: Winetricks binary not found")
    cache = {}
    saveCache()
  
def debug():
  for sec in sections():
    print sec
    for (name, desc) in options(sec):
      print "\t%s\t%s" % (name, desc)