import numpy as np # type: ignore
import random

from matrx.agents.agent_types.patrolling_agent import PatrollingAgentBrain # type: ignore
from matrx.actions import MoveNorth, OpenDoorAction, CloseDoorAction # type: ignore
from matrx.actions.move_actions import MoveEast, MoveSouth, MoveWest # type: ignore
from matrx.agents.agent_utils.state import State # type: ignore
from matrx.messages.message import Message # type: ignore
from matrx.agents.agent_brain import AgentBrain


#from bw4t.BW4TBrain import BW4TBrain

HELLO="Hello I'm "
WELCOME="Welcome "

class ShopAssist(AgentBrain):
    """
    Agent that broadcasts "hello I'm "+ID message to the other agents,
    and replies 'welcome '+ID to all received messages.
    It checks that received welcomes are indeed using my own ID
    """
    def __init__(self, slowdown:int = 1):
        super().__init__(slowdown)
        self._sentMessage=False
    
    
    #override
    def filter_observations(self, state):
        if not self._sentMessage:
            #broadcast
            self.send_message(Message(HELLO+self.agent_id, from_id=self.agent_id ))
            self._sentMessage=True
            
        for msg in self.received_messages:
            print("agent",self.agent_id,"received message:",msg)
            if msg.startswith(HELLO):
                id = msg[len(HELLO):]
                self.send_message(Message(WELCOME+id, from_id=self.agent_id, to_id=id))
            elif msg.startswith(WELCOME):
                id = msg[len(WELCOME):]
                if not id==self.agent_id:
                    print("Received welcome for someone else?!")
            else:
                print("Received not-understood message"+msg)
        #bug workaround
        self.received_messages=[]        
        return state

    def decide_on_action(self, state:State):
        return None,{}

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
    