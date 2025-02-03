import argparse
import glob
import os
import warnings
warnings.filterwarnings('ignore')

from src.utils import Experiments, extract_number

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dataset', type=str, required=True,
                        help="The path of dataset")
    parser.add_argument('-c', '--correct', action='store_true', default=False,
                        help="Use correct programs")
    parser.add_argument('-t', '--timeout', type=int, default=1,
                        help="Set timeout for compile program, default is 1sec")
    parser.add_argument('-g', '--generations', type=int, default=30,
                        help="Number of generations, default is 30")
    parser.add_argument('-e', '--executions', type=int, default=1,
                        help="Number of executions, default is 1")
    parser.add_argument('-r', '--reset', action='store_true', default=False,
                        help="Reset experimental results")
    parser.add_argument('-a', '--approach', type=str, default='mentored',
                        help="Select approach to run, e.g., 'mentored', 'pydex'")
    parser.add_argument('-m', '--multiprocess', action='store_true', default=False,
                        help="Run with multiprocessing")
    args = parser.parse_args()

    dataset = args.dataset
    correct = args.correct
    generations = args.generations
    timeout = args.timeout
    trials = args.executions
    approach = args.approach.lower()
    multi = args.multiprocess
    reset = args.reset
    
    assert os.path.isdir(dataset), "Wrong directory"
    datasets = glob.glob(f'{dataset}/**/dataset.json', recursive=True)
    assert datasets, "'dataset.json' file doesn't exists"
    datasets = sorted(datasets, key=extract_number)

    if approach not in ['mentored', 'pydex']:
        raise ValueError("Invalid approach, choose 'mentored' or 'pydex'")
    if approach == 'pydex' and multi:
        raise ValueError("gpt api of 'pydex' approach doesn't support multiprocessing")

    ex = Experiments(generations, trials, correct, timeout, approach, multi, reset)
    for dataset in datasets:
        ex.run(dataset)
    