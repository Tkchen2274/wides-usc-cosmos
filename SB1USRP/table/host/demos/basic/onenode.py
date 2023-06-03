"""
:Description: In this demo we control a single SDR node. We create an SDR object and an XY-Table object using the
`mmwsdr` library. The SDR object configures and controls a Xilinx RFSoC ZCU111 eval board and a Sivers IMA transceiver
board. A user can provide arguments to the script, such as the carrier frequency, the COSMOS node id and the transceiver
mode. The script by default starts a local connection with a carrier frequency at 60.48 GHz in receive mode.

:Organization: Wireless and Device System Lab, University of Southern California

:Authors: Yuning (Brian) Zhang

:Copyright: 2022
"""

"""
[B] This sections is the MATLAB code to provide the entire send-receive process. 

clc;clear;
rng(100)
n_fft = 1024;
sc = 400;
%% generate single tone frequency domain signal
TxSignalFreqDomain = zeros(n_fft, 1);
TxSignalFreqDomain(n_fft/2+sc) = 1;
TxSignalFreqDomain = circshift(TxSignalFreqDomain, n_fft/2);

%% Transform to time domain, normalization and get transmitted power
txtd = ifft(TxSignalFreqDomain);
txtd = txtd /max(abs(real(txtd)), abs(imag(txtd)));
txtd = txtd * 4000;
txtd = txtd(:, 1);


%% Data Transmission
n_parallel = 2;

x_real = reshape(int16(real(txtd)), n_parallel, [])';
x_imag = reshape(int16(imag(txtd)), n_parallel, [])';

% Transmitted signal
data = zeros(n_fft, n_parallel);
data(1:2:end, :) = x_real;
data(2:2:end, :) = x_imag;
data = reshape(data', [], 1);

% Add noise
data = data + randn(size(data, 1), size(data,2));

% Received signal
rxtd = reshape(int16(data), n_parallel, []).';

temp = (double(rxtd(1:2:end, :)) + 1j*double(rxtd(2:2:end, :)));
rxtd = temp;
rxtd = rxtd - mean(rxtd);
rxtd = reshape(rxtd.', [], 1);
% compare txtd and rxtd

"""

# ---------- Import Libraries ----------
import os
import sys
import socket
import argparse
import numpy as np
np.set_printoptions(threshold=np.inf)
import matplotlib
import configparser

matplotlib.use('TkAgg')
from matplotlib import pyplot as plt

path = os.path.relpath('../../')
if not path in sys.path:
    sys.path.append(path)
import mmwsdr


# ---------- Define Main ----------
def main():
    """
    Main function
    """

    # ---------- Parameters ----------
    N_fft = 1024  # num of continuous samples per frame
    N_skip = 1024  # num of samples to skip between frames
    N_frame = 1 # num of frames
  
    iscalibrated = True  # apply rx and tx calibration factors
    isdebug = True  # print debug messages
    islocal = True  # Eder array is connected directly to the node over USB
    # subCarrierIndex = 250  # subcarrier index
    #subCarrierMin = 0
    #subCarrierMax = 100
    mod = 'qam'
    seed = 100
    TxPwr = 4000  # transmit power
    f = np.linspace(-N_fft / 2, N_fft / 2 - 1, N_fft)  # subcarrier index vector for plotting


    # ---------- Create an argument parser ----------
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--freq", type=float, default=60.48e9, help="Carrier frequency in Hz (i.e., 60.48e9)")
    parser.add_argument("-n", "--node", type=str, default='srv1-in1', help="COSMOS-SB1 node name (i.e., srv1-in1)")
    parser.add_argument("-m", "--mode", type=str, default='rx', help="SDR mode (i.e., rx)")
    parser.add_argument("--min", dest='sc_min', type=str, default='-100')
    parser.add_argument("--max", dest='sc_max', type=str, default='100')
    parser.add_argument("-g", "--groupid", dest='groupID', type=str, default='1',help="1_x_data_file_name.txt")
    parser.add_argument("-d", "--dataid", dest='dataID', type=str, default='1',help="x_1_data_file_name.txt")
    parser.add_argument("-S", "--issavedata", dest='isSaveData', type=str, default='y',help="determine save data or not")
    args = parser.parse_args()


    # ---------- Create a configuration parser ----------
    config = configparser.ConfigParser()
    config.read('../../config/sivers.ini')

    # If the user is not providing a target node use the local node.
    if not args.node:
        node = socket.gethostname().split('.')[0]
    else:
        node = args.node


    # ---------- Create the SDR Class ----------
    # sdr_wides = mmwsdr.sdr.IBM28GHz(config=config, node=node, freq=args.freq, isdebug=isdebug, 
    #                               islocal=islocal, iscalibrated=iscalibrated)  
    sdr_wides = mmwsdr.sdr.Sivers60GHz(config=config, node=node, freq=args.freq, isdebug=isdebug, 
                                  islocal=islocal, iscalibrated=iscalibrated)
    # Create the XY-Table object
    if config[node]['table_name'] != None:
        xytable0 = mmwsdr.utils.XYTable(config[node]['table_name'], isdebug=isdebug)
        # move the RF front-head to the designed position and angle. 
        xytable0.move(x=float(config[node]['x']), y=float(config[node]['y']),
                      angle=float(config[node]['angle']))


    # ---------- Main experimentation loop ----------
    while (1):
        if args.mode == 'tx':
            # ----- Create a tone in frequency domain -----
            # scale time-domain signal multiply with Tx power;
            # txtd = mmwsdr.utils.waveform.onetone(subCarrierIndex=subCarrierIndex, nfft=N_fft)

            txtd = mmwsdr.utils.waveform.wideband(sc_min=int(args.sc_min), sc_max=int(args.sc_max), nfft=N_fft, mod=mod, seed=seed)
            sounding_file_name = "SoundingSignal_preNormalization" + "_minSc_" + str(args.sc_min) + "_maxSc_" + str(args.sc_max) + ".csv"
            np.savetxt(sounding_file_name, txtd, delimiter=',')
            txtd /= np.max([np.abs(txtd.real), np.abs(txtd.imag)])  # standard normalization method
            sounding_file_name = "SoundingSignal_prePower" + "_minSc_" + str(args.sc_min) + "_maxSc_" + str(args.sc_max) + ".csv"
            np.savetxt(sounding_file_name, txtd, delimiter=',')
            txtd *= TxPwr
            sounding_file_name = "SoundingSignal" + "_minSc_" + str(args.sc_min) + "_maxSc_" + str(args.sc_max) + ".csv"
            np.savetxt(sounding_file_name, txtd, delimiter=',')

            # ----- Transmit data -----
            sdr_wides.send(txtd)  # Transmit data, data is a column vector?

            # ----- print some data -----
            print('The length of the transmitted signal in TD is: ')
            print(len(np.transpose(txtd)))
            print('The first 30 samples of the transmitted signal in TD is: ')
            print(txtd[0:29,])

        elif args.mode == 'rx':
            """
            [B] RxSignaTimeDomain is a row vector, call its element by: [0, x].
            Receive N_frame x N_fft samples
            1. save N_fft samples
            2. pause for N_skip samples
            3. repeat steps 1, 2 N_frame times
            """
            # [B] RxSignaTimeDomain is a row vector, call its element by: [0, x].
            rxtd = sdr_wides.recv(N_fft, N_skip, N_frame)
            # print('The length of the received signal in TD is: ')
            # print(len(np.transpose(rxtd)))
            # print('The first 30 samples of the received signal in TD is: ')
            # print(rxtd[0,0:29])


            # [B]
            # ----- Save the Received Data -----
            # data_file_name = args.groupID + "_" + args.dataID + "_frame_" + str(N_frame) + "_minSc_" + str(args.sc_min) + "_maxSc_" + str(args.sc_max) + ".csv"
            # np.savetxt(data_file_name, np.transpose(rxtd), delimiter=',')
            data_file_name = args.groupID + "_" + args.dataID + "_frame_" + str(N_frame) + ".csv"
            data_file_path = os.path.abspath('./Result/Group_' + str(args.groupID) + '/' + data_file_name)
            if args.isSaveData == "y":
                np.savetxt(data_file_path, np.transpose(rxtd), delimiter=',')



            # ----- Convert the received data to frequncy domain -----
            rxfd = np.fft.fft(rxtd, axis=1)
            rxfd = np.fft.fftshift(rxfd, axes=1)
            print(rxfd[0,0:29])

            # ----- Find the magnitude of the data in dB -----
            mag = 20 * np.log10(np.abs(rxfd))

            # ----- Plot the data -----
            for iframe in range(N_frame):
                plt.plot(f, mag[iframe, :], '-')
            plt.xlabel('Sub-carrier Index')
            plt.ylabel('Magnitude [dB]')
            plt.tight_layout()
            y_min = np.mean(mag) - 20
            y_max = np.max(mag) + 20
            plt.ylim([y_min, y_max])
            plt.grid()
            # fig_name = args.groupID + "_" + args.dataID + "_frame_" + str(N_frame) + "_minSc_" + str(args.sc_min) + "_maxSc_" + str(args.sc_max) + ".png"
            fig_name = args.groupID + "_" + args.dataID + "_frame_" + str(N_frame) + ".png"
            fig_path = os.path.abspath('./Result/Group_' + str(args.groupID) + '/' + fig_name)
            if args.isSaveData == "y":
                plt.savefig(fig_path)
            # plt.savefig(fig_name)
            plt.show()
            
        else:
            raise ValueError("SDR mode can be either 'tx' or 'rx'")

        if sys.version_info[0] == 2:
            ans = raw_input("Enter 'q' to exit or\n press enter to continue ")
        else:
            ans = input("Enter 'q' to exit or\n press enter to continue ")

        # Exit from the loop when the input is 'q'. Otherwise continue.
        if ans == 'q':
            break


    # ---------- Close the TPC connections ----------
    # delete the sdr
    del sdr_wides



if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
