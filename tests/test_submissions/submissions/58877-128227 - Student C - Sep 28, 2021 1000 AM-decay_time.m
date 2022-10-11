% Incorrect k value for sodium and iron

function t = decay_time(n,x)

    switch n
        case {1 , 'H'}
            k = 1.784e-9;
        case {11 , 'Na'}
            k = 2;
        case {26 , 'Fe'}
            k = 2;
        otherwise
            error('Error: Requested compound not listed')
    end

    t = -log(x)/k;
end
