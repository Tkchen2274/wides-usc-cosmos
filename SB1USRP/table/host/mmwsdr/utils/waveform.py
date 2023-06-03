import numpy as np

"""
:Description: waveform is just a function;

:Organization: Wireless and Device System Lab, University of Southern California

:Authors: Yuning (Brian) Zhang

:Copyright: 2022
"""


def wideband(sc_min=-100, sc_max=100, nfft=1024, mod='qam', seed=100):
    """
    :param sc_min: minimum subcarrier index
    :type sc_min: int
    :param sc_max: maximum subcarrier index
    :type sc_max: int
    :param nfft: num of FFT points
    :type nfft: int
    :param mod: frequency domain symbol modulation
    :type mod: str
    :param seed:
    :type seed: int
    :return:
    :rtype:
    """
    np.random.seed(seed)
    qam = (1 + 1j, 1 - 1j, -1 + 1j, -1 - 1j)  # QAM symbols

    # Create the wideband sequence in frequency-domain
    fd = np.zeros((nfft,), dtype='complex')
    if mod == 'qam':
        # fd[((nfft >> 1) + sc_min):((nfft >> 1) + sc_max)] = np.random.choice(qam, len(range(sc_min, sc_max)))   # the range is [sc_min, sc_max)
        fd[((nfft >> 1) + sc_min):((nfft >> 1) + sc_max+1)] = np.random.choice(qam, len(range(sc_min, sc_max+1)))   # the range is [sc_min, sc_max]
    else:
        fd[((nfft >> 1) + sc_min):((nfft >> 1) + sc_max)] = 1
    fd = np.fft.fftshift(fd, axes=0)

    # Convert the waveform to time-domain
    td = np.fft.ifft(fd, axis=0)

    # Normalize the signal
    # td /= np.max([np.abs(td.real), np.abs(td.imag)])    # td is a row vector
    return td


def onetone(subCarrierIndex=400, nfft=1024):
    """

    :param subCarrierIndex: subcarrier index
    :type subCarrierIndex: int
    :param nfft: num of FFT points
    :type nfft: int
    :return: waveform
    :rtype: np.array
    """
    # Create a tone in frequency-domain
    fd = np.zeros((nfft,), dtype='complex') # returns a N_fft-by-1 vector;
    fd[(nfft >> 1) + subCarrierIndex] = 1   # "N_fft >> 1" means "N_fft/2";
    fd = np.fft.fftshift(fd, axes=0)   # shift half by all directions (only 1 dimension here)

    # Convert the waveform to time-domain
    td = np.fft.ifft(fd, axis=0)

    # Normalize the signal
    td /= np.max([np.abs(td.real), np.abs(td.imag)])  # td is a row vector, this is the standard normalization method
    return td
