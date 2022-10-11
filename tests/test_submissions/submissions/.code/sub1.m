% Student: ceffc

function t = decay_time(n,x)

    if n == 1
        k = 1.784e-9;
	t = -log(x)/k;
    elseif n == 11
        k = 1.288e-5;
	t = -log(x)/k;
    elseif n == 26
        k = 1.803e-7;
	t = -log(x)/k;
    end

    t = t(1)
end
