import numpy as np # type: ignore
import random
import heapq


#from matrx.actions import MoveNorth, OpenDoorAction, CloseDoorAction # type: ignore
#from matrx.actions.move_actions import MoveEast, MoveSouth, MoveWest # type: ignore
from matrx.agents.agent_utils.state import State # type: ignore
from matrx.messages.message import Message # type: ignore
from matrx.agents.agent_brain import AgentBrain
from tasks.task import Task, pool, min_pool_size, n_types_task
from matrx.actions.move_actions import *


i_task = 0

class TaskMaker(AgentBrain):
    """
    Agent that creates new tasks for taskpool
    """
    EUCLIDEAN_METRIC = "euclidean"
    MANHATTAN_METRIC = "manhattan" 

    def __init__(self, logger_name, prod_locations, action_set, metric = MANHATTAN_METRIC):
        super().__init__(memorize_for_ticks=None)
        self.logger_name = logger_name
        self.prod_locations = prod_locations
        if metric == self.EUCLIDEAN_METRIC:
            self.heuristic = lambda p1, p2: np.sqrt(np.sum((np.array(p1) - np.array(p2)) ** 2, axis=0))
        elif metric == self.MANHATTAN_METRIC:
            self.heuristic = lambda p1, p2: np.abs(p1[0] - p2[0]) + np.abs(p1[1] - p2[1])
        else:
            raise Exception(f"The distance metric {metric} for A* heuristic not known.")

        def get_move_actions(action_set):
            """ Returns the names of all move actions in the given agent's action set.

            Parameters
            ----------
            action_set : list
                The names of all actions an agent can perform.

            Returns
            -------
            dict
                The dictionary of all move actions that are part of the agent's actions it can perform. The keys are the action
                names and values are the delta x and y effects on an agent's location.

            """
            move_actions = {}
            for action_name in action_set:
                if action_name == MoveNorth.__name__:
                    move_actions[action_name] = (0, -1)
                elif action_name == MoveNorthEast.__name__:
                    move_actions[action_name] = (1, -1)
                elif action_name == MoveEast.__name__:
                    move_actions[action_name] = (1, 0)
                elif action_name == MoveSouthEast.__name__:
                    move_actions[action_name] = (1, 1)
                elif action_name == MoveSouthWest.__name__:
                    move_actions[action_name] = (-1, 1)
                elif action_name == MoveSouth.__name__:
                    move_actions[action_name] = (0, 1)
                elif action_name == MoveWest.__name__:
                    move_actions[action_name] = (-1, 0)
                elif action_name == MoveNorthWest.__name__:
                    move_actions[action_name] = (-1, -1)

            # And moving nowhere is also possible
            move_actions[None] = (0, 0)

            return move_actions

        self.move_actions = get_move_actions(action_set)
 
    def create_task(self, state):
        global i_task 

        products = self.agent_properties["custom_properties"]["tasks"][i_task]

        occupation_map, obj_grid = self.get_traversability_map(state, inverted=True)

        task_score = 0
        start_point = state[self.agent_id]['location']

        for product in products:
            prod_loc = self.prod_locations[product]
            #occupation_map = state.get_traverse_map()
            route = self.plan(start_point, prod_loc, occupation_map)
            task_score += len(route)
            start_point = prod_loc

        new_task = Task(self.logger_name, products = products, difficulty_heuristic = task_score)

        pool.put(new_task)

        i_task += 1
    
        return None   
    
    #override
    def filter_observations(self, state):
        global pool

        if pool.qsize() < min_pool_size:
            n_new_tasks = min_pool_size - pool.qsize()
            for i in range(n_new_tasks):
                self.create_task(state)
        return state

    def decide_on_action(self, state:State):
        return None, {}


    def get_traversability_map(self, state, inverted=False):
        """ Returns a map where the agent can move to.

        This map is based on the provided state dictionary that might represent the observations of an agent. Since
        these observations can be limited in sense of range and accuracy, the map might not be truthful to what is
        actually possible. This mimics the fact that an agent only knows what it can observe and infer from those
        observations.

        Parameters
        ----------
        inverted : bool (Default: False)
            Whether the map should be inverted (signalling where the agent cannot move to).
        state : dict
            The dictionary representing the agent's (memorized) observations to be used to create the map.

        Returns
        -------
        array
            An array of shape (width,height) equal to the grid world's size. Contains a 1 on each (x,y) coordinate where
            the agent can move to (a 0 when inverted) and a 0 where it cannot move to (a 1 when inverted).
        list
            A list of lists with the width and height of the gird world as size. Contains on each (x,y) coordinate the
            object ID if any according to the provided state dictionary.

        """
        map_size = state['World']['grid_shape']  # (width, height)
        traverse_map = np.array([[int(not inverted) for _ in range(map_size[1])] for _ in range(map_size[0])])
        obj_grid = [[[] for _ in range(map_size[1])] for _ in range(map_size[0])]

        for obj_id, properties in state.items():

            if obj_id == "World":
                continue

            loc = properties['location']

            # we store that there is an object there
            obj_grid[loc[0]][loc[1]].append(obj_id)

            # if another object on that location is intraversable, don't overwrite it
            if (traverse_map[loc[0], loc[1]] == 0 and not inverted) or (traverse_map[loc[0], loc[1]] == 1 and inverted):
                continue

            traverse_map[loc[0], loc[1]] = int(properties['is_traversable']) \
                if not inverted else int(not (properties['is_traversable']))

        return traverse_map, obj_grid




    def plan(self, start, goal, occupation_map):
        """ Plan a route from the start to the goal.

        A* algorithm, returns the shortest path to get from goal to start.
        Uses an 2D numpy array, with 0 being traversable, anything else (e.g. 1) not traversable
        Implementation from:
        https://www.analytics-link.com/single-post/2018/09/14/Applying-the-A-Path-Finding-Algorithm-in-Python-Part-1-2D-square-grid

        Parameters
        ----------
        start : tuple
            The starting (x,y) coordinate.
        goal : tuple
            The goal (x,y) coordinate.
        occupation_map : list
            The list of lists representing which grid coordinates are blocked and which are not.

        Returns
        -------

        """

        # possible movements
        neighbors = list(self.move_actions.values())

        close_set = set()
        came_from = {}
        gscore = {start: 0}
        fscore = {start: self.heuristic(start, goal)}
        #print("fscore", fscore)
        oheap = []

        heapq.heappush(oheap, (fscore[start], start))

        while oheap:
            current = heapq.heappop(oheap)[1]
            #print("current", current)

            if current == goal:
                #print("current == goal")
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                return path[::-1]

            close_set.add(current)
            for i, j in neighbors:
                neighbor = current[0] + i, current[1] + j
                #print("neighbor", neighbor)
                tentative_g_score = gscore[current] + self.heuristic(current, neighbor)
                #print("tentative_g_score", tentative_g_score)
                if 0 <= neighbor[0] < occupation_map.shape[0]:
                    #print("enter for continue 1")
                    if 0 <= neighbor[1] < occupation_map.shape[1]:
                        if occupation_map[neighbor[0]][neighbor[1]] != 0:
                            #print("enter for continue 1.1")
                            continue
                    else:
                        # array bound y walls
                        continue
                else:
                    # array bound x walls
                    continue

                if neighbor in close_set and tentative_g_score >= gscore.get(neighbor, 0):
                    #print("enter for continue 2")

                    continue
                
                #print("passed ifs")
                if tentative_g_score < gscore.get(neighbor, 0) or neighbor not in [i[1] for i in oheap]:
                    came_from[neighbor] = current
                    gscore[neighbor] = tentative_g_score
                    fscore[neighbor] = tentative_g_score + self.heuristic(neighbor, goal)
                    heapq.heappush(oheap, (fscore[neighbor], neighbor))

        # If no path is available we stay put
        return [start]
    