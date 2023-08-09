import pygame as p
import warnings

import global_values as g
import gameobjects
import cameras
import point_spawners
import projectiles
import sounds

class Tool():
    """
    Base class for tools
    """
    def __init__(self, player, name:str, cooldown:float, use_function, update_function=None, select_function=None) -> None:
        self.name = name
        player.tools[self.name] = self
        self.use_function = use_function
        self.update_function = update_function
        self.select_function = select_function

        self.cooldown = cooldown
        self.last_used = 0

    def select(self):
        """
        Select this tool
        """
        if self.select_function:
            self.select_function()

    def update(self):
        if self.update_function:
            self.update_function()

    def use(self):
        """
        Use this tool
        """

        if self.cooldown:
            current_time = p.time.get_ticks()
            if (current_time - self.last_used) >= self.cooldown*1000:
                self.last_used = current_time
                print('time',(current_time - self.last_used), self.last_used, current_time)
                self.use_function()
                return
        else:
            self.use_function()

class Player(gameobjects.DestructableGameObj):
    def __init__(self, origin: p.Vector3) -> None:
        self.start = p.Vector3(origin).copy()
        super().__init__(origin, 'cube2', collision_groups=set(), colour='gray')

        g.camera = cameras.Camera()

        self._selected_mouse_control = None#'look'#'target'
        self.selected_mouse_control = 'target'

        spawner1 = point_spawners.SmallRangePointSpawner()
        spawner2 = point_spawners.BurstPointSpawner()
        spawner3 = point_spawners.BeamSpawner()
        self.spawners = [spawner1, spawner2, spawner3]

        self.tools = {}
        Tool(self, 'Beam', 0, lambda: None, spawner1.shoot_ray, lambda: self.select_point_spawner(spawner1) )
        Tool(self, 'Vertical Scanner', 0, lambda: None, spawner2.update_burst, lambda: self.select_point_spawner(spawner2) )
        Tool(self, 'Horizontal Scanner', 0, lambda: None, spawner3.move_beam, lambda: self.select_point_spawner(spawner3) )
        #Tool(self, 'missile', 1.0, self.shoot_missile)

        self.selected_point_spawner = None
        self.selected_tool = None
        self.select_tool('Horizontal Scanner')
        

        self.velocity = p.Vector3(0,0,0)
        self.drag = 0.1
        self.velocity_damage_threshold = 9

        self.max_health = 10
        self.max_power = 12
        self._power = self.max_power
        self.powered_controls = {}
        self.current_drain = 0

        self.just_collided = False

        self.hum_sound = sounds.StartEndSound('hum_start', 'hum_middle', 'hum_end')

    @property
    def power(self):
        return self._power
    @power.setter
    def power(self, val):
        if val <= 0:
            self._power = 0
            self.destroy()
        elif val > self.max_power:
            self._power = self.max_power
        else:
            self._power = val

    def drain_power(self):
        """
        Drain the player's power by some amount based on what's active
        """
        #calculate drain
        scale = 0.004

        #UI
        drain_units = 1
        for name,control in self.powered_controls.items():
            if control.visible:
                drain_units += 2
        
        #VELOCITY
        move_scale = 0.15
        drain_units += self.velocity.magnitude()*move_scale

        #POINT
        if self.selected_point_spawner:
            drain_units += 2

        self.current_drain = drain_units

        #actually drain
        old_power = self.power
        self.power -= self.current_drain*scale*g.dt

        if int(old_power) > int(self.power):
            sounds.play_sound('blip2')
            g.info_box.set_info_if_finished( f'POWER REMAINING: { round((self.power/self.max_power)*100) }%' )

    def destroy(self):
        sounds.play_sound('die')
        g.events.append('lose')

    def reset(self):
        """
        Reset the player in between games
        """
        self.health = self.max_health
        self.power = self.max_power

        self.x = self.start.x
        self.y = self.start.y
        self.z = self.start.z

        self.velocity.x = 0
        self.velocity.y = 0
        self.velocity.z = 0

        self.just_collided = False
        self.select_point_spawner(None)
        self.select_tool(None)

        for spawner in self.spawners:
            spawner.clear()

        self.selected_tool = None
        self.select_tool('point_spawner2')

        self.selected_mouse_control = 'target'

    def update(self):
        super().update()

        self.drain_power()

        if g.dt:
            self.velocity *= 1 - (self.drag*g.dt)

        if self.velocity.magnitude():
            if self.velocity.magnitude() < 0.001:
                self.velocity.x = 0
                self.velocity.y = 0
                self.velocity.z = 0

            else:
                self.move(self.velocity*g.dt)


        #if self.velocity.magnitude() >= 4:
        #    self.hum_sound.play()
        #else:
        #    self.hum_sound.stop()
        

        g.camera.xyz = self.xyz
        if self.selected_mouse_control == 'look':
            p.mouse.set_pos((g.WIDTH/2, g.HEIGHT/2))

    def move(self, vec:p.Vector3):
        old_vec = self.xyz
        super().move(vec)

        if vec.magnitude() > 0:
            if old_vec == self.xyz:
                self.on_new_hit()
            else:
                self.just_collided = False

    def on_colliding(self, collider):
        return super().on_colliding(collider)

    def on_new_hit(self):
        self.just_collided = True
        
        if self.velocity.magnitude() >= self.velocity_damage_threshold:
            self.health -= 1
            sounds.play_sound('hit1')
        
        self.velocity = -self.velocity*0.2

    def shoot_missile(self):

        ray_vec = p.Vector3(g.mx, g.my, 100)#g.WIDTH/2, g.HEIGHT/2, 2)

        #proj = g.camera.get_projected(ray_vec, return_vec=False)

        world_ray_vec = g.camera.get_unprojected( ray_vec )
        direction_vec = world_ray_vec - g.camera


        proj = projectiles.Missile(p.Vector3(self.xyz), direction_vec.normalize(), 10)

    def select_point_spawner(self, point_spawner:point_spawners.PointSpawner):
        """
        Select a certain point spawner
        """
        if point_spawner:
            self.selected_point_spawner = point_spawner
        else:
            self.selected_point_spawner = None

    def select_tool(self, tool_name:Tool):
        """
        Select a certain tool
        """

        if not tool_name:
            self.selected_tool = None
        else:
            try:
                if not self.selected_tool or tool_name != self.selected_tool.name:
                    self.tools[tool_name].select()

                    if g.info_box:
                        g.info_box.set_info_if_finished(f'SELECTED TOOL: {tool_name}')

                self.selected_tool = self.tools[tool_name]
            except KeyError as ex:
                warnings.warn(f'Attempted to select non-existent tool {tool_name}')

    @property
    def selected_mouse_control(self) -> str:
        return self._selected_mouse_control
    @selected_mouse_control.setter
    def selected_mouse_control(self, val:str):
        self._selected_mouse_control = val
        if self._selected_mouse_control == 'target':
            p.mouse.set_visible(True)
            p.event.set_grab(False)
        else:
            p.mouse.set_visible(False)
            
            p.event.set_grab(True)
