import io
import multiprocessing
import os
import time


def run_matlab_function(function, arguments, n, engine):

    # Suppressing all MATLAB output
    null = io.StringIO("")

    command = "{}({})".format(function, ", ".join(arguments))
    future = engine.eval(
        command, stdout = null, stderr = null, nargout = n, background = True
    )

    start = time.perf_counter()

    while (not future.done()) and ((time.perf_counter() - start) < 0.5):
        pass

    if not future.done():
        future.cancel()

        # Leaving some time for process to cancel
        # (as not doing this seemed to mess up follow-up calls)
        time.sleep(2.0)
        raise TimeoutError

    value = future.result()

    if n > 1:
        value = value[n-1]

    return value            
