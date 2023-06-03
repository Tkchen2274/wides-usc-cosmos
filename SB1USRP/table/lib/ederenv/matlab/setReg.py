#!/usr/bin/python
# Code ran can only be code usuable from within a Eder instance.
import sys
import ast
#sys.path.append('..//')
sys.path.append('/home/pi/projects/eder')
import eder
import argparse




parser = argparse.ArgumentParser()
parser.add_argument("register", help = "", type = str)
parser.add_argument("value", help = "", type = str)

eder = eder.Eder()


inp = parser.parse_args()

if inp.value.startswith("0x"):
    value = int(inp.value,0)
elif inp.value.startswith("0b"):
    value = int(inp.value,0)
else:
    value = int(inp.value)

print eder.regs.wr(inp.register, value);


