function Y = snine2NaN(X)
    Y = zeros(length(X), 1);
    for i=1:length(X)
        x = X(i);
        if x < 0
            Y(i) = NaN;
        else
            Y(i) = x;
        end
    end
end