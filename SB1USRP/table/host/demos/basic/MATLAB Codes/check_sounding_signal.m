% clc;clear;

% read
sounding_signal_id = 2;
wides_real = csvread(['wides_ofdm_real_', num2str(sounding_signal_id), '.csv']);
wides_imag = csvread(['wides_ofdm_imag_', num2str(sounding_signal_id), '.csv']);
demo_imag = csvread(['demo_imag_', num2str(sounding_signal_id), '.csv']);
demo_real = csvread(['demo_real_', num2str(sounding_signal_id), '.csv']);

% combine
demo_signal = demo_real + 1i* demo_imag;
% demo_signal = demo_real;
wides_ofdm = wides_real + 1i* wides_imag;
wides_ofdm2 = wides_real;
wides_ofdm3 = 1i* wides_imag;
% wides_ofdm = wides_imag;

% clear
clear wides_imag wides_real demo_imag demo_real

% Plot
figure;plot(1:1024, 20*log10(abs(fft(wides_ofdm))));title('wides')
% figure;plot(1:1024, 20*log10(abs(fft(wides_ofdm2))));title('wides2')
% figure;plot(1:1024, 20*log10(abs(fft(wides_ofdm3))));title('wides3')
figure;plot(1:1024, 20*log10(abs(fft(demo_signal))));title('demo')
