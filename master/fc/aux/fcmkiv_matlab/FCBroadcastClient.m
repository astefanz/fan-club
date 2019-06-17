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
% Expected format:
% .........................................................
% INDEX|B|LISTENER_PORT|TIME_STAMP|NROWS|NCOLS|NLAYERS|RPMS
% 1.....2.3.............4..........5.....6.....7.......8...

classdef FCBroadcastClient < handle
    % Abstraction for all the behavior needed to use FC external control
    % broadcasts in MATLAB.
    properties(Constant)
        SYMBOL = "[FC BClient] ";
        MAIN_SEPARATOR = '|';
        LIST_SEPARATOR = ',';
        VALID_LENGTH = 8;
        
        I_INDEX = 1;
        I_B = 2;
        I_LISTENER_PORT = 3;
        I_TIMESTAMP = 4;
        I_ROWS = 5;
        I_COLUMNS = 6;
        I_LAYERS = 7;
        I_RPMS = 8;
        
        DEFAULT_PORT = 60069;
        DEFAULT_TIMEOUT = 10;
        DEFAULT_BUFFER_SIZE = 32768;
        DEFAULT_DELTA = 10;
        DEFAULT_IP = '0.0.0.0';
        DEFAULT_SILENCED = false;
        
        NO_SOCKET = '';
        CODE = 'B';
    end
    properties
        port;
        socket;
        index_in;
        buffer_size;
        timeout;
        delta;
        ip;
        silenced;
        
    end
    methods(Access = public)
        function obj = FCBroadcastClient()
            % Build a new (closed) FC Broadcast Client and initialize it to
            % its default values.
            warning('off', 'instrument:fscanf:unsuccessfulRead');
            obj.port = obj.DEFAULT_PORT;
            obj.timeout = obj.DEFAULT_TIMEOUT;
            obj.buffer_size = obj.DEFAULT_BUFFER_SIZE;
            obj.delta = obj.DEFAULT_DELTA;
            obj.index_in = 0;
            obj.socket = obj.NO_SOCKET;
            obj.ip = obj.DEFAULT_IP;
            obj.silenced = obj.DEFAULT_SILENCED;
            
        end
        
        % Basic socket control ............................................
        function open = isOpen(obj)
            % Return whether this object is "open" (ready to receive
            % broadcasts).
            open = ~isequal(obj.socket, obj.NO_SOCKET) ...
                && isequal(obj.socket.Status, 'open');
        end
        
        function open(obj)
            % Build the object's socket and prepare it to receive
            % broadcasts. If the object is already open, it will first be
            % closed.
            if obj.isOpen()
                obj.close();
            end
            obj.socket = udp(obj.ip, 'LocalPort', obj.port);
            obj.socket.DatagramTerminateMode = 'on';
            obj.socket.EnablePortSharing = 'on';
            obj.index_in = 0;
            obj.socket.Timeout = 0;
            obj.socket.InputBufferSize = obj.buffer_size;
            if ~obj.silenced
                obj.print("FC Broadcast client opened:");
                disp(obj.socket);
            end
            fopen(obj.socket);
        end
        
        function close(obj)
            % Close and delete the object's socket. Can be called
            % redundantly.
            if obj.isOpen()
                fclose(obj.socket);
                delete(obj.socket);
                if ~obj.silenced
                obj.print("FC Broadcast client closed");
                end
            end
            obj.socket = obj.NO_SOCKET;
        end
        
        function broadcast = getBroadcast(obj)
            % Listen for a broadcast, parse it and return the result. The
            % returned value is an FCBroadcast instance with the data of
            % the last valid broadcast received while listening, if any, or
            % an "invalid" FCBroadcast instance if no valid broadcast was
            % found before timing out.
            broadcast = FCBroadcast();
            if ~obj.isOpen()
                obj.print("Warning: can't receive broadcasts when closed");
            else
                tic;
                while true
                    raw = fscanf(obj.socket);
                    if isempty(raw)
                        if toc > obj.timeout
                            obj.print("Warning: FC Broadcast timed out.");
                            break;
                        elseif broadcast.isValid()
                            break;
                        end 
                    else
                        splitted =split(raw ,obj.MAIN_SEPARATOR);
                        if length(splitted) == obj.VALID_LENGTH
                            index = str2double(splitted{obj.I_INDEX});
                            code = splitted{obj.I_B};
                            if ~isequal(code, obj.CODE)
                                obj.print(fprintf("Error: unrecognized "...
                                    + " code %s in "...
                                    + " received broadcast\n: %s",code, ...
                                    raw));
                            end
                            
                            if ~isnan(index) && (index > obj.index_in ...
                                    || index < (obj.index_in - obj.delta))
                                % Build broadcast:
                                listener_port = str2double(...
                                    splitted{obj.I_LISTENER_PORT});
                                timestamp = str2double(...
                                    splitted{obj.I_TIMESTAMP});
                                rows = str2double(splitted{obj.I_ROWS});
                                columns = str2double(...
                                    splitted{obj.I_COLUMNS});
                                layers = str2double(...
                                    splitted{obj.I_LAYERS});
                                rpms = sscanf(splitted{obj.I_RPMS}, ...
                                    ['%f' obj.LIST_SEPARATOR]);
                                listener_ip = obj.socket.DatagramAddress;
                                
                                broadcast.fill(index, ...
                                    listener_port, listener_ip, ...
                                    timestamp, rows, columns, layers, ...
                                    rpms);
                                
                                % Update index:
                                obj.setIndex(index);
                            else
                                obj.print(sprintf("Warning: invalid "...
                                    + "index %d received. "...
                                    + "Valid range: [%d, %d].", ...
                                    index + 1,obj.index_in - obj.delta, ...
                                    obj.index_in ));
                            end
                        else
                            obj.print(sprintf(...
                                "Warning: FC Broadcast with "...
                                + "invalid splitted length %d received."...
                                + " Expected %d.", length(splitted), ...
                                obj.VALID_LENGTH));
                        end
                    end
                end
            end
        end
        
        % Attribute getters and setters ...................................
        function setPort(obj, new_port)
            % Set the instance's local port in which to receive broadcasts.
            % If the object is "open," it will be closed and reopened.
            obj.port = new_port;
            if obj.isOpen()
                obj.close();
                obj.open();
            end
        end
        
        function setIP(obj, new_ip)
            % Set the instance's "HostAddress." If the object is "open"
            % when this method is called, it will be closed and reopened.
            obj.ip = new_ip;
            if obj.isOpen()
                obj.close()
                obj.open()
            end
        end
        
        function setDelta(obj, new_delta)
            % Set the "delta" used in the range of validity of broadcast
            % indices:
            %   new_valid_index > last_valid_index or
            %   new_valid_index < last_valid_index - delta
            obj.delta = new_delta;
        end
        
        function setBufferSize(obj, size)
            % Set the input buffer size of the object's socket. If the
            % object is open, it will be closed and reopened.
            obj.buffer_size = size;
            if obj.isOpen()
                obj.socket.InputBufferSize = obj.buffer_size;
            end
        end
        
        function setIndex(obj, new_index)
            % Override the currently stored value of the input index.
            obj.index_in = new_index;
        end
        
        function setTimeout(obj, new_timeout)
            % Set the timeout, in seconds, after which to assume there is
            % no broadcast to fetch. If the object is open, it will be
            % closed and reopened.
            obj.timeout = new_timeout;
            if obj.isOpen()
                obj.socket.Timeout = obj.timeout;
            end
        end
        
        function resetIndex(obj)
            % Reset the input index to its default value.
            obj.index_in = 0;
        end
        
        function setSilent(obj, silenced)
            % Set whether to print information to the console.
            obj.silenced = silenced;
        end
        
    end
    methods(Access = private)
        % Internal methods ................................................
        function print(obj, message)
            % Print the given string to the console if the corresponding
            % "silenced" flag is set to false.
            if ~obj.silenced
                disp(obj.SYMBOL + message);
            end
        end
    end
end