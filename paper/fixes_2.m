Failed Testcase:
 - status: Failure
 - input:  search(7,[1,5,10])
 - expect: 2
 - output: 1

Execution Traces:
 - wrong:   [1,2,3,5,7,2,3,5,7,8]
 - correct: [1,2,3,5,7,2,3,5,6]

Variable Value Sequence:
 - wrong:   {"x":[7],"seq":[[1,5,10]],
             "i":[0,1]}
 - correct: {"x":[7],"seq":[[1,5,10]],
             "index":[0,1]}

Fault Location & Patch:
 - In line 8, fix "return i" 
               to "return i + 1"