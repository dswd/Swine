#!/usr/bin/env python

############################################################################
#    Copyright (C) 2007 by Dennis Schwerdel, Thomas Schmidt                #
#                                                                          #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
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

import os, sys
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

import swinelib, getopt
from swinelib import *

def usage():
	print '''Usage:
		--list
	-l,	--listSlots
	-L,	--listShortcuts SLOTNAME
	-C,	--create SLOTNAME
	-r,	--runShortcut SLOT | SLOT:SHORTCUT
	-R,	--run SLOTNAME PROGRAM [ARGUMENTS]
	-I,	--importShortcuts SLOTNAME
	-w,	--winecfg SLOTNAME'''

try:
	opts, otherargs = getopt.getopt(sys.argv[1:], "hlL:C:r:R:I:w:", ["help", "list", "listSlots", "listShortcuts=", "create=", "runShortcut=", "run=", "winecfg=", "importShortcuts="])
except getopt.GetoptError:
	# print help information and exit:
	usage()
	sys.exit(2)
for opt, val in opts:
	if opt in ("-h", "--help"):
		usage()

	elif opt in ("--list"):
		for slot in getAllSlots():
			print slot.name + "	default: " + str(slot.loadDefaultShortcut())
			for shortcut in slot.getAllShortcuts():
				print " |- " + shortcut.name + " : " + shortcut.data['program']
			print

	elif opt in ("-l","--listSlots"):
		for slot in getAllSlots():
			print slot.name + "	default: " + str(slot.loadDefaultShortcut())

	elif opt in ("-L","--listShortcuts"):
		slot = loadSlot(val)
		for shortcut in slot.getAllShortcuts():
			print shortcut.name + " : " + shortcut.data['program']

	elif opt in ("-I","--importShortcuts"):
		slot = loadSlot(val)
		for shortcut in slot.findShortcuts(True):
			shortcut.save()
		slot.saveConfig()

	elif opt in ("-C","--create"):
		Slot(val).create()

	elif opt in ("-w","--winecfg"):
		loadSlot(val).runWinecfg()

	elif opt in ("-r","--runShortcut"): 
		slot = val.split(":",1)
		if len(slot) == 1:
			print loadSlot(slot[0]).loadDefaultShortcut().run()
		else:
			print loadSlot(slot[0]).loadShortcut(slot[1]).run()
		try:
			os.wait()
		except Exception:
			print "killed"

	elif opt in ("-R","--run"): 
		print loadSlot(val).runWin(otherargs)
		try:
			os.wait()
		except Exception:
			print "killed"

	else:
		usage()
