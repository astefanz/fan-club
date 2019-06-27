% Build grid
maxRPM = 12000;
maxFans = 21;
cell_length = 1;
C = 11;
R = 11;


colormap('jet');
G = Grid(C, R, maxRPM, maxFans, cell_length);
    
fig_n = 1;
fig = figure(fig_n);
G = G.build(fig_n);

% Build networking
delete(instrfindall);
loopback = '127.0.0.1';
IP = loopback;
b_port = 60069;
broadcast = udp(IP, 'LocalPort', b_port);
broadcast.InputBufferSize = 32768;
broadcast.DatagramTerminateMode = 'on';
broadcast.Timeout = 0;
fopen(broadcast);

disp(broadcast.Status);

t = 0;
rpms = [];
rpms_char = '';
warning('off', 'instrument:fscanf:unsuccessfulRead');
while true
    
    B_ = fscanf(broadcast);
    B = B_;
    while ~isempty(B_)
        B = B_;
        B_ = fscanf(broadcast);
    end
    
    if ~isempty(B)

        splitted = split(B, "|");
        rpms_char_new = splitted(end);
        if ~isequal(rpms_char_new, rpms_char)
            rpms_char = rpms_char_new;
            rpms_splitted = split(rpms_char, ",");

            new_rpms = zeros(length(rpms_splitted));
            for i = 1:length(rpms_splitted)
                new_rpms(i) = str2double(rpms_splitted(i));
            end

            fprintf('[%05d] Parsed %d rpms\n', t, length(rpms));
            for g = 0:(length(rpms) - 1)
                if mod(g, C) == 0
                   fprintf('\n'); 
                end
                fprintf('%07d ', rpms(g + 1));
             end
%             fprintf('\n\n');
% 
%             if ~isequal(new_rpms, rpms)
%                 if length(new_rpms) >= R*C
%                     disp('applied');
%                     rpms = new_rpms;
%                     G.draw(t, rpms);
%                 else
%                     disp('ignored -- not large enough');
%                     disp(length(new_rpms));
%                     disp(rpms_char);
%                 end
%             else
%                 disp('ignored -- redundant');
%             end
            t = t + 1;
        end
    
    end
end