%------------------------------- Load Cell Calibration --------------------
clear all
close all
clc

delete(instrfindall)
%------------- Setup Connection with Load Cell Arduino ---------------------
a = arduino('/dev/ttyACM0','Mega2560')%,'Libraries','WheatstoneBridge');
pin = 'A0';


disp('Measuring Zero Offset') 
zerodata=[];
tic
while toc<5
 dat = readVoltage(a,pin)
 zerodata=[zerodata;dat];
end

offset=mean(zerodata)

disp('Zero Offset Done, Enter 4 Different Weights') 
calibrationdata(1,:)=[0,0];
for ii=1:4
    
prompt = {['Enter Weight' num2str(ii) ':']};
propmpttitle = 'Input';
dims = [1 35];
definput = {' ','hsv'};
weight =str2num(cell2mat((inputdlg(prompt,propmpttitle,dims,definput))));
caldata=[];
tic
while toc<5
 dat = readVoltage(a,pin)
 caldata=[caldata,dat];
end

calibrationdata(ii+1,:)=[weight,mean(caldata)-offset]
end

x = linspace(0,max(calibrationdata(:,2)),100);
p = polyfit(calibrationdata(:,2),calibrationdata(:,1),1);
y=polyval(p,x);


fig=figure('Units', 'pixels','Position', [100 400 750 600]);
hold on,
plot(calibrationdata(:,2),calibrationdata(:,1),'o')
plot(x,y,'--')
ylabel('Weight');
xlabel('Voltage')

title(['Calibration Factor: '  num2str(p(1)) ])

calibrationfactor=p(1);
save calibrationfactor.dat calibrationfactor -ascii;