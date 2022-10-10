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
@patch('sys.argv', ["matgrade", "lab.yaml"])
def grades():

    # Doing work in test directory
    path = pathlib.Path(__file__).parent.resolve()
    os.chdir(path)

    matgrade()
    d = pd.read_csv("lab.csv")
    d.sort_values("Student", inplace = True, ignore_index=True)
    print(d)
    return d

def test_name(grades):

    assert grades["name"][0] == 10
    assert grades["name"][1] == 10
    assert grades["name"][2] == 10
    assert grades["name"][3] == 0

def test_shape(grades):
    
    assert grades["sodium_shape"][0] == 10
    assert grades["sodium_shape"][1] == 0
    assert grades["sodium_shape"][2] == 10
    assert grades["sodium_shape"][3] == 10

def test_value(grades):

    assert grades["iron"][0] == 10
    assert grades["iron"][1] == 10
    assert grades["iron"][2] == 0
    assert grades["iron"][3] == 10

def test_error(grades):
    
    assert grades["id_error"][0] == 10
    assert grades["id_error"][1] == 0
    assert grades["id_error"][2] == 10
    assert grades["id_error"][3] == 10


