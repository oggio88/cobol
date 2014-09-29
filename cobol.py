#!/bin/env python3
import sys
import re,pdb

from random import random

from optparse import OptionParser

usage = "Usage: %prog COPY_COBOL_FILE  -o OUTPUT_FILE"
parser = OptionParser(usage)
parser.add_option("-o", "--output", dest="outfile", metavar="OUTPUT_FILE", help="Specify the eclipse workspace folder")

optlist, args = parser.parse_args()

if len(args) < 1:
    parser.print_usage()
    sys.exit(-1)
if not optlist.outfile:
        optlist.outfile = 'out.txt'
        
class Field:
    typeMap = {
        'int': 1,
        'String': 2,
        'BigDecimal': 3,
        'BigInteger': 3,
        'Date': 4,
    }

    def __init__(self, name=None, xmlid=None, dataType=None, io=None):
        self.name = name
        self.xmlid = xmlid
        self.dataType = dataType
        self.io = io

    def code(self):
        return Field.typeMap[self.dataType]

class Node:
        def __init__(self, name, parent=None, occurrency=None):
                self.occurrency = occurrency
                self.parent = parent
                self.level = (self.parent and (self.parent.level + 1)) or 0
                self.name = name
                if parent:
                        parent.children.append(self)
                self.children = []
        
        def __repr__(self):
                return str(self)
        
        def __str__(self):
                res = '%sname: %s parent: %s\n' % ('  '*self.level, self.name, self.parent and self.parent.__address__())
                for n in self.children:
                        res += str(n)
                return res
        
        def __address__(self):
                return '<%s.%s object at %s>' % (self.__class__.__module__, self.__class__.__name__, hex(id(self)))

        def xmlMap(self):
            res = ''
            for c in self.children:
                if not c.occurrency or c.occurrency == 1:
                    res += c.xmlMap() + '\n'
            return res

                

class PlaceHolder(Node):
        xmlFieldMap = open('templateField.xml', 'r').read()
        xmlListMap = open('templateList.xml', 'r').read()
        typeParser = re.compile('\((\d+)\)')
        ioParser = re.compile('^[a-zA-Z0-9_-]+-O-[a-zA-Z0-9_-]+$')
        intParser = re.compile('^(9|S9)\((\d+)\)$')
        decParser = re.compile('^(9|S9)\((\d+)\)V9\((\d+)\)$')
        stringParser = re.compile('^X\((\d+)\)$')
        cursorParser = re.compile('.*-NUMOCCURS$')

        def __init__(self, name, dataType, parent=None):
                m = PlaceHolder.cursorParser.search(name)
                if m:
                    self.isCursor = True
                else:
                    self.isCursor = False
                super(PlaceHolder, self).__init__(name, parent)
                self.size = sum([int(n) for n in PlaceHolder.typeParser.findall(dataType)])
                self.dataType = dataType
                if self.dataType[0] == 'S':
                        self.size += 1
                m = PlaceHolder.decParser.match(self.dataType)
                if m:
                        self.intSize = int(m.group(2))
                        self.decSize = int(m.group(3))
                else:
                    self.intSize = None
                    self.decSize = None
        
        def __str__(self):
                res = '%sname: %s parent: %s dataType: %s size: %s\n' % ('  '*self.level, self.name, self.parent and self.parent.__address__(), self.dataType, self.size)
                for n in self.children:
                        res += str(n)
                return res
        
        def getField(self):
                m = PlaceHolder.intParser.match(self.dataType)
                if m:
                        t = 'BigInteger'
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

        def xmlMap(self):
            if self.isCursor:
                xml = PlaceHolder.xmlListMap
                children = ''
                i = 0
                for ch in self.parent.children:
                    if ch is self:
                        listAncestor = self.parent.children[i+1]
                        length = listAncestor.occurrency
                    i += 1
                tmp = ' '*12
                for ch in listAncestor.children:
                    tmp += ch.xmlMap()
                children = ('>\n' + ' '*12 + '<').join(tmp.split('>\n<'))[:-1]

                d = {
                    'children': children,
                    'typeCode': self.getField().code(),
                    'size': length,
                    'io': self.getField().io,
                    'name': self.name,
                    'cursorDim': self.size,
                    'mapperClassPath': 'qwertyasdfg',
                }
                xml = PlaceHolder.xmlListMap.format(**d)
            else:
                if self.decSize:
                    others = ' stacippa' + str(self.decSize)
                else:
                    others = ''
                d = {
                    'name': self.name,
                    'typeCode': self.getField().code(),
                    'mapperField':  '',
                    'size': self.size,
                    'io': self.getField().io,
                    'others': others
                }
                xml = PlaceHolder.xmlFieldMap.format(**d)

            return xml
                
                  

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

class CodeTree():
    identRegExp = re.compile('^(\d+) +([A-Z0-9_\-]+)(?: .*|$)')
    typeRegExp = re.compile('PIC +(.+\(\d+\))+')
    typeParser = re.compile('\((\d+)\)')
    occurParser = re.compile(' OCCURS +(\d+)')
    templateConnector = open('templateConnector.xml', 'r').read()

    def __init__(self, ccobol):
        identList=[]
        self.root = Node('root')
        parent = self.root
        #pdb.set_trace()
        self.placeHolders = []
        self.nodes = []
        while True:
                occurrency = 1
                line = readStatement(ccobol)
                if line == '':
                        break
                elif line[0] == '*':
                        continue
                m = CodeTree.occurParser.search(line)
                if m:
                        occurrency = int(m.group(1))
                m = CodeTree.identRegExp.match(line)
                if not m:
                        continue
                ident = int(m.group(1))
                name = m.group(2)
                if len(identList):
                        if ident > identList[-1]:
                                parent = parent.children[-1]
                                identList.append(ident)
                        elif ident == identList[-1]:
                                pass
                        else:
                                while ident < identList[-1]:
                                        identList.pop()
                                        parent = parent.parent
                else:
                        identList.append(ident)
                #print(identList, parent)
                #print(parent)


                #pdb.set_trace()

                m = CodeTree.typeRegExp.search(line)
                if m:
                        dataType = m.group(1)
                        self.placeHolders.append(PlaceHolder(name, dataType, parent))
                else:
                        self.nodes.append(Node(name, parent, occurrency))

    def xmlMap(self):
        #for c in root.children():
        return

    def ptree(self):
        for t in self.tree.children:
            self.ptree()
            print(t)








#ptree(root)
ccobol = open(args[0], 'r')
tree = CodeTree(ccobol)
print(tree.root)
#tree.ptree()
print(tree.root.xmlMap())
for p in tree.placeHolders:
	print(p.getMock())
mock = open('mockResponse.txt', 'r').read()[:-1]
for p in tree.placeHolders:
	mock += p.getMock()
open(optlist.outfile, 'w').write(mock)
