import numpy as np
import os
np.set_printoptions(threshold=np.inf)
np.random.seed(100)
nfft = 1024
sc_min = -500
sc_max = 500
qam = (1 + 1j, 1 - 1j, -1 + 1j, -1 - 1j)
fd = np.zeros((nfft,), dtype='complex')

fd[((nfft >> 1) + sc_min):((nfft >> 1) + sc_max+1)] = np.random.choice(qam, len(range(sc_min, sc_max+1)))

# print(fd[1023])
fd = np.fft.fftshift(fd, axes=0)
# print(fd[1023])
td = np.fft.ifft(fd, axis=0)
# print(td[1023])

txtd = td
txtd /= np.max([np.abs(txtd.real), np.abs(txtd.imag)]) 
# print(txtd[1023])
aaa = np.fft.fft(txtd)
# print(aaa[1023])
txfd = np.fft.fft(txtd)
#txtd *= 4000
sounding_file_name = "SoundingSignal" + "_minSc_" + str(sc_min) + "_maxSc_" + str(sc_max) + ".csv"
sounding_file_path = os.path.abspath('./host/demos/basic/SoundingSignal/' + sounding_file_name)
np.savetxt(sounding_file_path, txtd, delimiter=',')
# print(txfd[1023])
# print(txtd[1023])