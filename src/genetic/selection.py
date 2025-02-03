import numpy as np
import pandas as pd
from paretoset import paretoset
from tqdm import tqdm

from .fitness import Fitness
from ..utils import Randoms

class Selection:
    def __init__(self, wrongs:dict, corrects:dict):
        self.wrongs = wrongs
        self.corrects = corrects
    
    def tournament(self, w_code:str, samples:dict) -> str:
        test_score_map = {}
        trace_score_map = {}
        for r_id, r_code in samples.items():
            scores = list(Fitness.run(w_code, r_code).values())
            test_score_map[r_id] = scores[0] + scores[1]
            trace_score_map[r_id] = scores[2] + scores[3]
        max_test_score = max(test_score_map.values())
        max_r_list = [r_id for r_id, score in test_score_map.items() 
                       if score == max_test_score]
        if len(max_r_list) == 1:
            return max_r_list[0]
        max_trace_score = max(trace_score_map.values())
        max_r_list = [r_id for r_id, score in trace_score_map.items() 
                       if score == max_trace_score]
        return max_r_list[0]
    
    def nsga_iii(self, w_code:str, samples:dict) -> str:
        # Paretoset
        scores = {r_id: list(Fitness.run(w_code, r_code).values()) 
                  for r_id, r_code in samples.items()
                  if r_code != w_code}
        scores_df = pd.DataFrame.from_dict(scores, orient='index')
        pareto_set = paretoset(scores_df, sense=["max", "max", "max", "max"])
        fronts = scores_df[pareto_set].index.tolist()

        # NSGA3
        r_candidates = []
        reference_points = np.array([
            [1.0, 1.0, 1.0, 1.0], # Best of All Objects
            [1.0, 0.0, 0.0, 0.0], # Best of First Object
            [0.0, 1.0, 0.0, 0.0], # Best of Second Object
            [0.0, 0.0, 1.0, 0.0], # Best of Third Object
            [0.0, 0.0, 0.0, 1.0], # Best of Fourth Object
            ])
        for reference_point in reference_points:
            # Distance from reference directions
            reference_direction = reference_point / np.linalg.norm(reference_point)
            r_distance_dict = {}
            for r_id in fronts:
                r_point = scores[r_id]
                distances = self.__perpendicular_distance(r_point, reference_direction)
                r_distance_dict[r_id] = distances
            min_distance = min(r_distance_dict.values())
            min_r_list = [r_id for r_id, score in r_distance_dict.items() 
                           if score == min_distance]
            r_candidates.extend(min_r_list)
        return Randoms.choice(r_candidates)
    
    def __perpendicular_distance(self, point, direction):
        point = np.array(point)
        direction = np.array(direction)
        projection_length = np.dot(point, direction)
        projection = projection_length * direction
        perpendicular_vector = point - projection
        return np.linalg.norm(perpendicular_vector)
    
    
    def run(self, population:dict, pop_size:int, solutions:dict=dict()) -> dict:
        # Select parents as large as pop_size with NSGA-iii
        wrongs = []
        samples = []
        for p_id in population.keys():
            origin_p_id = p_id.rsplit('_', 1)[0]
            if origin_p_id not in solutions.keys() \
                and p_id not in self.corrects.keys():
                wrongs.append(p_id)
            elif origin_p_id in solutions.keys() \
                and p_id not in solutions[origin_p_id].keys():
                # continue
                wrongs.append(p_id)
            else:
                samples.append(p_id)
        
        if len(wrongs) > pop_size:
            wrongs = Randoms.sample(wrongs, pop_size)
        if len(samples) > pop_size:
            samples = Randoms.sample(samples, pop_size)
        elif len(samples) < pop_size:
            pop_size -= len(samples)
            if pop_size > len(wrongs): pop_size = len(wrongs)
            samples.extend([p_id for p_id in Randoms.sample(wrongs, pop_size)])
        
        samples = {p_id:population[p_id] for p_id in samples}
        return {p_id:self.nsga_iii(population[p_id], samples) 
                for p_id in tqdm(wrongs, desc="Select", leave=False)}
    
