function fcplot(dataset, num_slaves, max_fans)
    % Given an FC log table, plot the duty cycle and RPM vectors.
    times = dataset.Times;
    rpm_vectors = [];
    dc_vectors = [];
    disp("Extracting RPM vectors");
    for s=1:num_slaves
        for f=1:max_fans
            rpm_vectors = [rpm_vectors dataset.(s*max_fans + f + 1)];
        end
    end
    disp("Building figure");
    figure
    hold on
    for i=1:length(times)/10
        plot(times, rpm_vectors(i));
        print(i);
    end
    hold off
end