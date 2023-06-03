#!/usr/bin/python
# Code ran can only be code usuable from within a Eder instance.
import sys
import ast
#sys.path.append('..//')
sys.path.append('/home/pi/projects/eder')
import eder
import argparse




parser = argparse.ArgumentParser()
parser.add_argument("code", help = "Code to run in python interpreter.\n Only usable if usable within Eder instance.", type = str)
eder = eder.Eder()

inp = parser.parse_args()

eval(inp.code);


