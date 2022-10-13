import argparse
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
@pytest.fixture(scope = 'session', autouse = True)
@patch(
    'argparse.ArgumentParser.parse_args',
    return_value=argparse.Namespace(path = "lab.yaml", moss = None)
)
def grades(placeholder):

    # Doing work in test directory
    path = pathlib.Path(__file__).parent.resolve()
    os.chdir(path)

    matgrade()
    d = pd.read_csv("grades.csv")
    d.sort_values("student", inplace = True, ignore_index=True)
    print()
    print(d)
    return d

def test_name(grades):

    assert grades["name"][0] == 10
    assert grades["name"][1] == 10
    assert grades["name"][2] == 10
    assert grades["name"][3] == 0

def test_shape(grades):
    
    assert grades["shape"][0] == 10
    assert grades["shape"][1] == 0
    assert grades["shape"][2] == 10
    assert grades["shape"][3] == 10

def test_value(grades):

    assert grades["plus"][0] == 10
    assert grades["plus"][1] == 10
    assert grades["plus"][2] == 0
    assert grades["plus"][3] == 10

def test_or(grades):

    assert grades["plus_or_minus"][0] == 10
    assert grades["plus_or_minus"][1] == 10
    assert grades["plus_or_minus"][2] == 10
    assert grades["plus_or_minus"][3] == 10

def test_and(grades):

    assert grades["plus_and_minus"][0] == 10
    assert grades["plus_and_minus"][1] == 0
    assert grades["plus_and_minus"][2] == 0
    assert grades["plus_and_minus"][3] == 10

def test_error(grades):
    
    assert grades["error"][0] == 10
    assert grades["error"][1] == 0
    assert grades["error"][2] == 10
    assert grades["error"][3] == 10


