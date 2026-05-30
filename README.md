# Secure Multi-party Computation System

In this project, you will develop a secure multi-party computation system in Python. We have provided the skeleton code to help you kick-start.

## Overview

The skeleton comprises multiple components, among which you need to implement:
- The SMC client
- The trusted parameter generator (TPP)
- Secret sharing
- Expressions

The rest are provided for you, including:
- The communication protocol
- The trusted server
- The test suite

Your task is to implement said parts such that your implementation passes the test suite without error.

## Getting started

You should have cloned this repository to your local computer by now. For this project, we strongly recommend you set up a Python 3.11 runtime either via your system package manager or via a dedicated container. Newer version of Python can and will cause problems (e.g., API changes in the `ast` package). Then, you can install the required packages marked in `requirements.txt`, preferably in a dedicated virtual environment (e.g., `venv` or `poetry`):

```bash
$ pip3 install -r requirements.txt
```

Now, you can run the provided test cases to verify that all dependencies have been installed correctly. You should see 10 failed tests from `NotImplementedError`, indicating that the program started normally, but failed as nothing has been implemented yet.

```bash
$ pytest ./test_integration.py
...
===================================================== short test summary info ====================================================== 
FAILED test_integration.py::test_suite1 - NotImplementedError: You need to implement this method.
FAILED test_integration.py::test_suite2 - NotImplementedError: You need to implement this method.
FAILED test_integration.py::test_suite3 - NotImplementedError: You need to implement this method.
FAILED test_integration.py::test_suite4 - NotImplementedError: You need to implement this method.
FAILED test_integration.py::test_suite5 - NotImplementedError: You need to implement this method.
FAILED test_integration.py::test_suite6 - NotImplementedError: You need to implement this method.
FAILED test_integration.py::test_suite7 - NotImplementedError: You need to implement this method.
FAILED test_integration.py::test_suite8 - NotImplementedError: You need to implement this method.
FAILED test_integration.py::test_suite9 - NotImplementedError: You need to implement this method.
FAILED test_integration.py::test_suite10 - NotImplementedError: You need to implement this method.
======================================================== 10 failed in 0.42s ======================================================== 
```

### Skeleton structure

The skeleton code consists of the following files:

- `expression.py`* contains code that define arithmetic expressions that can be computed by the SMC service.
- `secret_sharing.py`* contains code that implements the secret sharing protocol.
- `ttp.py`* contains code that implements the trusted parameter generator for the Beaver multiplication scheme.
- `smc_party.py`* contains code for SMC clients that work with each other to carry out the SMC computation.
- `communication.py` contains code that takes care of communication between different components.
- `server.py` contains code for the trusted server.
- `protocol.py` contains code that defines the structure of expressions.
- `.gitlab.ci.yaml` contains definition for the CI/CD pipeline.

You only need to work on files that are marked with `*` for this project.

Additionally, the skeleton also contains a series of test files. Some of them contain pre-defined tests, some do not. In either case, you are welcome to add your tests to make sure your code behave as you expect:

- `test_integration.py` checks if your implementation as a whole behaves correctly (e.g. if an SMC expression is correctly evaluated).
- `test_expression.py` checks if your expression implementation works as intended.
- `test_ttp.py` checks if your TTP implementation works as intended.
- `test_secret_sharing.py` checks if your secret sharing implementation works as intended.


You implementation should at least pass all the 10 test cases provided in `test_integration.py`. We may further test your implementation against a set of private test cases at grading time.


## Submitting your code

At any time during your development, you can commit and push your code to your personal repo. You are encouraged to keep your code in the `p1` branch, but in principle you can use any branch name. After every push, Gitlab will automatically run the tests in a `python:3.11-alpine` container. You can use the result as a reference for what we will see when we grade your submission.

To submit your code, push your code to your personal repo under the branch `p1-submission`. This must be done before the deadline, and this branch is configured as protected so you cannot force push to it. An example procedure can be:

```bash
# assuming you have committed all your changes
# create and checkout the submission branch
$ git checkout -b p1-submission

# make sure that your personal repo is configured as a remote
$ git remote -v

# push the submission branch
# origin is the name of the remote of your personal repo
$ git push origin p1-submission
```

In principle, you can use any way you like to manage your code. The one requirement is that you do not publish your code anywhere (e.g. storing your code in a public GitHub repository).
