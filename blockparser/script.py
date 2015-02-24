#!/bin/env python

import sys,os
import re,pdb
import json
from base64 import encode


from optparse import OptionParser
from copylib import *


usage = "Usage: %prog INPUT_FILE"
parser = OptionParser(usage)
parser.add_option("-o", "--output", dest="outdir", metavar="OUTPUT_FOLDER", help="Specify the eclipse workspace folder")

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
rows = []
with open('blocks.txt', 'rb') as infile:
    for line in infile:
        datas = line.split('\t')
        rows.append({'id': int(datas[0]), 'hash': datas([1]), 'time': int(datas[2])})

with open('blocks.dat', 'w') as outfile:
    for row in rows:
        row[hash] = "'" + encode(row[hash]) + "'"
        values = [i for i in row.values()]
        outfile.write('\t'.join(values) + '\n')
        
