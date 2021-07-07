import numpy as np # type: ignore
import random

#from matrx.actions import MoveNorth, OpenDoorAction, CloseDoorAction # type: ignore
#from matrx.actions.move_actions import MoveEast, MoveSouth, MoveWest # type: ignore
from matrx.agents.agent_utils.state import State # type: ignore
from matrx.messages.message import Message # type: ignore
from matrx.agents.agent_brain import AgentBrain
from tasks.task import Task, pool, min_pool_size, n_types_task

i_task = 0



class TaskMaker(AgentBrain):
    """
    Agent that creates new tasks for taskpool
    """
    def __init__(self):
        super().__init__(memorize_for_ticks=None)

 
    def create_task(self):
        global i_task 

        new_task = Task(products = self.agent_properties["custom_properties"]["tasks"][i_task])

        pool.put(new_task)

        i_task += 1
    
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
    