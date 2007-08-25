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

############################################################################
#    Wine Registry Format                                                  #
#                                                                          #
#    1. Line: WINE REGISTRY Version 2                                      #
#                                                                          #
#    Escaped string: All characters except the following are escaped       #
#    a..zA..Z,{}()[]/.;-0..9&@_:%*#'$<>?~                                  #
#    All other chars must be escaped using a \-escape sequence             #
#    Common short forms are \0 for the 0-byte, \\ for \ and \" for "       #
#                                                                          #
#    Folder line: [FOLDER_NAME] CHANGE_DATE                                #
#    FOLDER_NAME is an escaped string                                      #
#    CHANGE_DATE is the unix timestamp of the last change as a decimal     #
#                                                                          #
#    Attribute line: NAME=VALUE                                            #
#    NAME is an escaped string wrapped in "" or simply @                   #
#    VALUE may be the following:                                           #
#    - an escaped string wrapped in ""                                     #
#    - dword:DWORD where DWORD is a string of 8 hexadecimal digits         #
#      the value is interpreted as little-endian                           #
#    - str(2):STRING where STRING is an escaped string wrapped in ""       #
#    - str(7):STRING where STRING is an escaped string wrapped in ""       #
#    - hex:HEXSTR where HEXSTR is an arbitrary string of hexadecimal pairs #
#      separated by commas, this can be split into several lines using \   #
#                                                                          #
############################################################################

class Path:
	def __init__(self,name,chdate):
		print name
		self.name = name
		self.chdate = chdate
		self.attrs = {}
	def __str__(self):
		return "[" + escapeString(self.name) + "] " + str(self.chdate)
	def addAttr (self,name,typ,value):
		r = Attr(name,typ,value)
		self.attrs[name] = r
		return r
	def getAttr (self,name):
		try:
			return self.attrs[name]
		except (KeyError):
			return None
	
class Attr:
	def __init__(self,name,typ,value):
		self.name = name
		self.typ = typ
		self.value = value
	def __str__(self):
		name = self.name
		value = self.value
		if not self.name == "@": name = "\"" + escapeString ( name ) + "\""
		if self.typ[0:3] == "str": value = "\"" + escapeString ( value ) + "\""
		tv = self.typ + ":" + value
		if self.typ == "string": tv = value
		return name + "=" + tv

class Registry:
	def addPath (self,name,chdate):
		r = Path(name,chdate)
		self.paths[name] = r
		return r

	def getPath (self,name):
		try:
			return self.paths[name]
		except (KeyError):
			return None
	
	def save (self,file):
		fp = open(file,"w")
		fp.write ( "WINE REGISTRY Version 2\n" )
		for name, p in self.paths.iteritems():
			fp.write ( "\n" )
			fp.write ( str(p) + "\n" )
			for name, a in p.attrs.iteritems():
				fp.write ( str(a) + "\n" )
		fp.close ()
	
	def load (self,file):
		self.paths = {}
		fp = open(file,"r")
		path = None
		while True:
			s = fp.readline()
			if not s: break
			s = s[:-1]
			while s[-1:] == "\\":
				s = s[:-1] + fp.readline()[:-1]
			if s == "WINE REGISTRY Version 2": continue #ignore version 2 header
			if s[0:2] == ";;": continue #ignore comments
			if len(s) == 0: continue #ignore empty lines
			if s[0] == '[': #parse folder line
				space = s.rfind(" ")
				name = deescapeString(s[1:space-1])
				date = int(s[space+1:])
				path = self.addPath ( name, date )
				continue
			if s[0] == '"' or s[0] == '@': #parse attribute line
				eq = s.rfind("=")
				name = s[0:eq]
				if name[0] == "\"": name = deescapeString(s[1:eq-1])
				tv = s[eq+1:]
				if tv[0] == "\"":
					typ = "string" 
					value = deescapeString(tv[1:-1])
				else:
					sep = tv.find(":")
					typ = tv[0:sep]
					value = tv[sep+1:]
					if value[0] == "\"": value = deescapeString(value[1:-1])
				path.addAttr ( name, typ, value )
				continue
			raise Exception("Invalid line: " + s)


plainchrs = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ,{}()[]/.;-0123456789&@_:%*#'$<>?~ "
def escapeString(string):
	result = ""
	for ch in string:
		if ch in plainchrs:
			result += ch
			continue
		if ch == "\\":
			result += "\\\\"
			continue
		if ch == "\"":
			result += "\\\""
			continue
		if ch == "\n":
			result += "\\n"
			continue
		b = ord(ch)
		if b == 0:
			result += "\\0"
			continue
		hexStr = "0123456789abcdef"
		result += "\\x" + hexStr[b/16] + hexStr[b%16]
	return result
def deescapeString(string):
	result = ""
	i = 0
	while i < len(string):
		ch = string[i]
		i = i+1
		if ch in plainchrs:
			result+=ch
			continue
		if ch == "\\":
			ch = string[i]
			i = i+1
			if ch == "\\" or ch == "\"":
				result += ch
				continue
			if ch == "n":
				result += "\n"
				continue
			if ch == "0":
				result += "\0"
				continue
			if ch == "x":
				result += eval("\""+string[i-2:i+2]+"\"")  #this should be safe
				i+=2
				continue
			raise Exception("Invalid escape sequence: \\" + ch)
		raise Exception("Invalid character in escaped string: " + ch)
	return result
