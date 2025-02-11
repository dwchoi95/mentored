Failed Testcase:
 - status: Failure
 - input:  search(-100,())
 - expect: 0
 - output: 1

Execution Traces:
 - wrong:   [1,2,9]
 - correct: [1,2,5]

Variable Value Sequence:
 - wrong:   {"x": [-100],"seq": [()]}
 - correct: {"x": [-100],"seq": [()]}



Fault Location & Patch:
 - In line 9, fix "return len(seq) + 1" 
               to "return len(seq)"