#!/usr/bin/python

import sys
#sys.path.append('..//')
sys.path.append('/home/pi/projects/eder')
import eder
import argparse

eder = eder.Eder()

parser = argparse.ArgumentParser()
parser.add_argument("n",nargs="+" ,help = "Set r[row col data]", type = int)
args = parser.parse_args()

eder.tx.bf.awv.wr(args.n[0],args.n[1],args.n[2])
##print 'set value at (',args.n[0],',',args.n[1],') : ' , eder.tx.bf.awv.rd(args.n[0],args.n[1])
