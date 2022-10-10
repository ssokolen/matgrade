import pytest

import sys
sys.path.append('../')
sys.path.append('../matgrade')

import matlab.engine

from matgrade import ValueCheck, CheckError 

class CheckClass:
 
    eng = matlab.engine.start_matlab()

    #--------------------------------------------------------------------------
    # ValueCheck

    def test_value_scalar(self):
        """ ValueCheck should work with a list of scalar inputs."""

        check = ValueCheck([2.0, 2.0], 4.0, 1e-6, self.eng)
        assert check.evaluate("Student A", "sum")


    def test_value_matrix(self):
        """ ValueCheck should process list arguments as MATLAB double."""

        check = ValueCheck([[2.0, 2.0]], 4.0, 1e-6, self.eng)
        assert check.evaluate("Student A", "sum")


    def test_value_matrix_string(self):
        """ ValueCheck should raise meaningfull error for incorrect arrays."""

        with pycheck.raises(CheckError): 
            check = ValueCheck([['2.0', 2.0]], 4.0, 1e-6, self.eng)
        
