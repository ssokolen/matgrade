% Correct solution with no error, infinite loop for minus, and always outputs len 1

function z = plus_or_minus(x, y, op)

switch op
    case {'plus'}
      temp = x + y
    case {'minus'}
      while 1
        temp = x - y
      end
    otherwise
      disp('Invalid operation')
end

z = temp(1)

end

