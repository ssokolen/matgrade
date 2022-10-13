% Correct solution

function z = plus_or_minus(x, y, op)

switch op
    case {'plus'}
      z = x + y
    case {'minus'}
      z =  x - y
    otherwise
      error('Invalid operation')
end

end

