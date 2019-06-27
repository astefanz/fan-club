classdef FanArray
   properties
       C
       R
       maxVal
       maxFans
       mapping
       size
       array
       cell_length
       grid_width
       grid_height
       fig_n
   end
   methods
       function obj = FanArray(C, R, maxVal, maxFans, cell_length, mapping)
          obj.C = C;
          obj.R = R;
          obj.maxVal = maxVal;
          obj.maxFans = maxFans;
          obj.mapping = mapping;
          obj.size = R*C;
          obj.array = cell(R, C);
          obj.cell_length = cell_length;
          obj.grid_width = cell_length*C;
          obj.grid_height = cell_length*R;
       end
       function obj = build(obj, fig_n)
           obj.fig_n = fig_n;
           figure(fig_n);
           set(gca, 'FontSize', 16);
           axis([0 obj.grid_width 0 obj.grid_height 0 1]);
           title(sprintf("FAWT at t = %d s", 0), 'interpreter', 'latex');
           xlabel('Column', 'interpreter', 'latex', 'FontSize', 20);
           ylabel('Row', 'interpreter', 'latex', 'FontSize', 20);
           zlabel('$\frac{\omega}{\omega_{max}}$','interpreter', 'latex',...
            'FontSize', 30);
           view(-45, 75);
           hold on
           for c = 1:obj.C
               for r = 1:obj.R
                    obj.array{r, c} = FanRepr(c - 1, r - 1, 0, ...
                        obj.cell_length, 0);
               end
           end
           drawnow update
           hold off
       end
       function obj = draw(obj, t, dataset)
           data = dataset;
           figure(obj.fig_n);
           title(sprintf("FAWT at t = %.3f s", dataset.Times(t)), ...
               'interpreter', 'latex');
           for r = 1:obj.R
                for c = 1:obj.C
                    i = (c - 1) + (r - 1)*obj.C + 1;
                    s = obj.mapping(i, 1) + 1;
                    f = obj.mapping(i, 2) + 1;
                    raw_rpm = data{t, 1 + (s - 1)*obj.maxFans + f};
                    normd_rpm = min([1 raw_rpm/obj.maxVal]);  
                    fan = obj.array{r, c};
                    
                    fan.set(normd_rpm, normd_rpm);
                end
           end
            drawnow limitrate
       end
          
   end 
end