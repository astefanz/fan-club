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
% Expected formats:
% - To MkIV:
%   ................................
%   INDEX|COMMAND_CODE|COMMAND_VALUE
%   1.....2............3............
%
% - From MkIV:
%   ............................
%   INDEX|REPLY_CODE|REPLY_VALUE
%   1.....2..........3..........
classdef FCExternalController < handle
    % Abstraction for all functionality with which to externally control
    % an instance of FC MkIV.
    
    properties(Constant)
        I_IN_INDEX = 1;
        I_IN_CODE = 2;
        I_IN_VALUE = 3;
        
        I_OUT_INDEX = 1;
        I_OUT_CODE = 2;
        I_OUT_VALUE = 3;
        
        LENGTH_IN = 3;
        LENGTH_OUT = 3;
        
        CODE_F = 'F';
        CODE_N = 'N';
        CODE_S = 'S';
        CODE_ERROR = 'E';
        CODE_UNIFORM = 'U';
        CODE_DC_VECTOR = 'D';
        CODE_PROFILE = 'P';
        CODE_EVALUATE = 'V';
        CODE_RESET = 'R';
        
        DEFAULT_SOCKET = '';
        DEFAULT_PORT = 60269;
        DEFAULT_TARGET_IP = '';
        DEFAULT_TARGET_PORT = 60169;
        DEFAULT_TIMEOUT = 10;
        DEFAULT_INDEX_IN = 0;
        DEFAULT_INDEX_OUT = 1;
        DEFAULT_REPEAT = 0;
        DEFAULT_DELTA = 10;
        DEFAULT_BUFFER_SIZE = 32768;
        DEFAULT_SILENCED = false;
        
        SYMBOL = "[FC External] ";
        NO_SOCKET = '';
        
        MAIN_SEPARATOR = '|';
        LIST_SEPARATOR = ',';
       
    end
    properties
        socket
        port
        target_ip
        target_port
        timeout
        index_in
        index_out
        repeat
        delta
        buffer_size
        silenced
    end
    methods(Access = public)
        function obj = FCExternalController()
            % Create a new, closed, FC external controller, initialized to
            % the default values.
            % NOTE: UDP timeout warnings will be disabled.
            obj.socket = obj.NO_SOCKET;
            obj.port = obj.DEFAULT_PORT;
            obj.target_ip = obj.DEFAULT_TARGET_IP;
            obj.target_port = obj.DEFAULT_TARGET_PORT;
            obj.timeout = obj.DEFAULT_TIMEOUT;
            obj.index_in = obj.DEFAULT_INDEX_IN;
            obj.index_out = obj.DEFAULT_INDEX_OUT;
            obj.repeat = obj.DEFAULT_REPEAT;
            obj.delta = obj.DEFAULT_DELTA;
            obj.buffer_size = obj.DEFAULT_BUFFER_SIZE;
            obj.silenced = obj.DEFAULT_SILENCED;
            warning('off', 'instrument:fscanf:unsuccessfulRead');
        end
        
        function open(obj)
            % Build the object's socket and open it, leaving it ready to
            % receive messages. If the object is already open, it will be
            % closed first.
            if obj.isOpen()
                obj.close()
            end
            obj.socket = udp(obj.target_ip, 'LocalPort', obj.port,...
                'RemotePort', obj.target_port);
            obj.socket.DatagramTerminateMode = 'on';
            obj.socket.EnablePortSharing = 'on';
            obj.socket.Timeout = 0.01;
            obj.socket.InputBufferSize = obj.buffer_size;
            obj.socket.OutputBufferSize = obj.buffer_size;
            fopen(obj.socket);
            obj.resetIndices();
            obj.requestReset();
            if ~obj.silenced
               obj.print("Opened FC External Controller:");
               disp(obj.socket);
            end
        end
        
        function close(obj)
            % Close and delete the object's socket. Can be called
            % redundantly.
            if obj.isOpen()
                fclose(obj.socket);
                delete(obj.socket);
            end
            obj.socket = obj.NO_SOCKET;
            if ~obj.silenced
               obj.print("Closed FC External Controller.");
            end
        end
        
        function open = isOpen(obj)
            % Return whether the object is capable of sending and receiving
            % messages over a network.
            open = ~isequal(obj.socket, obj.NO_SOCKET) ...
                && isequal(obj.socket.Status, 'open');
        end
        
        % Core API .............................................................
        function reply = sendUniform(obj, dc)
            % Set the fan array to a given duty cycle (in the range [0.0, 1.0]).
            % Requires that this instance be "opened."
            reply = obj.sendToListener(obj.CODE_UNIFORM, string(dc), true);
        end
        
        function reply = sendDCVector(obj, R, C, L, vector)
            % Set the fan array to the given duty cycle vector.
            % Requires that this instance be "opened."
            %
            % R, C and L are the rows, columns and layers of the array
            % being controlled.
            %
            % vector is a single-dimensional array of numbers in the range
            % [0.0, 1.0] of length exactly R*C*L
            %
            % For example, to set a 2x2 array of 2 layers to full speed on the
            % first layer and zero on the second, do:
            %   myInstance.sendDCVector(2,2,2, [1 1 1 1 0 0 0 0]);
            %
            reply = obj.sendToListener(obj.CODE_DC_VECTOR, ...
                sprintf("%d|%d|%d|%s", R, C, L, ...
                    sprintf("%.2f,", vector)), true);
        end
        
        function reply = sendExpression(obj, expression)
            % Send a Python expression to be evaluated at the MkIV. The
            % result of the expression is returned as a string.
            % Requires that this instance be "opened."
            reply = obj.sendToListener(obj.CODE_EVALUATE, expression,true);
        end
        
        function F = queryFeedbackVector(obj)
            % Request the most recent feedback vector and return it as an
            % array of parsed numbers.
            % Requires that this instance be "opened."
            F_raw = obj.sendToListener(obj.CODE_F, '', true);
            F = sscanf(F_raw, ['%.2f' obj.LIST_SEPARATOR]);
        end
        
        function N = queryNetworkVector(obj)
            % Request the most recent network state vector and return it as
            % an array of strings or char arrays.
            % Requires that this instance be "opened."
            N_raw = obj.sendToListener(obj.CODE_N, '', true);
            N = split(N_raw, obj.LIST_SEPARATOR);
        end
        
        function S = querySlaveVector(obj)
            % Request the most recent slave status vector and return it as
            % an array of strings or char arrays.
            % Requires that this instance be "opened."
            S_raw = obj.sendToListener(obj.CODE_S, '', true);
            S = split(S_raw, obj.LIST_SEPARATOR);
        end
        
        function value = queryProfile(obj, attribute)
            % Request an attribute of the loaded FC profile. The given
            % attribute name must be a string that matches the name of an
            % FC profile attribute. The obtained value is returned as a
            % string.
            % Requires that this instance be "opened."
            value = obj.sendToListener(obj.CODE_PROFILE, attribute, true);
        end
        
        function requestReset(obj)
            % Request that the MkIV's incoming index be reset. This allows
            % a reset index from this end to be accepted even if there was
            % a previous external control client instance running.
            obj.sendToListener(obj.CODE_RESET, '', false);
        end
        
        function reply = sendCustom(obj, code, message, get_reply)
            % Send a custom command and return the result. Meant for
            % debugging and development.
            reply = obj.sendToListener(code, message, get_reply);
        end
        
        % Attribute getters and setters ...................................
        function setPort(obj, port)
            % Set the local port in which to receive replies.
            % If the instance is already open, it will be closed and
            % reopened.
            obj.port = port;
            if obj.isOpen()
                obj.close();
                obj.open();
            end
        end
        
        function setTargetPort(obj, port)
            % Set the port to which to send commands.
            % If the instance is already open, it will be closed and
            % reopened.
            if port == 0
                obj.print("Warning: received listener port 0. "...
                    + "Is the E.C. listener active?");
            else
                obj.target_port = port;
                if obj.isOpen()
                    obj.close();
                    obj.open();
                end
            end
        end
        
        function setTargetIP(obj, ip)
            % Set the IP address to which to send commands.
            % If the instance is already open, it will be closed and
            % reopened.
            obj.target_ip = ip;
            if obj.isOpen()
                obj.close();
                obj.open();
            end
        end
        
        function setIncomingIndex(obj, index)
            % Override the value of the incoming index (the one used to
            % determine whether a reply is to be discarded).
            obj.index_in = index;
        end
        
        function setOutgoingIndex(obj, index)
            % Override the value of the outgoing index (the one used by the
            % other end to determine whether to discard a command).
            obj.index_out = index;
        end
        
        function resetIndices(obj)
            % Reset both indices to their starting values.
            obj.index_in = obj.DEFAULT_INDEX_IN;
            obj.index_out = obj.DEFAULT_INDEX_OUT;
        end
        
        function setBufferSize(obj, size)
            % Set the input and output buffer sizes -- i.e the maximum size
            % of a packet that can be either received or sent.
            % If the instance is already open, it will be closed and
            % reopened.
            obj.buffer_size = size;
            if obj.isOpen()
                obj.close();
                obj.open();
            end
        end
        
        function setRepeat(obj, repeat)
            % Set how many times to re-send a message to ensure reception.
            obj.repeat = repeat;
        end
    end
    methods(Access = private)
        function print(obj, message)
            % Print a message to the console if the object is not
            % "silenced."
            if ~obj.silenced
                disp(obj.SYMBOL + message)
            end
        end
        
        function reply = sendToListener(obj, code, content, get_reply)
            % Send the a command with the given code and the given content
            % and listen for anr return a reply if get_reply is set to
            % true.
            %
            % content should be either a string or char array with the
            % "value" of the command to be sent. If the command being sent
            % does not require a value, set content to the empty char array ''.
            
            reply = '';
            if obj.isOpen()
                message = sprintf("%d|%s", obj.index_out, code);
                if ~isequal(content, '')
                    message = message + "|" + content;
                end
                obj.socket.Timeout = obj.timeout;
                for i = 1:1 + obj.repeat
                    fwrite(obj.socket, message);
                end
                obj.index_out = obj.index_out + 1;
                
                if get_reply
                    [~, reply] = obj.getReply();
                end
            else
                obj.print("Warning: tried to send while closed");
            end
        end
        
        function [reply_code, reply_content] = getReply(obj)
            reply_code = '';
            reply_content = '';
            if obj.isOpen()
                tic;
                while true
                    obj.socket.Timeout = 0;
                    raw = fscanf(obj.socket);
                    if isempty(raw)
                        if toc > obj.timeout
                            obj.print("Warning: timed out.");
                            break;
                        elseif ~isempty(reply_code)
                            break;
                        end
                    else
                        splitted = split(raw, obj.MAIN_SEPARATOR);
                        if length(splitted) == obj.LENGTH_IN
                            index_new = str2double(...
                                splitted{obj.I_IN_INDEX});
                            if obj.isValidIndex(index_new)      
                                reply_code = splitted{obj.I_IN_CODE};
                                reply_content = splitted{obj.I_IN_VALUE};
                                obj.index_in = index_new;
                                if isequal(reply_code, obj.CODE_ERROR)
                                    obj.handleError(reply_content);
                                    break;
                                end
                            end
                        else
                            obj.print(sprintf("Warning: Invalid split"...
                                + "length %d received. Expected %d",...
                                length(splitted), obj.LENGTH_IN));
                        end % End length check
                    end % End reception check
                end % End receive loop
            else
                obj.print("Warning: tried to receive while closed");
            end % End check open
        end
        
        function valid = isValidIndex(obj, i)
            % Return whether the given index corresponds to a reply that
            % should be used. If false, the reply is considered to be 
            % either redundant or obsolete and should be ignored.
           valid =  (i > obj.index_in) || (i < (obj.index_in - obj.delta));
        end
        
        function handleError(obj, error_message)
            % Handle an error message received from the other end, whose 
            % description is passed as a string or char array.
            obj.print("Error (from FC): " + error_message);
        end
    end
end