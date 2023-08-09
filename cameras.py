import pygame as p
import numpy as np
import math as m
import warnings

import global_values as g
import models

class Camera(p.Vector3):
    def __init__(self) -> None:
        self.ax = 0
        self.ay = 0
        self.az = 0

        self.far = 500
        self.near = 400


        self.draw_points = [models.Point(0,0,0) for i in range( 2000 )]
        self.draw_i = 0

        self.draw_lines = [(0,0) for i in range(1000)]
        self.draw_line_i = 0

        self.s_mat_translation = None
        self.s_mat_rotation = None
        self.s_mat_projection = None
        self.s_mat_full = None
        self.s_mat_full_inv = None
        self.update_matrices()

        super().__init__(5,0,-15)

    def project_point(self, point:models.Point) -> models.Point:

        projected = np.array([point.x, point.y, point.z, 1.0])
        self.s_mat_full.dot(projected, out=projected)

        #projected = (projected/projected[3])

        new_point = models.Point(projected[0]/projected[3] + (g.viewport.half_w), projected[1]/projected[3] + (g.viewport.half_h), projected[2]/projected[3], point.colour)
        new_point.delete_timestamp = point.delete_timestamp
        return new_point

    def draw_point(self, point:models.Point):
        if self.draw_i >= len(self.draw_points):
            return
        
        if point.delete_timestamp * (point.delete_timestamp - p.time.get_ticks()) < 0:
            return

        self.draw_points[self.draw_i].xyz = point.xyz
        self.draw_points[self.draw_i].colour = point.colour

        self.draw_points[self.draw_i].delete_timestamp = point.delete_timestamp

        self.draw_i += 1

    def project_and_draw_point(self, point:models.Point):
        """
        Combines projecting and drawing into one function to improve performance
        """
        if self.draw_i >= len(self.draw_points):
            return
        
        if point.delete_timestamp * (point.delete_timestamp - p.time.get_ticks()) < 0:
            return

        projected = np.array([point.x, point.y, point.z, 1.0])
        self.s_mat_full.dot(projected, out=projected)

        self.draw_points[self.draw_i].x = (projected[0]/projected[3]) + g.viewport.half_w
        self.draw_points[self.draw_i].y = (projected[1]/projected[3]) + g.viewport.half_h
        self.draw_points[self.draw_i].z = (projected[2]/projected[3]) 

        self.draw_points[self.draw_i].colour = point.colour
        self.draw_points[self.draw_i].delete_timestamp = point.delete_timestamp

        self.draw_i += 1

    def draw_line(self, si:int, ei:int, mi:int):
        """
        Record that we want to draw a line, given the two line vertex indices and the starting index
        """
        if self.draw_line_i >= len(self.draw_lines):
            return

        line = (mi+ si, mi + ei)

        self.draw_lines[self.draw_line_i] = line
        self.draw_line_i += 1

    def draw_model_instance(self, model_instance:models.ModelInstance):
        """
        Record that we want to draw an instance of a model
        """

        #check if we are going over limit
        if self.draw_i + len(model_instance.points) > len(self.draw_points):
            warnings.warn(f'Warning: drawing {model_instance.model.name} goes over point limit { len(self.draw_points) } ({self.draw_i + len(model_instance.points)})')
            return
        if self.draw_line_i + (len(model_instance.faces)*3) > len(self.draw_lines):
            warnings.warn(f'Warning: drawing {model_instance.model.name} goes over line limit { len(self.draw_lines) } ({self.draw_line_i + (len(model_instance.faces)*3)})')
            return 

        model = model_instance.model

        starting_draw_index = self.draw_i

        projected = np.array([1.0, 1.0, 1.0, 1.0])

        for i in range(len(model.points)):
            self.s_mat_full.dot(model_instance.transformed_vertex_array[i], out=projected)
            projected_point = models.Point(projected[0]/projected[3] +  (g.viewport.half_w), projected[1]/projected[3] + (g.viewport.half_h), projected[2]/projected[3], model.points[i].colour)
            self.draw_point(projected_point)


        #for point in model.points:
        #    self.s_mat_full.dot(point.array, out=projected)
        #    projected_point = models.Point(projected[0]/projected[3] + (g.WIDTH/2), projected[1]/projected[3] + (g.HEIGHT/2), projected[2]/projected[3], point.colour)
        #    self.draw_point(projected_point)
        
        for face in model.faces:
            for line_indices in face.line_index_pairs:
                if self.draw_points[line_indices[0]+starting_draw_index].z >= 0 and self.draw_points[line_indices[1]+starting_draw_index].z >= 0:
                    self.draw_line(line_indices[0], line_indices[1], starting_draw_index)


    def finish_draw(self):
        rect = p.Rect(0,0,1,1)
        for i,point in enumerate(self.draw_points):
            if i < self.draw_i:
                if point[2] <= 0.01 :
                    continue


                #p.draw.circle(g.screen, point.colour, (point[0], point[1]), 0.02*point[2] )
                
                rect.w = (0.02*point[2])*2
                rect.h = (0.02*point[2])*2
                rect.center = (point[0] + g.viewport.x, point[1] + g.viewport.y)

                p.draw.rect(g.screen, point.colour, rect)
            else:
                break
        self.draw_i = 0
        
        for i,indices in enumerate(self.draw_lines):
            if i < self.draw_line_i:
                start = self.draw_points[indices[0]] + g.viewport.vec
                end = self.draw_points[indices[1]] + g.viewport.vec

                if not start.is_finite() or not end.is_finite():
                    continue
                p.draw.line(g.screen, 'white', (start.x, start.y), (end.x, end.y), 2)
            else:
                break
                
        self.draw_line_i = 0


    @property
    def dax(self):
        return m.degrees(self.ax)
    @property
    def day(self):
        return m.degrees(self.ay)
    @property
    def daz(self):
        return m.degrees(self.az)
    
    @property
    def pos(self):
        return p.Vector3(self.x, self.y, self.z)

    @property
    def mat_translation(self) -> np.matrix:
        mat_translate = np.matrix([
            [1, 0, 0, -self.x],
            [0, 1, 0, -self.y],
            [0, 0, 1, -self.z],
            [0, 0, 0, 1]
            ])
        return mat_translate

    def get_translated(self, vec: p.Vector3):
        #use this for efficiency
        #translated_vec = vec - self.pos

        translated = self.mat_translation.dot(  np.array([vec.x, vec.y, vec.z, 1.0]) )
        translated_vec = p.Vector3(translated[0,0], translated[0,1], translated[0,2])
        return translated_vec

    def get_rotated(self, vec: p.Vector3):
        #rotated_vec = vec.rotate(self.dax, p.Vector3(1.0, 0.0, 0.0))
        #rotated_vec = rotated_vec.rotate(self.day, p.Vector3(0.0, 1.0, 0.0))
        #rotated_vec = rotated_vec.rotate(self.daz, p.Vector3(0.0, 0.0, 1.0))

        mat_full_rotation = self.mat_rotate_x*self.mat_rotate_y*self.mat_rotate_z
        rotated = mat_full_rotation.dot(  np.array([vec.x, vec.y, vec.z, 1.0]) )
        rotated_vec = p.Vector3(rotated[0,0], rotated[0,1], rotated[0,2])

        return rotated_vec
    
    @property
    def mat_projection(self) -> np.matrix:
        r = 1#g.WIDTH/2
        t = 1#g.HEIGHT/2

        v1 = -(self.far+self.near)/(self.far-self.near)
        v2 = (-2*self.far*self.near)/(self.far-self.near)
        mat_projection = np.matrix([
            [self.near/r, 0, 0, 0],
            [0, self.near/t, 0, 0],
            [0, 0, v1, v2],
            [0, 0, -1, 0]
        ])
        return mat_projection

    @property
    def mat_unprojection(self) -> np.matrix:
        r = 1#g.WIDTH/2
        t = 1#g.HEIGHT/2

        v1 = -(self.far+self.near)/(self.far-self.near)
        v2 = (-2*self.far*self.near)/(self.far-self.near)
        mat_unprojection = np.matrix([
            [v2 * (r/self.near), 0, 0, 0],
            [0, v2 * (t/self.near), 0, 0],
            [0, 0, 0, -v2],
            [0, 0, 1, v1]
        ])/v2
        return mat_unprojection

    def get_projected(self, vec:p.Vector3, return_vec=True):
        projected = self.mat_projection.dot(  np.array([vec.x, vec.y, vec.z, 1.0]) )
        projected = (projected/projected[0,3])

        projected_vec = p.Vector3(projected[0,0], projected[0,1], projected[0,2])
        projected_vec += p.Vector3( g.viewport.half_w,  g.viewport.half_h, 0)

        return projected_vec

    
    def get_unprojected(self, vec:p.Vector3):
        #mat_full_rotation = self.mat_rotate_x*self.mat_rotate_y*self.mat_rotate_z 
        #mat_view =  self.mat_projection * mat_full_rotation * self.mat_translation
        #mat_inverse = np.linalg.inv(mat_view)

        unprojected = vec - p.Vector3(g.WIDTH/2, g.HEIGHT/2, 0)
        #unprojected = unprojected * vec.z

        unprojected = self.s_mat_full_inv.dot(  np.array([unprojected.x, unprojected.y, unprojected.z, 1.0]) )
        unprojected_vec = p.Vector3(unprojected[0,0], unprojected[0,1], unprojected[0,2])

        w = 1/unprojected[0,3]
        unprojected_vec *= w

        return unprojected_vec

    @property
    def mat_rotate_x(self):
        mat_rotate_x = np.matrix([
            [1, 0, 0, 0],
            [0, m.cos(self.ax), -m.sin(self.ax), 0],
            [0, m.sin(self.ax), m.cos(self.ax), 0],
            [0, 0, 0, 1]
            ])
        return mat_rotate_x
    
    @property
    def mat_rotate_y(self):
        mat_rotate_y = np.matrix([
            [m.cos(self.ay), 0, m.sin(self.ay), 0],
            [0, 1, 0, 0],
            [-m.sin(self.ay), 0, m.cos(self.ay), 0],
            [0, 0, 0, 1]
            ])
        return mat_rotate_y
    
    @property
    def mat_rotate_z(self):
        mat_rotate_z = np.matrix([
            [m.cos(self.az), -m.sin(self.az), 0, 0],
            [m.sin(self.az), m.cos(self.az), 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
            ])
        return mat_rotate_z
    
    def update_matrices(self):
        """
        Update view matrices
        """
        self.s_translation = self.mat_translation
        self.s_mat_rotation= self.mat_rotate_x*self.mat_rotate_y*self.mat_rotate_z
        self.s_mat_projection = self.mat_projection

        self.s_mat_full = self.s_mat_projection * self.s_mat_rotation * self.s_translation
        self.s_mat_full_inv = np.linalg.inv(self.s_mat_full)

        #right
        #r = 1#g.WIDTH/2
        #top
        #t = 1#g.HEIGHT/2

        #v = -(self.far+self.near)/(self.far-self.near)
        #w = (-2*self.far*self.near)/(self.far-self.near)


        #self.full_matrix = np.matrix([
        #    [self.near*m.cos(self.ay)*m.cos(self.az)/r, self.near*m.cos(self.ay)*m.sin(self.az)/t, (v*m.sin(self.ay)) - self.x, w*m.sin(self.ay)],

        #    [ self.near*((m.sin(self.ax)*m.sin(self.ay)*m.cos(self.az)) + (m.cos(self.ax)*m.sin(self.az)))/r,
        #     self.near*((m.cos(self.ax)*m.cos(self.az)) - (m.sin(self.ax)*m.sin(self.ay)*m.sin(self.az)))/t,
        #     -self.y-(v*m.sin(self.ax)*m.cos(self.ay)), -(w*m.sin(self.ax)*m.cos(self.ay))],

        #    [self.near*((m.sin(self.ax)*m.sin(self.az)) - (m.cos(self.ax)*m.sin(self.az)*m.cos(self.az)))/r,
        #      self.near*((m.cos(self.ax)*m.cos(self.ay)*m.sin(self.az)) + (m.sin(self.ax)*m.cos(self.az)))/t,
        #      (v*m.cos(self.ax)*m.cos(self.ay))-self.z, w*m.cos(self.ax)*m.cos(self.ay)],
        #    [0, 0, -1, 0]
        #    ])
