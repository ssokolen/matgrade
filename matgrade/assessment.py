import functools
import hashlib
import matlab.engine
import os
import pandas as pd
import re
import requests
import socket
import shutil
import time
import warnings

from .checks import NameCheck, ShapeCheck, ValueCheck, ErrorCheck, CheckError
from .misc import run_matlab_function


class AssessmentError(Exception):
    pass


class Assessment:

    def __init__(self, solution, submissions):

        # Read in solution content
        try:
            f = open(solution)
        except:
            msg = "Could not open solution file: {}"
            raise AssessmentError({"message": msg.format(solution)})

        with f:
            self.solution = f.read()

        self.solution_call = "sol"

        # Double check submissions folder
        if not os.path.isdir(submissions):
            msg = "Could not open submissions folder: {}"
            raise AssessmentError({"message": msg.format(submissions)})

        try:
            filenames = os.listdir(submissions)
        except:
            msg = "Could not open submissions folder: {}"
            raise AssessmentError({"message": msg.format(submissions)})

        # Read in submissions, only keeping the latest ones
        self.hashes = {}
        self.submissions = {}
        self.calls = {}
        self.timestamps = {}
        self.functions = {}

        # Initialize regex for commant replacement
        re_comment = re.compile("%.*\n")

        for filename in filenames:

            # Skip directories
            submission = os.path.join(submissions, filename)
            if os.path.isdir(submission):
                continue

            # Parse file name
            components = [s.strip() for s in filename.split(" - ")]

            # Basic check on format
            try:
                assert(len(components) == 3)
                ids = components[0].split("-")
                float(ids[0])
                float(ids[1])
            except:
                msg = "File does not match submission pattern: {}"
                warnings.warn(msg.format(filename))
                continue 

            # Clip filename from time
            combined = components[2].split("-")
            timestamp = combined[0]
            function = "-".join(combined[1:])

            # Parse timestamp
            timestamp = time.strptime(timestamp, "%b %d, %Y %I%M %p")

            # If student has newer submission on record, ignore
            student = components[1]
            
            if student not in self.timestamps:
                pass
            elif self.timestamps[student] > timestamp:
                continue

            # Read in content
            try:
                f = open(submission)
            except:
                msg = "Could not open submission file: {}"
                raise AssessmentError({"message": msg.format(submission)})

            with f:
                submission = f.read()

            # Remove all comments to facilitate plagiarism submission checking 
            submission = re_comment.sub("", submission)

            # And add in student hash as an id
            student_id = hashlib.sha256(student.encode("utf-8")).hexdigest()

            self.hashes[student] = student_id
            self.submissions[student] = submission
            self.timestamps[student] = timestamp
            self.functions[student] = function

        # Ensure that there is at least on formattes submission
        if len(self.submissions) == 0:
            msg = "No valid submissions found."
            raise AssessmentError({"message": msg.format(submission)})

        # Trim hashes to keep things readable (but unique)
        ids = [i for i in self.hashes.values()]

        for n in range(5, len(ids[0])):
            trimmed = [i[:n] for i in ids]
            
            if len(set(trimmed)) == len(trimmed):

                for s, i in list(self.hashes.items()):
                    self.hashes[s] = i[:n]

                break

        # Generate m files for MATLAB code
        self.path = os.path.abspath(os.path.join(submissions, ".code"))

        # Delete path if it exists and then create it
        shutil.rmtree(self.path, ignore_errors = True)
        os.mkdir(self.path)

        # Add submissions in timestamp order for some traceability
        order = [(t, s) for (s, t) in self.timestamps.items()]
        order.sort()

        for i, (_, s) in enumerate(order):
            call = "sub{}".format(i)

            f = open(os.path.join(self.path, call + ".m"), "w")
            with f:
                student_id = self.hashes[s]
                submission = self.submissions[s]
                f.write("% Student: {}\n{}".format(student_id, submission))

            self.calls[s] = call 

        f = open(os.path.join(self.path, self.solution_call + ".m"), "w")
        with f:
            f.write(self.solution)

        self.checks = {}
        self.graded_components = []

        self.engine = matlab.engine.start_matlab()
        call = "addpath('{}')".format(self.path)
        self.engine.eval(call)

        # Initializing special name check (to perform filename comparisons)
        self.checks["name"] = NameCheck(self.functions, solution)

    #--------------------------------------------------------------------------
    # Add MATLAB variables

    def add_variable(self, name, call):
    
        try:
            value = self.engine.eval(call)
            self.engine.workspace[name] = value

        except (matlab.engine.MatlabExecutionError, SyntaxError):

            msg = "Defining variable \"{}\" with \"{}\" generated an error."
            raise AssessmentError({"message": msg.format(name, call)})

        except TimeoutError:

            msg = "Defining variable \"{}\" with \"{}\" timed out."
            raise AssessmentError({"message": msg.format(name, call)})


    #--------------------------------------------------------------------------
    # Initializing assessment by adding checks

    def add_shape_check(self, name, arguments, n):

        try:
            solution = run_matlab_function(
                self.solution_call, arguments, n, self.engine
            )

        except matlab.engine.MatlabExecutionError:
            msg = "Running solution with ({}) and nargout={} generated an error."
            arguments = ", ".join(arguments)
            raise AssessmentError({"message": msg.format(arguments, n)})

        except TimeoutError:

            msg = "Running solution with ({}) and nargout={} timed out."
            arguments = ", ".join(arguments)
            raise AssessmentError({"message": msg.format(arguments, n)})

        # Add check and then update dictionary
        try:
            check = ShapeCheck(arguments, solution, n, self.engine)
        except CheckError as e:
            raise AssessmentError({"message": msg.format(e.args[0])})

        self.checks[name] = check


    def add_value_check(self, name, arguments, tolerance, relative, n):

        try:
            solution = run_matlab_function(
                self.solution_call, arguments, n, self.engine
            )

        except matlab.engine.MatlabExecutionError:
            msg = "Running solution with ({}) and nargout={} generated an error."
            arguments = ", ".join(arguments)
            raise AssessmentError({"message": msg.format(arguments, n)})

        except TimeoutError:

            msg = "Running solution with ({}) and nargout={} timed out."
            arguments = ", ".join(arguments)
            raise AssessmentError({"message": msg.format(arguments, n)})

        # Add check and then update dictionary
        try:
            check = ValueCheck(
                arguments, solution, tolerance, relative, n, self.engine
            )
        except CheckError as e:
            raise AssessmentError({"message": msg.format(e.args[0])})

        self.checks[name] = check


    def add_error_check(self, name, arguments):

        self.checks[name] = ErrorCheck(arguments, self.engine)


    #--------------------------------------------------------------------------
    # Add a graded element

    def add_graded_component(self, name, checks, f, value):

        for check in checks:
            if check not in self.checks:

                msg = "\"{}\" check is undefined (referenced by \"{}\")"
                raise AssessmentError({"message": msg.format(check, name)})

        self.graded_components.append({
            "name": name,
            "checks": checks,
            "f": f,
            "value": value
        })
            
    #--------------------------------------------------------------------------
    # Generate results of all grades

    def grade(self, filename):

        # First, evaluate all checks
        checks = []
        
        for d in self.graded_components:
            checks.extend(d["checks"])

        checks = set(checks)
        results = {}

        for student, call in self.calls.items():

            results[student] = {}
            code = self.submissions[student]

            for check in checks:

                check_object = self.checks[check]
                result = check_object.evaluate(student, call, code)
                results[student][check] = result

        # Then iterate over all grades and combine
        grades = {}
        grade_names = []

        for component in self.graded_components:

            grade_results = {}

            for student in results:

                checks = component["checks"]
                temp = [results[student][check] for check in checks]
                result = functools.reduce(component["f"], temp)
                if result:
                    grade_results[student] = component["value"]
                else:
                    grade_results[student] = 0

            grades[component["name"]] = grade_results
            grade_names.append(component["name"])

        # Summing up total grade
        totals = {}

        for student in results:

            totals[student] = 0

            for value in grades.values():
                totals[student] += value[student]

        grades["total"] = totals
        grade_names.append("total")

        # Converting grade content into lists
        students = self.submissions.keys()

        content = {"student": students}

        for name in grade_names:
            content[name] = [grades[name][student] for student in students]

        d = pd.DataFrame(data = content)
        d.to_csv(filename, index = False)

    #--------------------------------------------------------------------------
    # Check plagiarism via moss

    def check_plagiarism(self, user_id, filename):

        s = socket.socket()
        s.connect(('moss.stanford.edu', 7690))

        s.send("moss {}\n".format(user_id).encode())
        s.send("directory 0\n".encode())
        s.send("X 0\n".encode())
        s.send("maxmatches 10\n".encode())
        s.send("show 100\n".encode())
        s.send("language matlab\n".encode())

        response = s.recv(1024)
        if response == "no":
            s.send(b"end\n")
            s.close()

            msg = "Something went wrong with MOSS submission."
            raise AssessmentError({"message": msg.format(arguments)})

        for i, (student, submission) in enumerate(self.submissions.items()):
            
            submission = submission.encode()

            message = "file {0} {1} {2} {3}\n".format(
                i + 1,
                "matlab",
                len(submission),
                self.hashes[student]
            )

            s.send(message.encode())
            s.send(submission)

        s.send("query 0 \n".encode())

        response = s.recv(1024)

        s.send(b"end\n")
        s.close()

        response = response.decode().strip()

        if response == "":
            msg = "Something went wrong with MOSS submission (check id)."
            raise AssessmentError({"message": msg})

        r = requests.get(response)

        if r.status_code != 200:
            msg = "MOSS submission did not return an output."
            raise AssessmentError({"message": msg})

        html = r.text

        # Convert hashes back to student names
        for student, student_id in self.hashes.items():

            student = "{} ({})".format(student, student_id)
            html = re.sub(student_id, student, html)

        # And write to file
        f = open(filename, "w")

        with f:
            f.write(html)
