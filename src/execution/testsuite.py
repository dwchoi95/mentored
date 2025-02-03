class Testcases:
    def __init__(self, testcases:list):
        self.testcases = [self.Testcase(tc) for tc in sorted(testcases, key=lambda x: x['no'])]

    class Testcase:
        def __init__(self, testcase:dict):
            self.no = testcase.get('no', 1)
            self.input = testcase.get('input', None)
            self.output = testcase.get('output', None)
            self.open = testcase.get('open', True)

class TestSuite:
    def __init__(self, testcases:list):
        self.testcases = Testcases(testcases).testcases
        self.current_index = 0
        

    def __iter__(self):
        self.current_index = 0
        return self

    def __next__(self):
        if self.current_index < len(self.testcases):
            testcase = self.testcases[self.current_index]
            self.current_index += 1
            return testcase
        raise StopIteration
    
    def __len__(self):
        return len(self.testcases)
    
    def __str__(self):
        prints = ''
        for testcase in self.testcases:
            # prints += f"No: {testcase.no}\n"
            prints += f"#input:\n{testcase.input}\n"
            prints += f"#output:\n{testcase.output}\n\n"
        return prints.strip()
    
    def make_tests(self):
        prints = ''
        for testcase in self.testcases:
            prints += f"print({str(testcase.input)} == {str(testcase.output)})\n"
        return prints.strip()
    
    def print_testcase(self, idx):
        prints = ''
        for testcase in self.testcases:
            if testcase.no == idx:
                prints += f"No: {testcase.no}\n"
                prints += f"Input: {testcase.input}\n"
                prints += f"Expect: {testcase.output}"
        return prints

    def get_open_tc_list(self):
        return [tc for tc in self.testcases if tc.open]

    def get_tc_no_list(self):
        return [tc.no for tc in self.testcases]
    
    def get_tc_by_no(self, no):
        for testcase in self.testcases:
            if testcase.no == no:
                return testcase
        raise IndexError
    
    


