import os, requests
import numpy as np
import time

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

hostage_type = ['robot', 'dog', 'baby', 'elderly']
hostage_image = {'robot': "/static/images/robot2.png", 'dog':"/static/images/dog1.gif", 'baby': "/static/images/baby2.png", 'elderly': "/static/images/grandma1.jpg"}
room_colors = ['#332288', '#117733', '#44AA99', '#88CCEE', '#DDCC77', '#CC6677', '#AA4499', '#882255', "#44AA99"]
room_themes = ['bread', 'carbs', 'vegetables', 'fishmeat', 'fruit', 'household', 'icecream', 'sweets', 'drinks']
wall_color = "#CC6677"
drop_off_color = "#878787"
average_hostages_per_room = 2.5


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

    np.random.seed(10)

    for room_name, locations in room_locations.items():
        theme = room_themes[room_nr]
        images_path = os.listdir(os.path.abspath(os.path.join(script_dir, "media/images/" + theme)))

        min_i = min(len(images_path), len(locations))

        np.random.shuffle(images_path)
        np.random.shuffle(locations)

        for i in range(min_i):

            loc = locations[i]
            image = "/images/" + theme + "/" + images_path[i]
        
            # Get the block's name
            name = f"Object {theme} in {room_name}"

            # Get the probability for adding a block so we get the on average the requested number of blocks per room

            builder.add_object(loc, name, callable_class=CollectableProduct, img_name=image)

        room_nr += 1


def add_agents(builder):
    '''
    Add bots as specified. All bots have the same sense_capability.
    '''
    sense_capability = SenseCapability({None: 50})

    #TODO random loc

    #TODO same color agent and human

    loc = [25,9] # agents start in horizontal row at top left corner.

    builder.add_agent(loc, ShopAssist(name="x",drop_zone_nr=1), name="Agent X",
#                sense_capability=sense_capability)
            sense_capability=sense_capability, img_name="/images/smile_glasses.png")

    loc = [25,19] # agents start in horizontal row at top left corner.
    builder.add_agent(loc, ShopAssist(name="z",drop_zone_nr=2), name="Agent Z", 
#                sense_capability=sense_capability)
            sense_capability=sense_capability, img_name="/images/smile_glasses.png")



def create_tasks(builder,logger_name):
    sense_capability = SenseCapability({None: 50})

    f = open("tasks.txt", "w")
    f2 = open("products.txt", "w")
    logger = open(logger_name,"w")

    logger.write("current_time,task_id,nr_products,agent,nr_moves_start,nr_moves_end,presented_time,time_start,time_end,completed_prod,status,score,success,success_done_points,unsuccess_done_points\n")
    logger.close() 

    world_products = [x['custom_properties']['img_name'] for x in builder.object_settings if x['callable_class'] == CollectableProduct ]

    f2.write(str(world_products))
    f2.close()

    tasks = []

    for i in range(20):
        n_items = np.random.choice(list(range(4))) + 1
        products = np.random.choice(world_products,n_items).tolist()
        tasks += [products]
        msg = str(products) + "\n"
        f.write(msg)
    
    f.close()

    loc = [26,19]

    builder.add_agent(loc, TaskMaker(logger_name), team="team_name", name = "taskmaker1", sense_capability=sense_capability, 
                visualize_opacity=0.0, custom_properties = {"tasks": tasks})

                #TODO check tasks structure. is array creating the error?

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


def create_builder(logger_name):
    tick_dur = 0.1

    goal = CollectionGoal(10000)

    builder = WorldBuilder(random_seed=1, shape=[32, 32], tick_duration=tick_dur, verbose=False, run_matrx_api=True,
                           run_matrx_visualizer=False, simulation_goal=goal,
                           visualization_bg_img='/images/Picture4.png')

    builder.add_room(top_left_location=[0, 0], width=32, height=32, wall_visualize_colour=wall_color,
                    wall_visualize_opacity=1.0, area_visualize_opacity=0.0, name="world_bounds")

    builder.add_object([26,9],'basket',EnvObject,is_traversable=False,is_movable=False,visualize_shape='img',img_name="/images/basket.png")
    builder.add_object([26,19],'basket',EnvObject,is_traversable=False,is_movable=False,visualize_shape='img',img_name="/images/basket.png")

    builder.add_object([28,30],'cart',EnvObject,is_traversable=False,is_movable=False,visualize_shape='img',img_name="/images/shopping_cart.png")
    builder.add_object([29,30],'cart',EnvObject,is_traversable=False,is_movable=False,visualize_shape='img',img_name="/images/shopping_cart.png")
    builder.add_object([30,30],'cart',EnvObject,is_traversable=False,is_movable=False,visualize_shape='img',img_name="/images/shopping_cart.png")

    
    #add_dropoffs(builder)

    rooms_locations = add_aisles(builder)
    add_dropoffs2(builder)

    time.sleep(3)
    add_products(builder, rooms_locations)
    #add_blocks(builder, rooms_locations)

    add_agents(builder)

    create_tasks(builder, logger_name)

    # add human agent
    key_action_map = {
        'w': MoveNorth.__name__,
        'd': MoveEast.__name__,
        's': MoveSouth.__name__,
        'a': MoveWest.__name__,
        'q': GrabObject.__name__,
        'e': DropObject.__name__,
    }

    sense_capability_h = SenseCapability({CollectableProduct: 2, GhostProduct:2, None:50}, )

    human_brain = Human(max_carry_objects=3, grab_range=0)
    builder.add_human_agent([20, 2], human_brain, team="Team 1", name="human", 
                            customizable_properties = ['nr_moves', 'score'],
                            key_action_map=key_action_map, sense_capability=sense_capability_h, img_name="/images/smile.png", 
                            nr_moves=0, score=0)
                            #key_action_map=key_action_map, sense_capability=sense_capability_h, img_name="/static/images/transparent.png")
#            builder.add_agent(loc, brain, team=team_name, name=agent['name'],
#                sense_capability=sense_capability)
#                sense_capability=sense_capability, img_name="/static/images/robot1.png")

    return builder

 
if __name__ == "__main__":
    #TODO pass name of logger
    logger_name = "test.csv"

    builder = create_builder(logger_name)

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


