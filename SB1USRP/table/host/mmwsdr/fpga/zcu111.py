"""
:Description: This class establishes a communication link over TCP between a host and a Xilinx Zynq Ultrascale+
RFSoC FPGA board. The host configures the RF data converter given a parameter file, receives samples from the ADCs,
and sends samples to the DACs in non-realtime mode. The application running in the processing system (PS) of the FPGA
is based on a modified version of Xilinx `rftool`.

:Organization: New York University, modified by Wireless and Device System Lab, University of Southern California

:Authors: Panagiotis Skrimponis

:Modifier: Yuning (Brian) Zhang  [B] 

:Copyright: 2021
"""

import os
import socket
import time
import struct
import numpy as np


class ZCU111(object):
    """
    Base class for the ZCU111 RFSoC
    """
    __nco = 0e9  # frequency of the NCO in Hz
    __nch = 1  # num of channels
    __ndac = 2  # num of D/A converters
    __nadc = 2  # num of A/D converters
    __nparallel = 2  # num of parallel samples per clock cycle, due to the FPGA property.  [B] This one is because of the 
                # Xilinx Zynq Ultrascale+ RFSoC FPGA board
    __pll = 3932.16e6  # basic Sample Rate of the converters in Hz, = 3.932GHz.     
    __drate = 4  # decimation rate  (ADC/DWC): actual ADC data rate = _pll / _drate = 983.04MHz
    __irate = 4  # interpolation rate   (DAC/UPC): _pll = actual DAC data rate * _irate = 983.04MHz
    __max_tx_samp = 32768  # store up to 16KB of tx data
    __max_rx_samp = 1024 ** 3  # store up to 1GB of rx data

    @property
    def fs(self):
        """
        A/D and D/A Sample rate

        :return fs: sample rate calculated based on the PLL frequency and the interpollation/decimation rate
        :rtype fs: float
        """
        return self.__pll / self.__irate

    @property
    def nch(self):
        """
        Number of Tx/Rx channels

        :return nch: num of trx channels
        :rtype nch: int
        """
        return self.__nch

    @property
    def nparallel(self):
        """
        Number of samples the FPGA process in parallel every clock cycle

        :return nparallel: num of parallel samples per clock cycle
        :rtype nparallel: int
        """
        return self.__nparallel


    def __init__(self, ip='10.113.1.3', isdebug=False):
        """
        Class constructor

        :param ip: IP address of the FPGA board
        :type ip: str
        :param isdebug: print debug messages
        :type isdebug: bool
        """

        # Set the parameters from constructor arguments
        self.ip = ip
        self.isdebug = isdebug

        # Establish the TCP connections
        self.__connect()
        self.__send_cmd('TermMode 1')

    def __del__(self):
        """
        Class destructor
        """
        self.__disconnect()

    def __connect(self):
        """
        This function establishes a communication link between a host and a Xilinx RFSoC device
        """
        self.sock_data = socket.create_connection((self.ip, 8082))
        self.sock_data.settimeout(100)

        self.sock_ctrl = socket.create_connection((self.ip, 8081))
        self.sock_ctrl.settimeout(100)

    def __disconnect(self):
        """
        This function disbands the communication link between a host and a Xilinx RFSoC device
        """
        if self.sock_data != None:
            self.sock_data.shutdown(socket.SHUT_RDWR)
            time.sleep(0.2)
            self.sock_data.close()

        if self.sock_ctrl != None:
            self.sock_ctrl.shutdown(socket.SHUT_RDWR)
            time.sleep(0.2)
            self.sock_ctrl.close()

    def __send_cmd(self, cmd):
        """
        This function sends a command to the `rftool` running on
        the of the processing system (PS).

        :param cmd:
        :type cmd:
        :return:
        :rtype:
        """

        # Send a command to the FPGA
        self.sock_ctrl.sendall((cmd + '\r\n').encode())

        # Wait for the FPGA to process the command
        time.sleep(0.1)

        # Read the response and print if `isdebug` is true
        rsp = self.sock_ctrl.recv(32768)
        if self.isdebug:
            print(rsp)

    def configure(self, file):
        """
        Parse the output file from the RFDC.

        :param file:
        :type file:
        :return:
        :rtype:
        """

        # Check if the file exists
        if not os.path.isfile(file):
            print('File %s does not exist' % (file))
            return

        with open(file, 'r') as fid:
            lines = fid.readlines()
            for line in lines:
                if line[0] != '%':
                    self.__send_cmd(line)
                else:
                    # if there is a comment pause. This is helpful to let the PLLs stabilize
                    time.sleep(0.1)

        # Make sure that the FPGA is not writing any values to the DACs
        self.send(np.zeros((1024,), dtype='int16'))




    def send(self, txtd):
        """
        This function sends a buffer to the FPGA. For the moment we assume that we receive only one channel. This will be
        extended to multiple channels.

        [B] All data here are in time-domain. 

        :param txtd: time-domain tx signal
        :type txtd:
        :return:
        :rtype:
        """

        # ------ Split the input data in real and imaginary ------
        # Since the FPGA is processing multiple data points per clock cycle, we will split the data based on that. 
        # [B] 2 parallel data for the Xilinx Zynq Ultrascale+ RFSoC FPGA board. The size of x_real and x_imag is 
        # "X -by- nparallel", X usually should be N_fft/nparallel. And 2 bytes per sample. 
        x_real = np.int16(txtd.real).reshape(-1, self.nparallel)    # [B] -1 means unknown dimension
        # MATLAB code: x_real = reshape(int16(real(TimeDomainSignal)), nparallel, [])';
        x_imag = np.int16(txtd.imag).reshape(-1, self.nparallel)


        # ------ Combine the real and imaginary data. Flatten the output buffer ------
        data = np.zeros((x_real.shape[0] * 2, x_real.shape[1]), dtype='int16')
        # [B] change 2 to self.nparallel:
        # data = np.zeros((x_real.shape[0] * self.nparallel, x_real.shape[1]), dtype='int16')
        data[::2, :] = x_real   # [B] Insert x_real to data from the 1st row and then every the other row
        data[1::2, :] = x_imag  # [B] Insert x_imag to data from the 2nd row and then every the other row
                                # [B] data structure: [real_1,real_2; imag_1,imag_2; real_3,real_4; imag_3,imag_4; real_5...]        

        data = data.flatten()   # [B] data structure: [real_1, real_2, imag_1, imag_2, real_3, real_4, imag_3, imag_4, real_5...]


        # ------ Send the data over TCP with the necessary commands in the control and data channel ------
        self.__send_cmd('LocalMemTrigger 1 0 0 0x0000')
        self.sock_data.sendall(b'WriteDataToMemory 0 0 %d 0\r\n' % (2 * data.shape[0])) # [B] data.shape[0] = 2*N_fft
        self.sock_data.sendall(data.tobytes())
        time.sleep(0.1)

        # Read response from the Data TCP Socket
        rsp = self.sock_data.recv(32768)
        if self.isdebug:
            print(rsp)

        self.__send_cmd('LocalMemTrigger 1 2 0 0x0001')





    def recv(self, nsamp):
        """
        :param nsamp: num of samples to read
        :type nsamp: int
        :return rxtd: time-domain rx signal
        :rtype rxtd: np.array
        """
        nbytes = 2 * nsamp  # num of bytes to read  [B] 2 bytes per sample is configured in self.send(), int16. 

        self.sock_data.sendall(b'ReadDataFromMemory 0 0 %d 0\r\n' % (nbytes))
        time.sleep(0.1)


        # ------ Read ADC data from the data TCP socket ------
        tmp = self.sock_data.recv(nbytes)
        while (len(tmp) < nbytes):
            tmp = tmp + self.sock_data.recv(nbytes - len(tmp))
        time.sleep(0.1)


        # ------ Read response from the data TCP socket ------
        rsp = self.sock_data.recv(32768)
        if self.isdebug:
            print(rsp)


        # ------ Process the data ------
        # [B] transfer from bytes to samples
        data = np.array(struct.unpack('<' + (len(tmp) >> 1) * 'h', tmp), dtype='int16')
        
        # [B] The data will be in a matrix with Nparallel columns. For example, when nparallel = 2:
        # [real_1,real_2; imag_1,imag_2; real_3,real_4; imag_3,imag_4; real_5...]
        # Samples will be int16. 
        data = data.reshape(-1, self.nparallel)
        
        # [B] Combine the real part and the image part to be another matrix. 
        rxtd = data[::2, :] + 1j * data[1::2, :]


        # ------ Clear the memory ------
        del tmp, data


        # ------ Return 1D array ------
        return rxtd.reshape(-1)





    
