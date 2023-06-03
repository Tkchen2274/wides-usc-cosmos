clc;clear;
close all



% % directory = 'D:\Storage\OneDrive - University of Southern California\Documents\USC\WiDes\Projects\1st Year\COSMOS\SB1 Files\host\demos\basic\Result';
% directory = 'C:\Storage\OneDrive - University of Southern California\Documents\USC\WiDes\Projects\1st Year\COSMOS\SB1 Files\host\demos\basic\Result\';
% 
% group_ID = 2;
% subgroup_ID = 2;
% measurement_ID = 1;
% directory = [directory, 'Group_', num2str(group_ID)];
% % ====== Measurement Profile ======
% 
% 
% 
% 
% 
% 
% 
% 
% 
% % =================================




%% Tx signal SINE


signal_rep_len = 500;



%% Read data
group_id = 8;
max_test = 32;
figure
for i = 1:max_test
    data_fid = fopen(['test_', num2str(group_id), '_', num2str(i), '.dat'],'r');
%     data_fid = fopen('test_000_000.dat','r');
    rx = fread(data_fid,'*double');
    

    metadata_fid = fopen(['test_', num2str(group_id), '_', num2str(i), '_metadata.dat'],'r');
%     tx_metadata_fid = fopen('test_000_000_tx_metadata.dat','r');
%     rx_metadata_fid = fopen('test_000_000_rx_metadata.dat','r');
%     tx_tick = fread(tx_metadata_fid,'*int64');
%     rx_tick = fread(rx_metadata_fid,'*int64');
    fclose all;

%     if group_id == 1
%         tx_tick = 2000000000;
%     elseif group_id == 2
%         tx_tick = 2000000000;
%     elseif group_id == 4
%         if i < 5
%             tx_tick = 220408928;
%         elseif i < 9
%             tx_tick = 220257140;
%         end
%     elseif group_id == 5
%         if i < 5
%             tx_tick = 220384207;
%         elseif i < 9
%             tx_tick = 220353437;
%         end
%     elseif group_id == 6
%         tx_tick = 2000000000;
%     end
% %     delayed_tick = mod(rx_tick - tx_tick, 500);
% delayed_tick = 0;

%     disp([num2str(i)])
%     disp(['rx tick = ', num2str(rx_tick)])
%     disp(['tx tick = ', num2str(tx_tick)])
% %     disp(['tx tick = ', num2str(tx_tick)])
% %     disp(['delayed tick = ', num2str(delayed_tick)])
%     disp(' ')
    



    
    center_freq = 100e6;
    sampling_rate = 200e6;

    t_step = 1/sampling_rate;
    t = (0: t_step : (signal_rep_len-1)*t_step)';
    
%     rx = circshift(rx, mod(tx_tick, 500), 1);
    rx = reshape(rx, 2, [])';
    rx = rx(:,1) + rx(:,2)*1i;
    

    % data(1:17) = [];
    % data(end-13:end) = [];
    
    
%     figure;
%     subplot(2,2,3)
%     if max(t) > 1e-6 && max(t) < 1e-3
%         plot(t(1:length(rx))*1e6, real(rx))
%         xlabel('Time [us]')
%         xlim([t(3901)*1e6, t(4001)*1e6])
%     elseif max(t) > 1e-3 && max(t) < 1
%         plot(t(1:length(rx))*1e3, real(rx))
%         xlabel('Time [ms]')
%         xlim([t(3901)*1e3, t(4001)*1e3])
%     end
%     ylabel('Amp [A]')
%     title('Received data, Real part')
%     ylim([-0.02, 0.02])
%     
% %     subplot(2,2,4)
%     if max(t) > 1e-6 && max(t) < 1e-3
%         fg = plot(t(1:length(rx))*1e6, real(rx));
%         xlabel('Time [us]')
% %         dt = datatip(fg, t(min(find(real(rx) == max(real(rx)))))*1e6, max(real(rx)));
%     elseif max(t) > 1e-3 && max(t) < 1
%         fg = plot(t(1:length(rx))*1e3, real(rx));
%         xlabel('Time [ms]')
% %         dt = datatip(fg, t(min(find(real(rx) == max(real(rx)))))*1e3, max(real(rx)));
%     end
%     ylabel('Amp [A]')
%     title(['Sampling rate = ', num2str(sampling_rate/1e6), 'MS/s'])
%     ylim([-0.02, 0.02])
%     grid minor
    



    rx = reshape(rx, signal_rep_len, []);
    f = linspace(-sampling_rate/2, sampling_rate/2, signal_rep_len+1);
    f(end) = [];
%     rx_fft = 20*log10(abs(fft(real(rx))));
%     rx_fft = 20*log10(abs(fft(rx)));

    
%     first_peak_idx(i) = find(rx_fft(1:5000) == max(rx_fft(1:5000)));
%     first_peak(i) = rx_fft(first_peak_idx(i));
% 
% 
%     second_peak_idx(i) = find(rx_fft(1:length(rx)/2) == max(rx_fft(1:length(rx)/2)));
%     second_peak(i) = rx_fft(second_peak_idx(i));


%     figure;
%     % hold on
%     % plot(f/1e6, 20*log10(abs(fft(rx))), "LineWidth",1.5)
%     fg = plot(linspace(-sampling_rate/2/1e6, sampling_rate/2/1e6, length(rx_fft)), ifftshift(rx_fft));
%     % plot(f/1e6, 20*log10(abs(fft(imag(rx)))))
%     xlabel('Frequency [MHz]')
%     ylabel('Pwr [dBm]')
% %     title(['center freq is ', num2str(center_freq/1e6), 'MHz'])
%     % legend('Complex', 'Real', 'Image')
%     grid minor
%     ylim([-80, 70])
% %     dp = datatip(fg, f(first_peak_idx)/1e6, first_peak(i));
% %     dp = datatip(fg, f(second_peak_idx)/1e6, second_peak(i));
    
    
%     figure;
%     hold on
%     if max(t) > 1e-6 && max(t) < 1e-3
%         plot(t*1e6, real(tx))
%         plot(t(1:length(rx))*1e6, real(rx)*50)
%         xlabel('Time [us]')
%         xlim([t(3901)*1e6, t(4001)*1e6])
%     elseif max(t) > 1e-3 && max(t) < 1
%         plot(t*1e3, real(tx))
%         plot(t(1:length(rx))*1e3, real(rx)*50)
%         xlabel('Time [ms]')
%         xlim([t(3901)*1e3, t(4001)*1e3])
%     end
    
    
%     f = linspace(0, tx_sampling_rate, length(tx)+1);
%     f(end) = [];
%     tmp = 20*log10(abs(fft(tx)));
%     tmp1=20*log10(abs(fft(real(tx))));
%     tmp2=20*log10(abs(fft(imag(tx))));
%     tmp(tmp<-100) = 0;
%     tmp1(tmp1<-100) = 0;
%     tmp2(tmp2<-100) = 0;
%     figure;
%     hold on
%     plot(f/1e6, tmp, "LineWidth",1.5)
%     plot(f/1e6, tmp1)
%     plot(f/1e6, tmp2)
%     xlabel('Frequency [MHz]')
%     ylabel('Pwr [dBm]')
%     title('Frequency Reponse of Sampled Original Signal')
%     legend('Complex', 'Real', 'Image')
%     grid minor


% rx_no_underrun = rx;
% delete_idx = [];
% for ii = 1:size(rx,2)
%     for j = 1:200
%         if abs(rx_no_underrun(j,ii)) <0.02
%             delete_idx = [delete_idx; ii];
%             break;
%         end
%         
%     end
% end
% 
% rx_no_underrun(:, delete_idx) = [];



% ========================================
% DO NOT DELETE!!!
% figure;
% plot(linspace(-sampling_rate/2/1e6, sampling_rate/2/1e6, size(rx, 1)),20*log10(abs(ifftshift(fft(mean(rx,2))))))
% title('FFT averaged over Temporal')
% xlabel('Frequency [MHz]')
% ylabel('Power [dBm]')
% grid minor
% 
% 
% figure;
% plot(linspace(-sampling_rate/2/1e6, sampling_rate/2/1e6, size(rx, 1)),20*log10(abs(ifftshift(mean(fft(rx),2)))))
% title('FFT averaged over Spectrum (complex)')
% xlabel('Frequency [MHz]')
% ylabel('Power [dBm]')
% grid minor
% 
% 
% % APDP is averaged PDPs over antennas"
% %
% % figure;
% % res = 1;
% % bw=200e6;
% % plot([0:res:500-res]/ bw* 3e8, 10*log10(mean(abs(1/res .* ifft(H,1/res * 500)).^2,2),'linewidth',1.5)
% % xlabel('distance [m]')
% % ylabel('$|h(\tau)|^2$ [dB]','interpreter','latex')
% % title('APDP')
%
%
% figure;
% plot(f/1e6, 20*log10(mean(abs(ifftshift(fft(rx))),2)))
% xlabel('Frequency [MHz]')
% ylabel('Power [dBm]')
% title('FFT averaged over Spectrum amplitude')
% grid minor
% % 
% figure;
% plot(f/1e6, 20*log10(abs(ifftshift(fft(rx(:, 1))))))
% xlabel('Frequency [MHz]')
% ylabel('Power [dBm]')
% title('FFT no averaging Spectrum amplitude')
% grid minor
% ========================================




bb_f = linspace(-sampling_rate/2/1e6, sampling_rate/2/1e6, size(rx, 1)+1);
bb_f(end) = [];

rx_amp = abs(rx);
rx_phase = angle(rx);
% ave_rx_amp = mean(rx_amp, 2);
% ave_rx_phase = mean(unwrap(rx_phase), 2);
% ave_rx = ave_rx_amp .* exp(1j * ave_rx_phase);
% ave_rx = mean(rx_no_underrun, 2);

% figure;
% plot(bb_f,20*log10(mean(abs(ifftshift(fft(rx))),2)))
% hold on
% % plot(bb_f,20*log10(mean(abs(ifftshift(fft(rx))),2)))
% plot(bb_f,20*log10(abs(ifftshift(fft(mean(rx,2))))), 'rs-')
% plot(bb_f,20*log10(abs(ifftshift(mean(fft(rx),2)))), 'b*-')
% % title('FFT averaged over Spectrum, losing phase')
% % legend('deleted underrun samples', 'with underrun samples', "Location","best")
% title('FFT')
% legend('average amplitude at FFT', 'average first, then fft', 'fft, then average', "Location","best")
% xlabel('Frequency [MHz]')
% ylabel('Power [dBm]')
% grid minor




subplot(ceil(max_test/4), 8, i)
% figure
% plot(t*1e6, abs(circshift(rx, delayed_tick, 1)))
plot(t*1e6, abs(rx(:, 1:3)))
xlabel('Time [us]')
ylabel('Power [dBm]')
title(['measurement ', num2str(i)])


end



% 
% D1 = 20*log10(0.7.*10.^((0:-1:-10)/10))';
% D2 = 20*log10(0.7.*10.^([0, -1, -2, -3, -4, -5]/10))';
% a = [2.8868e6, 13.8271; 2.8868e6, 17.8317; 2.8878e6, 1.4843; 2.8874e6, -5.59965; NaN,NaN; NaN,NaN];
% b = [3.119e6, 12.3454; 3.119e6, 5.74386; 3.1182e6, -4.00796; 3.1184e6, -9.56937; NaN,NaN; NaN,NaN];
% c = [NaN,NaN;NaN,NaN;NaN,NaN; 3.3492e6, -7.16315; 3.3508e6, -5.58888; 3.3508e6, -7.32124];
% 
% 
% figure
% hold on
% plot(D1, first_peak);
% plot(D1, second_peak);
% xlabel('Tx real(signal) power [dBm]')
% ylabel('Rx real(signal) power [dBm]')
% legend('peak @ 0.8848 MHz', 'peak @ 1.117 MHz', 'Location','best')
% grid minor
% 
% 
% 
% figure
% hold on
% plot(D2, a(:, 2));
% plot(D2, b(:, 2));
% plot(D2, c(:, 2));
% xlabel('Tx real(signal) power [dBm]')
% ylabel('Rx real(signal) power [dBm]')
% legend('peak @ 2.8868 MHz', 'peak @ 3.119 MHz', 'peak @ 3.3508 MHz', 'Location','best')
% grid minor
% % ylim([])
% 







