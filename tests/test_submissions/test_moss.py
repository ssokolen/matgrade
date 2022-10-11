import pandas as pd
import pytest
from unittest.mock import patch

import os
import pathlib
import sys
sys.path.append('../')
sys.path.append('../matgrade')

import matlab.engine

from matgrade import matgrade

# Generating grades
@pytest.fixture
@patch('sys.argv', ["matgrade", "lab.yaml", "988255842"])
def moss():

    # Doing work in test directory
    path = pathlib.Path(__file__).parent.resolve()
    os.chdir(path)

    matgrade()
    return False

def test_name(moss):

    assert moss
