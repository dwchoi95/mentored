import time
import json
import pandas as pd
from tqdm import tqdm
from texttable import Texttable
from tinydb import Query
from multiprocess import Process, Lock, Manager
import os

from .database import Database, DBKey
from .ted import TED
from .etc import divide

from ..approaches import MENTORED, PYDEX
from ..execution import Tester, CodeQuality


class Experiments:
    def __init__(self, 
                 generations:int=30, trials:int=10, 
                 correct:bool=False, timeout:int=1, 
                 approach:str='mentored', multi:bool=False,
                 reset:bool=False):
        
        self.generations = generations
        self.trials = trials
        self.correct = correct
        self.timeout = timeout
        self.approach = approach
        self.multi = multi
        self.reset = reset
        self.experiment_db_file = 'experiment.json'
        self.results_db_file = 'results.json'
        

    def __setup_dataset(self, dataset):
        db = Database(dataset)
        problem = db.get_data_from_table('problem')
        self.title = problem['title']
        self.description = problem['description']
        self.corrects = db.get_data_from_table('corrects')
        self.wrongs = db.get_data_from_table('wrongs')
        self.testcases = db.table('testcases').all()
        db.close()

    def __setup_logs(self, dataset):
        # Set Logs
        dataset_dir = os.path.dirname(dataset)
        self.problem = os.path.basename(dataset_dir)
        results_db_path = \
            os.path.join(dataset_dir, 'feedbacks', self.approach, self.results_db_file)
        self.feedback_db_path = \
            os.path.join(dataset_dir, 'feedbacks', self.approach)
        os.makedirs(self.feedback_db_path, exist_ok=True)
        
        self.experiment_db = Database(self.experiment_db_file, save=False)
        self.results_db = Database(results_db_path, save=True)

    def __close_logs(self):
        self.experiment_db.close()
        self.results_db.close()
        
    def delete_logs(self, dataset):
        import shutil
        dataset_dir = os.path.dirname(dataset)
        results_db_path = \
            os.path.join(dataset_dir, self.results_db_file)
        if os.path.isfile(results_db_path):
            os.remove(results_db_path)
        feedbacks_path = os.path.join(dataset_dir, 'feedbacks', self.approach)
        if os.path.isdir(feedbacks_path):
            shutil.rmtree(feedbacks_path)
                

    def __save_results(self, 
                       trial:int, 
                       time_taken:float, 
                       feedback_table:Database, 
                       lock:Lock=Lock()) -> dict:
        # Results
        solutions = {}
        results = feedback_table.search(Query().solution == True)
        for solution in tqdm(results, desc="Save", leave=False):
            wrong_id = solution['wrong_id']
            origin_w_id = wrong_id.rsplit('_', 1)[0]
            solutions.setdefault(origin_w_id, {})
            wrong = self.wrongs[origin_w_id]
            patch = solution['patch']
            rps = TED.relative_patch_size(wrong, patch)
            quality = CodeQuality.check(patch)
            solutions[origin_w_id][rps] = divide(quality, 10)
            with lock:
                feedback_table.update(
                    {DBKey.rps:rps, DBKey.quality:quality}, 
                    doc_ids=[solution.doc_id])
        
        total_rps = 0
        total_quality = 0
        for rps_quality in solutions.values():
            total_rps += min(rps_quality.keys())
            total_quality += max(rps_quality.values())
        
        with lock:
            results_db_id = self.results_db.insert({
                DBKey.trial: trial,
                DBKey.c_progs: len(self.corrects) if self.correct else 0,
                DBKey.w_progs: len(self.wrongs),
                DBKey.solutions: len(solutions),
                DBKey.rr: round(divide(len(solutions), len(self.wrongs)), 2),
                DBKey.rps: round(divide(total_rps, len(solutions)), 2),
                DBKey.att: round(divide(time_taken, len(self.wrongs)), 2),
                DBKey.quality: round(divide(total_quality, len(solutions)), 2)
            })
            result = self.results_db.get(doc_id=results_db_id)
        return result
    
    def __save_performance(self) -> dict:
        # Performance
        tot_solution = 0
        tot_rps = 0
        tot_time = 0
        tot_quality = 0
        
        best_feedback = None
        max_solution = 0
        correct_programs = len(self.corrects) if self.correct else 0
        lock = Lock()
        with lock:
            results = self.results_db.search(Query()['Correct Programs'] == correct_programs)
        for result in results:
            trial = result[DBKey.trial]
            if self.correct:
                feedback_file_name = f'with_correct_{trial}.json'
            else:
                feedback_file_name = f'without_correct_{trial}.json'
            feedback_file_path = \
                os.path.join(self.feedback_db_path, feedback_file_name)
            with open(feedback_file_path, 'r') as f:
                feedback = json.load(f)
            if best_feedback is None:
                best_feedback = feedback
            solutions = result[DBKey.solutions]
            if solutions > max_solution:
                max_solution = solutions
                best_feedback = feedback
            tot_solution += solutions
            tot_rps += result[DBKey.rps]
            tot_time += result[DBKey.att]
            tot_quality += result[DBKey.quality]
            os.remove(feedback_file_path)
        
        if self.correct:
            feedback_file_name = 'with_correct.json'
        else:
            feedback_file_name = 'without_correct.json'
        feedback_path = \
            os.path.join(self.feedback_db_path, feedback_file_name)
        with open(feedback_path, 'w') as f:
            json.dump(best_feedback, f, indent=4)
        
        import math
        avg_sol = math.ceil(divide(tot_solution, self.trials))
        
        ## Save performance
        self.experiment_id = self.experiment_db.insert({
            DBKey.problem: self.problem.split("_")[-1],
            DBKey.title: self.title,
            DBKey.approach: self.approach,
            DBKey.trials: self.trials,
            DBKey.generations: self.generations,
            DBKey.c_progs: len(self.corrects) if self.correct else 0,
            DBKey.w_progs: len(self.wrongs),
            DBKey.a_sol: avg_sol,
            DBKey.a_rr: f'{divide(avg_sol, len(self.wrongs)):.2f}',
            DBKey.a_rps: f'{divide(tot_rps, self.trials):.2f}',
            DBKey.a_att: f'{divide(tot_time, self.trials):.1f}',
            DBKey.a_cq: f'{divide(tot_quality, self.trials):.2f}'
        })
        return self.experiment_db.get(doc_id=self.experiment_id)
    
    def __print_database(self, database:dict):
            ## Print database
            tt = Texttable()
            tt.add_rows([[k,v] for k,v in database.items()])
            print(tt.draw())
            print()

    def nl_feedback(self):
        if self.correct:
            feedback_file_name = 'with_correct.json'
        else:
            feedback_file_name = 'without_correct.json'
        feedback_path = \
            os.path.join(self.feedback_db_path, feedback_file_name)
        with open(feedback_path, 'r') as f:
            feedback = json.load(f)
        
        feedback_map = {}
        for modification in feedback:
            original_id = modification['wrong_id'].rsplit('_', 1)[0]
            feedback_map.setdefault(original_id, [])
            feedback_map[original_id].append(modification)

        best_solutions = {original_id: self.__chain_modifications(mod_list)
                          for original_id, mod_list in feedback_map.items()}
        
        if self.correct:
            feedback_file_name = 'feedback_with_correct.json'
        else:
            feedback_file_name = 'feedback_without_correct.json'
        feedback_path = \
            os.path.join(self.feedback_db_path, feedback_file_name)
            
        with open(feedback_path, 'w') as f:
            json.dump(best_solutions, f, indent=4)

    def __chain_modifications(self, mod_list):
        patch_dict = {mod['patch_id']: mod for mod in mod_list}
        
        chains = []
        for mod in mod_list:
            if mod.get('solution') is True:
                chain = [mod]
                current = mod
                while current['wrong_id'] in patch_dict:
                    prev_mod = patch_dict[current['wrong_id']]
                    chain.insert(0, prev_mod)
                    current = prev_mod
                chains.append(chain)
        return chains
        
    
    def __core(self, trial:int, lock:Lock=Lock()):
        # Generate Feedback
        correct_programs = len(self.corrects) if self.correct else 0
        with lock:
            result = self.results_db.search(
                (Query()['Trial(#)'] == trial) & 
                (Query()['Correct Programs'] == correct_programs))
        if result:
            return None
        
        if self.correct:
            feedback_file_name = f'with_correct_{trial}.json'
        else:
            feedback_file_name = f'without_correct_{trial}.json'
        feedback_db_table_path = \
            os.path.join(self.feedback_db_path, feedback_file_name)
        
        Tester.init_global_data(self.testcases, self.timeout)
        feedback_db = Database(feedback_db_table_path, save=False)
        start_time = time.process_time()
        if self.approach == 'mentored':
            afg = MENTORED(feedback_db, 
                            self.wrongs, 
                            self.corrects if self.correct else {})
        elif self.approach == 'pydex':
            afg = PYDEX(feedback_db,
                        self.wrongs, 
                        self.corrects if self.correct else {})
        afg.run(generations=self.generations)
        time_taken = time.process_time() - start_time
        Tester.clear()
    
        result = self.__save_results(trial, time_taken, feedback_db)
        # self.__print_database(result)
        
        with open(feedback_db_table_path, 'w') as f:
            json.dump(feedback_db.all(), f, indent=4)
    
    def run(self, dataset):
        if self.reset: self.delete_logs(dataset)
        self.__setup_dataset(dataset)
        self.__setup_logs(dataset)
        
        print(self.problem)
        if self.multi:
            cpu_count = os.cpu_count()
            procs = []
            for trial in tqdm(range(1, self.trials+1), desc="Trials"):
                proc = Process(target=self.__core, args=(trial, ))
                proc.start()
                procs.append(proc)
                if len(procs) >= cpu_count:
                    procs[0].join()
                    procs.pop(0)
            for proc in procs: proc.join()
        else:
            for trial in tqdm(range(1, self.trials+1), desc="Trials"):
                self.__core(trial, )
        
        performance = self.__save_performance()
        self.__print_database(performance)
        self.__close_logs()
