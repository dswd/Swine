#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

import os, sys, traceback
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

import swinelib
import time
from swinelib import *
from qt import *
from threading import Thread
from AboutDialog import *
from ProgramDialog import *
from MainWindow import *

IMAGE_FOLDER = os.path.dirname(os.path.realpath(__file__)) + "/images/"
def loadPixmap ( name ):
	return QPixmap(QString(IMAGE_FOLDER+name))

def loadIcon ( name ):
	pm = QPixmap ( name )
	if not pm or pm.isNull():
		pm = loadPixmap("wabi.png")
	return QPixmap ( pm.convertToImage().smoothScale(32,32,QImage.ScaleMin) )

class SwineSlotItem(QListBoxPixmap):
	def __init__(self,parent,slot):
		self.slot=slot
		self.pixmap = loadPixmap("folder.png")
		shortcut = self.slot.loadDefaultShortcut()
		if shortcut:
			if shortcut.data.has_key("icon") and os.path.exists ( shortcut.data["icon"] ) :
				self.pixmap = loadIcon ( shortcut.data["icon"] )
		QListBoxPixmap.__init__(self,parent,self.pixmap,unicode(slot.name))
		self.listBox().sort()
	def mainWindow(self):
		return self.listBox().topLevelWidget()
	def refreshShortcutList(self):
		self.mainWindow().slotList_selectionChanged()
	def delete_cb(self):
		if QMessageBox.warning ( self.listBox(), "Delete Slot", "Are you sure ?", "&Yes", "&No", QString.null, 0, 1 ) == 0:
			self.slot.delete()
			self.listBox().takeItem(self)
	def rename_cb(self):
		result = QInputDialog.getText ( "Rename Slot", "New name:", QLineEdit.Normal, unicode(self.slot.name) )
		if result[1] and len(result[0]) > 0:
			self.slot.rename ( unicode(result[0]) )
			self.setText ( self.slot.name )
			self.listBox().sort()
	def copy_cb(self):
		result = QInputDialog.getText ( "Copy Slot", "New name:", QLineEdit.Normal, "New Slot" )
		if result[1]:
			self.slot.clone ( unicode ( result[0] ) )
			slot = Slot(unicode(result[0]))
			slot.loadConfig()
			SwineSlotItem(self.mainWindow().slotList,slot)
	def searchShortcuts_cb(self):
		for shortcut in self.slot.findShortcuts(False):
			shortcut.save()
		self.slot.saveConfig()
		self.refreshShortcutList()
	def run_cb(self):
		runDialog = SwineRunDialog(self.slot,self.mainWindow())
		runDialog.show()
	def filemanager_cb(self):
		self.slot.runWinefile()
	def shell_cb(self):
		self.slot.runWin(["cmd.exe"],runInTerminal=True)
	def taskmgr_cb(self):
		self.slot.runWin(["taskmgr.exe"])
	def runDefault_cb(self):
		if self.slot.loadDefaultShortcut():
			self.slot.loadDefaultShortcut().run()
	def export_cb(self):
		file = QFileDialog.getSaveFileName ( QString.null, "Swine Slots (*.swine)", self.mainWindow() )
		if not file:
			return
		if not os.path.splitext(str(file))[1].lower() == '.swine':
			file = str(file) + ".swine"
		self.slot.exportData ( str(file) )
	def import_cb(self):
		file = QFileDialog.getOpenFileName ( QString.null, "Swine Slots (*.swine)", self.mainWindow() )
		if file:
			self.slot.importData ( str(file) )
			self.refreshShortcutList()
	def wisrun_cb(self):
		file = QFileDialog.getOpenFileName ( QString.null, "WIS Scripts (*.wis)", self.mainWindow() )
		if file:
			self.slot.runWis ( os.path.realpath(str(file)) )
	def height(self,lb):
		return QListBoxPixmap.height(self,lb)+6
	def winetricks(self,tool):
		self.slot.runWinetricks(tool)
	def winetricks_callback(self,tool):
		return lambda x: self.winetricks(tool)

class SwineShortcutItem(QIconViewItem):
	def __init__(self,parent,shortcut):
		self.shortcut=shortcut
		name=shortcut.name
		if shortcut.isDefault():
			name = name + "*"
		QIconViewItem.__init__(self,parent,unicode(name),loadPixmap("wabi.png"))
		self.setRenameEnabled(False)
		self.setDragEnabled(False)
		if shortcut.data.has_key("icon") and os.path.exists ( shortcut.data["icon"] ):
			self.setPixmap ( loadIcon ( shortcut.data["icon"] ) )
	def mainWindow(self):
		return self.iconView().topLevelWidget()
	def refreshShortcutList(self):
		self.mainWindow().slotList_selectionChanged()
	def delete_cb(self):
		self.shortcut.delete()
		self.shortcut.slot.saveConfig()
		self.iconView().takeItem(self)
	def rename_cb(self):
		result = QInputDialog.getText ( "Rename Shortcut", "New name:", QLineEdit.Normal, unicode(self.shortcut.name) )
		if result[1]:
			self.shortcut.rename ( unicode ( result[0] ) )
			self.shortcut.slot.saveConfig()
			self.setText ( unicode ( self.shortcut.name ) )
	def copy_cb(self):
		result = QInputDialog.getText ( "Copy Shortcut", "New name:", QLineEdit.Normal, "New Shortcut" )
		if result[1]:
			self.shortcut.clone ( unicode ( result[0] ) )
			self.shortcut.slot.saveConfig()
			self.refreshShortcutList()	
	def edit_cb(self):
		dialog = SwineShortcutDialog ( self.shortcut, self.mainWindow(), "Edit Shortcut" )
		if dialog.exec_loop() == 1:
			self.shortcut.rename(unicode(self.shortcut.name))
			self.shortcut.save()
			self.shortcut.slot.saveConfig()
			self.mainWindow().slotList_selectionChanged()
	def setDefault_cb(self):
		self.shortcut.setDefault()
		self.shortcut.slot.saveConfig()
		main = self.mainWindow()
		main.slotList.takeItem (main.currentSlotItem())
		item = SwineSlotItem (main.slotList,self.shortcut.slot)
		main.slotList.setCurrentItem ( item )
	def createMenuEntry_cb(self):
		self.shortcut.createMenuEntry()
		QMessageBox.information ( self.mainWindow(), "Menu Entry", "Menu entry for "+unicode(self.shortcut.name)+" has been created" )
	def removeMenuEntry_cb(self):
		self.shortcut.removeMenuEntry()
		QMessageBox.information ( self.mainWindow(), "Menu Entry", "Menu entry for "+unicode(self.shortcut.name)+" has been removed" )
		



class SwineMainWindow(MainWindow):
	def currentSlotItem(self):
		item = self.slotList.selectedItem()
		if item and item.isSelected():
			return item
		return None
	def currentShortcutItem(self):
		item = self.shortcutList.currentItem()
		if item and item.isSelected():
			return item
		return None

	def createShortcutMenu(self, shortcut, parent):
		menu = QPopupMenu(parent)
		menu.insertItem( QIconSet(loadPixmap("application_add.png")), "&New Shortcut", self.createShortcut_cb )
		if not shortcut == None:
			menu.insertSeparator()
			menu.insertItem( QIconSet(loadPixmap("cog.png")), "&Run", shortcut.shortcut.run )
			menu.insertSeparator()
			menu.insertItem( QIconSet(loadPixmap("lightning_add.png")), "&Set Default", shortcut.setDefault_cb )
			if shortcut.shortcut.hasMenuEntry():
				menu.insertItem( QIconSet(loadPixmap("lightning_delete.png")), "&Remove Menu Entry", shortcut.removeMenuEntry_cb )
			else:
				menu.insertItem( QIconSet(loadPixmap("lightning_add.png")), "&Create Menu Entry", shortcut.createMenuEntry_cb )
			menu.insertSeparator()
			menu.insertItem( QIconSet(loadPixmap("application_edit.png")), "&Edit", shortcut.edit_cb )
			menu.insertItem( QIconSet(loadPixmap("textfield_rename.png")), "Re&name", shortcut.rename_cb )
			menu.insertItem( QIconSet(loadPixmap("arrow_divide.png")), "&Copy", shortcut.copy_cb )
			menu.insertItem( QIconSet(loadPixmap("application_delete.png")), "&Delete", shortcut.delete_cb )
		return menu
		
	def createSlotMenu(self, slot, parent):
		menu = QPopupMenu(parent)
		menu.insertItem( QIconSet(loadPixmap("drive_add.png")), "&New Slot", self.createSlot_cb )
		if slot == None:
			menu.insertItem( QIconSet(loadPixmap("package_add.png")), "&Import Slot", self.import_cb )
		if not slot == None:
			menu.insertSeparator()
			menu.insertItem( QIconSet(loadPixmap("application_lightning.png")), "Run default", slot.runDefault_cb )
			menu.insertItem( QIconSet(loadPixmap("application.png")), "&Run...", slot.run_cb )
			menu.insertSeparator()
			toolsMenu = QPopupMenu(self)
			toolsMenu.insertItem( QIconSet(loadPixmap("application_xp_terminal.png")), "&Shell", slot.shell_cb )
			toolsMenu.insertItem( QIconSet(loadPixmap("folder_explore.png")), "&File Manager", slot.filemanager_cb )
			toolsMenu.insertItem( QIconSet(loadPixmap("application_form_magnify.png")), "&Taskmanager", slot.taskmgr_cb )
			toolsMenu.insertSeparator()
			toolsMenu.insertItem( QIconSet(loadPixmap("computer_edit.png")), "&Winecfg", slot.slot.runWinecfg )
			toolsMenu.insertItem( QIconSet(loadPixmap("wrench.png")), "&Start Regedit", slot.slot.runRegedit )
			toolsMenu.insertItem( QIconSet(loadPixmap("application_delete.png")), "&Uninstall Software", slot.slot.runUninstaller )
			toolsMenu.insertItem( QIconSet(loadPixmap("computer.png")), "&Control-Center", slot.slot.runWineControl )
			menu.insertItem( QIconSet(loadPixmap("wrench_orange.png")), "&Tools", toolsMenu )
			commandsMenu = QPopupMenu(self)
			commandsMenu.insertItem( QIconSet(loadPixmap("drive_magnify.png")), "&Import Shortcuts", slot.searchShortcuts_cb )
			commandsMenu.insertItem( QIconSet(loadPixmap("arrow_refresh.png")), "&Reboot wine", slot.slot.runWineboot )
			commandsMenu.insertItem( QIconSet(loadPixmap("drive_cd.png")), "&Eject CD", slot.slot.runEject )
			commandsMenu.insertSeparator()
			commandsMenu.insertItem( QIconSet(loadPixmap("package_go.png")), "&Export", slot.export_cb )
			commandsMenu.insertItem( QIconSet(loadPixmap("package_add.png")), "Import &Data", slot.import_cb )
			menu.insertItem( QIconSet(loadPixmap("cog.png")), "&Commands", commandsMenu )
			
			menu.insertItem( QIconSet(loadPixmap("script_gear.png")), "&Run WIS script", slot.wisrun_cb) 
			
			winetricksMenu = QPopupMenu(self)
			
			winetricksMenu.insertItem( QIconSet(loadPixmap("script_gear.png")), "&Call Winetricks", slot.winetricks_callback("") )
			
			winetricksAppsMenu = QPopupMenu(self)
			winetricksAppsMenu.insertItem( QIconSet(loadPixmap("application_add.png")), "Unix apps for Windows (needed by some build scripts)", slot.winetricks_callback("cygwin") )
			winetricksAppsMenu.insertItem( QIconSet(loadPixmap("application_add.png")), "KDE for Windows installer", slot.winetricks_callback("kde") )
			winetricksMenu.insertItem( QIconSet(loadPixmap("application.png")), "&Applications", winetricksAppsMenu )

			winetricksBrowserMenu = QPopupMenu(self)
			winetricksBrowserMenu.insertItem( QIconSet(loadPixmap("world_add.png")), "Set registry to claim IE6sp1 is installed", slot.winetricks_callback("fakeie6") )
			winetricksBrowserMenu.insertItem( QIconSet(loadPixmap("world_add.png")), "The HTML rendering Engine (Mozilla), with debugging symbols", slot.winetricks_callback("gecko-dbg") )
			winetricksBrowserMenu.insertItem( QIconSet(loadPixmap("world_add.png")), "The HTML rendering Engine (Mozilla)", slot.winetricks_callback("gecko") )
			winetricksBrowserMenu.insertItem( QIconSet(loadPixmap("world_add.png")), "Firefox web browser", slot.winetricks_callback("firefox") )
			winetricksBrowserMenu.insertItem( QIconSet(loadPixmap("world_add.png")), "Microsoft Internet Explorer 6.0", slot.winetricks_callback("ie6") )
			winetricksBrowserMenu.insertItem( QIconSet(loadPixmap("world_add.png")), "Microsoft Internet Explorer 7.0", slot.winetricks_callback("ie7") )
			winetricksMenu.insertItem( QIconSet(loadPixmap("world.png")), "&Browser", winetricksBrowserMenu )
			
			winetricksMediaMenu = QPopupMenu(self)
			winetricksMediaMenu.insertItem( QIconSet(loadPixmap("film_add.png")), "All listed codecs (xvid, ffdshow, icodecs)", slot.winetricks_callback("allcodecs") )
			winetricksMediaMenu.insertSeparator()
			winetricksMediaMenu.insertItem( QIconSet(loadPixmap("film_add.png")), "divx video codec", slot.winetricks_callback("divx") )
			winetricksMediaMenu.insertItem( QIconSet(loadPixmap("film_add.png")), "ffdshow video codecs", slot.winetricks_callback("ffdshow") )
			winetricksMediaMenu.insertItem( QIconSet(loadPixmap("film_add.png")), "Intel Codecs (Indeo)", slot.winetricks_callback("icodecs") )
			winetricksMediaMenu.insertItem( QIconSet(loadPixmap("film_add.png")), "ogg filters/codecs: flac, theora, speex, vorbis, schroedinger", slot.winetricks_callback("ogg") )
			winetricksMediaMenu.insertItem( QIconSet(loadPixmap("film_add.png")), "xvid video codec", slot.winetricks_callback("xvid") )
			winetricksMediaMenu.insertSeparator()
			winetricksMediaMenu.insertItem( QIconSet(loadPixmap("film_add.png")), "Apple Quicktime 7.2", slot.winetricks_callback("quicktime72") )
			winetricksMediaMenu.insertItem( QIconSet(loadPixmap("film_add.png")), "Adobe Flash Player ActiveX and firefox plugins", slot.winetricks_callback("flash") )
			winetricksMediaMenu.insertItem( QIconSet(loadPixmap("film_add.png")), "Adobe Shockwave Player", slot.winetricks_callback("shockwave") )
			winetricksMediaMenu.insertSeparator()
			winetricksMediaMenu.insertItem( QIconSet(loadPixmap("film_add.png")), "Media Player Classic", slot.winetricks_callback("mpc") )
			winetricksMediaMenu.insertItem( QIconSet(loadPixmap("film_add.png")), "VLC media player", slot.winetricks_callback("vlc") )
			winetricksMediaMenu.insertItem( QIconSet(loadPixmap("film_add.png")), "MS Windows Media Encoder 9 (requires Windows license)", slot.winetricks_callback("wme9") )
			winetricksMediaMenu.insertItem( QIconSet(loadPixmap("film_add.png")), "MS Windows Media Player 10 (requires Windows license)", slot.winetricks_callback("wmp10") )
			winetricksMediaMenu.insertItem( QIconSet(loadPixmap("film_add.png")), "MS Windows Media Player 9 (requires Windows license)", slot.winetricks_callback("wmp9") )
			winetricksMediaMenu.insertSeparator()
			winetricksMediaMenu.insertItem( QIconSet(loadPixmap("film_add.png")), "Standard RGB color profile", slot.winetricks_callback("colorprofile") )
			winetricksMenu.insertItem( QIconSet(loadPixmap("film.png")), "&Multimedia", winetricksMediaMenu )
			
			winetricksFontsMenu = QPopupMenu(self)
			winetricksFontsMenu.insertItem( QIconSet(loadPixmap("font_add.png")), "Install all listed fonts (corefonts, tahoma, liberation)", slot.winetricks_callback("allfonts") )
			winetricksFontsMenu.insertSeparator()
			winetricksFontsMenu.insertItem( QIconSet(loadPixmap("font_add.png")), "Install MS Corefonts: Arial, Courier, Times fonts", slot.winetricks_callback("corefonts") )
			winetricksFontsMenu.insertItem( QIconSet(loadPixmap("font_add.png")), "Install Red Hat Liberation fonts (Sans, Serif, Mono)", slot.winetricks_callback("liberation") )
			winetricksFontsMenu.insertItem( QIconSet(loadPixmap("font_add.png")), "Install MS Tahoma font (not part of corefonts)", slot.winetricks_callback("tahoma") )
			winetricksFontsMenu.insertItem( QIconSet(loadPixmap("font_add.png")), "Install Droid fonts (on LCD, looks better with fontsmooth-rgb)", slot.winetricks_callback("droid") )
			winetricksFontsMenu.insertItem( QIconSet(loadPixmap("font_add.png")), "Install WenQuanYi CJK font (on LCD looks better with fontsmooth-rgb)", slot.winetricks_callback("wenquanyi") )
			winetricksFontsMenu.insertSeparator()			
			winetricksFontsMenu.insertItem( QIconSet(loadPixmap("wrench_orange.png")), "Fix bad fonts which cause crash in some apps (e.g. .net)", slot.winetricks_callback("fontfix") )
			winetricksFontsMenu.insertItem( QIconSet(loadPixmap("wrench_orange.png")), "Enable subpixel smoothing for BGR LCDs", slot.winetricks_callback("fontsmooth-bgr") )
			winetricksFontsMenu.insertItem( QIconSet(loadPixmap("wrench_orange.png")), "Enable grayscale font smoothing", slot.winetricks_callback("fontsmooth-gray") )
			winetricksFontsMenu.insertItem( QIconSet(loadPixmap("wrench_orange.png")), "Enable subpixel smoothing for RGB LCDs", slot.winetricks_callback("fontsmooth-rgb") )
			winetricksFontsMenu.insertItem( QIconSet(loadPixmap("wrench_orange.png")), "Disable font smoothing", slot.winetricks_callback("fontsmooth-disable") )
			winetricksMenu.insertItem( QIconSet(loadPixmap("font.png")), "&Fonts", winetricksFontsMenu )
			
			winetricksDirectXMenu = QPopupMenu(self)
			winetricksDirectXMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS ActiveX Control Pad", slot.winetricks_callback("controlpad") )
			winetricksDirectXMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS d3dx9_??.dll (from DirectX 9 user redistributable)", slot.winetricks_callback("d3dx9") )
			winetricksDirectXMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS dinput8.dll (from DirectX 9 user redistributable)", slot.winetricks_callback("dinput8") )
			winetricksDirectXMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS DirectPlay (from DirectX 9 user redistributable)", slot.winetricks_callback("directplay") )
			winetricksDirectXMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS DirectX 9 user redistributable (not recommended! use d3dx9 instead)", slot.winetricks_callback("directx9") )
			winetricksDirectXMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "the obsolete Dirac 0.8 directshow filter", slot.winetricks_callback("dirac0.8") )
			winetricksMenu.insertItem( QIconSet(loadPixmap("plugin.png")), "&DirectX", winetricksDirectXMenu )
			
			winetricksDotNetMenu = QPopupMenu(self)
			winetricksDotNetMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS .NET 1.1 (requires Windows license)", slot.winetricks_callback("dotnet11") )
			winetricksDotNetMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS .NET 2.0 (requires Windows license)", slot.winetricks_callback("dotnet20") )
			winetricksDotNetMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS .NET 2.0 sp2 (requires Windows license)", slot.winetricks_callback("dotnet20sp2") )
			winetricksDotNetMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS .NET 3.0 (requires Windows license, might not work yet)", slot.winetricks_callback("dotnet30") )
			winetricksMenu.insertItem( QIconSet(loadPixmap("plugin.png")), "&.Net", winetricksDotNetMenu )

			winetricksLibsMenu = QPopupMenu(self)
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS Access 2000 runtime.  Requires Access 2000 Dev license!", slot.winetricks_callback("art2kmin") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "Adobe Type Manager. Needed for Adobe CS4", slot.winetricks_callback("atmlib") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS common controls 5.80", slot.winetricks_callback("comctl32") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS comctl32.ocx and mscomctl.ocx, comctl32 wrappers for VB6", slot.winetricks_callback("comctl32.ocx") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS DCOM (ole32, oleaut32); requires Win98 license!", slot.winetricks_callback("dcom98") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS Forms 2.0 Object Library", slot.winetricks_callback("fm20") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS gdiplus.dll (from powerpoint viewer)", slot.winetricks_callback("gdiplus") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS Jet 4.0 Service Pack 8", slot.winetricks_callback("jet40") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS MDAC 2.5: Microsoft ODBC drivers, etc.", slot.winetricks_callback("mdac25") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS MDAC 2.7", slot.winetricks_callback("mdac27") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS MDAC 2.8", slot.winetricks_callback("mdac28") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS mfc40 (Microsoft Foundation Classes from Visual C++ 4)", slot.winetricks_callback("mfc40") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS mfc42 (same as vcrun6 below)", slot.winetricks_callback("mfc42") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "mono-2.0.1", slot.winetricks_callback("mono20") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "mono-2.2", slot.winetricks_callback("mono22") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "mono-2.4", slot.winetricks_callback("mono24") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS Hierarchical Flex Grid Control", slot.winetricks_callback("mshflxgd") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS Installer 2.0", slot.winetricks_callback("msi2") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS Line Services 3.1 (needed by native riched?)", slot.winetricks_callback("msls31") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS Masked Edit Control", slot.winetricks_callback("msmask") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS Script Control", slot.winetricks_callback("msscript") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS XML version 3", slot.winetricks_callback("msxml3") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS XML version 4", slot.winetricks_callback("msxml4") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS XML version 6", slot.winetricks_callback("msxml6") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS 16 bit OLE", slot.winetricks_callback("ole2") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS pdh.dll (Performance Data Helper)", slot.winetricks_callback("pdh") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "NVIDIA/AGEIA PhysX runtime", slot.winetricks_callback("physx") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS riched20 and riched32", slot.winetricks_callback("riched20") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS riched30", slot.winetricks_callback("riched30") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS urlmon.dll", slot.winetricks_callback("urlmon") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS Visual Basic 2 runtime", slot.winetricks_callback("vb2run") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS Visual Basic 3 runtime", slot.winetricks_callback("vb3run") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS Visual Basic 4 runtime", slot.winetricks_callback("vb4run") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS Visual Basic 5 runtime", slot.winetricks_callback("vb5run") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS Visual Basic 6 runtime", slot.winetricks_callback("vb6run") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS Visual C++ 2003 libraries (mfc71,msvcp71,msvcr71)", slot.winetricks_callback("vcrun2003") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS Visual C++ 2005 sp1 libraries (mfc80,msvcp80,msvcr80)", slot.winetricks_callback("vcrun2005") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS Visual C++ 2008 libraries (mfc90,msvcp90,msvcr90)", slot.winetricks_callback("vcrun2008") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS Visual C++ 6 sp4 libraries (mfc42, msvcp60, msvcrt)", slot.winetricks_callback("vcrun6") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS Visual J# 2.0 SE libraries (requires dotnet20)", slot.winetricks_callback("vjrun20") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS wininet.dll (requires Windows license)", slot.winetricks_callback("wininet") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS Windows scripting 5.6, jscript only, no cscript", slot.winetricks_callback("wsh56js") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS Windows Scripting Host 5.6", slot.winetricks_callback("wsh56") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS Windows scripting 5.6, vbscript only, no cscript", slot.winetricks_callback("wsh56vb") )
			winetricksLibsMenu.insertItem( QIconSet(loadPixmap("plugin_add.png")), "MS XACT Engine (x3daudio?_?.dll, xactengine?_?.dll)", slot.winetricks_callback("xact") )
			winetricksMenu.insertItem( QIconSet(loadPixmap("plugin.png")), "&Libraries", winetricksLibsMenu )

			winetricksDevelopMenu = QPopupMenu(self)
			winetricksDevelopMenu.insertItem( QIconSet(loadPixmap("pencil_add.png")), "Autohotkey (open source gui scripting language)", slot.winetricks_callback("autohotkey") )
			winetricksDevelopMenu.insertItem( QIconSet(loadPixmap("pencil_add.png")), "CMake, the cross-platform, open-source build system", slot.winetricks_callback("cmake") )
			winetricksDevelopMenu.insertItem( QIconSet(loadPixmap("pencil_add.png")), "GDB for MinGW", slot.winetricks_callback("mingw-gdb") )
			winetricksDevelopMenu.insertItem( QIconSet(loadPixmap("pencil_add.png")), "Minimalist GNU for Windows, including GCC for Windows!", slot.winetricks_callback("mingw") )
			winetricksDevelopMenu.insertItem( QIconSet(loadPixmap("pencil_add.png")), "Open Watcom C/C++ compiler (can compile win16 code!)", slot.winetricks_callback("openwatcom") )
			winetricksDevelopMenu.insertItem( QIconSet(loadPixmap("pencil_add.png")), "MS Platform SDK 2003", slot.winetricks_callback("psdk2003") )
			winetricksDevelopMenu.insertItem( QIconSet(loadPixmap("pencil_add.png")), "MS Vista SDK (does not install yet)", slot.winetricks_callback("psdkvista") )
			winetricksDevelopMenu.insertItem( QIconSet(loadPixmap("pencil_add.png")), "MS Windows 7 SDK (installing just headers and c++ compiler works)", slot.winetricks_callback("psdkwin7") )
			winetricksDevelopMenu.insertItem( QIconSet(loadPixmap("pencil_add.png")), "Python 2.6.2 (and pywin32)", slot.winetricks_callback("python26") )
			winetricksDevelopMenu.insertItem( QIconSet(loadPixmap("pencil_add.png")), "MS Visual C++ 2005 Express", slot.winetricks_callback("vc2005express") )
			winetricksDevelopMenu.insertItem( QIconSet(loadPixmap("pencil_add.png")), "MS Visual C++ 2005 Express SP1 (does not work yet)", slot.winetricks_callback("vc2005expresssp1") )
			winetricksDevelopMenu.insertItem( QIconSet(loadPixmap("pencil_add.png")), "MS Visual C++ 2005 Service Pack 1 (install trial 1st)", slot.winetricks_callback("vc2005sp1") )
			winetricksDevelopMenu.insertItem( QIconSet(loadPixmap("pencil_add.png")), "MS Visual C++ 2005 Trial", slot.winetricks_callback("vc2005trial") )
			winetricksDevelopMenu.insertItem( QIconSet(loadPixmap("pencil_add.png")), "Mozilla build environment", slot.winetricks_callback("mozillabuild") )
			winetricksDevelopMenu.insertSeparator()
			winetricksMenu.insertItem( QIconSet(loadPixmap("pencil.png")), "&Development tools", winetricksDevelopMenu )
			
			"""Rest
 hosts         Adds empty C:\windows\system32\drivers\etc\{hosts,services} files
 glsl-disable  Disable GLSL use by Wine Direct3D
 glsl-enable   Enable GLSL use by Wine Direct3D (default)
 native_mdac   Override odbc32 and odbccp32
 native_oleaut32 Override oleaut32
 nocrashdialog Disable the graphical crash dialog
 orm=backbuffer Registry tweak: OffscreenRenderingMode=backbuffer
 orm=fbo        Registry tweak: OffscreenRenderingMode=fbo (default)
 orm=pbuffer    Registry tweak: OffscreenRenderingMode=pbuffer
 sandbox       Sandbox the wineprefix - remove links to ~
 sound=alsa       Set sound driver to ALSA
 sound=audioio    Set sound driver to AudioIO
 sound=coreaudio  Set sound driver to CoreAudio
 sound=esound     Set sound driver to Esound
 sound=jack       Set sound driver to Jack
 sound=nas        Set sound driver to Nas
 sound=oss        Set sound driver to OSS
 nt40          Set windows version to nt40
 win98         Set windows version to Windows 98
 win2k         Set windows version to Windows 2000
 winxp         Set windows version to Windows XP
 vista         Set windows version to Windows Vista
 winver=       Set windows version to default (winxp)
 volnum        Rename drive_c to harddiskvolume0 (needed by some installers)"""
						
			menu.insertItem( QIconSet(loadPixmap("script_gear.png")), "&Winetricks", winetricksMenu )
			menu.insertSeparator()			
			if not slot.slot.name == SWINE_DEFAULT_SLOT_NAME:
				menu.insertItem( QIconSet(loadPixmap("drive_rename.png")), "R&ename", slot.rename_cb )
			menu.insertItem( QIconSet(loadPixmap("arrow_divide.png")), "&Copy", slot.copy_cb )
			if not slot.slot.name == SWINE_DEFAULT_SLOT_NAME:
				menu.insertItem( QIconSet(loadPixmap("drive_delete.png")), "&Delete", slot.delete_cb )
		return menu
	
	def slotListKeyReleaseEvent(self,e):
		if e.key() == Qt.Key_Delete:
			e.accept()
			if self.currentSlotItem():
				self.currentSlotItem().delete_cb()
		else:
			e.ignore()
	
	def shortcutListKeyReleaseEvent(self,e):
		if e.key() == Qt.Key_Delete:
			e.accept()
			if self.currentShortcutItem():
				self.currentShortcutItem().delete_cb()
		else:
			e.ignore()
	
	def rebuildMenuBar(self):
		bar = self.menuBar
		bar.clear()
		slot = self.currentSlotItem()
		shortcut = self.currentShortcutItem()
		bar.insertItem("&Swine",self.Swine,1)
		bar.insertItem("S&lot",self.createSlotMenu(slot,self),1)
		if not slot == None:
			bar.insertItem("Short&cut",self.createShortcutMenu(shortcut,self),1)
		bar.insertItem("&Help",self.Help,1)

	def rebuildShortcutList(self):
		self.shortcutList.clear()
		if self.currentSlotItem():
			for shortcut in self.currentSlotItem().slot.getAllShortcuts():
				SwineShortcutItem(self.shortcutList,shortcut)

	def rebuildSlotList(self):
		self.slotList.clear()
		for slot in getAllSlots():
			SwineSlotItem(self.slotList,slot)
		self.slotList.setCurrentItem ( self.slotList.firstItem() )

	def import_cb(self):
		file = QFileDialog.getOpenFileName ( QString.null, "Swine Slots (*.swine)", self )
		if file:
			result = QInputDialog.getText ( "Import Slot", "Name:", QLineEdit.Normal, os.path.splitext(os.path.basename(str(file)))[0] )
			if result[1]:
				slot = importSlot ( str(result[0]), str(file) )
				SwineSlotItem(self.slotList,slot)
	
	def createShortcut_cb(self):
		shortcut = Shortcut("New Shortcut",self.currentSlotItem().slot)
		dialog = SwineShortcutDialog ( shortcut, self, "New Shortcut" )
		if dialog.exec_loop() == 1:
			if self.currentSlotItem().slot.loadShortcut ( shortcut.name ):
				raise SwineException ( "Shortcut '" + unicode(shortcut.name) + "' already exists" )
			shortcut.save()
			shortcut.slot.saveConfig()
			self.slotList_selectionChanged()
	
	def createSlot_cb(self):
		result = QInputDialog.getText ( "Create Slot", "Name:", QLineEdit.Normal, "New Slot" )
		if result[1]:
			slot = Slot(str(result[0]))
			slot.create()
			SwineSlotItem(self.slotList,slot)

	def shortcutList_rightButtonClicked(self, shortcut, point):
		if not self.currentSlotItem():
			return
		menu = self.createShortcutMenu(shortcut,self)
		menu.popup(point)
		menu.show()

	def slotList_rightButtonClicked(self, slot, point):
		menu = self.createSlotMenu(slot,self)
		menu.popup(point)
		menu.exec_loop()

	def helpabout_SwineAction_activated(self):
		SwineAboutDialog().exec_loop()
	
	def helpAbout_WineAction_activated(self):
		loadDefaultSlot().runWin ( ["winver"] )
	
	def menuExitAction_activated(self):
		self.close()
	
	def slotList_selectionChanged(self):
		self.rebuildShortcutList()
		self.rebuildMenuBar()

	def shortcutList_selectionChanged(self):
		self.rebuildMenuBar()

	def shortcutList_itemExceuted(self,item):
		shortcut = item.shortcut
		shortcut.run()
			
	def slotList_itemExecuted(self,item):
		slot = item.slot
		if not slot.loadDefaultShortcut() == None:
			slot.loadDefaultShortcut().run()

	def excepthook(self, excType, excValue, tracebackobj):
		tb = tracebackobj
		while not tb.tb_next == None:
			tb = tb.tb_next
		f = tb.tb_frame
		obj = f.f_locals.get("self", None)
		functionName = f.f_code.co_name
		callStr = f.f_code.co_name+" (" + os.path.basename(f.f_code.co_filename) + ", line "+str(f.f_lineno)+")"
		if obj:
			callStr = obj.__class__.__name__+"::"+callStr
		if excType == SwineException:
			excStr = unicode(excValue)
			QMessageBox.critical (self, "Error", excStr )
		else:
			excStr = str(excType.__name__) + ": " + unicode(excValue) + "\nin " + callStr
			QMessageBox.critical (self, "Error", excStr )

	def __init__(self,parent = None,name = None,fl = 0):
		MainWindow.__init__(self,parent,name,fl)
		self.setCaption ( "Swine " + VERSION )
		self.slotList.keyReleaseEvent = self.slotListKeyReleaseEvent
		self.shortcutList.keyReleaseEvent = self.shortcutListKeyReleaseEvent





class SwineAboutDialog(AboutDialog):
	def __init__(self,parent = None,name = None,modal = False,fl = 0):
		AboutDialog.__init__(self,parent,name,modal,fl)
		self.versionLabel.setText ( "Swine Version " + VERSION )



class SwineProgramDialog(ProgramDialog):
	def cancelButton_clicked(self):
		self.close()

	def exeSelectButton_clicked(self):
		file = QFileDialog.getOpenFileName( self.shortcut.slot.getDosDrivesPath(), "Windows executables (*.exe *.EXE)", self )
		if not file == None:
			self.applicationInput.setText ( self.shortcut.slot.unixPathToWin(str(file)) )
			if len(str(self.workingDirectoryInput.text())) == 0:
				self.workingDirectoryInput.setText ( self.shortcut.slot.unixPathToWin(os.path.dirname(str(file))) )

	def wdSelectButton_clicked(self):
		file = QFileDialog.getExistingDirectory( self.shortcut.slot.getDosDrivesPath(), self )
		if not file == None:
			self.workingDirectoryInput.setText ( self.shortcut.slot.unixPathToWin(str(file)) )
	
	def icon_clicked(self):
		if not self.shortcut.data == {}:
			self.shortcut.extractIcons()
		dirStr = ""
		if self.shortcut.iconsDir():
			dirStr = self.shortcut.iconsDir()
		self.iconFile = QFileDialog.getOpenFileName( dirStr, "Icon files (*.png *.PNG *.bmp *.BMP *.xpm *.XPM *.pnm *.PNM)", self )
		if not self.iconFile == None:
			self.icon.setIconSet ( QIconSet ( loadIcon ( self.iconFile ) ) )
			self.shortcut.data["icon"] = self.iconFile

	def okButton_clicked(self):
		if len(unicode(self.nameInput.text())) == 0:
			raise SwineException ( "Shortcut name cannot be empty" )
		self.shortcut.name = unicode(self.nameInput.text())
		self.shortcut.data["icon"] = str(self.iconFile)
		prog = []
		prog.append(str(self.applicationInput.text()))
		prog.extend(str2args(str(self.paramsInput.text())))
		self.shortcut.data["program"] = str(prog)
		self.shortcut.data["working_directory"] = str(self.workingDirectoryInput.text())
		if self.desktopCheckBox.isChecked():
			self.shortcut.data["desktop"] = "default,"+str(self.desktopResolution.currentText())
		else:
			if self.shortcut.data.has_key("desktop"):
				del self.shortcut.data["desktop"]
		self.shortcut.data["interminal"]=str(int(self.runInTerminalCheckBox.isChecked()))

	def __init__(self,shortcut,parent = None,name = None,modal = False,fl = 0):
		self.shortcut = shortcut
		ProgramDialog.__init__(self,parent,name,modal,fl)
		self.nameInput.setText ( shortcut.name )
		self.setCaption ( name )
		self.iconFile = ""
		self.paramsInput.setText ( "" )
		if not shortcut.data == {}:
			self.nameInput.setEnabled ( False )
			if shortcut.data.has_key("icon" ) and not shortcut.data["icon"] == "":
				self.icon.setIconSet ( QIconSet ( loadIcon ( shortcut.data["icon"] ) ) )
				self.iconFile = shortcut.data["icon"]
			self.applicationInput.setText ( str2args(shortcut.data["program"])[0] )
			self.workingDirectoryInput.setText ( shortcut.data["working_directory"] )
			self.paramsInput.setText ( str(str2args(shortcut.data["program"])[1:]) )
			if shortcut.data.has_key("desktop"):
				self.desktopCheckBox.setChecked ( True )
				self.desktopResolution.setCurrentText ( shortcut.data["desktop"].split(",")[1] )
			else:
				self.desktopCheckBox.setChecked ( False )
			self.runInTerminalCheckBox.setChecked ( self.shortcut.data.has_key("interminal") and int(self.shortcut.data["interminal"])==1 )


class SwineRunDialog(SwineProgramDialog):
	def okButton_clicked(self):
		SwineProgramDialog.okButton_clicked(self)
		self.hide()
		prog = str2args(self.shortcut.data['program'])
		wait=False
		workingDirectory=self.shortcut.data['working_directory']
		runInTerminal=self.shortcut.data.has_key("interminal") and int(self.shortcut.data["interminal"]) == 1
		log=None
		if self.logfileCheckBox.isChecked():
			log=self.slot.getPath()+"/wine.log"
		debug="err+all,warn-all,fixme+all,trace-all"
		desktop=None
		if self.shortcut.data.has_key('desktop'):
			desktop=self.shortcut.data['desktop']
		result = self.slot.runWin ( prog, wait=wait, workingDirectory=workingDirectory, runInTerminal=runInTerminal, log=log, debug=debug, desktop=desktop ).returncode
		# status codes from include/winerror.h
		# 0: success
		if not result == 0 and not result == None :
			QMessageBox.critical ( self, "Error", "Code: " + str(result) )
		# 2: exe-file not found
		# 3: exe-path not found
		# 126: mod not found (path invalid)
		print result
		if self.addShortcutsCheckBox.isChecked():
			for shortcut in self.slot.findShortcuts(True):
				shortcut.save()
			self.slot.saveConfig()
			self.parent().slotList_selectionChanged()
		if self.winebootCheckBox.isChecked():
			self.slot.runWineboot()
	def __init__(self,slot,parent = None,name = "Run Program",modal = False,fl = 0):
		self.slot = slot
		self.shortcut = Shortcut ( "Run Program", slot )
		SwineProgramDialog.__init__(self,self.shortcut,parent,name,modal,fl)
		self.okButton.setText ("Run")
		self.icon.hide()
		self.nameLabel.hide()
		self.nameInput.hide()
		self.adjustSize()


class SwineShortcutDialog(SwineProgramDialog):
	def okButton_clicked(self):
		SwineProgramDialog.okButton_clicked(self)
		self.accept()
	def __init__(self,shortcut,parent = None,name = None,modal = False,fl = 0):
		SwineProgramDialog.__init__(self,shortcut,parent,name,modal,fl)
		self.okButton.setText ("Save")
		self.winebootCheckBox.hide()
		self.addShortcutsCheckBox.hide()
		self.logfileCheckBox.hide()
		self.adjustSize()


class UIThread(Thread):
	def __init__(self,args):
		Thread.__init__(self)
		self.args=args

	def run(self):
		app=QApplication(self.args)
		global win
		win=SwineMainWindow()
		win.show()
		sys.excepthook=excepthook
		win.shortcutList.clear()
		win.rebuildSlotList()
		app.connect(app, SIGNAL("lastWindowClosed()"), app, SLOT("quit()"))
		app.connect(app, SIGNAL("lastWindowClosed()"), self.quit)
		app.exec_loop()

	def quit(self):
		QApplication.exit(0)
		sys.exit(0)


win=None
		
def main(args):
	ui=UIThread(args)
	ui.start()
	sys.excepthook=excepthook
	while(1):
		time.sleep(1)
	
def excepthook(excType, excValue, tracebackobj):
	if excType == KeyboardInterrupt:
		sys.exit(0)
	else:
		global win
		win.excepthook(excType, excValue, tracebackobj)

if __name__=="__main__":
	main(sys.argv)
