#!/usr/bin/env python

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
from swinelib import *
from qt import *
from AboutDialog import *
from ProgramDialog import *
from MainWindow import *

IMAGE_FOLDER = os.path.dirname(os.path.realpath(__file__)) + "/images/"
def loadPixmap ( name ):
	return QPixmap(QString(IMAGE_FOLDER+name))

def loadIcon ( name ):
	pm = QPixmap ( name )
	pm.setMask ( pm.createHeuristicMask() )
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
		QListBoxPixmap.__init__(self,parent,self.pixmap,slot.name)
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
		result = QInputDialog.getText ( "Rename Slot", "New name:", QLineEdit.Normal, self.slot.name )
		if result[1] and len(result[0]) > 0:
			self.slot.rename ( str ( result[0] ) )
			self.setText ( str ( result[0] ) )
			self.listBox().sort()
	def copy_cb(self):
		result = QInputDialog.getText ( "Copy Slot", "New name:", QLineEdit.Normal, "New Slot" )
		if result[1]:
			self.slot.clone ( str ( result[0] ) )
			slot = Slot(str(result[0]))
			slot.loadConfig()
			SwineSlotItem(self.mainWindow().slotList,slot)
	def searchShortcuts_cb(self):
		for shortcut in self.slot.findShortcuts(False):
			shortcut.save()
		self.slot.saveConfig()
		self.refreshShortcutList()
	def install_corefonts_cb(self):
		if QMessageBox.information ( self.listBox(), "Install MS Corefonts", "This will download, unpack and install the Microsoft Corefonts.\nYou will need an internet connection and the 'cabextract' program for this to work.", "&Continue", "&Abort", QString.null, 0, 1 ) == 0:
			self.slot.installCorefonts()
			QMessageBox.information ( self.listBox(), "Install MS Corefonts", "MS Corefonts installed sucessfully.")
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
	def	export_cb(self):
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
	def height(self,lb):
		return QListBoxPixmap.height(self,lb)+6

class SwineShortcutItem(QIconViewItem):
	def __init__(self,parent,shortcut):
		self.shortcut=shortcut
		name=shortcut.name
		if shortcut.isDefault():
			name = name + "*"
		QIconViewItem.__init__(self,parent,name,loadPixmap("wabi.png"))
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
		result = QInputDialog.getText ( "Rename Shortcut", "New name:", QLineEdit.Normal, self.shortcut.name )
		if result[1]:
			self.shortcut.rename ( str ( result[0] ) )
			self.shortcut.slot.saveConfig()
			self.setText ( str ( result[0] ) )
	def copy_cb(self):
		result = QInputDialog.getText ( "Copy Shortcut", "New name:", QLineEdit.Normal, "New Shortcut" )
		if result[1]:
			self.shortcut.clone ( str ( result[0] ) )
			self.shortcut.slot.saveConfig()
			self.refreshShortcutList()	
	def edit_cb(self):
		dialog = SwineShortcutDialog ( self.shortcut, self.mainWindow(), "Edit Shortcut" )
		if dialog.exec_loop() == 1:
			self.shortcut.rename(self.shortcut.name)
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
			menu.insertItem( QIconSet(loadPixmap("application_edit.png")), "&Edit", shortcut.edit_cb )
			menu.insertSeparator()
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
			toolsMenu.insertItem( QIconSet(loadPixmap("package_go.png")), "&Export", slot.export_cb )
			toolsMenu.insertItem( QIconSet(loadPixmap("package_add.png")), "Import &Data", slot.import_cb )
			menu.insertItem( QIconSet(loadPixmap("wrench_orange.png")), "&Tools", toolsMenu )
			configMenu = QPopupMenu(self)
			configMenu.insertItem( QIconSet(loadPixmap("computer_edit.png")), "&Winecfg", slot.slot.runWinecfg )
			configMenu.insertItem( QIconSet(loadPixmap("wrench.png")), "&Start Regedit", slot.slot.runRegedit )
			configMenu.insertItem( QIconSet(loadPixmap("application_delete.png")), "&Uninstall Software", slot.slot.runUninstaller )
			configMenu.insertItem( QIconSet(loadPixmap("computer.png")), "&Control-Center", slot.slot.runWineControl )
			menu.insertItem( QIconSet(loadPixmap("wrench_orange.png")), "&Config", configMenu )
			commandsMenu = QPopupMenu(self)
			commandsMenu.insertItem( QIconSet(loadPixmap("drive_magnify.png")), "&Import Shortcuts", slot.searchShortcuts_cb )
			commandsMenu.insertItem( QIconSet(loadPixmap("arrow_refresh.png")), "&Reboot wine", slot.slot.runWineboot )
			commandsMenu.insertItem( QIconSet(loadPixmap("drive_cd.png")), "&Eject CD", slot.slot.runEject )
			commandsMenu.insertSeparator()
			commandsMenu.insertItem( QIconSet(loadPixmap("style_add.png")), "Install &MS Corefonts", slot.install_corefonts_cb )
			menu.insertItem( QIconSet(loadPixmap("wrench_orange.png")), "&Commands", commandsMenu )
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
				raise SwineException ( "Shortcut '" + shortcut.name + "' already exists" )
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
		QApplication.exit(0)
	
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
			excStr = str(excValue)
		else:
			excStr = str(excType) + ": " + str(excValue) + "\nin " + callStr
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
		file = QFileDialog.getOpenFileName( self.shortcut.slot.winPathToUnix("c:\\"), "Windows executables (*.exe *.EXE)", self )
		if not file == None:
			self.applicationInput.setText ( self.shortcut.slot.unixPathToWin(str(file)) )
			if len(str(self.workingDirectoryInput.text())) == 0:
				self.workingDirectoryInput.setText ( self.shortcut.slot.unixPathToWin(os.path.dirname(str(file))) )

	def wdSelectButton_clicked(self):
		file = QFileDialog.getExistingDirectory( self.shortcut.slot.winPathToUnix("c:\\"), self )
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
		if len(str(self.nameInput.text())) == 0:
			raise SwineException ( "Shortcut name cannot be empty" )
		self.shortcut.name = str(self.nameInput.text())
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
		runInTerminal=self.shortcut.data["interminal"]
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


def main(args):
	app=QApplication(args)
	win=SwineMainWindow()
	win.show()
	sys.excepthook = win.excepthook
	win.shortcutList.clear()
	win.rebuildSlotList()
	app.connect(app, SIGNAL("lastWindowClosed()"), app, SLOT("quit()"))
	app.exec_loop()

if __name__=="__main__":
	main(sys.argv)
