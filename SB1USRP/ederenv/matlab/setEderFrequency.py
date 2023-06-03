#!/usr/bin/python

import sys
#sys.path.append('..//')
sys.path.append('/home/pi/projects/eder')
import eder
import argparse

eder = eder.Eder()

parser = argparse.ArgumentParser()
parser.add_argument("freq", help = "Set 1 digit", type = str)


input = parser.parse_args()


n=int(input.freq, 16)

eder.pll.set(n)
