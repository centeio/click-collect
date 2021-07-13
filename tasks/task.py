import queue
import time

pool = queue.SimpleQueue()
min_pool_size = 5
n_types_task = 3
ids = 0
points = 2


class Task():
    def __init__(self, logger_filename, products, difficulty_heuristic, mode):
        global ids
        self.id = ids
        ids += 1

        self.logger_filename = logger_filename
        self.mode = mode

        self.agent = None
        self.human = None

        self.presented_time = None
        self.time_start = None
        self.time_end = None
        self.nr_moves_start = None
        self.nr_moves_end = None

        self.products = products
        self.nr_products = len(products)
        self.difficulty_heuristic = difficulty_heuristic

        self.completed_prod = None
        self.success = None

        self.success_done_score = points * self.nr_products
        self.unsuccess_done_score = 0
        self.give_up_score = -5

        self.score = None
        self.team_score = None

        self.status = None #possible values are None, PRESENTED, ACCEPTED, DISCARDED, GIVEUP, SUCCESSDONE, UNSUCCESSDONE

    def presented(self, agent):
        self.agent = agent
        self.status = "PRESENTED"
        self.presented_time = time.time()
        self.print_task()
        
    def accept(self, nr_moves):
        self.nr_moves_start = nr_moves
        self.status = "ACCEPTED"
        self.time_start = time.time()

        self.print_task()

    def discard(self):
        self.status = "DISCARDED"
        self.time_end = time.time()
        self.team_score = self.success_done_score
        self.print_task()

    def done(self, success, nr_prod, nr_moves):
        self.success = success
        self.completed_prod = nr_prod
        self.nr_moves_ends = nr_moves

        if success:
            self.status = "SUCCESSDONE"
            self.score = self.success_done_score
            self.team_score = self.success_done_score
        else:
            self.status = "UNSUCCESSDONE"
            self.score = self.unsuccess_done_score
            self.team_score = self.unsuccess_done_score
        self.time_end = time.time()
        self.print_task()

    def giveup(self, success, nr_prod, nr_moves):
        self.status = "GIVEUP"
        self.success = success
        self.completed_prod = nr_prod
        self.time_end = time.time()
        self.nr_moves_ends = nr_moves
        self.score = self.give_up_score
        self.team_score = self.give_up_score
        self.print_task()

    def print_task(self):
        logger = open(self.logger_filename, "a")  # append mode
        #"current_time,task,n_prods,min_path,agent,n_moves,presented_time,time_start,time_end,prod_completed,status,success"
        logger.write('{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}\n'.format(time.time(),self.id, self.nr_products, self.agent, \
            self.nr_moves_start, self.nr_moves_end, self.presented_time, self.time_start, self.time_end, \
                self.completed_prod, self.status, self.score, self.success, \
                    self.success_done_score, self.unsuccess_done_score, self.difficulty_heuristic, self.mode, self.team_score))
        logger.close()        
        return None