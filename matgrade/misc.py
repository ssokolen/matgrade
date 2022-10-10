import io
import os
import time

def run_matlab_function(function, arguments, engine):

    # Suppressing all MATLAB output
    null = io.StringIO("")

    command = "{}({})".format(function, ", ".join(arguments))
    value = engine.eval(command, stdout = null, stderr = null)

    return value                
