import numpy as np # type: ignore
import random

from matrx.agents.agent_types.patrolling_agent import PatrollingAgentBrain # type: ignore
from matrx.actions import MoveNorth, OpenDoorAction, CloseDoorAction # type: ignore
from matrx.actions.move_actions import MoveEast, MoveSouth, MoveWest # type: ignore
from matrx.agents.agent_utils.state import State # type: ignore
from matrx.messages.message import Message # type: ignore
from matrx.agents.agent_brain import AgentBrain
from tasks.task import Task, pool


#from bw4t.BW4TBrain import BW4TBrain

HELLO="Hello I'm "
WELCOME="Welcome "

DONE = "done"
GIVEUP = "give up"
ACCEPT = "accept"

max_tasks = 1

class ShopAssist(AgentBrain):
    """
    Agent that broadcasts "hello I'm "+ID message to the other agents,
    and replies 'welcome '+ID to all received messages.
    It checks that received welcomes are indeed using my own ID
    """
    def __init__(self):
        super().__init__(memorize_for_ticks=None)
        self._sentMessage=False
        self.tasks_required = {}
        self.tasks_assigned = {}
        self.tasks_completed = {}
        self.tasks_failed = {}
    
    
    #override
    def filter_observations(self, state):

        if not self._sentMessage:
            #broadcast
            self.send_message(Message(HELLO+self.agent_id, from_id=self.agent_id ))
            self._sentMessage=True

        # TODO automatically check whether task completed
        #for task in self.tasks_assigned:
        #    if task.is_completed():
        #        end_task_msg = "Thank you, " + str(task.assigned_to) + ", for completing the task " + task.id
        #        print(end_task_msg)
        #        self.send_message(Message(end_task_msg, from_id=self.agent_id, to_id=task.assigned_to))

        # check whether human wants a task
        for msg in self.received_messages:

            print("agent",self.agent_id,"received message:",msg)

            if msg.startswith(ACCEPT):
                request = msg.split()
                print(request)
                task_id = int(request[1])
                if task_id in self.tasks_required.keys():
                    self.tasks_required[task_id].assign(agent = self.agent_id, human = "h1")
                    self.tasks_assigned[task_id] = self.tasks_required[task_id]
                    del self.tasks_required[task_id]

            elif msg.startswith(DONE):
                request = msg.split()
                task_id = int(request[1])
                if task_id in self.tasks_assigned.keys():
                    self.tasks_assigned[task_id].set_is_completed(True)
                    self.tasks_completed[task_id] = self.tasks_assigned[task_id]
                    del self.tasks_assigned[task_id]

            elif msg.startswith(GIVEUP):
                request = msg.split()
                task_id = int(request[2])
                if task_id in self.tasks_assigned.keys():
                    self.tasks_failed[task_id] = self.tasks_assigned[task_id]
                    del self.tasks_assigned[task_id]

            else:
                print("Received not-understood message"+msg)


        # choose task
        if len(self.tasks_required) < max_tasks:
            #TODO
            global pool
            if not pool.empty():
                new_task = pool.get()
                new_task_msg = "New task: " + new_task.name + ", Id: " + str(new_task.id)
                print(new_task_msg)
                self.send_message(Message(new_task_msg, from_id=self.agent_id))
                self.tasks_required[new_task.id] = new_task
            else:
                print("pool empty")
            
        #for msg in self.received_messages:
        #    print("agent",self.agent_id,"received message:",msg)
        #    if msg.startswith(HELLO):
        #        id = msg[len(HELLO):]
        #        self.send_message(Message(WELCOME+id, from_id=self.agent_id, to_id=id))
        #    elif msg.startswith(WELCOME):
        #        id = msg[len(WELCOME):]
        #        if not id==self.agent_id:
        #            print("Received welcome for someone else?!")
        #    else:
        #        print("Received not-understood message"+msg)

        #bug workaround
        self.received_messages=[]        
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
    