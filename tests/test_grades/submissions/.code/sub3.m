% Student: a6aa9ed23c2ef0ff2d55d88d3e7a6ddf9835c06c63ccdd401605f1790548d56d

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
