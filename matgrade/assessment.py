import hashlib
import matlab.engine
import os
import pandas as pd
import re
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

        self.variables = {}
        self.checks = {}
        self.grades = {}

        self.engine = matlab.engine.start_matlab()
        call = "addpath('{}')".format(self.path)
        self.engine.eval(call)

        # Initializing special name check (to perform filename comparisons)
        self.checks["name"] = NameCheck(self.functions, solution)

    #def add_variables(self, **kwargs):
    #
    #    for key in kwargs.names():
    #        self.variables[key] = kwargs[key]


    #---------------------------------------------------------------------------
    # Initializing assessment by adding checks
    #

    def add_shape_check(self, name, arguments):

        try:
            solution = run_matlab_function(
                self.solution_call, arguments, self.engine
            )
        except matlab.engine.MatlabExecutionError:
            msg = "Running solution with ({}) generated an error."
            arguments = ", ".join(arguments)
            raise AssessmentError({"message": msg.format(arguments)})


        # Add check and then update dictionary
        try:
            check = ShapeCheck(arguments, solution, self.engine)
        except CheckError as e:
            raise AssessmentError({"message": msg.format(e.args[0])})

        self.checks[name] = check

    def add_value_check(self, name, arguments, tolerance):

        try:
            solution = run_matlab_function(
                self.solution_call, arguments, self.engine
            )
        except matlab.engine.MatlabExecutionError:
            msg = "Running solution with ({}) generated an error."
            arguments = ", ".join(arguments)
            raise AssessmentError({"message": msg.format(arguments)})


        # Add check and then update dictionary
        try:
            check = ValueCheck(arguments, solution, tolerance, self.engine)
        except CheckError as e:
            raise AssessmentError({"message": msg.format(e.args[0])})

        self.checks[name] = check


    def add_error_check(self, name, arguments):

        self.checks[name] = ErrorCheck(arguments, self.engine)


    #---------------------------------------------------------------------------
    # Grade submissions using specified check

    def grade(self, check, grade):

        self.grades[check] = {}

        for student, call in self.calls.items():

            code = self.submissions[student]
            correct = self.checks[check].evaluate(student, call, code)

            if correct:
                self.grades[check][student] = grade
            else:
                self.grades[check][student] = 0

    #---------------------------------------------------------------------------
    # Generate results of all grades

    def tabulate(self, name):

        # Converting grade content into lists
        students = self.submissions.keys()

        content = {"Student": students}

        for check, grades in self.grades.items():
            content[check] = [grades[s] for s in students]

        d = pd.DataFrame(data = content)
        d.to_csv(name, index = False)

    #---------------------------------------------------------------------------
    # Check plagiarism via moss

    def check_plagiarism(self, user_id):

        s = socket.socket()
        s.connect(('moss.stanford.edu', 7690))

        s.send("moss {}\n".format(user_id).encode())
        s.send("directory 0\n".encode())
        s.send("X 0\n".encode())
        s.send("maxmatches 10\n".encode())
        s.send("show 100\n".encode())
        s.send("language matlab\n".encode())

        recv = s.recv(1024)
        print(recv)
        print(recv.decode())
        if recv == "no":
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

            print(self.calls[student])
            print(message)
            s.send(message.encode())
            s.send(submission)

        s.send("query 0 \n".encode())

        response = s.recv(1024)
        print(response)

        s.send(b"end\n")
        s.close()

        print(response.decode())
