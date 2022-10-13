% Student: a6aa9

function [z1, z2] = plus_or_minus(x, y, op)

switch op
    case {'plus'}
      z1 = x + y
    case {'minus'}
      z1 =  x - y
    case {'both'}
      z1 = x + y
      z2 = x - y
    otherwise
      error('Invalid operation')
end

end

