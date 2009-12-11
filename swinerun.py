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
import time
from swinelib import *
from qt import *
from threading import Thread
from RunnerDialog import *
from swine import SwineSlotItem

IMAGE_FOLDER = os.path.dirname(os.path.realpath(__file__)) + "/images/"
def loadPixmap ( name ):
	return QPixmap(QString(IMAGE_FOLDER+name))

def loadIcon ( name ):
	pm = QPixmap ( name )
	pm.setMask ( pm.createHeuristicMask() )
	if not pm or pm.isNull():
		pm = loadPixmap("wabi.png")
	return QPixmap ( pm.convertToImage().smoothScale(32,32,QImage.ScaleMin) )

class NewSlotItem(QListBoxPixmap):
	def __init__(self,parent):
		self.pixmap = loadPixmap("folder_grey.png")
		QListBoxPixmap.__init__(self,parent,self.pixmap,"Create new slot...")
	def mainWindow(self):
		return self.listBox().topLevelWidget()
	def refreshShortcutList(self):
		self.mainWindow().slotList_selectionChanged()

class SwineRunnerDialog(RunnerDialog):
	def currentSlotItem(self):
		item = self.slots.selectedItem()
		if item and item.isSelected():
			return item
		return None
		
	def rebuildSlotList(self):
		self.slots.clear()
		for slot in getAllSlots():
			SwineSlotItem(self.slots,slot)
		NewSlotItem(self.slots)
		self.slots.setCurrentItem ( self.slots.firstItem() )

	def slots_itemExecuted(self,item):
		self.execute(item)
			
	def selectButton_clicked(self):
		self.execute(self.currentSlotItem())
		
	def execute(self,item):
		slot = None
		if item.__class__ == SwineSlotItem:
			slot = item.slot
		elif item.__class__ == NewSlotItem:
			result = QInputDialog.getText ( "Create Slot", "Name:", QLineEdit.Normal, "New Slot" )
			if result[1]:
				slot = Slot(str(result[0]))
				slot.create()
		if slot:
			self.hide()
			slot.runWin(self.args[1:], wait=True)
			self.close()

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
			QMessageBox.critical (self, "Error", excStr )
		else:
			excStr = str(excType.__name__) + ": " + str(excValue) + "\nin " + callStr
			QMessageBox.critical (self, "Error", excStr )

	def __init__(self,args,parent = None,name = None,fl = 0):
		RunnerDialog.__init__(self,parent,name,fl)
		self.setCaption ( "Swine " + VERSION )
		self.args = args

class UIThread(Thread):
	def __init__(self,args):
		Thread.__init__(self)
		self.args=args

	def run(self):
		app=QApplication(self.args)
		global win
		win=SwineRunnerDialog(self.args)
		win.show()
		sys.excepthook=excepthook
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
