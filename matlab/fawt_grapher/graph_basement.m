function graph_basement(data, rate, export, filename)

    % Array characteristics:
    C = 11;
    R = 11;
    maxRPM = 12000;
    maxFans = 21;
    cell_length = 1;

    % Mapping:
    mapping = [...
        3 0;
        3 1;	3 2;	3 3;	3 4;	4 19;	4 17;	4 13;	4 9;	4 5;	4 2;	3 5;
        3 6;	3 7;	3 8;	3 9;	4 18;	4 16;	4 12;	4 8;	4 4;	4 1;	3 10;
        3 11;	3 12;	3 13;	3 14;	3 15;	4 15;	4 11;	4 7;	4 3;	4 0;	2 18;
        2 19;	3 16;	3 17;	3 18;	3 19;	4 14;	4 10;	4 6;	5 9;	5 4;	2 13;
        2 14;	2 15;	2 16;	2 17;	5 20;	5 18;	5 15;	5 12;	5 8;	5 3;	2 7;
        2 8;	2 9;	2 10;	2 11;	2 12;	5 17;	5 14;	5 11;	5 7;	5 2;	2 2;
        2 3;	2 4;	2 5;	2 6;	5 19;	5 16;	5 13;	5 10;	5 6;	5 1;	2 0;
        2 1;	1 13;	1 9;	1 5;	0 19;	0 17;	0 13;	0 9;	5 5;	5 0;	1 19;
        1 16;	1 12;	1 8;	1 4;	0 18;	0 16;	0 12;	0 8;	0 5;	0 2;	1 18;
        1 15;	1 11;	1 7;	1 3;	1 1;	0 15;	0 11;	0 7;	0 4;	0 1;	1 17;
        1 14;	1 10;	1 6;	1 2;	1 0;	0 14;	0 10;	0 6;	0 3;	0 0;];

    colormap('jet');
    A = FanArray(C, R, maxRPM, maxFans, cell_length, mapping);
    
    fig_n = 1;
    fig = figure(fig_n);
    A = A.build(fig_n);

    for t = 1:rate:length(data.Times)
        A.draw(t, data);
        if export
           frame = getframe(fig);
           im = frame2im(frame);
           [imind, cm] = rgb2ind(im, 256);
           if t == 1
               imwrite(imind, cm, filename, 'gif', 'Loopcount', inf);
           else
               imwrite(imind,cm,filename,'gif','WriteMode','append');
           end
        end
    end

end