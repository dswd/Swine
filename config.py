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

VERSION = "0.7-rc2"

HOME_PATH = os.getenv("HOME")
SWINE_PATH = os.path.join(HOME_PATH, ".swine")
SWINE_SLOT_PATH = SWINE_PATH
SWINE_DEFAULT_SLOT_NAME = "DEFAULT"
SWINE_DEFAULT_SLOT_PATH = os.path.join(SWINE_PATH, SWINE_DEFAULT_SLOT_NAME)
WINE_PATH = os.path.join(HOME_PATH, ".wine")
WINETRICKS = "winetricks"
REAL_PATH = os.path.dirname(os.path.realpath(__file__))
WISRUN = os.path.join(REAL_PATH, "/wisrun")
DESKTOP_MENU_DIR = os.path.join(HOME_PATH, ".local/share/applications/swine")
TRANSLATION_DIRS = ["translations", "/usr/share/swine/translations", "/usr/local/share/swine/translations"]

def tr(s, context="@default"):
  return s
