import sys
import trace
import threading
from ordered_set import OrderedSet

from .results import Results

class Tracer(trace.Trace):
    def __init__(self, count=1, 
                 trace=0, 
                 countfuncs=0, 
                 countcallers=0,
                 ignoremods=(), 
                 ignoredirs=[sys.prefix, sys.exec_prefix], 
                 infile=None, 
                 outfile=None,
                 timing=False):
        super().__init__(count, trace, 
                        countfuncs, countcallers,
                        ignoremods, ignoredirs, 
                        infile, outfile,
                        timing)
        self.b_line = 1
        self.max_depth = 100
    
    def variable_trace(self, var_dict:dict):
        for k, v in var_dict.items():
            if self.b_line in Results.line_vars_map.keys() and \
                k in Results.line_vars_map[self.b_line]:
                Results.vari_traces.setdefault(k, OrderedSet())
                Results.vari_traces[k].add((str(v), self.b_line))
    
    def execution_trace(self, lineno:int):
        Results.exec_traces.append(lineno)
    
    def localtrace_count(self, frame, why, arg):
        self.max_depth -= 1
        if self.max_depth < 0:
            return self.localtrace
        if why == "line":
            # record the file name and line number of every trace
            filename = frame.f_code.co_filename
            lineno = frame.f_lineno
            key = filename, lineno
            self.counts[key] = self.counts.get(key, 0) + 1
            if lineno in Results.changed_line_map.keys():
                origin_lineno = Results.changed_line_map[lineno]
                # append line numbers to traces list
                self.execution_trace(origin_lineno)
                # append variable values
                # print(len(frame.f_locals))
                self.variable_trace(frame.f_locals)
                self.b_line = origin_lineno
        return self.localtrace
    
    def runctx(self, cmd, globals=None, locals=None):
        # Do not delete runctx
        if globals is None: globals = {}
        if locals is None: locals = {}
        if not self.donothing:
            threading.settrace(self.globaltrace)
            sys.settrace(self.globaltrace)
        try:
            exec(cmd, globals)
        finally:
            if not self.donothing:
                sys.settrace(None)
                threading.settrace(None)
