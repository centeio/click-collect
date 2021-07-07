from matrx.objects import EnvObject # type: ignore


class CollectableProduct(EnvObject):
    def __init__(self, location, name, img_name):
        super().__init__(location, name, is_traversable=True, is_movable=True,
                         img_name=img_name, class_callable=CollectableProduct,
                         is_drop_zone=False, is_goal_block=False, is_collectable=True, init_loc = location)

class GhostProduct(EnvObject):
    def __init__(self, location, drop_zone_nr, name, img_name):
        super().__init__(location, name, is_traversable=True, is_movable=False,
                         visualize_shape='img', img_name=img_name,
                         visualize_size=1, class_callable=GhostProduct,
                         visualize_depth=85, drop_zone_nr=drop_zone_nr, visualize_opacity=0.7,
                         is_drop_zone=False, is_goal_block=True, is_collectable=False)


#class CollectableBlock(EnvObject):
#    def __init__(self, location, name, visualize_colour, visualize_shape):
#        super().__init__(location, name, is_traversable=True, is_movable=True,
#                         visualize_colour=visualize_colour, visualize_shape=visualize_shape,
#                         visualize_size=block_size, class_callable=CollectableBlock,
#                         is_drop_zone=False, is_goal_block=False, is_collectable=True)

#class GhostBlock(EnvObject):
#    def __init__(self, location, drop_zone_nr, name, visualize_colour, visualize_shape):
#        super().__init__(location, name, is_traversable=True, is_movable=False,
#                         visualize_colour=visualize_colour, visualize_shape=visualize_shape,
#                         visualize_size=block_size, class_callable=GhostBlock,
#                         visualize_depth=85, drop_zone_nr=drop_zone_nr, visualize_opacity=0.5,
#                         is_drop_zone=False, is_goal_block=True, is_collectable=False)