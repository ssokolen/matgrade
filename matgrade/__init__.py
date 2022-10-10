import sys
import warnings

import yaml

from .assessment import Assessment, AssessmentError
from .checks import NameCheck, ValueCheck, CheckError

#-------------------------------------------------------------------------------
# Generating assessment from yaml input

def matgrade():

    filename = sys.argv[1]

    with open(filename) as f:
        content = f.read()

        # Using older load_all syntax
        documents = [d for d in yaml.load_all(content, yaml.Loader)]

    # Initializing general assessment from first document
    solution = documents[0]["solution"]
    submissions = documents[0]["submissions"]

    try:
        assessment = Assessment(solution, submissions)
    except Exception as e:
        details = e.args[0]
        print(details["message"])
        sys.exit()

    # Adding checks
    if "checks" in documents[0]:
        checks = documents[0]["checks"]

        if "shape" in checks:
            shape_checks = checks["shape"]

            for name in shape_checks:
                check = shape_checks[name]
                assessment.add_shape_check(name, check)

        if "value" in checks:
            value_checks = checks["value"]

            for name in value_checks:
                check = value_checks[name]
                assessment.add_value_check(name, check[0], check[1])

        if "error" in checks:
            error_checks = checks["error"]

            for name in error_checks:
                check = error_checks[name]
                assessment.add_error_check(name, check)

    #-------------------------------------------------------------------------------
    # Looping through the rest of documents and performing tasks

    for task in documents[1:]:

        #if "check" in task:
        #    
        #    assessment.check(task["checks"])

        if "grade" in task:
            assessment.grade(task["checks"], task["grade"])

    filename = filename.split(".")
    filename = filename[0] + ".csv"
    assessment.tabulate(filename)
