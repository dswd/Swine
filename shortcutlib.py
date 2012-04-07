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

import struct, collections

LnkFlags = collections.namedtuple("LnkFlags", ["customIcon", "commandLineArgs", "workingDirectory", "relativePath", "description", "pointsToFileDir", "shellIdList"])

FileAttributes = collections.namedtuple("FileAttributes", ["offline", "compressed", "reparse", "sparse", "temporary", "normal", "ntfsEfs", "archive", "directory", "volumeLabel", "system", "hidden", "readOnly"])

SW_HIDE = 0
SW_NORMAL = 1
SW_SHOWMINIMIZED = 2
SW_SHOWMAXIMIZED = 3
SW_SHOWNOACTIVE = 4
SW_SHOW = 5
SW_MINIMIZE = 6
SW_SHOWMINNOACTIVE = 7
SW_SHOWNA = 8
SW_RESTORE = 9
SW_SHOWDEFAULT = 10

LnkFile = collections.namedtuple("LnkFile", ["lnkFlags", "timeCreate", "timeAccess", "timeModify", "fileLength", "iconIndex", "showWindow", "hotkey", "fileAttributes", "target", "description", "relativePath", "workingDirectory", "commandLineArgs", "customIcon"])

def getBits(byte):
  return map(bool,(byte&0x80, byte&0x40, byte&0x20, byte&0x10, byte&0x08, byte&0x04, byte&0x02, byte&0x01))

def winTimeToUnix(time):
  return int(time * 0.0000001 - 11644473600)
  
def readLnkFromFp(fp):
  (magic,) = struct.unpack("B3x", fp.read(4))
  if magic != 0x4c:
    raise Exception("Not valid LNK format")
  (guid, lnkFlags) = struct.unpack("<16sB3x", fp.read(20))
  lnkFlags = LnkFlags(*(getBits(lnkFlags)[1:]))
  if lnkFlags.pointsToFileDir:
    (byte1, byte2) = struct.unpack("<2B2x", fp.read(4))
    fileAttributes = FileAttributes(*(getBits(byte1)[3:]+getBits(byte2)))
  fp.seek(0x1c)
  (timeCreate, timeAccess, timeModify) = map(winTimeToUnix, struct.unpack("<3d", fp.read(24)))
  (fileLength, iconIndex, showWindow, hotkey) = struct.unpack("<IIBI", fp.read(13))
  fp.seek(0x4c)
  if lnkFlags.shellIdList:
    (itemIdLen,) = struct.unpack("<H", fp.read(2))
    itemId = fp.read(itemIdLen)
  start = fp.tell()
  (structLength, firstOffset, volumeFlags, localVolumeTableOffset, basePathOffset, networkVolumeTableOffset, remainingPathOffset) = struct.unpack("<2IB3x4I", fp.read(28))
  onLocalVolume = bool(volumeFlags)
  assert firstOffset == 0x1c
  if onLocalVolume:
    fp.seek(start+localVolumeTableOffset)
    (volLength, volType, volSerial, volOffset) = struct.unpack("<IIII", fp.read(16))
    assert volOffset == 0x10
    fp.seek(start+localVolumeTableOffset+volOffset)
    (volumeName, basePathName) = fp.read(remainingPathOffset-(localVolumeTableOffset+volOffset)).rstrip("\x00").split("\x00")
    target = basePathName
  else:
    fp.seek(start+networkVolumeTableOffset)
    (length,) = struct.unpack("<I16x", fp.read(20))
    volumeName = fp.read(length)
    target = volumeName
  fp.seek(start+remainingPathOffset)
  remainingPath = fp.read(structLength-remainingPathOffset).rstrip("\x00")
  target += remainingPath
  description = None
  if lnkFlags.description:
    (length,) = struct.unpack("<H", fp.read(2))
    description = fp.read(length*2).decode("UTF-16").rstrip("\x00")
  relativePath = None
  if lnkFlags.relativePath:
    (length,) = struct.unpack("<H", fp.read(2))
    relativePath = fp.read(length*2).decode("UTF-16").rstrip("\x00")
  workingDirectory = None
  if lnkFlags.workingDirectory:
    (length,) = struct.unpack("<H", fp.read(2))
    workingDirectory = fp.read(length*2).decode("UTF-16").rstrip("\x00")
  commandLineArgs = None
  if lnkFlags.commandLineArgs:
    (length,) = struct.unpack("<H", fp.read(2))
    commandLineArgs = fp.read(length*2).decode("UTF-16").rstrip("\x00")
  customIcon = None
  if lnkFlags.customIcon:
    (length,) = struct.unpack("<H", fp.read(2))
    customIcon = fp.read(length*2).decode("UTF-16").rstrip("\x00")
  return LnkFile(lnkFlags=lnkFlags, timeCreate=timeCreate, timeAccess=timeAccess, timeModify=timeModify, fileLength=fileLength, iconIndex=iconIndex, showWindow=showWindow, hotkey=hotkey, fileAttributes=fileAttributes, target=target, description=description, relativePath=relativePath, workingDirectory=workingDirectory, commandLineArgs=commandLineArgs, customIcon=customIcon)
    
def readLnk(filename):
  with open(filename, "rb") as fp:
    return readLnkFromFp(fp)
    
if __name__ == "__main__":
  import sys
  print readLnk(sys.argv[1])