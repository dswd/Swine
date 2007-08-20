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

import os, stat, array

DWORD=4
QWORD=8

def bytes2long(bytes):
	return bytes[3]*256+bytes[2]*256+bytes[1]*256+bytes[0]

def getbit(value,number):
	return (value>>number) & 1

def readlnk(filename):
	fileobj = open(filename, mode='rb')
	size = os.lstat(filename)[stat.ST_SIZE]
	data = array.array("B")
	data.read ( fileobj, size )
	shortcut = {}
	shortcut['magic_number'] = bytes2long(data[0x0:0x0+DWORD])
	if not shortcut['magic_number'] == ord("L"):
		raise Exception("Magic number must be 76 ('L')")
	shortcut['GUID'] = data[0x4:0x4+16]
	if not shortcut['GUID'] == array.array ("B", [0x1, 0x14, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0xC0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x46 ] ):
		raise Exception("GUID must be 0114 0200 0000 0000 C000 0000 0000 0046")
	flags = bytes2long(data[0x14:0x14+DWORD])
	shortcut['flags'] = {
		"shell_item_id_present": getbit(flags,0),
		"file_or_directory": getbit(flags,1),
		"description": getbit(flags,2),
		"relative_path": getbit(flags,3),
		"working_directory": getbit(flags,4),
		"command_line_arguments": getbit(flags,5),
		"custom_icon": getbit(flags,6)
	}
	file_attr = bytes2long(data[0x18:0x18+DWORD])
	shortcut['file_attr'] = {
		"read_only": getbit(file_attr,0),
		"hidden": getbit(file_attr,1),
		"system_file": getbit(file_attr,2),
		"volume_label": getbit(file_attr,3),
		"directory": getbit(file_attr,4),
		"archive": getbit(file_attr,5),
		"encrypted": getbit(file_attr,6),
		"normal": getbit(file_attr,7),
		"temporary": getbit(file_attr,8),
		"sparse_file": getbit(file_attr,9),
		"reparse_point_data": getbit(file_attr,10),
		"compressed": getbit(file_attr,11),
		"offline": getbit(file_attr,12),
	}
	shortcut['creation_time'] = data[0x1C:0x1C+QWORD]
	shortcut['modification_time'] = data[0x24:0x24+QWORD]
	shortcut['access_time'] = data[0x2C:0x2C+QWORD]
	shortcut['file_length'] = bytes2long(data[0x34:0x34+DWORD])
	shortcut['icon_number'] = bytes2long(data[0x38:0x38+DWORD])
	shortcut['show_wnd'] = bytes2long(data[0x3C:0x3C+DWORD])
	shortcut['hot_key'] = bytes2long(data[0x40:0x40+DWORD])
	if not data[0x44:0x44+2*DWORD] == array.array("B",[0,0,0,0,0,0,0,0]):
		raise Exception("0x44-0x4C must be 00 00 00 00 00 00 00 00")
	start = 0x4C
	if shortcut['flags']['shell_item_id_present']:
		start += data[0x4C]+data[0x4D]*256+2	
	file_location = {}
	file_location['total_length'] = bytes2long(data[start+0x0:start+0x0+DWORD])
	if not bytes2long(data[start+0x4:start+0x4+DWORD]) == 0x1C:
		raise Exception("0x04-0x08 of file_location must be 0x1C")
	flags = bytes2long(data[start+0x08:start+0x08+DWORD])
	file_location['flags'] = {
		'on_local_volume': getbit ( flags, 0 ),
		'on_network_drive': getbit ( flags, 1 )
	}
	file_location['local_volume_info_offset'] = bytes2long(data[start+0xC:start+0xC+DWORD])
	file_location['base_pathname_offset'] = bytes2long(data[start+0x10:start+0x10+DWORD])
	file_location['network_volume_info_offset'] = bytes2long(data[start+0x14:start+0x14+DWORD])
	file_location['remaining_pathname_offset'] = bytes2long(data[start+0x18:start+0x18+DWORD])
	local_volume = {}
	
	if file_location['flags']['on_local_volume']:
		block = start + file_location['local_volume_info_offset']
		local_volume['length'] = bytes2long(data[block+0x0:block+0x0+DWORD])
		local_volume['type'] = bytes2long(data[block+0x4:block+0x4+DWORD])
		local_volume['serial_number'] = bytes2long(data[block+0x8:block+0x8+DWORD])
		if not bytes2long(data[block+0xC:block+0xC+DWORD]) == 0x10:
			raise Exception("0x0C-0x10 of local_volume_info must be 0x10")
		index = block + 0x10
		name = ""
		while not data[index] == 0:
			name += chr(data[index])
			index = index + 1
		local_volume['volume_label'] = name
		index = start + file_location['base_pathname_offset']
		name = ""
		while not data[index] == 0:
			name += chr(data[index])
			index = index + 1
		local_volume['base_pathname'] = name
	
	network_volume = {}
	if file_location['flags']['on_network_drive']:
		block = start + file_location['network_volume_info_offset']
		network_volume['length'] = bytes2long(data[block+0x0:block+0x0+DWORD])
		index = block + 0x14
		name = ""
		while not data[index] == 0:
			name += chr(data[index])
			index = index + 1
		network_volume['volume_label'] = name
	
	index = start + file_location['remaining_pathname_offset']
	name = ""
	while not data[index] == 0:
		name += chr(data[index])
		index = index + 1
	file_location['remaining_pathname'] = name
	
	start += file_location['total_length']
	
	if shortcut['flags']['description']:
		name = ""
		for i in range(0,2*(data[start]+256*data[start+1])):
			if i % 2 == 0:
				name += chr(data[start+2+i]+data[start+2+i+1]*256)
		start += i + 2 + 1
		shortcut['description']=str(name[:-1])
	else:
		shortcut['description']=""

	if shortcut['flags']['relative_path']:
		name = ""
		for i in range(0,2*(data[start]+256*data[start+1])):
			if i % 2 == 0:
				name += chr(data[start+2+i]+data[start+2+i+1]*256)
		start += i + 2 + 1
		shortcut['relative_path']=name
	else:
		shortcut['relative_path']=""
		
	if shortcut['flags']['working_directory']:
		name = ""
		for i in range(0,2*(data[start]+256*data[start+1])):
			if i % 2 == 0:
				name += chr(data[start+2+i]+data[start+2+i+1]*256)
		start += i + 2 + 1
		shortcut['working_directory']=str(name[:-1])
	else:
		shortcut['working_directory']=""
		
	if shortcut['flags']['command_line_arguments']:
		name = ""
		for i in range(0,2*(data[start]+256*data[start+1])):
			if i % 2 == 0:
				name += chr(data[start+2+i]+data[start+2+i+1]*256)
		start += i + 2 + 1
		shortcut['command_line_arguments']=str(name[:-1])
	else:
		shortcut['command_line_arguments']=""
	
	if shortcut['flags']['custom_icon']:
		name = ""
		for i in range(0,2*(data[start]+256*data[start+1])):
			if i % 2 == 0:
				name += chr(data[start+2+i]+data[start+2+i+1]*256)
		start += i + 2 + 1
		shortcut['custom_icon']=str(name[:-1])
	else:
		shortcut['custom_icon']=""

	file_location['network_volume'] = network_volume
	file_location['local_volume'] = local_volume
	shortcut['file_location'] = file_location
	
	if shortcut['file_location']['flags']['on_local_volume']:
		shortcut['target'] = shortcut['file_location']['local_volume']['base_pathname']
	elif shortcut['file_location']['flags']['on_network_drive']:
		shortcut['target'] = shortcut['file_location']['network_volume']['volume_label']
	shortcut['target'] += shortcut['file_location']['remaining_pathname']
	return shortcut

def lnkinfo ( filename ):
	print "Filename: " + filename
	lnk = readlnk ( filename )
	print "Target: " + lnk['target']
	print "Arguments: " + str(lnk['command_line_arguments'])
	print "Working directory: " + str(lnk['working_directory'])
	print "Relative path: " + str(lnk['relative_path'])
	print "Description: " + str(lnk['description'])
	print "Icon ID: " + str(lnk['icon_number'])
	print "Custom Icon: " + str(lnk['custom_icon'])
