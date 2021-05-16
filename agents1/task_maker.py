import numpy as np # type: ignore
import random

#from matrx.actions import MoveNorth, OpenDoorAction, CloseDoorAction # type: ignore
#from matrx.actions.move_actions import MoveEast, MoveSouth, MoveWest # type: ignore
from matrx.agents.agent_utils.state import State # type: ignore
from matrx.messages.message import Message # type: ignore
from matrx.agents.agent_brain import AgentBrain
from tasks.task import Task1, Task2, Task3, pool, min_pool_size, n_types_task


#from bw4t.BW4TBrain import BW4TBrain

class TaskMaker(AgentBrain):
    """
    Agent that creates new tasks for taskpool
    """
    def __init__(self):
        super().__init__(memorize_for_ticks=None)
        random.seed(10)
        for i in range(5):
            self.create_task()
 
    def create_task(self):
        n = random.randint(0,n_types_task-1)
        if n == 0:
            new_task = Task1()

        elif n == 1:
            new_task = Task2()

        elif n == 2:
            new_task = Task3()

        else:
            print("Couldn't recognize option! - Task maker ", n)
            return None   


        pool.put(new_task)
    
        return None   
    
    #override
    def filter_observations(self, state):
        global pool
        if pool.qsize() < min_pool_size:
            n_new_tasks = min_pool_size - pool.qsize()
            for i in range(n_new_tasks):
                self.create_task()
        return state

    def decide_on_action(self, state:State):
        return None, {}


    #Override
    #def decide_on_action(self, state:State):
    #    '''
    #    Final . Agents must override decide_on_bw4t_action instead
    #    '''
    #    act,params = self.decide_on_bw4t_action(state)
    #    wrong = self.NOT_ALLOWED_PARAMS.intersection(set(params.keys()))
    #    if len(wrong) > 0:
    #        raise ValueError("Parameter use not allowed ", wrong)
    #    params['grab_range']=1
    #    # door_range=1 does not work, doors don't open
    #    #params['door_range']=1
    #    params['max_objects']=3
    #    params['action_duration'] = self.__slowdown
    #    return act,params
    