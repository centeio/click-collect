import numpy as np # type: ignore
import random

from matrx.actions import Action, ActionResult, MoveNorth, OpenDoorAction, CloseDoorAction # type: ignore
from matrx.actions.move_actions import MoveEast, MoveSouth, MoveWest # type: ignore
from matrx.agents.agent_utils.state import State # type: ignore
from matrx.messages.message import Message # type: ignore
from matrx.agents.agent_brain import AgentBrain
from tasks.task import Task, pool
from matrx.objects import EnvObject, env_object # type: ignore


#from bw4t.BW4TBrain import BW4TBrain

HELLO="Hello I'm "
WELCOME="Welcome "

DONE = "done"
GIVEUP = "give up"
ACCEPT = "accept"

max_tasks = 1

i = 0

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
        action = None
        action_kwargs = {}
        global i
        if i == 100:
            if self.agent_name == "shopassist1":
                print("trying to add product !!!!!!!!!!!!")
                action = AddProduct.__name__
                i += 1
        else:
            i += 1
        return action, action_kwargs


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

    
class GhostBlock(EnvObject):
    def __init__(self, location, drop_zone_nr, name, visualize_colour, visualize_shape):
        super().__init__(location, name, is_traversable=True, is_movable=False,
                         visualize_colour=visualize_colour, visualize_shape=visualize_shape,
                         visualize_size=0.5, class_callable=GhostBlock,
                         visualize_depth=85, drop_zone_nr=drop_zone_nr, visualize_opacity=0.5,
                         is_drop_zone=False, is_goal_block=True, is_collectable=False)

class AddProduct(Action):
    """ An action that can add a patient agent to the gridworld """

    def __init__(self, duration_in_ticks=0):
        super().__init__(duration_in_ticks)

    def is_possible(self, grid_world, agent_id, **kwargs):

        # check that we have all variables
        #if 'brain_args' not in kwargs:
        #    return AddObjectResult(AddObjectResult.NO_AGENTBRAIN, False)

        #if 'body_args' not in kwargs:
        #    return AddObjectResult(AddObjectResult.NO_AGENTBODY, False)

        # success
        return AddObjectResult(AddObjectResult.ACTION_SUCCEEDED, True)


    def mutate(self, grid_world, agent_id, **kwargs):
        # create the agent brain
        # agentbrain = GhostBlock(**kwargs['brain_args'])

        # these properties can't be sent via the kwargs because the API can't JSON serialize these objects and would
        # throw an error

        loc = [24,10]
        #obj_body_args = {
        #    "sense_capability": SenseCapability({"*": np.inf}),
        #    "class_callable": PatientAgent,
        #    "callback_agent_get_action": agentbrain._get_action,
        #    "callback_agent_set_action_result": agentbrain._set_action_result,
        #    "callback_agent_observe": agentbrain._fetch_state,
        #    "callback_agent_log": agentbrain._get_log_data,
        #    "callback_agent_get_messages": agentbrain._get_messages,
        #    "callback_agent_set_messages": agentbrain._set_messages,
        #    "callback_agent_initialize": agentbrain.initialize,
        #    "callback_create_context_menu_for_other": agentbrain.create_context_menu_for_other
        #}

        obj_body_args = {
            "location": loc,
            "name": "Collect Block",
            #"class_callable": GhostBlock,
            "visualize_colour": '#332288',
            "visualize_shape": 0,
            "drop_zone_nr": 1
        }

        # merge the two sets of agent body properties
        #body_args = dict(kwargs['body_args'])
        #body_args.update(obj_body_args)

        # create the agent_body
        #env_object = grid_world.__create_env_object(obj_body_args)
        env_object = GhostBlock(**obj_body_args)

        # register the new object
        grid_world._register_env_object(env_object)

        return AddObjectResult(AddObjectResult.ACTION_SUCCEEDED, True)


class AddObjectResult(ActionResult):
    """ Result when assignment failed """
    # failed
    NO_AGENTBRAIN = "No object passed under the `agentbrain` key in kwargs"
    NO_AGENTBODY = "No object passed under the `agentbody` key in kwargs"
    # success
    ACTION_SUCCEEDED = "Object was succesfully added to the gridworld."

    def __init__(self, result, succeeded):
        super().__init__(result, succeeded)

