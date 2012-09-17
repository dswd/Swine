#!/usr/bin/env python

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

import swinelib
import time
from swinelib import *
from PyQt4.QtGui import *
from PyQt4.QtCore import Qt, QTranslator, QLocale
from threading import Thread
from RunnerDialog import *
from swine import SwineSlotItem, SwineShortcutImportDialog, loadIcon, excepthook, tr

class NewSlotItem(QListWidgetItem):
  def __init__(self,parent):
    self.icon = loadIcon(":/icons/images/folder_grey.png")
    QListWidgetItem.__init__(self, self.icon, " " + self.tr("Create new slot..."), parent)
  def tr(self, s):
    return tr(s, self.__class__.__name__)
  def mainWindow(self):
    return self.listWidget().topLevelWidget()
  def refreshShortcutList(self):
    self.mainWindow().slotList_selectionChanged()

class SwineRunnerDialog(QMainWindow, Ui_RunnerDialog):
  def __init__(self, args):
    QMainWindow.__init__(self)
    self.setupUi(self)
    self.setWindowTitle(unicode(self.windowTitle()) % VERSION)
    self.args = args
  def tr(self, s):
    return tr(s, self.__class__.__name__)
  def currentSlotItem(self):
    item = self.slots.currentItem()
    if item and item.isSelected():
      return item
    return None    
  def rebuildSlotList(self):
    self.slots.clear()
    NewSlotItem(self.slots)
    for slot in getAllSlots():
      SwineSlotItem(self.slots, slot)
    self.slots.setCurrentRow(0)
  def slots_itemExecuted(self, item):
    self.execute(item)      
  def selectButton_clicked(self):
    self.execute(self.currentSlotItem())
  def execute(self, item):
    slot = None
    if isinstance(item, SwineSlotItem):
      slot = item.slot
    elif isinstance(item, NewSlotItem):
      (text, code) = QInputDialog.getText(self, self.tr("Create Slot"), self.tr("Name:"), text=self.tr("New Slot"))
      if code:
        slot = Slot(unicode(text))
        slot.create()
    if slot:
      self.hide()
      (filename, args) = (self.args[1], self.args[2:])
      if filename.lower().endswith(".verb"):
        res = slot.runVerb(os.path.abspath(filename))
      else:
        res = slot.runWin([filename]+args)
      if res.returncode:
        dialog = QMessageBox(QMessageBox.Critical, self.tr("Error"), self.tr("Execution failed with code %s") % res.returncode, QMessageBox.Ok, self)
        dialog.setDetailedText(res.stderr_data)
        dialog.adjustSize()
        dialog.exec_()
      else:
        if config.getValue("auto_import_shortcuts"):
          SwineShortcutImportDialog(slot, self, onlyNew=True).exec_()
      self.close()

def main(args):
  swinelib.tr = tr
  app=QApplication(args)
  for path in TRANSLATION_DIRS:
    translator = QTranslator()
    translator.load(QLocale().name(), path)
    if not translator.isEmpty():
      app.installTranslator(translator)
      break
  win=SwineRunnerDialog(args)
  win.show()
  sys.excepthook=excepthook
  win.rebuildSlotList()
  sys.exit(app.exec_())
  
if __name__=="__main__":
  if len(sys.argv) > 1:
    main(sys.argv)
