"""
:Description: 

******** Original from COSMOS ********
This class creates an software defined radio (SDR) comprised with a Xilinx ZynqMP Ultrascale+ RFSoC FPGA
board and a Sivers IMA TRX BF/01. The TRX BF/01 is a 16+16 IEEE802.11ad beamforming transceiver with a 
compute radio front-end operating in the 57-66 GHz bands. This class has been designed for the setup in 
the COSMOS testbed. More information could be found in docs.
**************************************

********** Modify for WiDeS **********
Band is targeted to 28GHz, using the IBM PAAM array. 
**************************************

:Organization: Wireless and Device System Lab, University of Southern California

:Authors: Panagiotis Skrimponis
          Tommy Azzino

:Modifier: Yuning (Brian) Zhang

:Copyright: 2022
"""


import os
import sys
import time
import math
import mmwsdr
import socket
import requests
import subprocess
import numpy as np

path = os.path.abspath('../../../lib/ederenv/Eder_A/')
if path not in sys.path:
    sys.path.append(path)
import eder


# class IBM28GHz(object):
class Sivers60GHz(object):
    """
    Sivers60GHz class

    or 

    IBM28GHz class
    """


    # def __init__(self, config, node='srv1-in2', freq=28e9, isdebug=False, islocal=False, 
    #             iscalibrated=False):

    # =====================
    # =====================
    def __init__(self, config, node='srv1-in2', freq=60.48e9, isdebug=False, islocal=False, iscalibrated=False):
        self.ip = config[node]['ip']
        self.iscalibrated = iscalibrated
        self.isdebug = isdebug
        self.islocal = islocal
        self.sock = None
        self.fpga = None
        self.array = None
        self.mode = None


        # ---------- Start a session to speed-up the HTTP requests ----------
        self.session = requests.Session()
        # self.eder_url = 'http://{}.sb1.cosmos-lab.org:8000/'.format(node) ???
        self.eder_url = 'http://{}.sb1.cosmos-lab.org:8000/'.format(node)


        # ---------- Create the Array object ----------
        if self.islocal:
            self.array = mmwsdr.array.EderArray(init=True, unit_name=config[node]['unit_name'],
                                                board_type=config[node]['board_type'],
                                                eder_version=config[node]['eder_version'])
        """
        The following lines make everything *very* slow. For the moment, we will start the remote server manually.
        
        else:
            self.proc = subprocess.Popen(
                ["ssh", "-t", "root@{}".format(node),
                "python /root/mmwsdr/host/mmwsdr/array/ederarray.py -u {}".format(config[node]['unit_name'])],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(10)
        """

        # ---------- Configure the carrier frequency ----------
        self.freq = freq


        # ---------- Configure the FPGA object ----------
        self.fpga = mmwsdr.fpga.ZCU111(ip=self.ip, isdebug=isdebug)
        self.__connect()
        self.fpga.configure(os.path.join('../../config/', config['fpga']['config']))


        # ---------- Load the calibration parameters ----------
        self.cal_iq_rx_a = float(config[node]['cal_iq_rx_a'])
        self.cal_iq_rx_v = float(config[node]['cal_iq_rx_v'])
        self.cal_iq_tx_a = float(config[node]['cal_iq_tx_a'])
        self.cal_iq_tx_v = float(config[node]['cal_iq_tx_v'])
    # =====================
    # =====================


    def __del__(self):
        self.__disconnect()
        del self.fpga

        if self.islocal:
            del self.array


    def __connect(self):
        self.sock = socket.create_connection((self.ip, 8083))
        self.sock.settimeout(5)


    def __disconnect(self):
        if self.sock != None:
            self.sock.sendall(b'disconnect')
            time.sleep(0.1)
            self.sock.close()


    def apply_iq_cal(self, td, a, v):
        """

        :param td:
        :type td:
        :param a:
        :type a:
        :param v:
        :type v:
        :return:
        :rtype:
        """

        # Apply RX IQ cal factors
        re = (1 / a) * td.real
        im = ((-1) * re * math.tan(v)) + (td.imag / math.cos(v))
        return re + 1j * im


    def send(self, txtd):
        """

        :param txtd:
        :type txtd:
        :return:
        :rtype:
        """
        if self.mode is not 'TX':   # [B] self.mode depends on either the "recv" been called or "send" been called. 
            self.mode = 'TX'

        if self.iscalibrated:
            txtd = self.apply_iq_cal(td=txtd, a=self.cal_iq_tx_a, v=self.cal_iq_tx_v)
        # [B] The transmitted signal is a row vector: 
        # [real_1, real_2, imag_1, imag_2, real_3, real_4, imag_3, imag_4, real_5...]
        self.fpga.send(txtd)


    def recv(self, nread, nskip, nframe):
        """

        :param nread: is also N_fft
        :type nread:
        :param nskip:
        :type nskip:
        :param nframe:
        :type nframe:
        :return: rxtd
        :rtype:
        """

        # Calculate the total number of samples to read:
        # (Number of frames) * (samples per frame) * (# of channel) * (I/Q)
        nsamp = nframe * nread * self.fpga.nch * 2  # [B] by default on 2/15/2022, N_ch = 1.

        if self.mode is not 'RX':   # [B] self.mode depends on either the "recv" been called or "send" been called. 
            self.mode = 'RX'
        self.sock.sendall(b'+ %d %d %d\r\n' % (nread / self.fpga.nparallel, nskip / self.fpga.nparallel, nsamp * 2))

        # [B] The samples will be in a matrix with Nparallel columns. For example, when nparallel = 2:
        # [sample_1,sample_2; sample_3,sample_4; sample_5,sample_6; ...]
        rxtd = self.fpga.recv(nsamp)

        # remove mean
        rxtd -= np.mean(rxtd)

        # [B] Reshape the received signal to the same shape with transmitted signal. 
        rxtd = rxtd.reshape(nframe, nread)
        
        # [B] Apply calibration
        if self.iscalibrated:
            rxtd = self.apply_iq_cal(td=rxtd, a=self.cal_iq_rx_a, v=self.cal_iq_rx_v)
        return rxtd


    def beamsweep(self, start=0, stop=64, step=1):
        """
        Set the receive (RX) and transmit (TX) beamforming (BF) vectors.

        :param index: Index of the RX BF vector (row of the RX BF AWV Table)
        :type index: int
        """
        if self.islocal:
            for index in range(start, stop, step):
                self.array.tx.bf.awv.set(index)
        else:
            params = {'start': start, 'stop': stop, 'step': step}
            try:
                r = self.session.get(url=self.eder_url + 'beamsweep', params=params, verify=False)
            except requests.exceptions.HTTPError as err:
                raise SystemExit(err)


    @property
    def freq(self):
        """
        Get the carrier frequency of the SDR

        :return: The carrier frequency in Hz
        :rtype: float
        """
        return self.__freq


    @freq.setter
    def freq(self, fc):
        """
        Set the SDR carrier frequency

        :param freq: Carrier frequency in Hz
        :type freq: float
        """
        self.__freq = fc

        if self.islocal:
            self.array.freq = fc
        else:
            params = {'freq': fc}
            try:
                r = self.session.get(url=self.eder_url + 'setfreq', params=params, verify=False)
                r.raise_for_status()
            except requests.exceptions.HTTPError as err:
                raise SystemExit(err)


    @property
    def mode(self):
        """
        Get the Sivers' array mode

        :return: 'RX' in receive mode or TX' in transmit mode
        :rtype: str
        """
        return self.__mode


    @mode.setter
    def mode(self, array_mode):
        """
        Set the Sivers' array mode

        :param array_mode: 'RX' for receive mode or TX' for transmit mode
        :type array_mode: str
        """
        self.__mode = array_mode

        if (array_mode == 'RX') | (array_mode == 'TX'):
            if self.islocal:
                self.array.mode = array_mode
            else:
                params = {'mode': array_mode}
                try:
                    r = self.session.get(url=self.eder_url + 'setup', params=params, verify=False)
                    r.raise_for_status()
                except requests.exceptions.HTTPError as err:
                    raise SystemExit(err)


    @property
    def beam_index(self):
        """
        Get the SDR beamforming (BF) vector

        :return: Index of the RX or TX BF vector (row of the RX BF AWV Table)
        :rtype: int
        """
        return self.array.beam_index


    @beam_index.setter
    def beam_index(self, index):
        """
        Set the receive (RX) and transmit (TX) beamforming (BF) vectors.

        :param index: Index of the RX BF vector (row of the RX BF AWV Table)
        :type index: int
        """
        if self.islocal:
            self.array.beam_index = index
        else:
            params = {'index': index}
            try:
                r = self.session.get(url=self.eder_url + 'setbeam', params=params, verify=False)
            except requests.exceptions.HTTPError as err:
                raise SystemExit(err)
