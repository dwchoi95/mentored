import unittest
from io import StringIO
from unittest.mock import patch, mock_open
from timeout_decorator import timeout
# from timeout_function_decorator import timeout

from .results import Results
from .tracer import Tracer

class UnitTestStatus:
    success = 'Success'
    error = 'Error'
    failure = 'Failure'

class TextTestResult(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super_class = super(TextTestResult, self)
        super_class.__init__(stream, descriptions, verbosity)
        self.status = 'Timed Out'
        self.stdout = stream.getvalue()
    def addSuccess(self, test):
        super(TextTestResult, self).addSuccess(test)
        self.status = UnitTestStatus.success
    def addError(self, test, err):
        super(TextTestResult, self).addError(test, err)
        self.status = UnitTestStatus.error
    def addFailure(self, test, err):
        super(TextTestResult, self).addFailure(test, err)
        self.status = UnitTestStatus.failure

class Running(unittest.TestCase):
    def setUp(self):
        self.original_globals = dict(globals()).copy()
        globals()['__name__'] = '__main__'
        self.input_data = StringIO(Results.input)
        self.mock_stdout = StringIO()
        self.mock_stderr = StringIO()
    
    def tearDown(self) -> None:
        globals().clear()
        globals().update(self.original_globals)
        self.input_data.close()
        self.mock_stdout.close()
        self.mock_stderr.close()

    def assertEqual(self, actual, expected, msg=None):
        try: super().assertEqual(actual, expected, msg)
        except AssertionError as e:
            raise AssertionError(actual)

    @timeout(Results.timeout)
    def test(self):
        with (
            patch('sys.stdin', self.input_data),
            patch('builtins.open', mock_open(read_data=Results.input)),
            patch('builtins.input', side_effect=self.input_data),
            patch('sys.stdout', self.mock_stdout),
            patch('sys.stderr', self.mock_stderr)):
            try:
                exec(Results.test_code, globals())
                output = self.mock_stdout.getvalue().strip()
                self.assertEqual(output, Results.output)
            except Exception as e:
                output = str(e)
                self.fail(output)
        

class Tracing(unittest.TestCase):
    def setUp(self):
        self.original_globals = dict(globals()).copy()
        globals()['__name__'] = '__main__'
        self.input_data = StringIO(Results.input)
        self.mock_stdout = StringIO()
        self.mock_stderr = StringIO()
    
    def tearDown(self) -> None:
        globals().clear()
        globals().update(self.original_globals)
        self.input_data.close()
        self.mock_stdout.close()
        self.mock_stderr.close()

    def assertEqual(self, actual, expected, msg=None):
        try: super().assertEqual(actual, expected, msg)
        except AssertionError as e:
            raise AssertionError(actual)

    @timeout(Results.timeout)
    def test(self):
        with (
            patch('sys.stdin', self.input_data),
            patch('builtins.open', mock_open(read_data=Results.input)),
            patch('builtins.input', side_effect=self.input_data),
            patch('sys.stdout', self.mock_stdout),
            patch('sys.stderr', self.mock_stderr)):
            try:
                Tracer().runctx(Results.test_code, globals())
                output = self.mock_stdout.getvalue().strip()
                self.assertEqual(output, Results.output)
            except Exception as e:
                output = str(e)
                self.fail(output)
                

class RunUnitTest:
    def run(cls, UnitTest=Running):
        suite = unittest.TestLoader().loadTestsFromTestCase(UnitTest)
        stream = StringIO()
        runner = unittest.TextTestRunner(stream=stream)
        runner.resultclass = TextTestResult
        res = runner.run(suite)
        Results.status = res.status
        stream.close()
