import os, requests, sys
import numpy as np
import time
from datetime import datetime

from matrx.agents import PatrollingAgentBrain, HumanAgentBrain
from matrx.world_builder import WorldBuilder
from matrx.actions import *
from matrx.agents import AgentBrain, SenseCapability # type: ignore
from matrx.grid_world import GridWorld, DropObject, GrabObject, AgentBody # type: ignore
from matrx.objects import EnvObject # type: ignore
from matrx.world_builder import RandomProperty # type: ignore
from matrx.goals import WorldGoal # type: ignore
from matrx.utils import get_room_locations

from agents1.shopassist import ShopAssist
from agents1.task_maker import TaskMaker
from agents1.human import Human
from world1.objects import GhostProduct, CollectableProduct
from supermarket_gui import visualization_server


script_dir = os.path.dirname(__file__)

room_colors = ['#332288', '#117733', '#44AA99', '#88CCEE', '#DDCC77', '#CC6677', '#AA4499', '#882255', "#44AA99"]
room_themes = ['bread', 'carbs', 'vegetables', 'fishmeat', 'fruit', 'household', 'icecream', 'sweets', 'drinks']
wall_color = "#CC6677"
drop_off_color = "#878787"

room_size = (6, 4)  # width, height
nr_rooms = 9
rooms_per_row = 3
average_blocks_per_room = 5
block_shapes = [0, 1, 2]
block_colors = ['#332288', '#117733', '#44AA99', '#88CCEE', '#DDCC77', '#CC6677', '#AA4499', '#882255']
block_size = 0.5
#nr_drop_zones = 1
#nr_blocks_needed = 3
hallway_space = 2 # width, height of corridors
drop_zone_size = 5

agent_locations = [(25,9),(25,19)]

agent_sense_range = 2  # the range with which agents detect other agents
block_sense_range = 2  # the range with which agents detect blocks
other_sense_range = np.inf  # the range with which agents detect other objects (walls, doors, etc.)
agent_memory_decay = 5  # we want to memorize states for seconds / tick_duration ticks
fov_occlusion = True

deadline = 2000 # Ticks after which world terminates anyway 



def add_aisles(builder):
    room_locations = {}
    w=16
    h=4
    locs = {0: (4,2), 1: (4,6), 2: (4,10), 
            3: (4,14), 4: (4,18), 5: (4,22),
            6: (4,26), 7: (1,2), 8:(1,17)}
    for room_nr in range(7):
        room_top_left_x, room_top_left_y = locs[room_nr]

        # We assign a simple random color to each room. Not for any particular reason except to brighting up the place.
        wall_color = room_colors[room_nr]

        door_locs = [(room_top_left_x, room_top_left_y),(room_top_left_x, room_top_left_y+1),
            (room_top_left_x, room_top_left_y+2),(room_top_left_x, room_top_left_y+3),
            (room_top_left_x+w-1, room_top_left_y),(room_top_left_x+w-1, room_top_left_y+1),
            (room_top_left_x+w-1, room_top_left_y+2),(room_top_left_x+w-1, room_top_left_y+3)]

        # Add the room
        room_name = f"room_{room_nr}"
        builder.add_room(top_left_location= (room_top_left_x, room_top_left_y), width=w, height=h, name=room_name,
                         door_locations=door_locs, doors_open = True,  door_visualization_opacity=0.0,
                         wall_visualize_colour=wall_color,
                         with_area_tiles=True,
                         wall_visualize_opacity=1.0, area_visualize_opacity=0.0)

        # Find all inner room locations where we allow objects (making sure that the location behind to door is free)
        room_locations[room_name] = get_room_locations((room_top_left_x, room_top_left_y), w, h)

    w2 = 3
    h2 = 13

    for room_nr in range(2):
        room_nr += 7
        room_top_left_x, room_top_left_y = locs[room_nr]
        

        # We assign a simple random color to each room. Not for any particular reason except to brighting up the place.
        wall_color = room_colors[room_nr]

        door_locs = [(room_top_left_x+1, room_top_left_y),(room_top_left_x+1, room_top_left_y+h2-1)]

        for d in range(h2):
            door_locs += [(room_top_left_x+2, room_top_left_y+d)]

        # Add the room
        room_name = f"room_{room_nr}"
        builder.add_room(top_left_location= (room_top_left_x, room_top_left_y), width=w2, height=h2, name=room_name,
                         door_locations=door_locs, doors_open = True, door_visualization_opacity=0.0,
                         wall_visualize_colour=wall_color,
                         with_area_tiles=True,
                         wall_visualize_opacity=1.0, area_visualize_opacity=0.0)

        # Find all inner room locations where we allow objects (making sure that the location behind to door is free)
        room_locations[room_name] = get_room_locations((room_top_left_x, room_top_left_y), w2, h2)
    
    return room_locations


def add_dropoffs2(builder):
    builder.add_area(top_left_location=[24,10], width=4, height=1, wall_visualize_colour=wall_color, name="x",
        visualize_colour='#88CCEE', visualize_opacity=1.0, drop_zone_nr=1)
    builder.add_area(top_left_location=[24, 20], width=4, height=1, wall_visualize_colour=wall_color, name="z", 
        visualize_colour='#88CCEE', visualize_opacity=1.0, drop_zone_nr=2)


def add_products(builder, room_locations):
    room_nr = 0
    prod_locations = {}

    

    for room_name, locations in room_locations.items():
        theme = room_themes[room_nr]
        images_path = os.listdir(os.path.abspath(os.path.join(script_dir, "media/images/" + theme)))

        min_i = min(len(images_path), len(locations))

        np.random.shuffle(images_path)
        np.random.shuffle(locations)

        for i in range(min_i):

            loc = locations[i]
            image = "/images/" + theme + "/" + images_path[i]

            prod_locations[image] = loc
        
            # Get the block's name
            name = f"Object {theme} in {room_name}"

            # Get the probability for adding a block so we get the on average the requested number of blocks per room

            builder.add_object(loc, name, callable_class=CollectableProduct, img_name=image)

        room_nr += 1

    return prod_locations


def add_agents(builder,mode):
    '''
    Add bots as specified. All bots have the same sense_capability.
    '''
    sense_capability = SenseCapability({None: 50})
    # TODO update seed ?
    np.random.shuffle(agent_locations)

    #TODO same color agent and human
    if mode == "benevolence":
        agent_x_img = "/images/smile_glasses_ben.png"
        friendly_writing = True
    else:
        agent_x_img = "/images/smile_glasses.png"
        friendly_writing = False



    builder.add_agent(agent_locations[0], ShopAssist(name="x",drop_zone_nr=1, drop_zone_size = drop_zone_size, friendly_writing = friendly_writing), name="Agent X",
#                sense_capability=sense_capability)
            sense_capability=sense_capability, img_name=agent_x_img)
    builder.add_object([agent_locations[0][0]+2,agent_locations[0][1]],'agent_id_x',EnvObject,is_traversable=True,is_movable=False,visualize_shape='img',img_name="/images/x.png")

    builder.add_agent(agent_locations[1], ShopAssist(name="z",drop_zone_nr=2, drop_zone_size = drop_zone_size, friendly_writing = False), name="Agent Z", 
#                sense_capability=sense_capability)
            sense_capability=sense_capability, img_name="/images/smile_glasses.png")
    builder.add_object([agent_locations[1][0]+2,agent_locations[1][1]],'agent_id_z',EnvObject,is_traversable=True,is_movable=False,visualize_shape='img',img_name="/images/z.png")




def create_tasks(builder, folder_name, prod_locations):
    sense_capability = SenseCapability({None: 50})

    f = open(folder_name + "/" + "tasks.txt", "w")
    f2 = open(folder_name + "/" + "products.txt", "w")
    logger_name = folder_name + "/" + "logger.csv"
    logger = open(logger_name,"w")

    logger.write("current_time,folder_name,task_id,agent,nr_moves,nr_products,difficulty_heuristic,nr_completed_prod,status,is_success,mode\n")
    logger.close() 

    world_products = [x['custom_properties']['img_name'] for x in builder.object_settings if x['callable_class'] == CollectableProduct ]

    f2.write(str(world_products))
    f2.close()

    tasks = []

    for i in range(100):
        n_items = np.random.choice(list(range(4))) + 1
        products = np.random.choice(world_products,n_items).tolist()
        tasks += [products]
        msg = str(products) + "\n"
        f.write(msg)
    
    f.close()

    loc = [26,15]

    possible_actions = [MoveNorth.__name__, MoveEast.__name__, MoveSouth.__name__, MoveWest.__name__]

    builder.add_agent(loc, TaskMaker(folder_name, logger_name, prod_locations, action_set = possible_actions, mode=mode), is_traversable=True, team="team_name", name = "taskmaker1", sense_capability=sense_capability, 
                visualize_opacity=0.0, custom_properties = {"tasks": tasks})


    print("FINISHED CREATING TASK MAKER")


class CollectionGoal(WorldGoal):

    def __init__(self, max_nr_ticks:int):
        '''
        @param max_nr_ticks the max number of ticks to be used for this task
        '''
        super().__init__()
        self.max_nr_ticks = max_nr_ticks

        # A dictionary of all drop locations. The keys is the drop zone number, the value another dict.
        # This dictionary contains as key the rank of the to be collected object and as value the location
        # of where it should be dropped, the shape and colour of the block, and the tick number the correct
        # block was delivered. The rank and tick number is there so we can check if objects are dropped in
        # the right order.
        self.__drop_off:dict = None

        # We also track the progress
        self.__progress = 0

    #override
    def goal_reached(self, grid_world: GridWorld):
        if grid_world.current_nr_ticks >= self.max_nr_ticks:
            return True
        return False

    # def __check_completion(self, grid_world):


def create_builder(folder_name, mode):

    print("MODE", mode)
    tick_dur = 0.0

    # TODO change goal to 10min
    goal = CollectionGoal(10000)

    builder = WorldBuilder(random_seed=1, shape=[32, 32], tick_duration=tick_dur, verbose=False, run_matrx_api=True,
                           run_matrx_visualizer=False, simulation_goal=goal,
                           visualization_bg_img='/images/Picture4.png')

    builder.add_room(top_left_location=[0, 0], width=32, height=32, wall_visualize_colour=wall_color,
                    wall_visualize_opacity=1.0, area_visualize_opacity=0.0, name="world_bounds")

    #TODO change locations to global values
    builder.add_object([agent_locations[0][0]+1,agent_locations[0][1]],'basket',EnvObject,is_traversable=False,is_movable=False,visualize_shape='img',img_name="/images/basket.png")
    builder.add_object([agent_locations[1][0]+1,agent_locations[1][1]],'basket',EnvObject,is_traversable=False,is_movable=False,visualize_shape='img',img_name="/images/basket.png")

    builder.add_object([28,30],'cart',EnvObject,is_traversable=False,is_movable=False,visualize_shape='img',img_name="/images/shopping_cart.png")
    builder.add_object([29,30],'cart',EnvObject,is_traversable=False,is_movable=False,visualize_shape='img',img_name="/images/shopping_cart.png")
    builder.add_object([30,30],'cart',EnvObject,is_traversable=False,is_movable=False,visualize_shape='img',img_name="/images/shopping_cart.png")

    
    #add_dropoffs(builder)

    rooms_locations = add_aisles(builder)
    add_dropoffs2(builder)

    #time.sleep(3)
    prod_locations = add_products(builder, rooms_locations)

    add_agents(builder, mode)

    create_tasks(builder, folder_name, prod_locations)

    # add human agent
    key_action_map = {
        'w': MoveNorth.__name__,
        'd': MoveEast.__name__,
        's': MoveSouth.__name__,
        'a': MoveWest.__name__,
        'q': GrabObject.__name__,
        'e': DropObject.__name__,
    }

    if mode == "ability":
        sense_capability_h = SenseCapability({None:50})
    else:
        sense_capability_h = SenseCapability({CollectableProduct: 2, GhostProduct:2, None:50})

    if mode == "benevolence":
        human_img = "/images/smile_bene.png"
    else:
        human_img = "/images/smile.png"

    human_brain = Human(max_carry_objects=3, grab_range=0)
    builder.add_human_agent([22,15], human_brain, team="Team 1", name="human", 
                            customizable_properties = ['nr_moves', 'score', 'team_score', 'todo'],
                            key_action_map=key_action_map, sense_capability=sense_capability_h, img_name=human_img, 
                            nr_moves=0, score=0, team_score=0, todo="choose")
                            #key_action_map=key_action_map, sense_capability=sense_capability_h, img_name="/static/images/transparent.png")
#            builder.add_agent(loc, brain, team=team_name, name=agent['name'],
#                sense_capability=sense_capability)
#                sense_capability=sense_capability, img_name="/static/images/robot1.png")

    return builder

 
if __name__ == "__main__":
    modes = ["ability","benevolence","integrity","normal","trial"]
    print("arg:", len(sys.argv), str(sys.argv))


    if len(sys.argv) != 2 or sys.argv[1] not in modes:
        raise Exception("Please specify one argument: 'random', 'benevolence', 'integrity', 'normal' or 'trial'.")

    mode = sys.argv[1]

    print(int(datetime.now().timestamp()))

    if mode == "random":
        modes = ["ability","benevolence","integrity"]
        mode = np.random.choice(modes)
   
    #TODO show team score ? 

    t = (2021, 7, 8, 8, 0, 0, 0, 0, 0)

    local_time = int(time.mktime(t))

    folder_name = "logger" + "/" + str(int(time.time()) - local_time)
    os.makedirs(os.path.abspath(os.path.join(script_dir, folder_name)))

    builder = create_builder(folder_name, mode)

    #media_folder = os.path.dirname(os.path.join(script_dir, "images"))
    media_folder = os.path.abspath(os.path.join(script_dir, "media"))

    builder.startup(media_folder=media_folder)

    print("Starting custom visualizer")
    vis_thread = visualization_server.run_matrx_visualizer(verbose=False, media_folder=media_folder)
   
    world = builder.get_world()
    world.run(builder.api_info)

    # stop the custom visualizer
    print("Shutting down custom visualizer" + " http://localhost:" + str(visualization_server.port))
    r = requests.get("http://localhost:" + str(visualization_server.port) + "/shutdown_visualizer")
    vis_thread.join()

    # stop MATRX scripts such as the api and visualizer (if used)
    builder.stop()


