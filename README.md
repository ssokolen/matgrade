A work-in-progress attempt at auto-grading student MATLAB work.

## Installation

Installation should be as simple as:

```
pip install .
```

However, there may be some issues with the MATLAB-Python interface.

MATLAB code evaluation is performed via the `matlab.engine` package. Although it is added as a `pip` dependency, it might not be available for all Python versions. Manual installation of `matlab.engine` may be required by following Mathworks instructions (available online).

Mathworks documentation suggests that the most recent supported version of Python is 3.9.13, so `pyenv` may be required to install `matgrade`.

```
pyenv install 3.9.13
pyenv shell 3.9.13
pip install .
```
Note, `matlab.engine` requires access to the Python shared library, which may need to be installed separately.

## Running

The installation process should provide access to the `matgrade` binary file which currently has just one argument -- the path to the yaml config file.

```
matgrade assessment.yaml
```

Which will then produce `assessment.csv` output.

## Configuration

Grading setup is managed entirely via an input `yaml` file. See `tests/test_grades` for a working example. Examples will be added here once the API stabilizes a bit.
