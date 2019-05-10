times = data.Times;

rpm1 = data.VarName2;
dc1 = data.VarName10;

rpm2 = data.VarName3;
dc2 = data.VarName11;

rpm3 = data.VarName6;
dc3 = data.VarName14;

rpm4 = data.VarName7;
dc4 = data.VarName15;

num_entries = length(times);
dcfloor = ones(num_entries, 1)*300;
dcmid = ones(num_entries, 1)*650;
dcroof = ones(num_entries, 1)*1000;

F = figure;
plot(times, dcfloor, "--k",...
    times, dcmid, "--k",...
    times, dcroof,"--k",...
    times, 1000*dc1, "g",...
    times,rpm1,"g",...
    times, 1000*dc2, "y",...
    times, rpm2, "y",...
    times, 1000*dc3,"r",.... 
    times, rpm3,"r",...
    times, 1000*dc4,"b",... 
    times, rpm4,"b");
title("4 fans, 2 boards, c.period 90ms, fn.period 100ms, for almost 10min");
xlabel("Time (s)");
ylabel("RPM above, DC (scaled by 1000) below");
% Function used:
% a_freq = 4*math.pi/500
% t_offset = a_freq*2*math.pi*c
% dc_offset = 0.65
% activation = 1 if t > t_offset else 0
% amplitude = 0.35
 
% return activation*amplitude*math.sin(a_freq*(t - t_offset)) + dc_offset
