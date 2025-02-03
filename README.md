# MENTORED: autoMated fEedback geNearTiOn in pRogramming assignmEnts through Diversification

## Dataset

data.zip : The dataset from Refactory and AssignmentMender.

```
|-data
    |-problem_xx
    |    |-feedbacks
    |    |    |-{approach}
    |    |         |-with_correct_x.json
    |    |         |-without_correct_x.json
    |    |         |-...
    |    |         |-results.json
    |    |-dataset.json
    |-...
```

> problem_xx : Dataset folder of xxth problem.  
> dataset.json : Dataset of problem which include correct & wrong programs and set of test cases, etc.  
> feedbacks: Folder that stores logs of feedback.  
> {approach} : Folder where feedback logs are stored by approach.  
> with_correct_x.json : xth feedback log of experiment without correct program.  
> without_correct_x.json : xth feedback log of experiment with correct program.  
> results.json : Each result of xth experiment.  

## Setup

1. Environment
   `python >= 3.12`
2. Install library

   ```
   pip install -r requirements.txt
   ```
3. Make openai_key file for PyDex approach (option)

   ```
   vim openai.key
   ```

   ```
   write your openai api key
   ```
4. Unzip Dataset

   ```
   unzip data.zip
   ```

## How to Run

+ Run single problem without correct programs
  ```
  python run.py -d data/problem_1
  ```
+ Run single problem with correct programs
  ```
  python run.py -d data/problem_1 -c
  ```
+ Run single problem with PyDex approach
  ```
  python run.py -d data/problem_1 -a pydex
  ```
+ Run all problems
  ```
  python run.py -d data
  ```

### Command line arguments

- `-d` flag specifies the path of Dataset directory.
- `-c` flag specifies the using Correct programs, default is False.
- `-t` flag specifies the Timeout for test case validation, default is 1.
- `-g` flag specifies the number of Generations, default is 30.
- `-e` flag specifies the number of Executions(trials) of experiments, default is 100.
- `-r` flag specifies the Reset all results of experiments, default is False.
- `-a` flag specifies the Approach, choose mentored or pydex. The default is mentored.
- `-m` flag specifies the Multiprocess, default is False.
