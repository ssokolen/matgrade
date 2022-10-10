% Student: a07d8b11a6b1229e3e48fb7ef72c153b6864690c0930d773df776e02b450c465

function t = decay_time(n,x)

    switch n
        case {1 , 'H'}
            k = 1.784e-9;
        case {11 , 'Na'}
            k = 1.288e-5;
        case {26 , 'Fe'}
            k = 1.803e-7;
        otherwise
            error('Error: Requested compound not listed')
    end

    t = -log(x)/k;
end
