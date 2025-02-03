from pylint.lint import Run
import tempfile
import contextlib
from io import StringIO

from .tester import Tester
from ..utils import divide


class CodeQuality:
    @staticmethod
    def check(code:str) -> float:
        total = 0
        for testcase in Tester.testsuite:
            test_code = Tester.gen_test_code(code, testcase.input)
            test_code += "\n"
            with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp_file:
                tmp_file.write(test_code.encode('utf-8'))
                tmp_file_name = tmp_file.name

            stdout = StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stdout):
                results = Run([tmp_file_name], exit=False)
            stdout.close()
            
            score = results.linter.stats.global_note
            total += score
        return round(divide(total, len(Tester.testsuite)), 2)
    