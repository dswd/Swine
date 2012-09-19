#!/usr/bin/env python
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

import os, sys, traceback
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

import swinelib, config, icolib
import time, webbrowser, pipes, thread
from PyQt4.QtGui import *
from PyQt4.QtCore import Qt, QTranslator, QLocale, SIGNAL, SLOT
from swinelib import *
from threading import Thread
from AboutDialog import *
from ProgramDialog import *
from IconDialog import *
from MainWindow import *
from ShortcutImport import *
from Settings import *
from SlotSettings import *

def loadIcon (name, folder="", cache=True, scale=None):
  path = os.path.join(folder, name)
  icon = QPixmap(path)
  if not icon or icon.isNull():
    return None
  if scale:
    icon = icon.scaled(scale[0], scale[1], aspectRatioMode=Qt.KeepAspectRatio, transformMode=Qt.SmoothTransformation)
  return QIcon(icon)

def loadIconFromData (data, scale=None):
  icon = QPixmap()
  icon.loadFromData(data)
  if not icon or icon.isNull():
    return None
  if scale:
    icon = icon.scaled(scale[0], scale[1], aspectRatioMode=Qt.KeepAspectRatio, transformMode=Qt.SmoothTransformation)
  return QIcon(icon)
  
  
def tr(s, context="@default"):
  return unicode(QApplication.translate(context, s, None, QApplication.UnicodeUTF8))
  


_threads = []
class WrapperThread(QtCore.QThread):
  def __init__(self, func, args, kwargs):
    QtCore.QThread.__init__(self)
    self.func = func
    self.args = args
    self.kwargs = kwargs
    _threads.append(self)
  def run(self):
    try:
      self.func(*self.args, **self.kwargs)
    finally:
      _threads.remove(self)

    
#NOTICE: Do not access other Qt objects from detached functions, use signals+slots
def detached(func):
  def call(*args, **kwargs):
    wrapper = WrapperThread(func, args, kwargs)
    wrapper.start()
  return call
  

  
  
  
class IconListItem(QListWidgetItem, QtCore.QObject):
  def __init__(self, parent, name, icon=None, description=None, **kwargs):
    QListWidgetItem.__init__(self, icon, name, parent)
    if description:
      self.setToolTip(description)
    self.__dict__.update(kwargs)
  def tr(self, s):
    return tr(s, self.__class__.__name__)



class SwineSlotItem(IconListItem):
  def __init__(self, parent, slot):
    self.slot = slot
    shortcut = slot.loadDefaultShortcut()
    self.iconObj = None
    if shortcut:
      if shortcut.getIcon():
        self.iconObj = loadIconFromData(shortcut.getIcon())
    if not self.iconObj:
      self.iconObj = loadIcon(":/icons/images/folder.png")
    IconListItem.__init__(self, parent, unicode(slot.getName()), self.iconObj)
    self.setFlags(Qt.ItemIsEditable|Qt.ItemIsSelectable|Qt.ItemIsEnabled)
    self.listWidget().sortItems()
  def tr(self, s):
    return tr(s, self.__class__.__name__)
  def mainWindow(self):
    return self.listWidget().topLevelWidget()
  def refreshShortcutList(self):
    self.listWidget().emit(SIGNAL('changed()'))
  def delete_cb(self):
    if QMessageBox.warning(self.listWidget(), self.tr("Delete Slot"), self.tr("Are you sure ?"), QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
      self.slot.delete()
      self.listWidget().takeItem(self.listWidget().row(self))
  def renameTo(self, name):
    if unicode(name) != unicode(self.slot.getName()):
      self.slot.rename(unicode(name))
      self.setText(name)
      self.listWidget().sortItems()
  def rename_cb(self):
    self.listWidget().editItem(self)
  def copy_cb(self):
    slot = self.slot.clone(self.slot.getName() + "_2")
    slotItem = SwineSlotItem(self.listWidget(), slot)
    slotItem.rename_cb()
  def searchShortcuts_cb(self):
    SwineShortcutImportDialog(self.slot, self.listWidget()).exec_()
    self.refreshShortcutList()
  def run_cb(self):
    SwineRunDialog(self.slot, self.mainWindow()).show()
  @detached
  def filemanager_cb(self):
    self.slot.runWinefile()
  @detached
  def shell_cb(self):
    self.slot.runWin(["cmd.exe"], runInTerminal=True)
  @detached
  def taskmgr_cb(self):
    self.slot.runWin(["taskmgr.exe"])
  def runDefault_cb(self):
    if self.slot.loadDefaultShortcut():
      self.mainWindow().runShortcut(self.slot.loadDefaultShortcut())
  def settings_cb(self):
    SwineSlotSettingsDialog(self.listWidget(), self.slot).exec_()
  def export_cb(self):
    path = QFileDialog.getSaveFileName(self.listWidget(), self.tr("Select archive file"), "", self.tr("Swine Slots (*.swine *.tar.gz)"))
    if not path:
      return
    self.exportTo(path)
  @detached
  def exportTo(self, path):
    self.slot.exportData(unicode(path))
  def import_cb(self):
    path = QFileDialog.getOpenFileName(self.listWidget(), self.tr("Select archive file"), "", self.tr("Swine Slots (*.swine *.tar.gz)"))
    if path:
      self.importFrom(path)
  @detached
  def importFrom(self, path):
    self.slot.importData(unicode(path))
    self.refreshShortcutList()
  def verbrun_cb(self):
    path = QFileDialog.getOpenFileName(self.listWidget(), self.tr("Select script file"), "", self.tr("Winetricks scripts (*.verb)"))
    if path:
      self.runVerb(os.path.realpath(unicode(path)))
  @detached    
  def runVerb(self, path):
    self.slot.runVerb(path)
    if config.getValue("auto_import_shortcuts"):
      SwineShortcutImportDialog(self.slot, self.listWidget(), onlyNew=True).exec_()
      self.refreshShortcutList()
  @detached
  def winetricks(self, tool):
    self.slot.runWinetricks(tool)
    if config.getValue("auto_import_shortcuts"):
      SwineShortcutImportDialog(self.slot, self.listWidget(), onlyNew=True).exec_()
      self.refreshShortcutList()
  def winetricks_callback(self, tool):
    return lambda :self.winetricks(tool)



class SwineShortcutItem(IconListItem):
  def __init__(self, parent, shortcut):
    self.parent = parent
    self.shortcut = shortcut
    self.iconObj = None
    if shortcut.getIcon():
        self.iconObj = loadIconFromData(shortcut.getIcon())
    if not self.iconObj:
      self.iconObj = loadIcon(":/icons/images/wabi.png")
    IconListItem.__init__(self, parent, shortcut.getName(), self.iconObj, shortcut["description"])
    self.setFlags(Qt.ItemIsEditable|Qt.ItemIsSelectable|Qt.ItemIsEnabled)
    self.updateDefaultState()
  def tr(self, s):
    return tr(s, self.__class__.__name__)
  def mainWindow(self):
    return self.listWidget().topLevelWidget()
  def updateDefaultState(self):
    font = self.font()
    font.setBold(self.shortcut.isDefault())
    self.setFont(font)
  def refreshShortcutList(self):
    self.listWidget().emit(SIGNAL('changed()'))
  def run_cb(self):
    self.mainWindow().runShortcut(self.shortcut)
  def delete_cb(self):
    self.shortcut.delete()
    self.listWidget().takeItem(self.listWidget().row(self))
  def renameTo(self, name):
    if name != self.shortcut.getName():
      self.shortcut.rename(unicode(name))
      self.setText(name)
      self.listWidget().sortItems()
  def rename_cb(self):
    self.listWidget().editItem(self)
  def copy_cb(self):
    shortcut = self.shortcut.clone(self.shortcut.getName() + "_2")
    shortcutItem = SwineShortcutItem(self.listWidget(), shortcut)
    shortcutItem.rename_cb()
  def edit_cb(self):
    dialog = SwineShortcutDialog(self.shortcut, self.listWidget(), self.tr("Edit Shortcut"))
    if dialog.exec_():
      self.shortcut.rename(unicode(self.shortcut.getName()))
      if self.shortcut.isDefault():
        self.mainWindow().currentSlotItem().setIcon(self.icon())
      self.refreshShortcutList()
  def setDefault_cb(self):
    self.shortcut.setDefault()
    self.mainWindow().currentSlotItem().setIcon(self.icon())
    shortcuts = self.listWidget()
    for i in xrange(0, shortcuts.count()):
      shortcuts.item(i).updateDefaultState()
  def createMenuEntry_cb(self):
    self.shortcut.createMenuEntry()
    QMessageBox.information(self.listWidget(), self.tr("Menu Entry"), self.tr("Menu entry for %s has been created") % self.shortcut.getName())
  def removeMenuEntry_cb(self):
    self.shortcut.removeMenuEntry()
    QMessageBox.information(self.listWidget(), self.tr("Menu Entry"), self.tr("Menu entry for %s has been removed") % self.shortcut.getName())



class SwineMainWindow(QMainWindow, Ui_MainWindow):
  def __init__(self):
    QMainWindow.__init__(self)
    self.setupUi(self)
    self.setWindowTitle(unicode(self.windowTitle()) % VERSION)
    self.winetricksVersion.setText(self.tr("Version: %s") % winetricks.version) 
    self.slotList.keyReleaseEvent = self.slotListKeyReleaseEvent
    self.shortcutList.keyReleaseEvent = self.shortcutListKeyReleaseEvent
    QtCore.QObject.connect(self.slotList, SIGNAL('changed()'), self.reloadShortcuts)
    QtCore.QObject.connect(self.shortcutList, SIGNAL('changed()'), self.reloadShortcuts)
    QtCore.QObject.connect(self, SIGNAL('winetricksUpdated(QString)'), self.winetricksUpdated)
  def tr(self, s):
    return tr(s, self.__class__.__name__)
  def currentSlotItem(self):
    item = self.slotList.currentItem()
    if item and item.isSelected():
      return item
    return None
  def currentShortcutItem(self):
    item = self.shortcutList.currentItem()
    if item and item.isSelected():
      return item
    return None
  def rebuildShortcutList(self):
    self.shortcutList.clear()
    if self.currentSlotItem():
      for shortcut in self.currentSlotItem().slot.getAllShortcuts():
        SwineShortcutItem(self.shortcutList, shortcut)
  def rebuildSlotList(self):
    self.slotList.clear()
    for slot in getAllSlots():
      SwineSlotItem(self.slotList, slot)
    self.slotList.setCurrentRow(0)
  def rebuildMenuBar(self):
    bar = self.menuBar
    bar.clear()
    slot = self.currentSlotItem()
    shortcut = self.currentShortcutItem()
    bar.addMenu(self.menuSwine)
    bar.addMenu(self.createSlotMenu(slot, self))
    if slot:
      bar.addMenu(self.createShortcutMenu(shortcut, self))
    bar.addMenu(self.menuWinetricks)
    bar.addMenu(self.menuHelp)
  def createShortcutMenu(self, shortcut, parent):
    menu = QMenu(self.tr("Shortcut"), parent)
    menu.addAction(loadIcon(":/icons/images/application_add.png"), self.tr("New Shortcut"), self.createShortcut_cb)
    if shortcut:
      menu.addSeparator()
      menu.addAction(loadIcon(":/icons/images/cog.png"), self.tr("Run"), shortcut.run_cb)
      menu.addSeparator()
      menu.addAction(loadIcon(":/icons/images/lightning_add.png"), self.tr("Set Default"), shortcut.setDefault_cb)
      if shortcut.shortcut.hasMenuEntry():
        menu.addAction(loadIcon(":/icons/images/lightning_delete.png"), self.tr("Remove Menu Entry"), shortcut.removeMenuEntry_cb)
      else:
        menu.addAction(loadIcon(":/icons/images/lightning_add.png"), self.tr("Create Menu Entry"), shortcut.createMenuEntry_cb)
      menu.addSeparator()
      menu.addAction(loadIcon(":/icons/images/application_edit.png"), self.tr("Edit"), shortcut.edit_cb)
      menu.addAction(loadIcon(":/icons/images/textfield_rename.png"), self.tr("Rename"), shortcut.rename_cb)
      menu.addAction(loadIcon(":/icons/images/arrow_divide.png"), self.tr("Copy"), shortcut.copy_cb)
      menu.addAction(loadIcon(":/icons/images/application_delete.png"), self.tr("Delete"), shortcut.delete_cb)
    return menu    
  def createSlotMenu(self, slot, parent):
    menu = QMenu(self.tr("Slot"), parent)
    menu.addAction(loadIcon(":/icons/images/drive_add.png"), self.tr("New Slot"), self.createSlot_cb)
    menu.addAction(loadIcon(":/icons/images/package_add.png"), self.tr("Import Slot"), self.import_cb)
    if slot:
      menu.addSeparator()
      menu.addAction(loadIcon(":/icons/images/application_lightning.png"), self.tr("Run default"), slot.runDefault_cb)
      menu.addAction(loadIcon(":/icons/images/application.png"), self.tr("Run..."), slot.run_cb)

      menu.addSeparator()

      toolsMenu = menu.addMenu(loadIcon(":/icons/images/wrench_orange.png"), self.tr("Tools"))
      toolsMenu.addAction(loadIcon(":/icons/images/application_xp_terminal.png"), self.tr("Shell"), slot.shell_cb)
      toolsMenu.addAction(loadIcon(":/icons/images/folder_explore.png"), self.tr("File Manager"), slot.filemanager_cb)
      toolsMenu.addAction(loadIcon(":/icons/images/application_form_magnify.png"), self.tr("Taskmanager"), slot.taskmgr_cb)
      toolsMenu.addSeparator()
      toolsMenu.addAction(loadIcon(":/icons/images/computer_edit.png"), self.tr("Winecfg"), slot.slot.runWinecfg )
      toolsMenu.addAction(loadIcon(":/icons/images/wrench.png"), self.tr("Start Regedit"), slot.slot.runRegedit )
      toolsMenu.addAction(loadIcon(":/icons/images/application_delete.png"), self.tr("Uninstall Software"), slot.slot.runUninstaller )
      toolsMenu.addAction(loadIcon(":/icons/images/computer.png"), self.tr("Control-Center"), slot.slot.runWineControl )

      commandsMenu = menu.addMenu(loadIcon(":/icons/images/cog.png"), self.tr("Commands"))
      commandsMenu.addAction(loadIcon(":/icons/images/drive_magnify.png"), self.tr("Import Shortcuts"), slot.searchShortcuts_cb)
      commandsMenu.addAction(loadIcon(":/icons/images/arrow_refresh.png"), self.tr("Reboot wine"), slot.slot.runWineboot )
      commandsMenu.addAction(loadIcon(":/icons/images/drive_cd.png"), self.tr("Eject CD"), slot.slot.runEject )
      commandsMenu.addSeparator()
      commandsMenu.addAction(loadIcon(":/icons/images/package_go.png"), self.tr("Export"), slot.export_cb)
      commandsMenu.addAction(loadIcon(":/icons/images/package_add.png"), self.tr("Import Data"), slot.import_cb)
      
      menu.addAction(loadIcon(":/icons/images/script_gear.png"), self.tr("Run winetricks script"), slot.verbrun_cb)
      
      if winetricks.version:
        winetricksMenu = menu.addMenu(loadIcon(":/icons/images/script_gear.png"), self.tr("Winetricks"))
        winetricksMenu.addAction(loadIcon(":/icons/images/script_gear.png"), self.tr("Call Winetricks"), slot.winetricks_callback("") )
      else:
        menu.addAction(loadIcon(":/icons/images/script_gear.png"), self.tr("Winetricks is not installed"), lambda :winetricks.init() and self.rebuildMenuBar())
      perPage = 20
      for sec in winetricks.sections():
        options = list(winetricks.options(sec))
        secMenu = winetricksMenu.addMenu(loadIcon(":/icons/images/script_gear.png"), sec)
        if len(options) > perPage:
          pages = len(options)/perPage+1
          for page in xrange(0, pages):
            pageOptions = options[page*perPage:(page+1)*perPage]
            pageName = "%s to %s" % (pageOptions[0][0], pageOptions[-1][0])
            pageMenu = secMenu.addMenu(loadIcon(":/icons/images/script_gear.png"), pageName)
            for (name, desc) in pageOptions:
              pageMenu.addAction(loadIcon(":/icons/images/script_gear.png"), "[%s] %s" % (name, desc), slot.winetricks_callback(name))
        else:
          for (name, desc) in options:
            secMenu.addAction(loadIcon(":/icons/images/script_gear.png"), "[%s] %s" % (name, desc), slot.winetricks_callback(name))
 
      menu.addSeparator()
      
      defaultSlot = slot.slot.getName() == SWINE_DEFAULT_SLOT_NAME
      menu.addAction(loadIcon(":/icons/images/wrench.png"), self.tr("Settings"), slot.settings_cb)
      if not defaultSlot:
        menu.addAction(loadIcon(":/icons/images/drive_rename.png"), self.tr("Rename"), slot.rename_cb)
      menu.addAction(loadIcon(":/icons/images/arrow_divide.png"), self.tr("Copy"), slot.copy_cb)
      if not defaultSlot:
        menu.addAction(loadIcon(":/icons/images/drive_delete.png"), self.tr("Delete"), slot.delete_cb)
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
  def shortcutList_itemRenamed(self, item):
    item.renameTo(item.text())
  def slotList_itemRenamed(self, item):
    item.renameTo(item.text())
  def import_cb(self):
    path = QFileDialog.getOpenFileName(self, self.tr("Select archive"), "", self.tr("Swine Slots (*.swine *.tar.gz)"))
    if path:
      (name, code) = QInputDialog.getText(self, self.tr("Import Slot"), self.tr("Name:"), QLineEdit.Normal, os.path.splitext(os.path.basename(unicode(path)))[0])
      if code:
        slot = importSlot(unicode(name), unicode(path))
        SwineSlotItem(self.slotList, slot)
  def createShortcut_cb(self):
    shortcut = Shortcut(self.tr("New Shortcut"), self.currentSlotItem().slot)
    dialog = SwineShortcutDialog(shortcut, self, self.tr("New Shortcut"))
    if dialog.exec_():
      self.reloadShortcuts()
  def createSlot_cb(self):
    (name, code) = QInputDialog.getText(self, self.tr("Create Slot"), self.tr("Name:"), QLineEdit.Normal, self.tr("New Slot"))
    if code:
      slot = Slot(unicode(name))
      slot.create()
      SwineSlotItem(self.slotList, slot)
  def shortcutList_rightButtonClicked(self, point):
    if not self.currentSlotItem():
      return
    shortcut = self.shortcutList.itemAt(point)
    menu = self.createShortcutMenu(shortcut, self)
    menu.popup(self.shortcutList.mapToGlobal(point))
  def slotList_rightButtonClicked(self, point):
    slot = self.slotList.itemAt(point)
    menu = self.createSlotMenu(slot, self)
    menu.popup(self.slotList.mapToGlobal(point))
  def showSwineHelp(self):
    SwineAboutDialog(self).show()
  @detached
  def showWineHelp(self):
    loadDefaultSlot().runWin(["winver"])  
  def showWinetricksHelp(self):
    winetricks.showHelp()
  def openSwineWebsite(self):
    webbrowser.open(SWINE_WEBSITE)
  def openAppdbWebsite(self):
    webbrowser.open(APPDB_WEBSITE)
  @detached
  def downloadWinetricks(self):
    oldVersion = winetricks.version
    winetricks.download()
    self.emit(SIGNAL('winetricksUpdated(QString)'), oldVersion)
  def winetricksUpdated(self, oldVersion):
    self.winetricksVersion.setText(self.tr("Version: %s") % winetricks.version)
    if winetricks.version == oldVersion:
      QMessageBox.information(self, self.tr("Winetricks"), self.tr("Winetricks is already at version %s") % winetricks.version)
    else:
      QMessageBox.information(self, self.tr("Winetricks"), self.tr("Winetricks has been updated to version %s") % winetricks.version)
  def checkWinetricks(self):
    version = winetricks.getCacheVersion()
    if not version:
      if QMessageBox.question(self, self.tr("Winetricks"), self.tr("Winetricks not found. Do you want to download Winetricks now?"), QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
        self.downloadWinetricks()
    elif time.mktime(time.strptime(version, "%Y%m%d")) < time.time() - 3*30*24*60*60:
      if QMessageBox.question(self, self.tr("Winetricks"), self.tr("Winetricks is quite old, version %s. Do you want to update Winetricks now?") % version, QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
        self.downloadWinetricks()
  def menuExitAction_activated(self):
    self.close()
  def shortcutList_itemExecuted(self, item):
    self.runShortcut(item.shortcut)
  def slotList_itemExecuted(self, item):
    slot = item.slot
    if slot.loadDefaultShortcut():
      self.runShortcut(slot.loadDefaultShortcut())
  @detached
  def runShortcut(self, shortcut):
    res = shortcut.run()
    if res.returncode:
      self.emit(SIGNAL("executionFailed(int,QString)"), res.returncode, res.stderr_data)
    self.emit(SIGNAL("executionFinished(PyQt_PyObject)"), shortcut.slot)
  def settingsDialog(self):
    SwineSettingsDialog(self).exec_()
  def onExecutionFailed(self, code, msg):
    dialog = QMessageBox(QMessageBox.Critical, self.tr("Error"), self.tr("Execution failed with code %s") % code, QMessageBox.Ok, self)
    dialog.setDetailedText(msg)
    dialog.adjustSize()
    dialog.exec_()
  def importShortcuts(self, slot):
    if SwineShortcutImportDialog(slot, self, onlyNew=True).exec_():
      self.slotList_selectionChanged()
  def reloadShortcuts(self):
    self.rebuildShortcutList()
    self.rebuildMenuBar()



class SwineAboutDialog(QDialog, Ui_AboutDialog):
  def __init__(self, parent):
    QDialog.__init__(self, parent)
    self.setupUi(self)
    self.versionLabel.setText(unicode(self.versionLabel.text()) % VERSION)
  def tr(self, s):
    return tr(s, self.__class__.__name__)



class SwineIconDialog(QDialog,Ui_IconDialog):
  def __init__(self, icons, parent, name):
    QDialog.__init__(self, parent)
    self.setupUi(self)
    self.setWindowTitle(name)
    self.icons = icons
    self.iconData = None
    for icon in icons:
      image = loadIconFromData(icon.data, scale=(32, 32))
      if image:
        IconListItem(self.iconView, "%dx%d %d-bit" % (icon.width, icon.height, icon.bits), image, iconData=icon.data)
  def tr(self, s):
    return tr(s, self.__class__.__name__)
  def okButton_clicked(self):
    item = self.iconView.currentItem()
    self.iconData = item.iconData if item else None
    self.accept()
  def cancelButton_clicked(self):
    self.close()



class SwineProgramDialog(QDialog, Ui_ProgramDialog):
  def __init__(self, shortcut, parent, name):
    self.shortcut = shortcut
    self.parent = parent
    QDialog.__init__(self, parent)
    self.setupUi(self)
    self.nameInput.setText(shortcut.getName())
    self.setWindowTitle(name)
    self.iconData = None
    self.paramsInput.setText("")
    if shortcut.getProgram():
      self.nameInput.setEnabled(False)
      if shortcut.getIcon():
        icon = loadIconFromData(shortcut.getIcon(), scale=(32,32))
        if icon:
          self.icon.setIcon(icon)
          self.iconData = shortcut.getIcon()
      self.applicationInput.setText(shortcut.getProgram())
      self.workingDirectoryInput.setText(shortcut.getWorkingDirectory())
      self.paramsInput.setText(" ".join(map(pipes.quote, shortcut.getArguments())))
      self.desktopCheckBox.setChecked(bool(shortcut.getDesktop()))
      if shortcut.getDesktop():
        self.desktopResolution.setCurrentText(shortcut.getDesktop().split(",")[1])
      self.runInTerminalCheckBox.setChecked(bool(self.shortcut["interminal"]))
  def tr(self, s):
    return tr(s, self.__class__.__name__)
  def cancelButton_clicked(self):
    self.close()
  def exeSelectButton_clicked(self):
    fileName = QFileDialog.getOpenFileName(self, self.tr("Executable selection"), self.shortcut.slot.getDosDrivesPath(), self.tr("Windows executables (*.exe *.EXE);;Windows installers (*.msi *.MSI);;All files (*)"))
    if not fileName:
      return
    fileName = unicode(fileName)
    self.applicationInput.setText(self.shortcut.getSlot().unixPathToWin(fileName))
    if not unicode(self.workingDirectoryInput.text()):
      self.workingDirectoryInput.setText(self.shortcut.getSlot().unixPathToWin(os.path.dirname(fileName)))
  def wdSelectButton_clicked(self):
    fileName = QFileDialog.getExistingDirectory(self, self.shortcut.getSlot().getDosDrivesPath())
    if fileName:
      self.workingDirectoryInput.setText(self.shortcut.getSlot().unixPathToWin(unicode(fileName)))
  def icon_clicked(self):
    prog = unicode(self.applicationInput.text())
    if not prog:
      return
    workDir = str(self.workingDirectoryInput.text())
    prog = self.shortcut.getSlot().winPathToUnix(prog, basedir=workDir)
    icons = icolib.readExeIcons(prog)
    dialog = SwineIconDialog(icons, self.parent, self.tr("Select Icon"))
    if dialog.exec_():
      pass
    self.iconData = dialog.iconData
    if self.iconData:
      self.icon.setIcon(loadIconFromData(self.iconData))
  def okButton_clicked(self):
    if not self.nameInput.text():
      raise SwineException(self.tr("Shortcut name cannot be empty"))
    self.shortcut.rename(unicode(self.nameInput.text()))
    self.shortcut.setIcon(self.iconData)
    self.shortcut.setProgram(unicode(self.applicationInput.text()))
    self.shortcut.setArguments(str(self.paramsInput.text()))
    self.shortcut.setWorkingDirectory(str(self.workingDirectoryInput.text()))
    if self.desktopCheckBox.isChecked():
      self.shortcut.setDesktop("main,%s" % unicode(self.desktopResolution.currentText()))
    else:
      self.shortcut.setDesktop("")
    self.shortcut["interminal"] = "1" if self.runInTerminalCheckBox.isChecked() else ""
    #TODO: update slot icon if this is default shortcut


class SwineRunDialog(SwineProgramDialog):
  def okButton_clicked(self):
    SwineProgramDialog.okButton_clicked(self)
    self.hide()
    self.parent.runShortcut(self.shortcut)
    if config.getValue("auto_import_shortcuts"):
      SwineShortcutImportDialog(self.shortcut.slot, self, onlyNew=True).exec_()
      self.parent.reloadShortcuts()
  def __init__(self, slot, parent):
    self.slot = slot
    name = tr("Run Program")
    self.parent = parent
    self.shortcut = Shortcut(name, slot, virtual=True)
    SwineProgramDialog.__init__(self, self.shortcut, parent, name)
    self.okButton.setText(self.tr("Run"))
    self.icon.hide()
    self.nameLabel.hide()
    self.nameInput.hide()
    self.adjustSize()
  def tr(self, s):
    return tr(s, self.__class__.__name__)



class SwineShortcutDialog(SwineProgramDialog):
  def okButton_clicked(self):
    SwineProgramDialog.okButton_clicked(self)
    self.accept()
  def __init__(self, shortcut, parent, name):
    SwineProgramDialog.__init__(self, shortcut, parent, name)
    self.okButton.setText(self.tr("Save"))
    self.adjustSize()
  def tr(self, s):
    return tr(s, self.__class__.__name__)


    
class SwineShortcutImportDialog(QDialog, Ui_ShortcutImport):
  def __init__(self, slot, parent, onlyNew=False):
    QDialog.__init__(self, parent)
    self.setupUi(self)
    self.slot = slot
    self.lnkFiles = self.slot.findLnkFiles(onlyNew=onlyNew)
    for fname in self.lnkFiles:
      fname = slot.winPathToUnix(fname)
      shortcut = slot.createShortcutFromFile(fname)
      SwineShortcutItem(self.shortcutList, shortcut)
  def tr(self, s):
    return tr(s, self.__class__.__name__)
  def exec_(self):
    if self.lnkFiles:
      return QDialog.exec_(self)
  def importShortcuts(self):
    items = self.shortcutList.selectedItems()
    for item in items:
      item.shortcut.save()
    if items:
      self.accept()
    else:
      self.reject()



class SwineSettingsDialog(QDialog, Ui_Settings):
  class WinePathItem(QListWidgetItem):
    def __init__(self, path, version):
      self.path = path
      self.version = version
      QListWidgetItem.__init__(self, "%s [%s]" % (path, version))
  def __init__(self, parent):
    QDialog.__init__(self, parent)
    self.setupUi(self)
    self.load()
  def tr(self, s):
    return tr(s, self.__class__.__name__)
  def load(self):
    self._addWinePath("System", swinelib.getWineVersion(None))
    for path, version in config.getValue("wine_paths").iteritems():
      self._addWinePath(path, version)
    self._winePathsChanged()
    self.defaultWinePath.setCurrentIndex(max(0, self.defaultWinePath.findData(config.getValue("default_wine_path"))))
    self.allowMenuEntryCreation.setChecked(config.getValue("allow_menu_entry_creation"))
    self.autoImportShortcuts.setChecked(config.getValue("auto_import_shortcuts"))
    self.debugLine.setText(config.getValue("debug_line"))
    self.architecture.setCurrentIndex(max(0, self.architecture.findText(config.getValue("architecture"))))
  def _winePaths(self):
    return dict([(item.path, item.version) for item in self.winePathsList.findItems("/", Qt.MatchStartsWith)])
  def save(self):
    config.setValue("wine_paths", self._winePaths())
    config.setValue("default_wine_path", str(self.defaultWinePath.itemData(self.defaultWinePath.currentIndex()).toString()))
    config.setValue("allow_menu_entry_creation", self.allowMenuEntryCreation.isChecked())
    config.setValue("auto_import_shortcuts", self.autoImportShortcuts.isChecked())
    config.setValue("debug_line", str(self.debugLine.text()))
    config.setValue("architecture", str(self.architecture.currentText()))
    config.save()
  def _winePathsChanged(self):
    selected = self.defaultWinePath.currentText()
    self.defaultWinePath.clear()
    self.defaultWinePath.addItem("System [%s]" % swinelib.getWineVersion(None), None)
    for path, version in self._winePaths().iteritems():
      self.defaultWinePath.addItem("%s [%s]" % (path, version), path)
    self.defaultWinePath.setCurrentIndex(max(0, self.defaultWinePath.findText(selected)))
  def _addWinePath(self, path, version):
    self.winePathsList.addItem(SwineSettingsDialog.WinePathItem(path, version))
  def accept(self):
    self.save()
    QDialog.accept(self)
  def addWinePath(self):
    path = QFileDialog.getExistingDirectory(self, self.tr("Wine path selection"), "/")
    if not path:
      return
    path = unicode(path)
    version = swinelib.getWineVersion(path)
    if not version:
      raise SwineException(self.tr("No wine binary found in %s") % path)
    self._addWinePath(path, version)
    self._winePathsChanged()
  def removeWinePath(self):
    self.winePathsList.takeItem(self.winePathsList.currentRow())
    self._winePathsChanged()
  def findWinePaths(self):
    for path in swinelib.findWinePaths():
      version = swinelib.getWineVersion(path)
      self._addWinePath(path, version)
    self._winePathsChanged()



class SwineSlotSettingsDialog(QDialog, Ui_SlotSettings):
  def __init__(self, parent, slot):
    QDialog.__init__(self, parent)
    self.slot = slot
    self.setupUi(self)
    self.load()
  def tr(self, s):
    return tr(s, self.__class__.__name__)
  def load(self):
    self.winePath.clear()
    self.winePath.addItem("System [%s]" % swinelib.getWineVersion(None), None)
    for path in config.getValue("wine_paths"):
      version = swinelib.getWineVersion(path)
      self.winePath.addItem("%s [%s]" % (path, version), path)
    self.winePath.setCurrentIndex(max(0, self.winePath.findData(self.slot.getWinePath())))
  def save(self):
    self.slot.setWinePath(str(self.winePath.itemData(self.winePath.currentIndex()).toString()))
  def accept(self):
    self.save()
    QDialog.accept(self)

    
    
def excepthook(excType, excValue, tracebackObj):
  import traceback, sys
  if excType == KeyboardInterrupt:
    sys.exit(0)
  if excType == SwineException:
    return QMessageBox.critical(QApplication.desktop(), tr("Error"), unicode(excValue))
  tracebackStr = "".join(traceback.format_tb(tracebackObj))
  excStr = "%s: %s" % (excType.__name__, excValue)
  detailStr = excStr+"\n"+tracebackStr
  print >>sys.stderr, detailStr
  dialog = QMessageBox(QMessageBox.Critical, tr("Error"), excStr, QMessageBox.Ok, QApplication.desktop(), Qt.Dialog)
  dialog.setDetailedText(detailStr)
  dialog.adjustSize()
  dialog.exec_()



def main(args):
  swinelib.tr = tr
  app=QApplication(args)
  for path in TRANSLATION_DIRS:
    translator = QTranslator()
    translator.load(QLocale().name(), path)
    if not translator.isEmpty():
      app.installTranslator(translator)
      break
  win=SwineMainWindow()
  win.show()
  sys.excepthook=excepthook
  win.shortcutList.clear()
  win.rebuildSlotList()
  win.checkWinetricks()
  sys.exit(app.exec_())
  
if __name__=="__main__":
  main(sys.argv)
