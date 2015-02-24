#!/bin/env python3
import sys,os
import re,pdb
import json


from optparse import OptionParser
from copylib import *


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


if optlist.json:
    json_data = open(optlist.json)
    data = json.load(json_data)
    json_data.close()
    optlist.serviceName = data['serviceName']
    optlist.packageName = data['packageName']

init(optlist.packageName, optlist.serviceName)
#ptree(root)
ccobol = open(args[0], 'r')
tree = CodeTree(ccobol)
#print(tree.xmlMap())
#tree.ptree()
#print(tree.root.xmlMap())
for p in tree.placeHolders:
    print(p.getMock())


if not os.path.isdir(optlist.outdir):
    os.mkdir(optlist.outdir)
outpath = optlist.outdir
     

open(outpath + '/%sMQMock.properties' % (optlist.serviceName), 'w').write(tree.getMock())
open(outpath + '/%sConnector.xml' % (optlist.serviceName), 'w').write(tree.xmlMap())
open(outpath + '/I%sConnector.java' % (optlist.serviceName), 'w').write(tree.getInterface())
open(outpath + '/%sConnectorImpl.java' % (optlist.serviceName), 'w').write(tree.getImpl())

