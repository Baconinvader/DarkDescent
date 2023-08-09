import os
import pygame as p

import global_values as g

def li(name:str, extension:str='png'):
    """
    Load an image
    """
    surf = p.image.load(os.path.join(g.DIR_GFX, name) + '.' + extension).convert_alpha()

    return surf