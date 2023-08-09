import pygame as p
import math as m

import models
import global_values as g

import random as r

class PointSpawner():
    """
    Base class for radar/lidar stuff
    """
    def __init__(self, max_points:int) -> None:
        self.max_points = max_points
        #TODO use set?
        self.points_list: list[models.Point] = [None for i in range(self.max_points)]
        self.point_count = 0
        self.current_i = 0

        self.delete_time = 1.0

        g.point_spawners.append(self)

    def clear(self):
        """
        Clear all the recorded point data for this spawner
        """
        self.points_list: list[models.Point] = [None for i in range(self.max_points)]
        self.point_count = 0
        self.current_i = 0

    def shoot_ray(self, x:int, y:int):
        """
        Shoot a single ray out of the camera at a point on the viewport and record the result
        """

        #1 -> 500 (far)
        #-1 -> 400 (far - near?)
        ray_vec = p.Vector3(x + g.viewport.x, y + g.viewport.y, 100)#g.WIDTH/2, g.HEIGHT/2, 2)

        #proj = g.camera.get_projected(ray_vec, return_vec=False)

        world_ray_vec = g.camera.get_unprojected( ray_vec )
        direction_vec = world_ray_vec - g.camera

        world_point = models.Ray(g.camera.x, g.camera.y, g.camera.z, direction_vec, colour='white')

        if world_point.colour == 'yellow':
            world_point.delete_timestamp = p.time.get_ticks() + (self.delete_time*1000)

        
        self.add_point(world_point)

    def add_point(self, point:models.Point):
        """
        Add a new point to this spawner
        """
        #TODO would this be better if the point was premade and the positions were passed in?

        if point.res and point.res.colour:
           point.colour = point.res.colour


        self.points_list[self.current_i] = point
        self.current_i = (self.current_i+1)%self.max_points

        self.point_count = max(self.point_count, self.current_i)

    def update(self):
        pass


    def draw(self):
        for i in range(self.point_count):
            point = self.points_list[i]
            g.camera.project_and_draw_point(point)
            #g.camera.draw_point(g.camera.project_point(point))
    #    if not point:
    #        continue
    #    

class SmallRangePointSpawner(PointSpawner):
    def __init__(self) -> None:
        super().__init__(700)

    def shoot_ray(self):
        x,y = g.mx - g.viewport.x, g.my - g.viewport.y
        for i in range(5):
            
            #x = int(g.WIDTH/2)
            #y = int(g.HEIGHT/2)


            mag = 150 * (r.random()-0.5)
            
            ang = r.random()*m.pi*2
            mx = m.cos( ang )*mag
            my = m.sin( ang )*mag
            x += mx
            y += my

            
            super().shoot_ray(x,y)

class BurstPointSpawner(PointSpawner):
    def __init__(self) -> None:
        super().__init__(1000)

        self.burst_time = 6.0
        self.bursting = False
        self.burst_shot_count = 0
        self.burst_state_x = 0
        self.burst_state_y = 0

        
        self.burst_cooldown = 6.0
        self.last_burst_time = -self.burst_cooldown*1000
        

    def update_burst(self):
        if self.bursting:
            #figure out how many rays to shoot this frame
            burst_amount = self.max_points * g.dt / self.burst_time
            if self.burst_shot_count + burst_amount > self.max_points:
                #this will be the last burst frame
                burst_amount = self.max_points - self.burst_shot_count
                self.bursting = False
            
            pixels = g.viewport.w * g.viewport.h
            

            for i in range(int(burst_amount)):
                super().shoot_ray(self.burst_state_x,self.burst_state_y)

                self.burst_step = 534 + r.randint(-5,5)
                self.burst_state_x += self.burst_step
                while self.burst_state_x >= g.viewport.w:
                    self.burst_state_x -= g.viewport.w
                    self.burst_state_y += r.randint(1,3)
                    if self.burst_state_y >= g.viewport.h:
                        self.burst_state_y -= g.viewport.h

            self.burst_shot_count += burst_amount
        else:
            if p.time.get_ticks() - self.last_burst_time >= self.burst_cooldown*1000:
                self.start_burst()

    def start_burst(self):
        
        """
        Start a new burst
        """
        r.seed(100)

        self.burst_state_x = 0
        self.burst_state_y = 0
        self.bursting = True
        self.burst_shot_count = 0



class BeamSpawner(PointSpawner):
    def __init__(self) -> None:
        super().__init__(400)

        self.h_speed = 0.6
        self.x = 0

    def move_beam(self):
        self.x = (self.x + self.h_speed*g.dt) % 1
        x = self.x*g.viewport.w

        h_rand = int(30*g.dt)
        for i in range(int(self.max_points*self.h_speed*g.dt) ):
            self.shoot_ray(x+r.randint(-h_rand,h_rand) ,r.randint(0,g.viewport.h))

    

   
        