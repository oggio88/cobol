#!/bin/env python3
import sys
import re,pdb

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

class Node:
        def __init__(self, parent=None, repeat=1):
                self.childs = []
                self.parent = parent
                self.repeat = repeat
                if parent:
                        parent.addChild(self)
                
        def addChild(self, child):
                self.childs.append(child)
        
        def __str__(self):
                return '{parent: %s, childs: %s, repeat: %d}' % (str(self.parent), str(self.childs), self.repeat)
        
        def __repr__(self):
                return str(self)
        
           

class PlaceHolder(Node):
        typeParser = re.compile('\((\d+)\)')

        def __init__(self,parent,name,dataType):
                super(PlaceHolder,self).__init__(parent)
                self.name = name
                self.size = sum([int(n) for n in PlaceHolder.typeParser.findall(dataType)])
        
        def __str__(self):
                return '{name: %s, size: %d, parent: %s, childs: %s, repeat: %d}' % (self.name, self.size, str(self.parent), str(self.childs), self.repeat)
        
        def __repr__(self):
                return str(self)
        

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


class CodeTree:
    identRegExp = re.compile('^(\d+) +([A-Z0-9_\-]+)(?: .*|$)')
    typeRegExp = re.compile('PIC +(.+\(\d+\))+')
    typeParser = re.compile('\((\d+)\)')
    occurParser = re.compile(' OCCUR +(\d+)')

    def __init__(self, ccobol):
        identList=[]
        self.root = Node()
        parent = self.root
        #pdb.set_trace()
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
            if len(identList):
                    if ident > identList[-1]:
                            parent = parent.childs[-1]
                    elif ident == identList[-1]:
                            pass
                    else:
                            while ident < identList[-1]:
                                    identList.pop()
                                    parent = parent.parent

            else:
                    identList.append(ident)

            pdb.set_trace()

            name = m.group(2)
            m = CodeTree.typeRegExp.search(line)
            if m:
                    dataType = m.group(1)
                    PlaceHolder(parent, name, dataType)
            else:
                    Node(parent, occurrency)

        def print(self):
            for t in self.root.children:
                self.print(t)
                print(t)
ccobol = open(args[0], 'r')
tree = CodeTree(ccobol)

tree.print()
