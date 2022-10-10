function t = decay_time(symbol, fraction)

switch symbol
    case {'H', 1}
        k = 1.784e-9;
    case {'Na', 11}
        k = 1.288e-5;
    case {'Fe', 26}
        k = 1.803e-7;
    otherwise
        error('Invalid input number or symbol')
end

t = log(fraction)/(-k);

end
