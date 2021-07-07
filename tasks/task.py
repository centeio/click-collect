import queue
import time

pool = queue.SimpleQueue()
min_pool_size = 5
n_types_task = 3
ids = 0
points = 2
nr_clicks = 0

class Task():
    def __init__(self, products):
        global ids
        self.id = ids
        ids += 1
        self.agent = None
        self.human = None

        self.presented_time = None
        self.time_start = None
        self.time_end = None
        self.nr_clicks_start = 0
        self.nr_clicks_start = 0

        self.products = products
        self.nr_products = len(products)
        self.max_score = points * self.nr_products

        self.completed_prod = 0
        self.success = False

        self.status = None #possible values are None, PRESENTED, ACCEPTED, DISCARDED, GIVEUP, SUCCESSDONE, UNSUCCESSDONE

    def presented(self, agent):
        self.agent = agent
        self.status = "PRESENTED"
        self.presented_time = time.time()
        self.print_task()
        
    def accept(self):
        global nr_clicks
        self.status = "ACCEPTED"
        self.time_start = time.time()
        nr_clicks = 0
        self.print_task()

    def discard(self):
        self.status = "DISCARDED"
        self.time_end = time.time()
        self.print_task()

    def done(self, success, score):
        self.success = success
        if success:
            self.status = "SUCCESSDONE"
        else:
            self.status = "UNSUCCESSDONE"
        self.time_end = time.time()
        self.print_task()

    def giveup(self, success, score):
        self.status = "GIVEUP"
        self.success = success
        self.completed_prod = score
        self.time_end = time.time()
        self.print_task()

    def print_task(self):
        #TODO log task
        return None