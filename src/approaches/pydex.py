from tqdm import tqdm
from functools import cache
from scipy.spatial.distance import hamming
import time
import openai
openai.api_key = open('openai.key').read().strip()

from ..utils import Log, Database, Randoms
from ..execution import Tester, UnitTestStatus

prog_prompt = """
[[Buggy Program Starts]]
### Buggy Program ###
{buggy_program}
[[Buggy Program Ends]]

### Correct Program ###
""".strip()

prog_test_prompt = """
[[Buggy Program Starts]]
### Buggy Program ###
{buggy_program}
[[Buggy Program Ends]]

[[Test Suite Starts]]
{testsuite}
[[Test Suite Ends]]

### Correct Program ###
""".strip()

prog_shot_prompt = """
[[Shot Starts]]
# Incorrect Program #
{incorrect_program}
# Correct Program #
{correct_program}
[Shot Ends]

[[Buggy Program Starts]]
### Buggy Program ###
{buggy_program}
[[Buggy Program Ends]]

### Correct Program ###
""".strip()

prog_test_shot_prompt = """
[[Shot Starts]]
# Incorrect Program #
{incorrect_program}
# Correct Program #
{correct_program}
[Shot Ends]

[[Buggy Program Starts]]
### Buggy Program ###
{buggy_program}
[[Buggy Program Ends]]

[[Test Suite Starts]]
{testsuite}
[[Test Suite Ends]]

### Correct Program ###
""".strip()


class PYDEX:
    def __init__(self,
                 database:Database,
                 wrongs:dict,
                 corrects:dict={},
                 model:str="gpt-3.5-turbo", 
                 temperature:float=0.8):
        self.wrongs = self.__preproc(wrongs)
        self.corrects = self.__preproc(corrects)
        self.model = model
        self.temperature = temperature
        self.log = Log(database)
        self.peers = list(self.corrects.items()) if self.corrects else list(self.wrongs.items())
    
    def __preproc(self, programs:dict) -> dict:
        return {f'{p_id}_0':code for p_id, code in programs.items()}
    
    @cache
    def __choose_refer(self, wrong_id:str, wrong_program:str) -> str:
        w_test_hist = Tester.validation(wrong_program)
        w_test_values = [1 if UnitTestStatus.success == status 
                        else 0 for status in w_test_hist.values()]
    
        max_sim = 0
        refer_id, refer_program = Randoms.choice(self.peers)
        for (peer_id, peer_program) in self.peers:
            if peer_id == wrong_id: continue
            r_test_hist = Tester.validation(peer_program)
            r_test_values = [1 if UnitTestStatus.success == status 
                            else 0 for status in r_test_hist.values()]
            
            similarity = 1 - hamming(w_test_values, r_test_values)
            
            if similarity > max_sim:
                max_sim = similarity
                refer_program = peer_program
                refer_id = peer_id
        return refer_id, refer_program

    def __patch_generation(self, content:str) -> str:
        try:
            response = openai.chat.completions.create(
                model=self.model, 
                messages=[{
                    "role": "user", 
                    "content": content
                }],
                temperature=self.temperature,
            )
            patch = response.choices[0].message.content
            # Post-process the patch
            if patch and patch.startswith("```python\n"):
                patch = patch[10:-3]
            return patch
        except Exception as e:
            pass
            # print(e)
            # print(content)
        return None
    
    def run(self, generations:int=10):
        for generation in tqdm(range(1, generations*3+1, 3), desc="PyDex", leave=False):
            for wrong_id, buggy_program in tqdm(self.wrongs.items(), 
                                            total=len(self.wrongs), 
                                            desc="wrongs", 
                                            leave=False):
                
                # Choose a correct program as a reference
                refer_id, refer_program = self.__choose_refer(wrong_id, buggy_program)

                # Generate patches with 3 different prompts
                for i, prompt in enumerate([prog_prompt, 
                                            prog_test_prompt, 
                                            prog_test_shot_prompt]):
                    content = prompt.format(
                        incorrect_program=buggy_program,
                        correct_program=refer_program,
                        buggy_program=buggy_program, 
                        testsuite=str(Tester.testsuite))
                    
                    gen_no = generation + i
                    origin_w_id = wrong_id.rsplit('_', 1)[0]
                    patch_id = f'{origin_w_id}_{gen_no}'
                    patch = self.__patch_generation(content)
                    
                    self.log.insert({'generation':gen_no})
                    self.log.update({'wrong_id':wrong_id, 'refer_id':refer_id})
                    self.log.update({'wrong_code':buggy_program, 'refer_code':refer_program})
                    self.log.update({'content':content})
                    self.log.update({'patch_id':patch_id})
                    self.log.update({'patch':patch})
                    self.log.update({'solution':False})

                    if patch:
                        try:
                            # Check the patch is solution
                            origin_w_id = wrong_id.rsplit("_", 1)[0]
                            p_test_hist = Tester.validation(patch)
                            if Tester.is_all_pass(p_test_hist):
                                self.log.update({'solution':True})
                        except: pass
