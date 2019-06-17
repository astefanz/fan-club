%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%------------------------------------------------------------------------------%
% CALIFORNIA INSTITUTE OF TECHNOLOGY % GRADUATE AEROSPACE LABORATORY  %        %
% CENTER FOR AUTONOMOUS SYSTEMS AND TECHNOLOGIES                      %        %
%------------------------------------------------------------------------------%
%       ____      __      __  __      _____      __      __    __    ____      %
%      / __/|   _/ /|    / / / /|  _- __ __\    / /|    / /|  / /|  / _  \     %
%     / /_ |/  / /  /|  /  // /|/ / /|__| _|   / /|    / /|  / /|/ /   --||    %
%    / __/|/ _/    /|/ /   / /|/ / /|    __   / /|    / /|  / /|/ / _  \|/     %
%   / /|_|/ /  /  /|/ / // //|/ / /|__- / /  / /___  / -|_ - /|/ /     /|      %
%  /_/|/   /_/ /_/|/ /_/ /_/|/ |\ ___--|_|  /_____/| |-___-_|/  /____-/|/      %
%  |_|/    |_|/|_|/  |_|/|_|/   \|___|-    |_____|/   |___|     |____|/        %
%                    _ _    _    ___   _  _      __  __   __                   %
%                   | | |  | |  | T_| | || |    |  ||_ | | _|                  %
%                   | _ |  |T|  |  |  |  _|      ||   \\_//                    %
%                   || || |_ _| |_|_| |_| _|    |__|  |___|                    %
%                                                                              %
%------------------------------------------------------------------------------%
% Alejandro A. Stefan Zavala % <astefanz@berkeley.edu>   %                     %
% Chris J. Dougherty         % <cdougher@caltech.edu>    %                     %
% Marcel Veismann            % <mveisman@caltech.edu>    %                     %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% FCMkIV External Control MATLAB Listener client API demo script  %%%%%%%%%
% -------------------------------------------------------------------------
% This example script uses the FC MkIV external control broadcast to 
% find the external control listener address and uses it to send sample
% commands, displaying the data received from each exchange.
% -------------------------------------------------------------------------
% NOTE: The MkIV is expected to be running and with both its external 
% control listener and broadcast activated.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
delete(instrfindall);
MAX_VALUE = 16000;
MAX_FANS = 21;
FAWT_FIGURE = 1;
FAWT_NAME = "Basement FAWT";

GRAPH_3D = true;

disp("");
disp("** FCMkIV External Control Demo started **");

% Set up broadcast client .................................................
B = FCBroadcastClient();
B.open();

% Set up controller .......................................................
X = FCExternalController();
X.open();

% Build array representation ..............................................
G = '';

% Main loop ...............................................................
disp("Starting main loop");
i = 0;
max_i = 100.0;
t_0 = tic;
while true
    % Get broadcast data:
    b = B.getBroadcast();
    if ~b.isValid()
        % If the broadcast timed out, exit loop:
        disp("Timed out. Terminating");
        break
    elseif ~isequal(b.listener_port, X.target_port) ...
            || ~isequal(b.listener_ip, X.target_ip)
        % If the listener's address is different from what is currently
        % stored, update the stored address:
        fprintf("Updating target to %s and %d", target_ip, target_port);
        X.close();
        X.setTargetIP(b.listener_ip);
        X.setTargetPort(b.target_port);
        X.open();
    elseif isequal(G, '') && GRAPH_3D
        % If this is the first 3D graph, initialize the figure:
        disp("Building FAWT model");
        G = FAWT3DGraph(FAWT_NAME, b.rows, b.columns, MAX_VALUE, 1);
        G.build(FAWT_FIGURE);
    else
        % Standard loop cycle:
        
        % Display broadcast:
        if GRAPH_3D
            G.draw(b.timestamp, b.array);
        else
            disp(b.index);
        end
        % Control the tunnel:
        % Ramp up the duty cycle by about 3% every second:
        dt = 3*(tic - t_0)/1000000;
        dm = mod(ceil(dt), max_i);
        dc = double(dm)/max_i;
        X.sendDCVector(b.rows, b.columns, b.layers, ...
            dc*ones(1, b.rows*b.columns*b.layers));
    end
end
disp("** FCMkIV External Control Demo ended **");