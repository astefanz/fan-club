clear all
close all
clc
delete(instrfindall);
 fig=figure('Units', 'pixels','Position', [100 0 1800 1000]);
%User Defined Properties 
serialPort = 'COM19';    % define COM port #
plotTitle = 'Starting.....'
xLabel = 'Elapsed Time (s)';    % x-axis label
yLabel = 'Data';                % y-axis label
plotGrid = 'on';                % 'off' to turn off grid
min = -5000;                     % set y-min
max = 5000;                      % set y-max
scrollWidth = 10;               % display period in plot, plot entire data log if <= 0
delay = .0001;                    % make sure sample faster than resolution
 
%Define Function Variables
time = 0;
data = 0;
data2 = 0;
count = 0;
 
%Set up Plot
hold on
plotGraph = plot(time,data,'-s','LineWidth',2,'MarkerEdgeColor','b','MarkerFaceColor',[.49 1 .63],'MarkerSize',2);
%plotGraph2 = plot(time,data2,'-v','LineWidth',2,'MarkerEdgeColor','r','MarkerFaceColor',[.49 1 .63],'MarkerSize',2);
hold off     


xlabel(xLabel,'FontSize',15);
ylabel(yLabel,'FontSize',15);
axis([0 10 min max]);
grid(plotGrid);
 
%Open Serial COM Port
s = serial(serialPort)
s.Baudrate = 9600;
disp('Close Plot to End Session');
fopen(s);
tic
 
while ishandle(plotGraph) %Loop when Plot is Active
     
    dat = fscanf(s, '%f'); %Read Data from Serial as Float
    %dat2 = fscanf(s, '%f'); %Read Data from Serial as Float
  
    if(~isempty(dat) && isfloat(dat) ) %Make sure Data Type is Correct        
        count = count + 1;    
        time(count) = toc;    %Extract Elapsed Time
        data(count) = dat(1); %Extract 1st Data Element         
      % data2(count) = dat2(1);
        
        if (count>2)
%         if (abs(data(count)-data(count-1)) >= 6000)
%             data(count)=data(count-1);
%         end
        
%            if (abs(data2(count)-data2(count-1)) >= 6000)
%             data2(count)=data2(count-1);
%         end
        end
        
        %Set Axis according to Scroll Width
        if(scrollWidth > 0)
        set(plotGraph,'XData',time(time > time(count)-scrollWidth),'YData',data(time > time(count)-scrollWidth));
        %set(plotGraph2,'XData',time(time > time(count)-scrollWidth),'YData',data2(time > time(count)-scrollWidth));
        axis([time(count)-scrollWidth time(count) min max]);
        else
        set(plotGraph,'XData',time,'YData',data);
        %set(plotGraph2,'XData',time,'YData',data2);
        axis([0 time(count) min max]);
        end
        
        if(mod(count,10)==0)
        plotTitle = (['Torque: ' num2str(data(count)) ' Nm'  ]);  % plot title
        %plotTitle = (['Lift: ' num2str(data2(count) )]);  % plot title
        end
        title(plotTitle,'FontSize',25);
        
        
        %Allow MATLAB to Update Plot
        pause(delay);
    end
end
 
%Close Serial COM Port and Delete useless Variables
fclose(s);
% clear count dat delay max min plotGraph plotGrid plotTitle s ...
%         scrollWidth serialPort xLabel yLabel;
%   
disp('Session Terminated...');

%% DATA Processing 
DATA=[time',data'];
%save CAST_Helicopter_Test_Second_Day_4_ms_full_array.dat DATA -ascii


%% DATA Plotting

time=DATA(:,1);
 ymin=-100;
 ymax=200;
 liftassist=190;
 liftassist2=223
 yvertline=ymin:ymax;
 xvertline=liftassist*ones(ymax-ymin+1,1)';
  xvertline2=liftassist2*ones(ymax-ymin+1,1)';
  
  
  % Subtracting the hover baseline
  

fig=figure('Units', 'pixels','Position', [750 100 1000 750]);
hold on;
dragplot=plot(DATA(:,1),DATA(:,2),'-v');


set(dragplot                         , ...
  'LineWidth'       , 0.2           , ...
  'Marker'          , 'v'         , ...
  'MarkerSize'      , 2           , ...
  'MarkerEdgeColor' , [.2 .2 .2]  , ...
  'MarkerFaceColor' , [.7 .7 .7]  );

set(liftplot                         , ...
  'LineWidth'       , 0.2           , ...
  'Marker'          , 's'         , ...
  'MarkerSize'      , 2           , ...
  'MarkerEdgeColor' , 'r'  , ...
  'MarkerFaceColor' , 'r'  );




hLegend = legend( ...
  [ dragplot, liftplot ], ...
  'DRAG' , ...
  'THRUST/LIFT'      , ...
  'Cruise Configuration'       , ...
  'Fitted Curve'    , ...
  '95% CI'                , ...
  'location', 'SouthEast' );

hTitle  = title ('v_{FA}=4.52 m/s (Full Array); v_i=7.89 m/s (Semi-Corrected Drag)');
hXLabel = xlabel('Time [s]'                     );
hYLabel = ylabel('Aerodynamic Forces [N]'                      );


hText   = text(196, 180, ...
  sprintf('\\it{Fan Array Operation}'));

hText2   = text(68, 180, ...
  sprintf('\\it{Helicopter Failure & Force Gauge Saturation}'));

set( gca                       , ...
    'FontName'   , 'Helvetica' );
set([hTitle, hXLabel, hYLabel, hText, hText2], ...
    'FontName'   , 'AvantGarde');
set([hLegend, gca]             , ...
    'FontSize'   , 8           );
set([hXLabel, hYLabel, hText, hText2]  , ...
    'FontSize'   , 10          );
set([ hText]  , ...
    'FontSize'   , 10          );

set( hTitle                    , ...
    'FontSize'   , 12          , ...
    'FontWeight' , 'bold'      );

set(gca, ...
  'Box'         , 'off'     , ...
  'TickDir'     , 'out'     , ...
  'TickLength'  , [.02 .02] , ...
  'XMinorTick'  , 'on'      , ...
  'YMinorTick'  , 'on'      , ...
  'YGrid'       , 'on'      , ...
  'XColor'      , [.3 .3 .3], ...
  'YColor'      , [.3 .3 .3], ...
  'YTick'       , -10*scalefactor:scalefactor:20*scalefactor, ...
  'LineWidth'   , 1         );


set(gcf, 'PaperPositionMode', 'auto');
saveas(fig,'Results.png')

% print -depsc2 finalPlot1.eps
% close;











%% Averaging over specific Time
for i=1:length(time)
    if time(i)<150
        i=i+1;
    else 
        i
        break
    end
end



for j=1:length(time)
    if time(j)<188
        j=j+1;
    else 
        j
        break
    end
end


x=linspace(0,max(round(-0.0098*DATA(i:j,3))),1000);
p = polyfit(-0.0098*DATA(i:j,3),-0.0098*DATA(i:j,2),1)
p2 = polyfit(-0.0098*DATA(i:j,3),-0.0098*DATA(i:j,2),2)
p3 = polyfit(-0.0098*DATA(i:j,3),-0.0098*DATA(i:j,2),3)
p4 = polyfit(-0.0098*DATA(i:j,3),-0.0098*DATA(i:j,2),4)
p5 = polyfit(-0.0098*DATA(i:j,3),-0.0098*DATA(i:j,2),5)
f1 = polyval(p,x);
f2 = polyval(p2,x);
f3 = polyval(p3,x);
f4 = polyval(p4,x);
f5 = polyval(p5,x);



figure
hold on,
plot(-0.0098*DATA(i:j,3),-0.0098*DATA(i:j,2),'*')
plot(x,f1,'*')
plot(x,f2,'*')
plot(x,f3,'*')
plot(x,f4,'*')
plot(x,f5,'*')






