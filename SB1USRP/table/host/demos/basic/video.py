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

    # Create an argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--node", type=str, default='srv1-in1', help="COSMOS-SB1 node name (i.e., srv1-in1)")
    parser.add_argument("--x", type=int, default=0, help="x coordinate on XY table")
    parser.add_argument("--y", type=int, default=0, help="y coordinate on XY table")
    parser.add_argument("--a", type=int, default=0, help="angle of the array on XY table")
    parser.add_argument("--t", dest='videotime', type=int, default=10800, help="video duration")
    args = parser.parse_args()

    # Create a configuration parser
    config = configparser.ConfigParser()
    config.read('../../config/sivers.ini')

    xytable0 = mmwsdr.utils.XYTable(config[args.node]['table_name'], isdebug=isdebug)

    if args.x and args.y and args.a:
        xytable0.move(x=args.x, y=args.y, angle=args.a)


    t = threading.Thread(target=xytable0.video(t=args.videotime))
    t.daemon = True
    t.start()

    # Create a move
    # xytable0.move(x=500, y=500, angle=-45)

    t.join()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
