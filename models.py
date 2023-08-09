
import pygame as p
import numpy as np
import math as m
import warnings
import os
from copy import deepcopy

import global_values as g
import plyfile
import GJK

class Point(p.Vector3):
    def __init__(self, x, y, z, colour=None):
        super().__init__(x,y,z)
        self.colour = colour
        #todo remove
        self.array = np.array([self.x, self.y, self.z, 1.0])
        self.delete_timestamp = -1

    def update_array(self):
        """
        Pre-generate the array for this point, so it doesn't need be done at runtime
        This will need to be redone if the point moved
        """
        self.array = np.array([self.x, self.y, self.z, 1.0])

    def update_through_array(self, arr:np.ndarray):
        """
        Update the position of this point using a np array
        """
        self.array = arr
        self.x = arr[0]
        self.y = arr[1]
        self.z = arr[2]

    def is_finite(self):
        max_mag = 10_000
        if m.isinf(self.x) or m.isinf(self.y) or m.isinf(self.z) or self.magnitude() >= max_mag:
            return False
        else:
            return True


class Ray(Point):
    out_of_range_colour = (96, 96, 96)

    def __init__(self, x, y, z, direction:p.Vector3, colour=None, max_dist=100, colliding_groups=set(('models','rays'))):
        super().__init__(x,y,z, colour=colour)
        self.origin = self.copy()

        self.direction = direction.normalize()

        self.colliding_groups = colliding_groups

        self.update_array()

        self.max_dist = max_dist
        self.res = self.move()
        if self.res:
            if self.res.colour:
                self.colour = self.res.colour
        else:
            self += self.direction*max_dist
            self.colour = Ray.out_of_range_colour
            

        self.update_array()

    def update_array(self):
        """
        Pre-generate the array for this point, so it doesn't need be done at runtime
        This will need to be redone if the point moved
        """
        super().update_array()
        self.array = np.array([self.x, self.y, self.z])
        self.direction_array = np.array([self.direction.x, self.direction.y, self.direction.z])

    def move(self):
        """
        Shoot the ray and get a result
        """
        res = self.is_colliding()
        if res[0]:
            self.xyz = res[1].xyz
            return res[0]
        else:
            return None
        
    def is_colliding(self): #-> object|tuple[object, p.Vector3]|None|tuple[None,None]:
        """
        Check whether this ray collides with any model
        """

        colliding_models = []

        for model_instance in g.model_instances:
            if model_instance.collision_groups.isdisjoint(self.colliding_groups):
                continue

        
            res = model_instance.colliding_ray(self)
            if res[0]:
                colliding_models.append( (model_instance, res[1]) )

            #res = model_instance.colliding_ray(self)
            #if res[0]:
            #    colliding_models.append( (model_instance, res[1]) )


        if colliding_models:
            #figure out which model was hit first
            lowest_mag = 999
            closest_intersection = None
            closest_model = None
            for model, intersection in colliding_models:
                mag = (intersection-self).magnitude()
                if mag < lowest_mag:
                    closest_model = model
                    closest_intersection = intersection
                    lowest_mag = mag

            return (closest_model, closest_intersection)

                
        return (None, None)


        


class Face():
    """
    Triangular face
    """
    def __init__(self, model, vertex_indices) -> None:
        self.vertex_indices = vertex_indices
        if len(self.vertex_indices) != 3:
            raise Exception(f'Expected 3 vertex face, got {len(self.vertex_indices)}')

        self.model = model
        
        #don't use this, since faces are maintained between model instances
        #self.points: tuple[Point]  = tuple(model.points[i] for i in self.vertex_indices)

        #precalculated for optimisation
        self.line_index_pairs = [(self.vertex_indices[0], self.vertex_indices[1]),
                                 (self.vertex_indices[1], self.vertex_indices[2]),
                                 (self.vertex_indices[2], self.vertex_indices[0])]
        
    def generate_AABB(self, model_instance):
        """
        Generate a box that contains this face
        """
        lb = self.get_point(model_instance, 0).xyz
        rt = self.get_point(model_instance, 0).xyz

        #todo remove first loop
        for i in range(3):
            point = self.get_point(model_instance, i)
            rt.x = max(rt.x, point.x)
            rt.y = max(rt.y, point.y)
            rt.z = max(rt.z, point.z)

            lb.x = min(lb.x, point.x)
            lb.y = min(lb.y, point.y)
            lb.z = min(lb.z, point.z)
        
        bounding_box = AABB(lb, rt)
        return bounding_box

    def get_point(self, model_instance, index:int):
        return model_instance.points[self.vertex_indices[index]]

    def colliding_triangle(self, model_instance, p0:p.Vector3, p1:p.Vector3, p2:p.Vector3) -> bool:
        """
        Check if this face is colliding with a triangle
        """
        #todo optimise

        def get_other_index(arr):
            epsilon = 0.000_000_001
            if (arr[0] * arr[1]) > epsilon :
                return 2
            if (arr[0] * arr[2])  > epsilon :
                return 1
            if (arr[1] * arr[2])  > epsilon :
                return 0

            warnings.warn(f'get_other_index first check failed with {arr}, epsilon: {epsilon}')

            #more precise check
            if (arr[0] <= 0 and arr[1] <= 0 and arr[2] > 0) or (arr[0] > 0 and arr[1] > 0 and arr[2] < 0) :
                return 2
            if (arr[0] <= 0 and arr[2] <= 0 and arr[2] > 0) or (arr[0] > 0 and arr[2] > 0 and arr[1] < 0) :
                return 1
            if (arr[1] <= 0 and arr[2] <= 0 and arr[0] > 0) or (arr[1] > 0 and arr[2] > 0 and arr[0] < 0) :
                return 0

            warnings.warn(f'get_other_index second check failed!')

            #just guess and hope it doesn't lead to an error, hopefully we never get here
            return 0


            
        def get_projection(po1, po2, po3, d0, d1, d2):
            #project onto plane intersection line
            proj0 = D.dot(po1)
            proj1 = D.dot(po2)
            proj2 = D.dot(po3)
            i = get_other_index([d0, d1, d2])
            proj = [proj0, proj1, proj2]
            #rearrange vertices

            if i != 0:
                temp = proj0
                proj[0] = proj[i]
                proj[i] = temp

                d = [d0, d1, d2]
                temp = d0
                d[0] = d[i]
                d[i] = temp
                d0, d1, d2 = d

            t1 = proj[0] + (proj[1] - proj[0]) * (d0 / (d0 - d1) )
            t2 = proj[0] + (proj[2] - proj[0]) * (d0 / (d0 - d2) )
            return t1, t2


        #check SAT
        anchor1 = self.get_point(model_instance, 0)

        edge1 = self.get_point(model_instance, 2) - self.get_point(model_instance, 0)
        edge2 = self.get_point(model_instance, 1) - self.get_point(model_instance, 0)

        normal1 = (edge1).cross(edge2)
        d1 = (-normal1).dot( self.get_point(model_instance, 0) )

        sides1 = []
        for point in [p0, p1, p2]:
            side = normal1.dot(point) + d1

            sides1.append(side)

        #check if we are on the same side
        if not any(sides1):
            return False
        if (sides1[0] < 0) and (sides1[1] < 0) and (sides1[2] < 0):
            return False
        if (sides1[0] > 0) and (sides1[1] > 0) and (sides1[2] > 0):
            return False
        
        #now the other way around
        anchor2 = p0

        edge1 = p2 - p0
        edge2 = p1 - p0

        normal2 = (edge1).cross(edge2)
        d2 = (-normal2).dot( p0 )

        sides2 = []
        for point in [self.get_point(model_instance, 0), self.get_point(model_instance, 1), self.get_point(model_instance, 2)]:
            side = normal2.dot(point) + d2

            sides2.append(side)


        #check if we are on the same side     
        if not any(sides2):
            return False
        if (sides2[0] < 0) and (sides2[1] < 0) and (sides2[2] < 0):
            return False
        if (sides2[0] > 0) and (sides2[1] > 0) and (sides2[2] > 0):
            return False
        
        
        #get intersection of planes
        D = normal1.cross(normal2)
        
        #triangle1
        t1, t2 = get_projection(self.get_point(model_instance, 0), self.get_point(model_instance, 1), self.get_point(model_instance, 2), *sides2)
        #triangle2
        t3, t4 = get_projection(p0, p1, p2, *sides1)
        
        if t2 < t1:
            t1, t2 = t2, t1
        if t4 < t3:
            t3, t4 = t4, t3
        
        if (t1 <= t2 <= t3 <= t4) or (t3 <= t4 <= t1 <= t2):
            return False

        return True

    

    def colliding_ray(self, ray:Ray, model_instance): #-> bool|tuple[bool, p.Vector3]:
        """
        Check for collision with Moller-Trumbore
        """
        #TODO: Cython this at the end

        edge1 = model_instance.points[self.vertex_indices[1]] - model_instance.points[self.vertex_indices[0]]
        edge2 = model_instance.points[self.vertex_indices[2]] - model_instance.points[self.vertex_indices[0]]

        h = ray.direction.cross(edge2)
        a = edge1.dot(h)

        if (a > -ray.epsilon and a < ray.epsilon):
            return  None
        
        f = 1.0 / a
        s = ray.origin - model_instance.points[self.vertex_indices[0]]
        u = f * s.dot(h)

        if (u < 0.0 or u > 1.0):
            return None
        
        q = s.cross(edge1)
        v = f * ray.direction.dot(q)

        if (v < 0.0 or u + v > 1.0):
            return None
        
        t = f * edge2.dot(q)

        if (t > ray.epsilon):
            out_intersection = ray.origin + (ray.direction * t)
            
            return out_intersection
        else:
            return None




class Model():
    
    def __init__(self, name:str, points, faces_data, is_convex:bool=False, colour='red'):
        self.name = name
        self.points = points

        point_list = []
        for point in self.points:
            if colour and not point.colour:
                point.colour = colour
            point_list.append( [point[0], point[1], point[2]] )

        self.point_array = np.array(point_list)

        self.faces = [Face(self, d) for d in faces_data]

        self.is_convex = is_convex

        #create our bounding box
        self.bounding_radius:float = 0
        for point in self.points:
            mag = point.magnitude()
            if mag > self.bounding_radius:
                self.bounding_radius = mag

        g.models[self.name] = self
        self.generate_point_arrays()

    def generate_point_arrays(self):
        for point in self.points:
            point.update_array()

    
class AABB():
    """
    Simple AABB box
    """
    def __init__(self, lb:p.Vector3, rt:p.Vector3):
        self.lb = lb
        self.rt = rt

        #todo properties?
        self.diff = self.rt-self.lb
        self.half_diff = self.diff/2

        self.lx = self.diff.x
        self.ly = self.diff.y
        self.lz = self.diff.z

        self.children = []

        self.colliding_face_indices = set()

    def __str__(self):
        return f'AABB {self.lb} -> {self.rt}'

    def generate_children(self, depth, max_depth):
        """
        Generate octree child nodes
        """

        c1 = AABB(self.lb, self.lb+self.half_diff )
        c2 = AABB(self.lb + p.Vector3(self.lx/2,0,0), self.lb + p.Vector3(self.lx/2,0,0)+self.half_diff )
        c3 = AABB(self.lb + p.Vector3(0,0,self.lz/2), self.lb + p.Vector3(0,0,self.lz/2)+self.half_diff )
        c4 = AABB(self.lb + p.Vector3(self.lx/2,0,self.lz/2), self.lb + p.Vector3(self.lx/2,0,self.lz/2)+self.half_diff )

        c5 = AABB(self.lb + p.Vector3(0,self.ly/2,0), self.lb + p.Vector3(0,self.ly/2,0)+self.half_diff )
        c6 = AABB(self.lb + p.Vector3(self.lx/2,self.ly/2,0), self.lb + p.Vector3(self.lx/2,self.ly/2,0)+self.half_diff )
        c7 = AABB(self.lb + p.Vector3(0,self.ly/2,self.lz/2), self.lb + p.Vector3(0,self.ly/2,self.lz/2)+self.half_diff )
        c8 = AABB(self.lb+self.half_diff, self.rt )

        self.children = [c1, c2, c3, c4, c5, c6, c7, c8]

        if depth+1 < max_depth:
            for child in self.children:
                child.generate_children(depth+1, max_depth)

    def colliding_ray_with_frac(self, ox, oy, oz, dirfracx, dirfracy, dirfracz):
        """
        Alternate form of checking ray collision 
        """
        #def mmin(a,b):
        #    return a if a < b else b
        #def mmax(a,b):
        #    return a if a > b else b

        t1 = (self.lb.x - ox)*dirfracx
        t2 = (self.rt.x - ox)*dirfracx

        t3 = (self.lb.y - oy)*dirfracy
        t4 = (self.rt.y - oy)*dirfracy

        t5 = (self.lb.z - oz)*dirfracz
        t6 = (self.rt.z - oz)*dirfracz

        #tmin = max(max(min(t1, t2), min(t3, t4)), min(t5, t6))
        #tmax = min(min(max(t1, t2), max(t3, t4)), max(t5, t6))

        tmin = max(min(t1, t2), min(t3, t4), min(t5, t6))
        tmax = min(max(t1, t2), max(t3, t4), max(t5, t6))

        #tmin = mmax(mmax(mmin(t1, t2), mmin(t3, t4)), mmin(t5, t6))
        #tmax = mmin(mmin(mmax(t1, t2), mmax(t3, t4)), mmax(t5, t6))

        if tmax < 0:
            return False
        if tmin > tmax:
            return False
        return True
    

    def colliding_ray(self, ray:Ray):
        """
        Check for collision against ray
        """
        #taken from https://gamedev.stackexchange.com/questions/18436/most-efficient-aabb-vs-ray-collision-algorithms#18459
        if ray.direction.x:
            dirfracx = 1.0/ray.direction.x
        else:
            dirfracx = 0
            
        if ray.direction.y:
            dirfracy = 1.0/ray.direction.y
        else:
            dirfracy = 0

        if ray.direction.z:
            dirfracz = 1.0/ray.direction.z
        else:
            dirfracz = 0

        t1 = (self.lb.x - ray.origin.x)*dirfracx
        t2 = (self.rt.x - ray.origin.x)*dirfracx

        t3 = (self.lb.y - ray.origin.y)*dirfracy
        t4 = (self.rt.y - ray.origin.y)*dirfracy

        t5 = (self.lb.z - ray.origin.z)*dirfracz
        t6 = (self.rt.z - ray.origin.z)*dirfracz

        tmin = max(max(min(t1, t2), min(t3, t4)), min(t5, t6))
        tmax = min(min(max(t1, t2), max(t3, t4)), max(t5, t6))

        if tmax < 0:
            return False
        if tmin > tmax:
            return False
        return True
    
    def get_faces_to_test_recursive_ray_with_frac(self, ox, oy, oz, dirfracx, dirfracy, dirfracz, depth=0):
        """
        Alternate way of doing get_faces_to_test_recursive_ray
        """
        if not self.colliding_ray_with_frac(ox, oy, oz, dirfracx, dirfracy, dirfracz):
            return set()

        if self.children:
            faces = set()
            for child in self.children:
                faces |= child.get_faces_to_test_recursive_ray_with_frac(ox, oy, oz, dirfracx, dirfracy, dirfracz, depth+1)
            return faces
        else:
            return self.colliding_face_indices

    def get_faces_to_test_recursive_ray(self, ray:Ray, depth=0):
        """
        Get the face indices we could be colliding with (using a ray)
        """
        if not self.colliding_ray(ray):
            return set()

        if self.children:
            faces = set()
            for child in self.children:
                faces |= child.get_faces_to_test_recursive_ray(ray, depth+1)
            return faces
        else:
            return self.colliding_face_indices
        
    def get_faces_to_test_recursive_AABB(self, aabb, depth=0):
        """
        Get the face indices we could be colliding with (using a ray)
        """
        if not self.colliding_AABB(aabb):
            return set()

        if self.children:
            faces = set()
            for child in self.children:
                faces |= child.get_faces_to_test_recursive_AABB(aabb, depth+1)
            return faces
        else:
            return self.colliding_face_indices


    def colliding_point(self, point):
        if point.x < self.lb.x or point.x > self.tr.x:
            return False
        if point.y < self.lb.y or point.y > self.tr.y:
            return False 
        if point.z < self.lb.z or point.z > self.tr.z:
            return False 
        return True

    def colliding_AABB(self, aabb):
        if (self.lb.x <= aabb.rt.x \
            and self.rt.x >= aabb.lb.x \
            and self.lb.y <= aabb.rt.y \
            and self.rt.y >= aabb.lb.y \
            and self.lb.z <= aabb.rt.z \
            and self.rt.z >= aabb.lb.z):

            return True
        else:
            return False

    def colliding_AABB_recursive(self, aabb, face_index, depth=0):
        """
        Go through our children recursively and check if we collide, and store the result
        """
        if not self.colliding_AABB(aabb):
            return False

        if self.children:
            for child in self.children:
                child.colliding_AABB_recursive(aabb, face_index, depth=depth+1)
        else:
            self.colliding_face_indices.add(face_index)


class ModelInstance(p.Vector3):
    def __init__(self, origin:p.Vector3, model_name:str, **kwargs):
        self.model:Model = g.models.get(model_name)
        if not self.model:
            #attempt to load model
            warnings.warn(f'Could not find loaded model "{model_name}", attempting to load.')
            load(model_name + '.ply')
        self.model:Model = g.models[model_name]

        super().__init__(origin)
        self.old_origin = p.Vector3(-1,0,-0.5)
        

        self.ax = 0
        self.ay = 0
        self.az = 0

        self.old_ax = self.ax
        self.old_ay = self.ay
        self.old_az = self.az

        self.points = []
        #store a copy of the model point data in a numpy array for quick access
        self.vertex_array:np.ndarray = None
        #store a copy of the TRANSFORMED model point data so calculations don't need to be repeated
        self.transformed_vertex_array:np.ndarray = None
        self.do_convex_check = True

        self.s_translation:np.matrix = None
        self.s_mat_rotation:np.matrix = None
        self.s_mat_full:np.matrix = None
        

        #defines which instances check for collision against this instance
        self.collision_groups = set(('models',))

        #defines which instances this instance checks against
        self.colliding_groups = set(('models',))
        
        self.colour = None

        self.octree_depth = 0
        self.bounding_AABB = None

        #unlike bounding_AABB, which is only generated for octrees
        #this is a looser box that works with rotation and is only used for octree tests
        self.loose_bounding_AABB = None

        self.__dict__.update(**kwargs)

        self.deleted = False
        g.model_instances.append(self)

        self.generate_model_copy()
        self.update_matrices()
        self.update_vertex_array()
        
        #if we are using an octree, generate the AABBs for that
        #NOTE: only do this with static model instances
        if self.octree_depth:
            self.generate_AABB()
        self.generate_loose_AABB()

    def generate_loose_AABB(self):
        #generate loose bounding
        lb = self.xyz - p.Vector3(self.model.bounding_radius, self.model.bounding_radius, self.model.bounding_radius)
        rt = self.xyz + p.Vector3(self.model.bounding_radius, self.model.bounding_radius, self.model.bounding_radius)
        self.loose_bounding_AABB = AABB(lb, rt)      

    def generate_AABB(self):
        """
        generate an AABB that bounds this model instance
        """

        #if octree depth is set, we devide the model using an octree data structure and record which faces are in which nodes

        lb = self.xyz
        rt = self.xyz

        for point in self.points:
            rt.x = max(rt.x, point.x)
            rt.y = max(rt.y, point.y)
            rt.z = max(rt.z, point.z)

            lb.x = min(lb.x, point.x)
            lb.y = min(lb.y, point.y)
            lb.z = min(lb.z, point.z)

        self.bounding_AABB = AABB(lb, rt)

        self.bounding_AABB.generate_children(0, self.octree_depth)
        
        face_i = 0
        for face in self.faces:
            aabb = face.generate_AABB(self)
            self.bounding_AABB.colliding_AABB_recursive(aabb, face_i)

            face_i += 1

    def generate_model_copy(self):
        """
        Copy the model data into this instance so we can manipulate it with matrices
        """
        self.points = deepcopy(self.model.points)

        if self.colour:
            for point in self.points:
                point.colour

        self.vertex_array = np.ones( (len(self.points), 4) )

        for i,point in enumerate(self.points):
            self.vertex_array[i] = [point.x, point.y, point.z, 1.0]
        
        self.transformed_vertex_array = self.vertex_array.copy()

            

    def update(self):
        """
        Update this model instance.
        For the base ModelInstance this is mostly updating the stored vertex array
        """
        self.update_matrices()
        self.update_vertex_array()
        self.generate_loose_AABB()
        

    def update_vertex_array(self):
        if self.old_origin != self or (self.ax != self.old_ax or self.ay != self.old_ay or self.az != self.old_ay):
            for i in range(len(self.points)):
                self.s_mat_full.dot(self.vertex_array[i], out=self.transformed_vertex_array[i])

                self.points[i].update_through_array(self.transformed_vertex_array[i])
            
            self.old_origin.xyz = self.xyz
            self.old_ax = self.ax
            self.old_ay = self.ay
            self.old_az = self.az

            

    def is_bounding_model_instance(self, model_instance):
        """
        Check whether this instance's bounding sphere is intersecting with the bounding sphere of another instance
        """
        dist = self-model_instance
        if dist.magnitude() <= self.bounding_radius + model_instance.bounding_radius:
            return True
        else:
            return False
        
    def is_colliding_model_instance(self, model_instance):
        """
        Check whether this instance is colliding with another instance
        """
        #check for bounding
        if not self.is_bounding_model_instance(model_instance):
            return False
        
        #check for convex collision first
        if self.do_convex_check and model_instance.do_convex_check:
            res = GJK.GJK(self.transformed_vertex_array, model_instance.transformed_vertex_array)
            if not res[0]:
                return False
            #if the model IS convex, just return here
            elif self.is_convex and model_instance.is_convex:
                model_instance.on_colliding(self)
                return res[0]
        
        #check for face
        if model_instance.octree_depth:
            face_indices = model_instance.bounding_AABB.get_faces_to_test_recursive_AABB(self.loose_bounding_AABB)
            faces1 = [model_instance.faces[i] for i in face_indices]
        else:
            faces1 = model_instance.faces

        if self.octree_depth:
            face_indices = self.bounding_AABB.get_faces_to_test_recursive_AABB(model_instance.loose_bounding_AABB)
            faces2 = [self.faces[i] for i in face_indices]
        else:
            faces2 = self.faces

        i = 0
        for face in faces1:
            p0 = model_instance.points[face.vertex_indices[0]]
            p1 = model_instance.points[face.vertex_indices[1]]
            p2 = model_instance.points[face.vertex_indices[2]]

            j = 0
            for self_face in faces2:
                res = self_face.colliding_triangle(self, p0, p1, p2)
                if res:
                    model_instance.on_colliding(self)
                    return res
                j += 1
            i += 1

        return False
    
    def is_colliding(self):
        """
        Check whether this instance is colliding with any other model instance
        """
        for model_instance in g.model_instances:
            if model_instance == self:
                continue

            if model_instance.collision_groups.isdisjoint(self.colliding_groups):
                continue

            res = self.is_colliding_model_instance(model_instance)
            if res:
                return model_instance
        return False

    def on_colliding(self, collider):
        """
        Called when collision occurs
        """
        pass
            

    def set_rotation(self, direction_vec:p.Vector3):
        """
        Sort of set the rotation of this instance based on
        """

        ay = m.atan2(direction_vec.x, direction_vec.z)
        ax = m.atan2(direction_vec.z, direction_vec.y)

        #todo I hate rotations
        #self.az = m.pi#az#theta
        self.ay = ay
        #self.ax = ax - (m.pi/2) #self.direction.y * m.pi
        #self.az = self.direction.z * m.pi

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
            [1, 0, 0, self.x],
            [0, 1, 0, self.y],
            [0, 0, 1, self.z],
            [0, 0, 0, 1]
            ])
        return mat_translate
    
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
    
    @property
    def faces(self):
        return self.model.faces
    
    @property
    def bounding_radius(self) -> float:
        return self.model.bounding_radius

    @property
    def is_convex(self):
        return self.model.is_convex

    def update_matrices(self):
        """
        Update view matrices
        """
        self.s_translation = self.mat_translation
        self.s_mat_rotation= self.mat_rotate_x*self.mat_rotate_y*self.mat_rotate_z

        self.s_mat_full = self.s_translation * self.s_mat_rotation 

    def colliding_ray_bounding_sphere(self, ray:Ray) -> bool:
        """
        Check whether this ray collides with this model's bounding sphere
        """
        #taken from https://gamedev.stackexchange.com/questions/96459/fast-ray-sphere-collision-code
        m = ray.origin - self
        b = m.dot(ray.direction)
        c = m.dot(m) - (self.bounding_radius * self.bounding_radius)

        if c > 0 and b > 0:
            return False
        
        discr = (b*b)-c

        if  discr < 0:
            return False
        return True

    def colliding_ray(self, ray:Ray): #-> Face|None|tuple[Face,p.Vector3]|tuple[None,None]:
        """
        Check whether this ray collides with any face in the model
        """

        if (self-ray.origin).magnitude() > ray.max_dist + self.bounding_radius:
            return (None, None)

        if not self.colliding_ray_bounding_sphere(ray):
            return (None, None)
        
        if self.octree_depth:
            faces_indices = self.bounding_AABB.get_faces_to_test_recursive_ray_with_frac(ray.origin.x, ray.origin.y, ray.origin.z,
                                                                       1.0/ray.direction.x if ray.direction.x else 0,
                                                                       1.0/ray.direction.y if ray.direction.y else 0,
                                                                       1.0/ray.direction.z if ray.direction.z else 0) #todo precalculate div?
            faces = [self.faces[i] for i in faces_indices]
        else:
            faces = self.faces


        lowest_mag = 999
        closest_face = None
        closest_intersection = None
        for face in faces:
            #todo: parallelise this?
            res = face.colliding_ray(ray, self)

            if res:
                #colliding_faces.append( (face, res) )
                mag = (res-ray.origin).magnitude()
                if mag < lowest_mag:
                    lowest_mag = mag
                    closest_face = face
                    closest_intersection = res
        return (closest_face, closest_intersection)
        
        #if colliding_faces:
            #figure out which face was hit first
        #    lowest_mag = 999
        #    closest_intersection = None
        #    closest_face = None
        #    for face, intersection in colliding_faces:
        #        mag = (intersection-ray.origin).magnitude()
        #        if mag < lowest_mag:
        #            closest_face = face
        #            closest_intersection = intersection
        #            lowest_mag = mag
        #    return (closest_face, closest_intersection)
        #else:
        #    return (None, None)

    def delete(self):
        """
        Delete this instance from the worls
        """
        if not self.deleted:
            self.deleted = True
            g.model_instances.remove(self)

            
def load(filename: str, name:str=None, is_convex:bool=False) -> Model:
    """
    Load a model from a file
    """
    data = plyfile.PlyData.read(os.path.join(g.DIR_MODELS,filename))

    points = []
    
    for vert in data['vertex']:
        x = vert['x']
        y = vert['y']
        z = vert['z']
        new_point = Point(x,y,z)
        points.append(new_point)

    faces = []
    for face in data['face']:
        new_face = face['vertex_indices']
        faces.append(new_face)

    if not name:
        name = filename.split('.')[0]
    new_model = Model(name, points, faces, is_convex=is_convex)
    

class ConvexPolygon(Model):
    """
    Mainly a test class
    """
    def __init__(self, points, colour='red') -> None:
        self.points = points

        super().__init__(self.points, [], colour=colour)

    def colliding_convex_polygon(self, poly) -> bool:
        res = GJK.GJK(self.point_array, poly.point_array)
        return res[0]
    
class Box(ConvexPolygon):
    def __init__(self, pos, size, colour=None):
        points = [
            Point(-(size/2), -(size/2), -(size/2)),
            Point((size/2), -(size/2), -(size/2)),
            Point(-(size/2), (size/2), -(size/2)),
            Point((size/2), (size/2), -(size/2)),

            Point(-(size/2), -(size/2), + ((size/2)) ),
            Point((size/2), -(size/2), + ((size/2))),
            Point(-(size/2), (size/2), + ((size/2))),
            Point((size/2), (size/2), + ((size/2)))
        ]

        for point in points:
            point += pos

        super().__init__(points, colour)



