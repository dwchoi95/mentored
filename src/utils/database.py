from tinydb import TinyDB
from tinydb.storages import JSONStorage, MemoryStorage
from tinydb.middlewares import CachingMiddleware

class Database(TinyDB):
    def __init__(self, *args, **kwargs):
        if kwargs.pop('save', True):
            kwargs['indent'] = 2
            kwargs['separators'] = (',', ':')
            kwargs.setdefault('storage', JSONStorage)
        else:
            args = ()
            kwargs.setdefault('storage', CachingMiddleware(MemoryStorage))
        super().__init__(*args, **kwargs)

    def get_data_from_table(self, tablename):
        return {k:v 
                for d in self.table(tablename).all() 
                for k, v in d.items()}

class DBKey:
    problem = 'Problem'
    title = 'Title'
    approach = 'Approach'
    generations = 'Generations'
    populations = 'Populations'
    popsize = 'Population Size'
    max_generation = 'Max Generation'
    trials = 'Trials(#)'
    trial = 'Trial(#)'
    w_progs = 'Wrong Programs'
    c_progs = 'Correct Programs'
    b_sol = 'Best Solutions'
    a_sol = 'AVG Solutions'
    w_sol = 'Worst Solutions'
    b_rr = 'Best RR'
    a_rr = 'AVG RR'
    w_rr = 'Worst RR'
    b_rps = 'Best RPS'
    a_rps = 'AVG RPS'
    w_rps = 'Worst RPS'
    b_att = 'Best ATT(sec)'
    a_att = 'AVG ATT(sec)'
    a_cq = 'AVG CQ'
    w_att = 'Worst ATT(sec)'
    solutions = 'Solutions'
    rr = 'Repair Rate'
    rps = 'rps'
    att = 'AVG Time Taken(sec)'
    quality = 'quality'
