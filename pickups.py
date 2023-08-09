import pygame as p

import global_values as g
import gameobjects
import sounds
import controls

class Pickup(gameobjects.GameObj):
    def __init__(self, origin:p.Vector3, model_name:str, colour='greeen'):
        super().__init__(  origin, model_name, colour=colour )

    def on_colliding(self, collider):
        if collider == g.player:
            self.on_pickup()
        return super().on_colliding(collider)

    def on_pickup(self):
        """
        Called when the pickup is actually picked up
        """

        self.delete()


class Health(Pickup):
    def __init__(self, origin:p.Vector3):
        super().__init__(origin, 'health', colour='green')

    def on_pickup(self):
        g.player.health += 5
        g.info_box.set_info_if_finished('BODY INTEGRITY RESTORED.')
        sounds.play_sound('health_pickup')
        return super().on_pickup()
    
class Battery(Pickup):
    def __init__(self, origin:p.Vector3):
        super().__init__(origin, 'battery', colour='blue')

    def on_pickup(self):
        g.player.power += 3
        sounds.play_sound('battery_pickup')
        g.info_box.set_info_if_finished('POWER RECHARGED.')
        return super().on_pickup()

class Goal(Pickup):
    def __init__(self, origin:p.Vector3):
        super().__init__(origin, 'goal', colour='purple')
        g.goal = self

        self.reached_timestamp = 0
        self.win_time = 6.0
        self.fully_reached = False

    def update(self):
        if self.reached_timestamp and not self.fully_reached:
            if p.time.get_ticks() - self.reached_timestamp >= self.win_time*1000:
                self.win()


        return super().update()
    
    def win(self):
        """
        Win in a delayed manner
        """
        g.events.append('win')
        self.fully_reached = True

    def on_pickup(self):
        if not self.reached_timestamp:
            controls.Overlay(g.SCREEN_RECT, 'black', 0, 255, self.win_time)

            g.info_box.info = 'TARGET CARGO HAS BEEN RE-ACQUIRED. MISSION ACCOMPLISHED'
            g.player.power += 3
            g.player.health = g.player.max_health

            self.reached_timestamp = p.time.get_ticks()
            #return super().on_pickup()
    