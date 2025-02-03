class Results:
    exec_traces = []
    vari_traces = {}
    vari_names = []
    line_vars_map = {}
    changed_line_map = {}
    status = None
    timeout = 1
    test_code = ''
    input = ''
    output = ''
    stdout = None
    globals = None
    end_line = 0

    @classmethod
    def init_global_vars(cls):
        cls.exec_traces = []
        cls.vari_traces = {}
        cls.vari_names = []
        cls.line_vars_map = {}
        cls.changed_line_map = {}
        cls.status = None
        cls.timeout = 1
        cls.test_code = ''
        cls.input = ''
        cls.output = ''
        cls.stdout = None
        cls.globals = None
        cls.end_line = 0