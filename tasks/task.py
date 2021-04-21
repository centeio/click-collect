import queue

pool = queue.SimpleQueue()
min_pool_size = 5
n_types_task = 3
ids = 0


class Task():
    def __init__(self, task_name, task_type, agent = None, human = None):
        global ids
        self.type = task_type
        self.name = task_name
        self.id = ids
        ids += 1
        self.assigned_by = agent
        self.assigned_to = human
        #TODO
        self.start_time = 0
        self.is_completed = False

    def set_assigned_by(self, agent):
        self.assigned_by = agent

    def set_is_completed(self, is_completed):
        self.is_completed = is_completed

    def assign(self, agent, human):
        self.assigned_by = agent
        self.assigned_to = human

class Task1(Task):
    def __init__(self, agent = None, human = None):
        task_name = "This is Task 1"
        task_type = "task1"

        super().__init__(task_name, task_type, agent, human)

class Task2(Task):
    def __init__(self, agent = None, human = None):
        task_name = "This is Task 2"
        task_type = "task2"
        super().__init__(task_name, task_type, agent, human)

class Task3(Task):
    def __init__(self, agent = None, human = None):
        task_name = "This is Task 3"
        task_type = "task3"
        super().__init__(task_name, task_type, agent, human)