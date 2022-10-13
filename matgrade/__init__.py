import argparse
import sys
import warnings

import yaml

from .assessment import Assessment, AssessmentError
from .checks import NameCheck, ValueCheck, CheckError


#------------------------------------------------------------------------------
# Defining command-line arguments

parser = argparse.ArgumentParser()

parser.add_argument("path", help = "path to yaml config file")

msg = "MOSS userid (e.g. 98xxxxxxx) for optional plagiarism detection"
parser.add_argument("-m", "--moss", help = msg)


#------------------------------------------------------------------------------
# Generating assessment from yaml input

def matgrade():

    args = parser.parse_args()

    filename = args.path

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

    # Adding variables 
    if "variables" in documents[0]:
        variables = documents[0]["variables"]

        for name, call in variables.items():

            try:
                assessment.add_variable(name, call)
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
                if len(check) > 1:
                    n = check[1]
                else:
                    n = 1

                try:
                    assessment.add_shape_check(name, check[0], n)
                except Exception as e:
                    details = e.args[0]
                    print(details["message"])
                    sys.exit()

        if "absolute_value" in checks:
            value_checks = checks["absolute_value"]

            for name in value_checks:
                check = value_checks[name]
                if len(check) > 2:
                    n = check[2]
                else:
                    n = 1

                try:
                    assessment.add_value_check(name, check[0], check[1], False, n)
                except Exception as e:
                    details = e.args[0]
                    print(details["message"])
                    sys.exit()

        if "relative_value" in checks:
            value_checks = checks["relative_value"]

            for name in value_checks:
                check = value_checks[name]
                if len(check) > 2:
                    n = check[2]
                else:
                    n = 1

                try:
                    assessment.add_value_check(name, check[0], check[1], True, n)
                except Exception as e:
                    details = e.args[0]
                    print(details["message"])
                    sys.exit()

        if "error" in checks:
            error_checks = checks["error"]

            for name in error_checks:
                check = error_checks[name]

                try:
                    assessment.add_error_check(name, check)
                except Exception as e:
                    details = e.args[0]
                    print(details["message"])
                    sys.exit()


    #--------------------------------------------------------------------------
    # Looping through the rest of documents and performing tasks

    for task in documents[1:]:

        if "grade" in task:

            if "checks" not in task:
                print("Each grade task must define checks")
                sys.exit()
            elif not isinstance(task["checks"], list):
                checks = [task["checks"]]
            else:
                checks = task["checks"]

            if "combination" not in task:
                task["combination"] = "or"
                f = lambda a, b: a and b
            elif task["combination"] == "or":
                f = lambda a, b: a or b
            elif task["combination"] == "and":
                f = lambda a, b: a and b
            else:
                print("Grade task combination may only be \"and\"/\"or\"")
                sys.exit()

            if "name" not in task:
                if task["combination"] == "or":
                    name = " / ".join(checks)
                elif task["combination"] == "and":
                    name = " + ".join(checks)
            else:
                name = task["name"]

            value = task["grade"]

            assessment.add_graded_component(name, checks, f, value)


    #--------------------------------------------------------------------------
    # Generating output

    assessment.grade("grades.csv")

    if args.moss:

        try:
            assessment.check_plagiarism(args.moss, "plagiarism_report.html")
        except Exception as e:
            details = e.args[0]
            print(details["message"])
            sys.exit()

        
