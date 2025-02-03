from tqdm import tqdm


from ..utils import Database, Log, Regularize
from ..execution import Tester
from ..genetic import Selection, Variation


class MENTORED:
    def __init__(self, database:Database, wrongs:dict, corrects:dict={}):
        self.solutions = dict()
        self.wrongs = self.__preproc(wrongs)
        self.corrects = self.__preproc(corrects)
        self.log = Log(database)
        self.select = Selection(self.wrongs, self.corrects)
        self.variation = Variation(self.log)
        
    def __preproc(self, programs:dict) -> dict:
        return {f'{p_id}_0':Regularize.run(code) for p_id, code in programs.items()}
    
    def run(self, generations:int=30) -> dict:
        # Initial population
        population = self.wrongs | self.corrects
        pop_size = len(self.wrongs)
        
        # Generation
        for generation in tqdm(range(1, generations+1), desc="MENTORED", leave=False):
            # Selection
            parents = self.select.run(population, pop_size, self.solutions)
            for wrong_id, refer_id in tqdm(parents.items(), total=len(parents), desc="wrongs", leave=False):
                origin_w_id = wrong_id.rsplit('_', 1)[0]
                first_w_id = f'{origin_w_id}_0'
                patch_id = f'{origin_w_id}_{generation}'
                wrong_code, refer_code = population[wrong_id], population[refer_id]
                self.log.insert({'generation':generation})
                self.log.update({'wrong_id':wrong_id, 'refer_id':refer_id})
                self.log.update({'wrong_code':wrong_code, 'refer_code':refer_code})

                # Variation
                patch = self.variation.run(wrong_code, refer_code)
                self.log.update({'patch_id':patch_id, 'patch':patch})

                ## Check the patch is solution
                p_test_hist, _, _ = Tester.trace(patch)
                self.log.update({'p_test_hist':str(p_test_hist)})
                self.log.update({'solution':False})
                if Tester.is_all_pass(p_test_hist):
                    self.log.update({'solution':True})
                    self.solutions.setdefault(origin_w_id, {})
                    self.solutions[origin_w_id][patch_id] = patch
                
                ## Population update with all solutions
                # population[patch_id] = patch
                
                # Population update with tournament selection
                solutions = {wrong_id:wrong_code, patch_id:patch}
                if origin_w_id in self.solutions.keys():
                    solutions.update(self.solutions[origin_w_id])
                best_solution = self.select.tournament(
                    self.wrongs[first_w_id], solutions)
                if best_solution == patch_id and patch not in population.values():
                    population[patch_id] = patch
                    self.log.update({'descendant':True})
            