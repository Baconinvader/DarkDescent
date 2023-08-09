import models
import global_values as g

import pygame as p

class GameObj(models.ModelInstance):
    """
    Base class for game objects
    """
    def __init__(self, origin:p.Vector3, model_name:str, **kwargs):
        super().__init__(origin, model_name, **kwargs)

    def __str__(self):
        return f'GameObJ: {self.model.name}{id(self)}'

    def move(self, vec:p.Vector3):
        if vec.magnitude() <= 0.000_000_1:
            return 

        step = vec.copy()
        max_steps = 4
        start_point = p.Vector3(self)

        colliding = False
        for i in range(max_steps):
            if colliding:
                self -= step
            else:
                self += step

            self.update_matrices()
            self.update_vertex_array()

            colliding = self.is_colliding()

            if i == 0 and not colliding:
                #we have moved fully and is not colliding so break
                break

            step /= 2

        #we have done all the stepping and are still colliding
        if colliding:
            self.xyz = start_point
            self.update_matrices()
            self.update_vertex_array()


    def delete(self):
        if not self.deleted:

            super().delete()

class DestructableGameObj(GameObj):
    """
    Base class for objects with health
    """
    def __init__(self, origin:p.Vector3, model_name:str, **kwargs):
        super().__init__(origin, model_name, **kwargs)

        self.max_health = 10
        self._health = self.max_health

    @property
    def health(self):
        return self._health
    @health.setter
    def health(self, val):
        if val < 0:
            if g.info_box.displayed_current_info():
                g.info_box.info = f'IMPACT DETECTED. BODY INTEGRITY NOW AT f{ round(self.health/self.max_health)*100 }%.'

        if val <= 0:
            self._health = 0
            self.destroy()
        elif val > self.max_health:
            self._health = self.max_health
        else:
            self._health = val

    def destroy(self):
        print('Destroy',self)
        self.delete()

class Hint(p.Vector3):
    """
    Class for giving the player new information when they reach a certain point
    """
    def __init__(self, origin:p.Vector3, text:str, radius=3):
        super().__init__(origin)
        self.text = text
        self.radius = radius

        g.hints.append(self)
        self.deleted = False

    def update(self):
        dist = (self-g.player).magnitude()
        if dist <= self.radius:
            self.show()

    def show(self):
        """
        Put this hint in the players info box
        """
        g.info_box.info = self.text

    def delete(self):
        if not self.deleted:
            self.deleted = True
            g.hints.remove(self)