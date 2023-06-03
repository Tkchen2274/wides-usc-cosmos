clc;clear;
close all

% directory = 'D:\Storage\OneDrive - University of Southern California\Documents\USC\WiDes\Projects\1st Year\COSMOS\SB1 Files\host\demos\basic\Result';
directory = 'C:\Storage\OneDrive - University of Southern California\Documents\USC\WiDes\Projects\1st Year\COSMOS\SB1 Files\host\demos\basic\Result\';

group_ID = 2;
subgroup_ID = 2;
measurement_ID = 1;
directory = [directory, 'Group_', num2str(group_ID)];
% ====== Measurement Profile ======









% =================================

evaluate_folder = [directory, '\evaluate_', num2str(group_ID), '_', num2str(subgroup_ID), '_x'];
if ~exist(evaluate_folder, 'dir')
    mkdir(evaluate_folder)
end


N_frame = 1;


% filename = [num2str(test_group), '_', file_order, '_frame_', num2str(N_frame), '_subCrIdx_250.csv'];
filename = [num2str(group_ID), '_', num2str(subgroup_ID), '_', num2str(measurement_ID), '_frame_', num2str(N_frame), '.csv'];



fileID = fopen([directory, '\', filename]);
A = textscan(fileID, '%s');
fclose(fileID);

aa = A{1,1};
data_char = char(aa);

clear A  aa  fileID  filename  directory

% delete the useless "(" at the beginning
data_char(:, 1) = [];

% add the "+" sign at the beginning for positive real parts
N_fft = size(data_char, 1);
for i = 1:N_fft
    if data_char(i, 1) ~= "-"
        temp = data_char(i, :);
        temp(end) = [];
        temp = ['+', temp];
        data_char(i, :) = temp;
    end
end
clear temp  i

% delete the last 1 or 2 useless char(s), i.e., remove either ") " or ",)"
if N_frame > 1
    data_char(:, end-1:end) = [];
else
    data_char(:, end) = [];
end

% transfer char string to double number
td = zeros(N_fft, 1);
for i = 1:N_fft
    td(i) = str2double(data_char(i,:));
end
td = reshape(td, N_frame, []).';
clear data_char



%% Evaluation 1, recover the COSMOS evaluation process
fd = zeros(size(td, 1), size(td, 2));
for i = 1:N_frame
    fd(:, i) = fft(td(:, i));
end
shifted_fd = circshift(fd,N_fft/2);

% rxfd = circshift(rxfd, 512);

% Plot
legendInfo = cell(N_frame, 1);

figure
hold on
for i = 1:N_frame
    plot(-N_fft/2:N_fft/2-1, 20*log10(abs(shifted_fd(:, i))));
    legendInfo{i} = ['frame ' num2str(i)]; 
end
% plot(-512:1:511, 20*log10(abs(RxSignalFreqDomain(:, 1))));
y_min = min(mean(20*log10(abs(fd)))) - 20;
y_max = max(max(20*log10(abs(fd)))) + 20;
ylim([y_min, y_max])
title(['Received Signal of Measurement ', num2str(group_ID), '\_', num2str(subgroup_ID), '\_', num2str(measurement_ID), ', COSMOS version'])
xlabel('Subcarrier Index')
ylabel('Magnitude [dB]')
grid minor
legend(legendInfo)

clear i  y_min  y_max  ans  legendInfo


%% Evaluation 2
fs = 3932.16e6/4;
df = fs/N_fft;
f = 0:df:(fs-df);
figure;
hold on
for i = 1:N_frame
    plot(20*log10(abs(shifted_fd(:, i))))
end
y_min = min(mean(20*log10(abs(fd)))) - 20;
y_max = max(max(20*log10(abs(fd)))) + 20;
ylim([y_min, y_max])
title(['Received Signal of Measurement ', num2str(group_ID), '\_', num2str(subgroup_ID), '\_', num2str(measurement_ID), ', COSMOS version'])
xlabel('Sample Index')
ylabel('Magnitude [dB]')
grid minor


crop_range = N_fft/2 - 










