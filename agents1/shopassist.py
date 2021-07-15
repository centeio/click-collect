import numpy as np # type: ignore
import random

from matrx.actions import Action, ActionResult, MoveNorth, OpenDoorAction, CloseDoorAction # type: ignore
from matrx.actions.move_actions import MoveEast, MoveSouth, MoveWest # type: ignore
from matrx.agents.agent_utils.state import State # type: ignore
from matrx.messages.message import Message # type: ignore
from matrx.agents.agent_brain import AgentBrain
from matrx.objects import EnvObject, env_object # type: ignore

from tasks.task import pool
from world1.objects import GhostProduct, CollectableProduct

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
    def __init__(self,name,drop_zone_nr,drop_zone_size,friendly_writing):
        super().__init__(memorize_for_ticks=None)
        self.id = name
        self.drop_zone_nr = drop_zone_nr
        self.drop_zone_size = drop_zone_size
        self.task_required = None
        self.new_task = False
        self.update_human_score = None
        self.update_team_score = None
        self.friendly_writing = friendly_writing
        self.welcome = False
        self.human_todo = "choose"
    
    #override
    def filter_observations(self, state):
        global unsucess_done_points, sucess_done_points
        self.update_human_score = None
        send_msg = None
        human = state.get_agents_with_property({'name': 'human'})[0]

        for msg in self.received_messages:

            print("agent",self.agent_id,"received message:",msg)

            if self.task_required != None:

                if self.task_required.status == "PRESENTED":

                    if msg.startswith(ACCEPT):
                        request = msg.split()
                        agent_id = request[1]
                        success, nr_prod = self.check_success(state)

                        if agent_id == self.id:
                            self.task_required.update(self.id, human['nr_moves'], success=success, completed_prod=nr_prod, status="ACCEPTED")

                            if self.friendly_writing:
                                send_msg = "Thanks!"
                        else:
                            self.update_team_score = human['team_score'] + self.task_required.success_done_score
                            self.human_todo = "finish"
                            self.task_required.update(self.id, human['nr_moves'], success=success, completed_prod=nr_prod, status="DISCARDED")
                            self.task_required = None
                
                elif self.task_required.status == "ACCEPTED":

                    if msg.startswith(DONE):
                        success, nr_prod = self.check_success(state)
                        if success:
                            self.update_human_score = human['score'] + self.task_required.success_done_score
                            self.update_team_score = human['team_score'] + self.task_required.success_done_score
                        else:
                            #self.update_human_score = human['score'] + self.task_required.unsuccess_done_score
                            self.update_team_score = human['team_score'] + self.task_required.unsuccess_done_score
                        self.task_required.update(self.id, human['nr_moves'], success=success, completed_prod=nr_prod, status="DONE")
                        self.task_required = None
                        if self.friendly_writing:
                            send_msg = "Great job!"

                    elif msg.startswith(GIVEUP):
                        success, nr_prod = self.check_success(state)
                        self.update_human_score = human['score'] + self.task_required.give_up_score
                        self.update_team_score = human['team_score'] + self.task_required.give_up_score
                        self.task_required.update(self.id, human['nr_moves'], success=success, completed_prod=nr_prod, status="GIVEUP")
                        self.task_required = None
                        if self.friendly_writing:
                            send_msg = "No problem!"
                    
                    self.human_todo = "choose"

            if send_msg != None:
                self.send_message(Message(send_msg, from_id=self.agent_id))
            


        # present task
        if self.task_required == None:
            global pool

            if not pool.empty():
                self.task_required = pool.get()
                #self.task_required.presented(self.id)
                self.task_required.update(self.id, human['nr_moves'], success=False, completed_prod=0, status="PRESENTED")
               # self.p_i = 0
                self.new_task = True
            else:
                print("pool empty")

        self.received_messages=[]        
        return state


    def decide_on_action(self, state:State):
        action = None
        action_kwargs = {}
        replace_objects = []
        remove_objects = []
        add_objects = []

        if self.welcome == False:

            if self.friendly_writing == True:
                new_task_msg = "Hi buddy! I'm glad we will be working together again today!"
            else:
                new_task_msg = "Hi there"

            self.send_message(Message(new_task_msg, from_id=self.agent_id))
            self.welcome = True

        if self.new_task == True:
            action = ReplaceProduct.__name__
            loc_x, loc_y = state[self.agent_id]['location']

            dropped_found = state.get_with_property({'is_collectable': True})
            if dropped_found != None:
                #print("::::::::: DROPPED FOUND ::::::::", dropped_found)
                replace_objects += dropped_found

            for i in range(self.drop_zone_size): 
                p_loc = (loc_x + i - 1, loc_y + 1)

                previous_objs = state.get_with_property({'is_collectable': False, 'location': p_loc})
                if previous_objs != None:
                    #print("::::::::: PREVIOUS TAKS OBJS ::::::::", previous_objs)
                    remove_objects += [previous_objs[0]]

            for i in range(len(self.task_required.products)):
                p_loc = (loc_x + i - 1, loc_y + 1)
                obj_kwargs = {}

                obj_kwargs['location'] = p_loc
                obj_kwargs['img'] = self.task_required.products[i]
                obj_kwargs['drop_zone_nr'] = self.drop_zone_nr

                add_objects += [obj_kwargs]

            if self.friendly_writing == True:
                new_task_msg = "I have a new task. Can you help please?"
            else:
                new_task_msg = "New task!"
            self.send_message(Message(new_task_msg, from_id=self.agent_id))
            #TODO check if we need to put messages together!
            self.new_task = False

        action_kwargs["remove_objects"] = remove_objects
        action_kwargs["replace_objects"] = replace_objects
        action_kwargs["add_objects"] = add_objects
        action_kwargs["human_id"] = state.get_agents_with_property({'name': 'human'})[0]['obj_id']
        action_kwargs['update_human_score'] = self.update_human_score
        action_kwargs['update_team_score'] = self.update_team_score
        action_kwargs['todo'] = self.human_todo

        self.human_todo = None

        return action, action_kwargs



    def check_success(self, state:State):
        n_prod = len(self.task_required.products)
        loc_x, loc_y = state[self.agent_id]['location']

        score = 0
        check = False

        for i in range(n_prod):
            p_loc = (loc_x + i - 1, loc_y + 1)
            goal_found = state.get_with_property({'name': "Collect Product", 'location': p_loc}) 
            dropped_found = state.get_with_property({'is_collectable': True, 'location': p_loc})
            if goal_found != None and dropped_found != None:
                if goal_found[0]['img_name'] == dropped_found[0]['img_name']:
                    score += 1

        if score == n_prod:
            check = True

        return (check, score)

class ReplaceProduct(Action):
    """ An action that can add a product to the gridworld """

    def __init__(self, duration_in_ticks=0):
        super().__init__(duration_in_ticks)

    def is_possible(self, grid_world, agent_id, **kwargs):

        # check that we have all variables
        #if 'brain_args' not in kwargs:
        #    return AddObjectResult(AddObjectResult.NO_AGENTBRAIN, False)

        #if 'body_args' not in kwargs:
        #    return AddObjectResult(AddObjectResult.NO_AGENTBODY, False)

        # success
        return ReplaceProductResult(ReplaceProductResult.ACTION_SUCCEEDED, True)


    def mutate(self, grid_world, agent_id, **kwargs):
        # update human's score
        if kwargs['update_human_score'] != None:
            human = grid_world.registered_agents[kwargs['human_id']]
            human.change_property('score', kwargs['update_human_score'])

        if kwargs['update_team_score'] != None:
            human = grid_world.registered_agents[kwargs['human_id']]
            human.change_property('team_score', kwargs['update_team_score'])

        if kwargs['todo'] != None:
            human = grid_world.registered_agents[kwargs['human_id']]
            human.change_property('todo', kwargs['todo'])

        for i_rep in range(len(kwargs['replace_objects'])):

            obj = kwargs['replace_objects'][i_rep]
            if obj['location'] != obj['init_loc']:
                obj2 =  grid_world.environment_objects[obj['obj_id']]
                grid_world.remove_from_grid(object_id=obj['obj_id'])
                props = obj2.change_property('location',obj['init_loc'])
                print(props)
                grid_world._register_env_object(obj2)

        for i_rem in range(len(kwargs['remove_objects'])):

            grid_world.remove_from_grid(kwargs['remove_objects'][i_rem]['obj_id'])


        for i_add in range(len(kwargs['add_objects'])):

            obj_body_args = {
                "location": kwargs['add_objects'][i_add]['location'],
                "name": "Collect Product",
                #"class_callable": GhostBlock,
                "drop_zone_nr": kwargs['add_objects'][i_add]['drop_zone_nr'],
                "img_name": kwargs['add_objects'][i_add]['img']
            }

            env_object = GhostProduct(**obj_body_args)

            grid_world._register_env_object(env_object)


        return ReplaceProductResult(ReplaceProductResult.ACTION_SUCCEEDED, True)


class ReplaceProductResult(ActionResult):
    """ Result when assignment failed """
    # failed
    NO_AGENTBRAIN = "No object passed under the `agentbrain` key in kwargs"
    NO_AGENTBODY = "No object passed under the `agentbody` key in kwargs"
    # success
    ACTION_SUCCEEDED = "Object was succesfully added to the gridworld."

    def __init__(self, result, succeeded):
        super().__init__(result, succeeded)
