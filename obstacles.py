import pygame as p

import global_values as g
import gameobjects
import sounds

class Obstacle(gameobjects.DestructableGameObj):
    """
    Base class for creatures and various other objects that interact with the player
    """
    def __init__(self, origin:p.Vector3, model_name:str, collision_damage:int, collision_cooldown=2.0, **kwargs):
        self.collision_damage = collision_damage
        self.collision_cooldown = collision_cooldown
        self.last_collided_time = 0
        self.cooling_down = False

        _kwargs = {'colour':'yellow'}
        _kwargs.update(kwargs)
        super().__init__(origin, model_name, **_kwargs)

    def update(self):
        if self.cooling_down:
            if p.time.get_ticks() - self.last_collided_time >= self.collision_cooldown*1000:
                self.on_collision_cooldown_ended()

    def on_colliding(self, collider):
        """
        Called when collision occurs
        """

        if collider == g.player:

            current_time = p.time.get_ticks()
            if current_time - self.last_collided_time >= self.collision_cooldown*1000:
                self.last_collided_time = current_time
                self.cooling_down = True
                self.on_hit_player()

        super().on_colliding(collider)

    def on_collision_cooldown_ended(self):
        """
        Automatically called when obstacle can hit player again
        """
        self.cooling_down = False
        

    def on_hit_player(self):
        """
        Called each time this obstacle collides with the player
        Respects the collision_cooldown attribute
        """

        if self.collision_damage:
            g.player.health -= self.collision_damage
            

        

class Mine(Obstacle):
    def __init__(self, origin:p.Vector3):
        super().__init__(origin, 'sphere1', 2)

        self.sound_cooldown = 2.0
        self.last_sound_time = 0

        self.sound_range = 25

    def update(self):
        if p.time.get_ticks() - self.last_sound_time >= self.sound_cooldown*1000:
            if (self - g.player).magnitude() <= self.sound_range:
                self.play_sound()
            self.last_sound_time = p.time.get_ticks()

        return super().update()

    def play_sound(self):
        sounds.WorldSound(self.xyz, 'blip1', vol=6)

    def on_hit_player(self):
        super().on_hit_player()

        hit_vec = (g.player.xyz - self.xyz)
        hit_force = 5

        g.player.velocity += hit_vec*hit_force

        sounds.WorldSound(self.xyz, 'mine_explode', vol=8)
        self.delete()

class Fish(Obstacle):
    def __init__(self, origin:p.Vector3, **kwargs):
        super().__init__(origin, 'shark', 2, **kwargs)

        self.range = 30
        self.player_in_range = False
        self.min_range = 0.5
        self.speed = 2.0

        self.in_range_sound = None
        
        
    def update(self):
        mag = p.Vector3(self - g.player).magnitude()
        super().update()

        if mag <= self.range:
            if not self.player_in_range:
                if not self.in_range_sound or self.in_range_sound.deleted:
                    self.in_range_sound = sounds.WorldSound(self.xyz, 'fish_in_range', vol=10)

                self.player_in_range = True

            direction_vec = p.Vector3(g.player - self)
            direction_vec.normalize_ip()
            if mag > self.bounding_radius+self.min_range:
                self.set_rotation(direction_vec)

                self.move(direction_vec * self.speed * g.dt)
            elif mag <= 1: #don't get TOO close
                self.move(direction_vec * -self.speed * g.dt)
        else:
            self.player_in_range = False

    def on_collision_cooldown_ended(self):
        self.collision_groups = set(('models',))
        return super().on_collision_cooldown_ended()

    def on_hit_player(self):
        
        hit_vec = (g.player.xyz - self.xyz)
        hit_force = 2

        g.player.velocity += hit_vec*hit_force

        self.collision_groups = set(('rays',))


        return super().on_hit_player()
        
    