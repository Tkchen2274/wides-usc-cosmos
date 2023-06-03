"""
"""

# Import Libraries
import os
import sys
import argparse
import numpy as np
import matplotlib
import configparser
import threading

matplotlib.use('TkAgg')
from matplotlib import pyplot as plt

path = os.path.abspath('../../')
if not path in sys.path:
    sys.path.append(path)
import mmwsdr


def main():
    """

    :return:
    :rtype:
    """
    # Parameters
    isdebug = True

    # Create a configuration parser
    config = configparser.ConfigParser()
    config.read('../../config/sivers.ini')

    xytable1 = mmwsdr.utils.XYTable(config["srv1-in1"]['table_name'], isdebug=isdebug)
    xytable2 = mmwsdr.utils.XYTable(config["srv1-in2"]['table_name'], isdebug=isdebug)

    
    print(" ")
    print("Checking XY table 1 position...")
    xytable1.check()

    print(" ")

    print("Checking XY table 2 position...")
    xytable2.check()

    print(" ")

    # t = threading.Thread(target=xytable0.video(t=args.videotime))
    # t.start()

    # Create a move
    # xytable0.move(x=500, y=500, angle=-45)

    # t.join()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
