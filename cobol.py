#!/bin/env python3
import sys
import re,pdb

from random import random

from optparse import OptionParser

usage = "Usage: %prog COPY_COBOL_FILE  -o OUTPUT_FILE"
parser = OptionParser(usage)
parser.add_option("-o", "--output", dest="outfile",metavar="OUTPUT_FILE",
          help="Specify the eclipse workspace folder")

optlist, args = parser.parse_args()

if len(args) < 1:
	parser.print_usage()
	sys.exit(-1)
if not optlist.outfile:
        optlist.outfile = 'out.txt'
        
class Field:
	def __init__(self, name=None, xmlid=None, dataType=None, io=None):
		self.name = name
		self.xmlid = xmlid
		self.dataType = dataType
		self.io = io

class Node:
        def __init__(self,name,parent=None):
                self.parent = parent
                self.level = (self.parent and (self.parent.level + 1)) or 0
                self.name = name
                if parent:
                        parent.childs.append(self)
                self.childs=[]
        
        def __repr__(self):
                return str(self)
        
        def __str__(self):
                res = '%sname: %s parent: %s\n' % ('  '*self.level, self.name, self.parent and self.parent.__address__())
                for n in self.childs:
                        res += str(n)
                return res
        
        def __address__(self):
                return '<%s.%s object at %s>' % (self.__class__.__module__, self.__class__.__name__,hex(id(self)))

                

class PlaceHolder(Node):
        typeParser = re.compile('\((\d+)\)')
        ioParser = re.compile('^[a-zA-Z0-9_-]+-O-[a-zA-Z0-9_-]+$')
        intParser = re.compile('^(9|S9)\((\d+)\)$')
        decParser = re.compile('^(9|S9)\((\d+)\)V9\((\d+)\)$')
        stringParser = re.compile('^X\((\d+)\)$')

        def __init__(self,name,dataType,parent=None):
                super(PlaceHolder,self).__init__(name,parent)
                self.size = sum([int(n) for n in PlaceHolder.typeParser.findall(dataType)])
                self.dataType = dataType
                if self.dataType[0] == 'S':
                        self.size += 1
        
        def __str__(self):
                res = '%sname: %s parent: %s dataType: %s\n' % ('  '*self.level, self.name, self.parent and self.parent.__address__(), self.dataType)
                for n in self.childs:
                        res += str(n)
                return res
        
        def getField():
                m = PlaceHolder.intParser.match(self.dataType)
                if m:
                        t = 'BigInt'
                elif PlaceHolder.decParser.match(self.dataType):
                        t = 'BigDecimal'
                elif PlaceHolder.stringParser.match(self.dataType):
                        t = 'String'
                if PlaceHolder.ioParser.match(self.name):
                        i = 'OUT'
                else:
                        i = 'IN'
                return Field(self.name, self.name, t, i)
        
        def getMock(self):
                if PlaceHolder.ioParser.match(self.name):
                        i = 'OUT'
                else:
                        return ''               
                        
                m = PlaceHolder.intParser.match(self.dataType)
                if m:
                        size = int(m.group(2))
                        if 'OCCURS' in self.name:
                            return str(1).zfill(size)
                        res = str(int(random() * 10**size)).zfill(size)
                        if m.group(1) == 'S9':
                                size+=1
                                res = '-' + res
                        return res
                m = PlaceHolder.decParser.match(self.dataType)
                if m:
                        intSize = int(m.group(2))
                        decSize = int(m.group(3))
                        
                        res = str(int(random() * 10**intSize)).zfill(intSize) + str(int(random() * 10**decSize)).zfill(decSize)
                        if m.group(1) == 'S9':
                                intSize+=1
                                res = '-' + res
                        return res
                m = PlaceHolder.stringParser.match(self.dataType)
                if m:
                    size = int(m.group(1))
                    res = self.name[:size]
                    return res.rjust(size, 'F')
                 
                
                  

def readStatement(instream):
        res = ''
        comment = False
        while True:
                c = instream.read(1)
                if comment and c == '\n':
                        comment = False
                elif comment:
                        continue
                
                if c == '.' or c == '':
                        break
                elif c == '*':
                        comment = True
                        continue
                else:
                        res += c
        return res.strip().upper()
                 
ccobol = open(args[0],'r')
identRegExp = re.compile('^(\d+) +([A-Z0-9_\-]+)(?: .*|$)')
typeRegExp = re.compile('PIC +(.+\(\d+\))+')
typeParser = re.compile('\((\d+)\)')
occurParser = re.compile(' OCCUR +(\d+)')

identList=[]
root = Node('root')
parent = root
#pdb.set_trace()
placeHolders = []
while True:
        occurrency = 1
        line = readStatement(ccobol)
        if line == '':
                break
        elif line[0] == '*':
                continue
        m = occurParser.search(line)
        if m:
                occurrency = int(m.group(1))
        m = identRegExp.match(line)
        if not m:
                continue
        ident = int(m.group(1))
        name = m.group(2)
        if len(identList):
                if ident > identList[-1]:
                        parent = parent.childs[-1]
                        identList.append(ident)
                elif ident == identList[-1]:
                        pass
                else:
                        while ident < identList[-1]:
                                identList.pop()
                                parent = parent.parent
        else:
                identList.append(ident)
        print(identList,parent)
        
        
        #pdb.set_trace()
        
        m = typeRegExp.search(line)
        if m:
                dataType = m.group(1)
                placeHolders.append(PlaceHolder(name,dataType,parent))
        else:
                Node(name,parent)
                

def ptree(tree):
        for t in tree.childs:
                ptree(t)
                print(t)
#ptree(root)
print(root)
for p in placeHolders:
	print(p.getMock())
mock = open('mockResponse.txt','r').read()[:-1]
for p in placeHolders:
	mock += p.getMock()
open(optlist.outfile, 'w').write(mock)
