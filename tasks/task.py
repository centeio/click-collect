import queue
import time

pool = queue.SimpleQueue()
min_pool_size = 5
n_types_task = 3
ids = 0
points = 2


class Task():
    def __init__(self, folder_name, logger_filename, products, difficulty_heuristic, mode):
        global ids
        self.id = ids
        ids += 1

        self.folder_name = folder_name
        self.logger_filename = logger_filename
        self.mode = mode

        self.agent = None
        self.human = None

        #self.presented_time = None
        #self.time_start = None
        #self.time_end = None
        #self.nr_moves_start = None
        #self.nr_moves_end = None
        self.nr_moves = None

        self.products = products
        self.nr_products = len(products)
        self.difficulty_heuristic = difficulty_heuristic

        self.completed_prod = None
        self.success = None

        self.success_done_score = 10
        self.unsuccess_done_score = -10
        self.give_up_score = -5

        self.score = None
        self.team_score = None

        self.status = None #possible values are None, PRESENTED, ACCEPTED, DISCARDED, GIVEUP, SUCCESSDONE, UNSUCCESSDONE

    def update(self, agent, nr_moves, success, completed_prod, status):
        self.agent = agent
        self.status = status

        logger = open(self.logger_filename, "a")  # append mode
        #"current_time,task,n_prods,min_path,agent,n_moves,presented_time,time_start,time_end,prod_completed,status,success"
        logger.write('{},{},{},{},{},{},{},{},{},{},{}\n'.format(time.time(), self.folder_name, self.id, agent, \
            nr_moves, self.nr_products, self.difficulty_heuristic, completed_prod, status, success, self.mode))
        logger.close()
