clc;clear;
close all

signal_rep_len = 500;
center_freq = 100e6;
sampling_rate = 200e6;
BW = 200e6;
f_IF = 300e6;
ifft_factor = 1;


t_step = 1/sampling_rate;
t = (0: t_step : (signal_rep_len-1)*t_step)';

f = linspace(-sampling_rate/2, sampling_rate/2, signal_rep_len+1);
f(end) = [];

group_id =  9;
max_test = 32;
test_N = 8;
for i = 1:max_test
    data_fid = fopen(['test_', num2str(group_id), '_', num2str(i), '.dat'],'r');
    rx = fread(data_fid,'*double');
    fclose all;
    
    rx = reshape(rx, 2, [])';
    rx = rx(:,1) + rx(:,2)*1i;

    rx = reshape(rx, signal_rep_len, []);
    
%     rx_1 = rx;
    eval(['rx_', num2str(i), ' = rx;'])
end
clear rx


% FFT
for i = 1:max_test
    % fft_rx_1 = fft(rx_1);
    eval(['fft_rx_', num2str(i), ' = fft(rx_', num2str(i), ');'])
end


% calibration base data
base = fft_rx_4(:, 1);


% Averaging
for i = 1:max_test
%     % ave_fft_rx_1 = mean(fft_rx_1, 2);
%     eval(['ave_fft_rx_', num2str(i), ' = mean(fft_rx_', num2str(i), ', 2);'])

%     % ave_fft_rx_1 = fft_rx_1(:, 1);
%     eval(['ave_fft_rx_', num2str(i), ' = fft_rx_', num2str(i), '(:, 1);'])

%     % ave_fft_rx_1 = mean(abs(fft_rx_1), 2);
%     eval(['ave_fft_rx_', num2str(i), ' = mean(abs(fft_rx_', num2str(i), '), 2);'])

%     % ave_fft_rx_1 = fft_rx_1;
    eval(['ave_fft_rx_', num2str(i), ' = fft_rx_', num2str(i), ';'])
end




tau_max = signal_rep_len / BW;
tau_step = tau_max / signal_rep_len / ifft_factor;
tau = 0 : tau_step : tau_max;
tau(end) = [];

% figure
% for i = 1:4
% %     test_1 = ave_fft_rx_5;
% %     test_2 = ave_fft_rx_9;
% %     test_3 = ave_fft_rx_13;
%     eval(['test_', num2str(i), ' = ave_fft_rx_', num2str(i+8), ';'])
% 
% %     test_1_cal = test_1 / base;
%     eval(['test_', num2str(i), '_cal = test_', num2str(i), ' ./ base;'])
% 
% %     cir_1 = ifft(test_1_cal);
%     eval(['cir_', num2str(i), ' = ifft(test_', num2str(i), '_cal);'])
% 
%     subplot(2,2,i)
% %     plot(20*log10(abs(cir_1)))
%     eval(['plot(tau*3e8, 20*log10(abs(cir_', num2str(i), ')))'])
%     xlabel('Distance [m]')
%     ylabel('Power [dBm]')
%     title('calibrated 21.3m over 20m')
%     grid minor
% end

figure
idx = 1;
for i = 1:1:max_test
    % test_i = ave_fft_rx_i;
    eval(['test_', num2str(i), ' = ave_fft_rx_', num2str(i), ';'])

    % test_i_cal = test_i ./ base;
    eval(['test_', num2str(i), '_cal = test_', num2str(i), ' ./ base;'])

    % CIR_i = ifft_factor*ifft(test_i_cal, signal_rep_len * ifft_factor);
    eval(['CIR_', num2str(i), ' = ifft_factor*ifft(test_', num2str(i), '_cal, signal_rep_len * ifft_factor);'])

    % ave_CIR_i = mean(abs(CIR_i), 2);
    eval(['ave_CIR_', num2str(i), ' = mean(abs(CIR_', num2str(i), '), 2);'])

    subplot(max_test/test_N,test_N,idx)
    idx = idx + 1;

    % plot(20*log10(abs(ave_CIR_1)))
    eval(['plot(tau*3e8, 20*log10(abs(ave_CIR_', num2str(i), ')))'])

    xlabel('Distance [m]')
    ylabel('Power [dBm]')
    if i < test_N+1
        title('calibrated 20m over 20m channel, pos 1')
    elseif i < test_N*2+1
        title('calibrated 21.3m over 20m channel, pos 2')
    elseif i < test_N*3+1
        title('calibrated 21.3m over 20m channel, pos 3')
    else
        title('calibrated 22.6m over 20m channel, pos 4')
    end
    grid minor
    ylim([-80, 1])
    xlim([0, 800])
end


