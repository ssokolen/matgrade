import re

import matlab.engine

from .misc import run_matlab_function


class CheckError(Exception):
    pass


class NameCheck:

    def __init__(self, filenames, solution):

        self.solution = solution
        self.filenames = filenames

    def evaluate(self, student, _call, _code):

        return self.filenames[student] == self.solution


class ShapeCheck:

    def __init__(self, arguments, solution, n, engine):

        self.arguments = arguments
        self.solution = solution
        self.n = n
        self.engine = engine

    def evaluate(self, _student, call, _code):

        try:
            value = run_matlab_function(
                call, self.arguments, self.n, self.engine,
            )
        except (matlab.engine.MatlabExecutionError, TimeoutError):
            return False

        # Either both value and solution have no size of rows/columns match
        if "size" in self.solution.__dir__():
            if "size" in value.__dir__():
                if value.size == self.solution.size:
                    return True
        else:
            if "size" not in value.__dir__():
                return True
        
        return False


class ValueCheck:

    def __init__(self, arguments, solution, tolerance, relative, n, engine):

        self.arguments = arguments
        self.solution = solution
        self.tolerance = tolerance
        self.relative = relative
        self.n = n
        self.engine = engine

    def evaluate(self, _student, call, _code):

        try:
            value = run_matlab_function(
                call, self.arguments, self.n, self.engine
            )
        except (matlab.engine.MatlabExecutionError, TimeoutError):
            return False

        # Compare percent deviations
        diff = self.engine.minus(value, self.solution)

        # If relative, divide this difference by the solution
        if self.relative:
            diff = self.engine.rdivide(diff, self.solution)

        diff = self.engine.abs(diff)
        diff = self.engine.max(diff)

        return diff < self.tolerance


class ErrorCheck:

    def __init__(self, arguments, engine):

        self.arguments = arguments
        self.engine = engine
        self.re_line = re.compile(r"(?<=line )\d+")

    def evaluate(self, _student, call, code):

        try:
            run_matlab_function(call, self.arguments, 1, self.engine)
        except matlab.engine.MatlabExecutionError as e:

            # Find error line
            line = self.re_line.search(str(e))
            if line is None:
                return False
            else:
                line = int(line.group(0))

            # And then check to see if there was an error defined there
            lines = code.split("\n")

            # Line numbering starts at 1 and hash line is added after code is stored
            # (resulting in a total offset of +2)
            lines = [i+2 for i, l in enumerate(lines) if "error(" in l]

            if line in lines:
                return True

        except TimeoutError:

            return False

        return False
