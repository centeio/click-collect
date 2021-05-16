import os
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

from agents1.shopassist import ShopAssist
from agents1.task_maker import TaskMaker
from agents1.human import Human

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


class CollectableProduct(EnvObject):
    def __init__(self, location, name, img_name):
        super().__init__(location, name, is_traversable=True, is_movable=True,
                         img_name=img_name, class_callable=CollectableProduct,
                         is_drop_zone=False, is_goal_block=False, is_collectable=True)

class CollectableBlock(EnvObject):
    def __init__(self, location, name, visualize_colour, visualize_shape):
        super().__init__(location, name, is_traversable=True, is_movable=True,
                         visualize_colour=visualize_colour, visualize_shape=visualize_shape,
                         visualize_size=block_size, class_callable=CollectableBlock,
                         is_drop_zone=False, is_goal_block=False, is_collectable=True)

class GhostBlock(EnvObject):
    def __init__(self, location, drop_zone_nr, name, visualize_colour, visualize_shape):
        super().__init__(location, name, is_traversable=True, is_movable=False,
                         visualize_colour=visualize_colour, visualize_shape=visualize_shape,
                         visualize_size=block_size, class_callable=GhostBlock,
                         visualize_depth=85, drop_zone_nr=drop_zone_nr, visualize_opacity=0.5,
                         is_drop_zone=False, is_goal_block=True, is_collectable=False)

class ShopAssistant2(AgentBrain):
    def __init__(self, slowdown:int = 1):
        super().__init__(slowdown)

def add_rooms(builder):
    room_locations = {}
    locs = {0: (7,7), 1: (13,7), 2: (19,7), 
            3: (7,13), 4: (13,13), 5: (19,13),
            6: (7,19), 7: (13,19), 8: (19,19)}
    for room_nr in range(9):
        room_top_left_x, room_top_left_y = locs[room_nr]

        # We assign a simple random color to each room. Not for any particular reason except to brighting up the place.
        np.random.shuffle(room_colors)
        room_color = room_colors[0]

        # Add the room
        room_name = f"room_{room_nr}"
        builder.add_room(top_left_location= (room_top_left_x, room_top_left_y), width=6, height=4, name=room_name,
                         door_locations=[(room_top_left_x+2, room_top_left_y)], doors_open = True,
                         wall_visualize_colour=wall_color, with_area_tiles=True,
                         area_visualize_colour=room_color, area_visualize_opacity=0.1)

        # Find all inner room locations where we allow objects (making sure that the location behind to door is free)
        room_locations[room_name] = builder.get_room_locations((room_top_left_x, room_top_left_y), 6, 4)

    return room_locations

def add_rooms2(builder):
    room_locations = {}
    w=16
    h=4
    locs = {0: (4,2), 1: (4,6), 2: (4,10), 
            3: (4,14), 4: (4,18), 5: (4,22),
            6: (4,26)}
    for room_nr in range(7):
        room_top_left_x, room_top_left_y = locs[room_nr]

        # We assign a simple random color to each room. Not for any particular reason except to brighting up the place.
        np.random.shuffle(room_colors)
        room_color = room_colors[0]

        door_locs = [(room_top_left_x, room_top_left_y),(room_top_left_x, room_top_left_y+1),
            (room_top_left_x, room_top_left_y+2),(room_top_left_x, room_top_left_y+3),
            (room_top_left_x+w-1, room_top_left_y),(room_top_left_x+w-1, room_top_left_y+1),
            (room_top_left_x+w-1, room_top_left_y+2),(room_top_left_x+w-1, room_top_left_y+3)]

        # Add the room
        room_name = f"room_{room_nr}"
        builder.add_room(top_left_location= (room_top_left_x, room_top_left_y), width=w, height=h, name=room_name,
                         door_locations=door_locs, doors_open = True,
                         wall_visualize_colour=wall_color,
                         with_area_tiles=True,
                         wall_visualize_opacity=0.1,
                         area_visualize_colour=room_color, area_visualize_opacity=0.0)

        # Find all inner room locations where we allow objects (making sure that the location behind to door is free)
        room_locations[room_name] = builder.get_room_locations((room_top_left_x, room_top_left_y), 16, 4)
    


    return room_locations

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
                         door_locations=door_locs, doors_open = True,
                         wall_visualize_colour=wall_color,
                         with_area_tiles=True,
                         wall_visualize_opacity=0.1, area_visualize_opacity=0.0)

        # Find all inner room locations where we allow objects (making sure that the location behind to door is free)
        room_locations[room_name] = builder.get_room_locations((room_top_left_x, room_top_left_y), w, h)

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
                         door_locations=door_locs, doors_open = True,
                         wall_visualize_colour=wall_color,
                         with_area_tiles=True,
                         wall_visualize_opacity=0.1, area_visualize_opacity=0.0)

        # Find all inner room locations where we allow objects (making sure that the location behind to door is free)
        room_locations[room_name] = builder.get_room_locations((room_top_left_x, room_top_left_y), w2, h2)
    
    return room_locations

def add_dropoffs(builder):
    builder.add_area(top_left_location=[0, 0], width=8, height=4, wall_visualize_colour=wall_color, name="helicopter",
        visualize_colour='#990500', visualize_opacity=0.3)
    builder.add_area(top_left_location=[27, 1], width=4, height=4, wall_visualize_colour=wall_color, name="ambulance", 
        visualize_colour='#990500', visualize_opacity=0.3)
    builder.add_area(top_left_location=[1, 26], width=30, height=5, wall_visualize_colour=wall_color, name="hospital", 
        visualize_colour='#0099ff', visualize_opacity=0.5)


def add_dropoffs2(builder):
    builder.add_area(top_left_location=[24,10], width=4, height=1, wall_visualize_colour=wall_color, name="c1",
        visualize_colour='#88CCEE', visualize_opacity=1.0, drop_zone_nr=1)
    builder.add_area(top_left_location=[24, 20], width=4, height=1, wall_visualize_colour=wall_color, name="c2", 
        visualize_colour='#88CCEE', visualize_opacity=1.0, drop_zone_nr=2)


def add_hostages(builder, room_locations):
    for room_name, locations in room_locations.items():
        for loc in locations:

            # Create a MATRX random property of type of hostage so each hostage varies per created world.
            # These random property objects are used to obtain a certain value each time a new world is
            # created from this builder.
            np.random.shuffle(hostage_type)
            hostage = hostage_type[0]
            image = hostage_image[hostage]
        
            # Get the block's name
            name = f"Hostage {hostage} in {room_name}"

            # Get the probability for adding a block so we get the on average the requested number of blocks per room
            prob = min(1.0, average_hostages_per_room / len(locations))

            builder.add_object_prospect(loc, name, callable_class=CollectableHostage, probability=prob, img_name=image)

def add_products(builder, room_locations):
    room_nr = 0

    for room_name, locations in room_locations.items():
        theme = room_themes[room_nr]
        images_path = os.listdir(os.path.abspath(os.path.join(script_dir, "media/images/" + theme)))

        min_i = min(len(images_path), len(locations))

        np.random.shuffle(images_path)
        np.random.shuffle(locations)

        for i in range(min_i):

            # Create a MATRX random property of type of hostage so each hostage varies per created world.
            # These random property objects are used to obtain a certain value each time a new world is
            # created from this builder.
            loc = locations[i]
            image = "/images/" + theme + "/" + images_path[i]
        
            # Get the block's name
            name = f"Object {theme} in {room_name}"

            # Get the probability for adding a block so we get the on average the requested number of blocks per room

            builder.add_object(loc, name, callable_class=CollectableProduct, img_name=image)

        room_nr += 1


def add_blocks(builder, room_locations):
    i = 0
    for room_name, locations in room_locations.items():
        
        for loc in locations:
            # Get the block's name
            name = f"Block {str(i)}in {room_name}"

            # Get the probability for adding a block so we get the on average the requested number of blocks per room
            prob = min(1.0, average_blocks_per_room / len(locations))

            # Create a MATRX random property of shape and color so each block varies per created world.
            # These random property objects are used to obtain a certain value each time a new world is
            # created from this builder.
            colour_property = RandomProperty(values=block_colors)
            shape_property = RandomProperty(values=block_shapes)

            # Add the block; a regular SquareBlock as denoted by the given 'callable_class' which the
            # builder will use to create the object. In addition to setting MATRX properties, we also
            # provide a `is_block` boolean as custom property so we can identify this as a collectible
            # block.
            builder.add_object_prospect(loc, name, callable_class=CollectableBlock, probability=prob,
                                        visualize_shape=shape_property, visualize_colour=colour_property)
            i += 1

def add_agents(builder):
    '''
    Add bots as specified. All bots have the same sense_capability.
    '''
    sense_capability = SenseCapability({None: 50})

    loc = [25,9] # agents start in horizontal row at top left corner.
    team_name = "Team 1" # currently this supports 1 team 
    builder.add_agent(loc, ShopAssist(), team=team_name, name="shopassist1",
#                sense_capability=sense_capability)
            sense_capability=sense_capability, img_name="/images/smile_glasses.png")

    loc = [25,19] # agents start in horizontal row at top left corner.
    builder.add_agent(loc, ShopAssist(), team=team_name, name="shopassist2", 
#                sense_capability=sense_capability)
            sense_capability=sense_capability, img_name="/images/smile_glasses.png")

    loc = [26,19]
    builder.add_agent(loc, TaskMaker(), team = team_name, name = "taskmaker1", sense_capability=sense_capability, visualize_opacity=0.0)


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


def create_builder():
    tick_dur = 0.1

    goal = CollectionGoal(10000)

    factory = WorldBuilder(random_seed=1, shape=[32, 32], tick_duration=tick_dur, verbose=False, run_matrx_api=True,
                           run_matrx_visualizer=True, simulation_goal=goal,
                           visualization_bg_img='/images/Picture4.png')

    factory.add_room(top_left_location=[0, 0], width=32, height=32, wall_visualize_colour=wall_color,
                    wall_visualize_opacity=0.0, area_visualize_opacity=0.0, name="world_bounds")

    factory.add_object([26,9],'basket',EnvObject,is_traversable=False,is_movable=False,visualize_shape='img',img_name="/images/basket.png")
    factory.add_object([26,19],'basket',EnvObject,is_traversable=False,is_movable=False,visualize_shape='img',img_name="/images/basket.png")

    factory.add_object([28,30],'cart',EnvObject,is_traversable=False,is_movable=False,visualize_shape='img',img_name="/images/shopping_cart.png")
    factory.add_object([29,30],'cart',EnvObject,is_traversable=False,is_movable=False,visualize_shape='img',img_name="/images/shopping_cart.png")
    factory.add_object([30,30],'cart',EnvObject,is_traversable=False,is_movable=False,visualize_shape='img',img_name="/images/shopping_cart.png")

    
    #add_dropoffs(factory)

    rooms_locations = add_aisles(factory)
    add_dropoffs2(factory)

    time.sleep(3)
    add_products(factory, rooms_locations)
    #add_blocks(factory, rooms_locations)

    add_agents(factory)

    # add human agent
    key_action_map = {
        'w': MoveNorth.__name__,
        'd': MoveEast.__name__,
        's': MoveSouth.__name__,
        'a': MoveWest.__name__,
        'r': RemoveObject.__name__,
        'q': GrabObject.__name__,
        'e': DropObject.__name__,
    }

    sense_capability_h = SenseCapability({CollectableProduct: 2, None:50})

    human_brain = HumanAgentBrain(max_carry_objects=3, grab_range=0)
    factory.add_human_agent([20, 2], human_brain, team="Team 1", name="human",
                            key_action_map=key_action_map, sense_capability=sense_capability_h, img_name="/images/smile.png")
                            #key_action_map=key_action_map, sense_capability=sense_capability_h, img_name="/static/images/transparent.png")
#            builder.add_agent(loc, brain, team=team_name, name=agent['name'],
#                sense_capability=sense_capability)
#                sense_capability=sense_capability, img_name="/static/images/robot1.png")

    return factory

 
if __name__ == "__main__":
    builder = create_builder()

    #media_folder = os.path.dirname(os.path.join(script_dir, "images"))
    media_folder = os.path.abspath(os.path.join(script_dir, "media"))

    builder.startup(media_folder=media_folder)

    world = builder.get_world()

    world.run(builder.api_info)

