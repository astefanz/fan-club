%% Drone Tracking Script
   % You need to set up the natnetclient in your main code, then you can use a
% function similar to this to actually return the position values. You need
% to have the NatNetSDK files 
clc
clear all
close all
delete(instrfindall)
t_sample=0.001;    %1/sampling frequency
addpath('NatNetMatlab/') 
%addpath('Free Flight Data Sets/') 
%% Include to set up natnetclient in main script
%% Set up NatNet Client
natnetclient = natnet;

% Multicast. 
natnetclient.HostIP = '192.168.1.149';         %Ip of router from optitrack computer (ipconfig on optitrack computer)
natnetclient.ClientIP = '192.168.1.118';     %Ip of router from logging computer (ipconfig on logging computer)


% Loopback.
% natnetclient.HostIP = '127.0.0.1';
% natnetclient.ClientIP = '127.0.0.1';

% Connection type
natnetclient.ConnectionType = 'Multicast';

% Connect
natnetclient.connect;

% Error check
if ( natnetclient.IsConnected == 0 )
    fprintf( 'Client failed to connect\n' )
    fprintf( '\tMake sure the host is connected to the network\n' )
    fprintf( '\tand that the host and client IP addresses are correct\n\n' )
    return
end

% get the asset descriptions for the asset names
model = natnetclient.getModelDescription;
if ( model.RigidBodyCount < 1 )
    return
end





%% UDP Connection
remPort=4210;      
host='192.168.1.119';  
locPort=64761;
u = udp(host,'RemotePort',remPort,'LocalPort',locPort); 
u.ReadAsyncMode = 'manual';
fopen(u)



%%

        dat = fscanf(u,'%s')
        
            [a,p]=localData(natnetclient);   %a: roll(+ is right roll) pitch(-is pitch forward) yaw(+ is yaw right) p: x,y,z

 