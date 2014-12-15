#!/bin/env python3
import sys,os
import re,pdb
import json

from random import random,choice
from optparse import OptionParser

usage = "Usage: %prog COPY_COBOL_FILE  -o OUTPUT_FOLDER -s SERVICE_NAME"
parser = OptionParser(usage)
parser.add_option("-o", "--output", dest="outdir", metavar="OUTPUT_FOLDER", help="Specify the eclipse workspace folder")
parser.add_option("-s", "--service-name", dest="serviceName", metavar="SERVICE_NAME", help="Specify the service name")
parser.add_option("-p", "--package-name", dest="packageName", metavar="PACKAGE_NAME", help="Specify the package name")
parser.add_option("-c", "--configuration", dest="json", help="Read configuration from JSON configuration file, this configuration will override all the others")

optlist, args = parser.parse_args()

if len(args) < 1:
    parser.print_usage()
    sys.exit(-1)
if not optlist.outdir:
        optlist.outdir = '.'
if not optlist.serviceName:
    optlist.serviceName = 'GenericService'
if not optlist.packageName:
    optlist.packageName = 'classpath'

def lowFirst(string):
    return string[0].lower() + string[1:]

if optlist.json:
    json_data = open(optlist.json)
    data = json.load(json_data)
    json_data.close()
    optlist.serviceName = data['serviceName']
    optlist.packageName = data['packageName']

def convertCamelCase(s):
    lower = False
    res = ''
    for c in s:
        old = lower
        if c.lower() == c:
            lower = True
        else:
            lower = False
        if not lower and lower != old:
            res += '_' + c.lower()
        else:
            res += c.lower()
    return res

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
        xmlFieldMap = open('templateField.xml', 'r').read()
        xmlListMap = open('templateList.xml', 'r').read()
        ioParser = re.compile('^[a-zA-Z0-9_-]+-O-[a-zA-Z0-9_-]+$')
        def __init__(self, name, parent=None, occurrency=None):
                self.isCursor = False
                self.occurrency = occurrency
                self.parent = parent
                self.level = (self.parent and (self.parent.level + 1)) or 0
                self.name = name
                if parent:
                        parent.children.append(self)
                self.children = []
                if Node.ioParser.match(self.name):
                        self.io = 'OUT'
                else:
                        self.io = 'IN'
        
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
            if self.occurrency and self.occurrency > 1:
                i = 0
                for ch in self.parent.children:
                    if ch is self:
                        myindex = i
                    i += 1
                i = 0
                cursor = None
                for i in range(myindex):
                    ch = self.parent.children[i]
                    if ch.isCursor:
                        cursor = ch
                    i += 1
                tmp = ' '*12
                for ch in self.children:
                    tmp += ch.xmlMap()
                children = ('>\n' + ' '*12 + '<').join(tmp.split('>\n<'))[:-1]
                if cursor:
                    typeCode = '1'
                    name = cursor.name
                    others = 'p:dimCursorLenght="%d"' % cursor.size
                else:
                    typeCode = self.getField().code
                    name = self.name
                    others = ''
                d = {
                    'children': children,
                    'typeCode': typeCode,
                    'size': self.occurrency,
                    'io': self.io,
                    'name': name,
                    'mapperClassPath': optlist.packageName + '.' + optlist.serviceName + 'MQMapper',
                    'others': others
                }
                xml = Node.xmlListMap.format(**d)
            else:
                xml=''
                for c in self.children:
                    xml += c.xmlMap()
            return xml

                

class PlaceHolder(Node):
        typeParser = re.compile('\((\d+)\)')
        intParser = re.compile('^(9|S9)\((\d+)\)$')
        decParser = re.compile('^(S)?(9+)(\((\d+)\))?V(9+)(\((\d+)\))?$')
        stringParser = re.compile('^(X+)(\((\d+)\))?$')
        cursorParser = re.compile('.*-NUMOCCURS$|.*-NUM-ELEMENTI$')
        dateParser = re.compile('-DATA?-')
        signParser = re.compile('^.*-S$')

        def __init__(self, name, dataType, parent=None):
                super(PlaceHolder, self).__init__(name, parent)
                m = PlaceHolder.cursorParser.match(name)
                if m:
                    self.isCursor = True
                else:
                    self.isCursor = False
                self.intSize = None
                self.decSize = None
                self.size = sum([int(n) for n in PlaceHolder.typeParser.findall(dataType)])
                self.dataType = dataType
                m = PlaceHolder.decParser.match(self.dataType)
                #if self.name == 'XDPH919C-O-OF-PFL-LEAS':
                #     pdb.set_trace()   
                if m:                        
                        self.intSize = ((m.group(4) and (int(m.group(4)))-1) or 0) + ((m.group(2) and len(m.group(2))>0 and len(m.group(2))) or 0)
                        self.decSize = ((m.group(7) and (int(m.group(7)))-1) or 0) + ((m.group(5) and len(m.group(5))>0 and len(m.group(5))) or 0)
                        self.size = self.intSize
                
                m=PlaceHolder.intParser.match(self.dataType)
                if m: 
                    self.intSize = int(m.group(2))
                    self.size = self.intSize

                if self.dataType[0] == 'S':
                    self.size += 1

        
        def __str__(self):
                res = '%sname: %s parent: %s dataType: %s size: %s\n' % ('  '*self.level, self.name, self.parent and self.parent.__address__(), self.dataType, self.size)
                for n in self.children:
                        res += str(n)
                return res
        
        def getField(self):
                m = PlaceHolder.intParser.match(self.dataType)
                t = None
                if m:
                        t = 'BigInteger'
                elif PlaceHolder.decParser.match(self.dataType):
                        t = 'BigDecimal'
                elif PlaceHolder.stringParser.match(self.dataType):
                        t = 'String'
                n = PlaceHolder.dateParser.search(self.name)
                if m and n and self.size == 8:
                    t = 'Date'
                return Field(self.name, self.name, t, self.io)
        
        def getMock(self):
                if PlaceHolder.ioParser.match(self.name):
                        i = 'OUT'
                else:
                        return ''
                m = PlaceHolder.signParser.match(self.name)
                if self.size == 1 and m:
                        return choice(('+','-'))
                        
                if self.getField().dataType == 'Date':
                    return datetime.date.today().strftime('%Y%m%d')
                    
                m = PlaceHolder.intParser.match(self.dataType)
                if m:
                        size = int(m.group(2))
                        if PlaceHolder.cursorParser.match(self.name):
                            return str(1).zfill(size)
                        res = str(int(random() * 10**size)).zfill(size)
                        if m.group(1) == 'S9':
                                size+=1
                                res = '-' + res
                        return res
                m = PlaceHolder.decParser.match(self.dataType)
                if m:
                        intSize = self.intSize
                        decSize = self.decSize
                        
                        res = str(int(random() * 10**intSize)).zfill(intSize) + str(int(random() * 10**decSize)).zfill(decSize)
                        if m.group(1):
                                #intSize+=1
                                res = choice(['-','+']) + res
                        return res
                m = PlaceHolder.stringParser.match(self.dataType)
                if m:
                    if m.group(3):
                            size = int(m.group(3))
                    else:
                        size = len(m.group(1))
                    res = self.name[:size]
                    return res.rjust(size, 'F')

        def xmlMap(self):
            if self.isCursor:
                return ''
            others = ''
            if self.decSize:
                others += ' p:decimalLength="%d"' % (self.decSize)
            elif self.getField().dataType == 'Date':
                others += ' p:dateFormat="yyyyMMdd"'
            if self.io == 'IN':
                others += ' p:signatureIndex="1"'
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
    typeRegExp = re.compile('PIC +([\w\d\(\)]+)(\s+|$)')
    typeParser = re.compile('\((\d+)\)')
    occurParser = re.compile(' OCCURS +(\d+)')
    templateConnector = open('templateConnector.xml', 'r').read()
    mockResponse = open('mockResponse.txt', 'r').read()[:-1]
    templateConnectorImpl = open('TemplateConnectorImpl.java', 'r').read()
    templateConnectorInterface = open('TemplateConnectorInterface.java', 'r').read()

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
        mapping = self.root.xmlMap()
        d = {
        'mapping': mapping,
        'connectorName': lowFirst(optlist.serviceName) + 'Connector',
        'moduleName': lowFirst(optlist.serviceName) + 'ConnectorModule',
        'beanName': lowFirst(optlist.serviceName) + 'ConnectorBean',
        'interfaceClassPath': optlist.packageName + '.I' + optlist.serviceName + 'Connector',
        'implClassPath': optlist.packageName + '.' + optlist.serviceName + 'ConnectorImpl',
        }
        return CodeTree.templateConnector.format(**d)

    def ptree(self):
        for t in self.tree.children:
            self.ptree()
            print(t)

    def getMock(self):
        mock = CodeTree.mockResponse
        for p in self.placeHolders:
            mock += p.getMock()
        return mock

    def getInterface(self):
        d = {
        'serviceName': optlist.serviceName,
        'packageName': optlist.packageName,
        }
        return CodeTree.templateConnectorInterface.format(**d)

    def getImpl(self):
        d = {
        'serviceName': optlist.serviceName,
        'packageName': optlist.packageName,
        }
        return CodeTree.templateConnectorImpl.format(**d)

#ptree(root)
ccobol = open(args[0], 'r')
tree = CodeTree(ccobol)
#print(tree.xmlMap())
#tree.ptree()
#print(tree.root.xmlMap())
for p in tree.placeHolders:
    print('%s\t%s' %(p.getMock(), p.name))


if not os.path.isdir(optlist.outdir):
    os.mkdir(optlist.outdir)
outpath = optlist.outdir
     

open(outpath + '/%sMQMock.properties' % (optlist.serviceName), 'w').write(tree.getMock())
open(outpath + '/%sConnector.xml' % (optlist.serviceName), 'w').write(tree.xmlMap())
open(outpath + '/I%sConnector.java' % (optlist.serviceName), 'w').write(tree.getInterface())
open(outpath + '/%sConnectorImpl.java' % (optlist.serviceName), 'w').write(tree.getImpl())

