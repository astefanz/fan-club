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
classdef FCBroadcast < handle
    % Represents one state broadcast sent by the FC MkIV External Control.
    properties
        valid
        index
        listener_port
        listener_ip
        timestamp
        rows
        columns
        layers
        array
    end
    methods
        function obj = FCBroadcast()
            % Create an "empty" FCBroadcast instance and set it as invalid.
            % To make it valid, use its "fill" method.
            obj.valid = false;
            obj.index = 0;
            obj.listener_port = 0;
            obj.listener_ip = '';
            obj.timestamp = 0;
            obj.rows = 0;
            obj.columns = 0;
            obj.layers = 0;
            obj.array = cell(0);
        end
        
        function fill(obj, index, listener_port, listener_ip, ...
                timestamp, rows, columns, layers, array)
            % Make the FCBroadcast valid by giving a value to all of its
            % attributes.
            obj.index = index;
            obj.listener_port = listener_port;
            obj.listener_ip = listener_ip;
            obj.timestamp = timestamp;
            obj.rows = rows;
            obj.columns = columns;
            obj.layers = layers;
            obj.array = array;
            obj.valid = true;
        end
        
        function valid = isValid(obj)
            % Get whether this FCBroadcast is valid.
            valid = obj.valid;
        end
    end
end