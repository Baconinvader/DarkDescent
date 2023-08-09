import math as m
import pygame as p

import gameobjects
import obstacles
import global_values as g

class Projectile(gameobjects.DestructableGameObj):
    """
    Base class for creatures and various other objects that interact with the player
    """
    def __init__(self, origin:p.Vector3, direction:p.Vector3, speed:float, model_name:str, collision_damage:int, lifetime:float=2.0, **kwargs):
        self.collision_damage = collision_damage

        self.direction = direction
        
        

        self.speed = speed

        self.lifetime = lifetime

        _kwargs = {'colour':'green', 'collision_groups':set(('',)), 'colliding_groups':set(('',))}
        _kwargs.update(kwargs)
        super().__init__(origin, model_name, **_kwargs)

        self.set_rotation(self.direction)
    
    def update(self):
        super().update()
        self.move(self.direction*self.speed*g.dt)

        self.lifetime -= g.dt
        if self.lifetime <= 0:
            self.delete()

    def on_colliding(self, collider):
        """
        Called when collision occurs
        """
        #todo better player check
        if self.collision_damage and isinstance(collider, gameobjects.DestructableGameObj) and collider != g.player:
            collider.health -= self.collision_damage

        super().on_colliding(collider)

class Missile(Projectile):
    def __init__(self, origin:p.Vector3, direction:p.Vector3, speed:float):
        super().__init__(origin, direction, speed, 'missile', 2, lifetime=10)