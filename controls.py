import pygame as p
import pygame.gfxdraw as pg
import math as m

import global_values as g
import gfx
import sounds

class Control():
    """
    Base class for all UI control stuff
    """
    def __init__(self, rect:p.Rect, surf:p.Surface=None, active_state='main', visible=True, **kwargs) -> None:
        self.rect = rect
        self.surf = surf

        self.active_state = active_state
        self.visible = visible

        self.__dict__.update(kwargs)

        self.deleted = False
        g.controls.append(self)

    def set_visible(self, val):
        self.visible = val

    def reset(self):
        """
        Reset this control back (somewhat) to its original state
        """
        pass

    def delete(self):
        if not self.deleted:
            self.deleted = True
            g.controls.remove(self)

    def update(self):
        pass

    def draw(self):
        if self.surf:
            g.screen.blit(self.surf, self.rect)
        else:
            p.draw.rect(g.screen, 'green', self.rect, 2)

class Overlay(Control):
    """
    Temporary overlay over screen
    """
    def __init__(self, rect:p.Rect, colour, start_alpha:int, end_alpha:int, time:float, **kwargs):
        surf = p.Surface((rect.w, rect.h))
        surf.fill(colour)
        
        self.start_timestamp = p.time.get_ticks()
        self.time = time

        self.start_alpha = start_alpha
        self.end_alpha = end_alpha
        
        super().__init__( rect, surf)


    def reset(self):
        self.delete()
        return super().reset()
        
    def update(self):
        super().update()
        frac = (p.time.get_ticks() - self.start_timestamp)/(self.time*1000)
        if frac >= 1:
            self.delete()
        else:
            change_alpha = self.end_alpha-self.start_alpha
            a = min(max( int(self.start_alpha + (change_alpha*frac)), 0), 255)

            self.surf.set_alpha(a)

    def draw(self):
        return super().draw()

class Background(Control):
    def __init__(self, rect: p.Rect, surf: p.Surface = None, **kwargs) -> None:
        super().__init__(rect, surf, **kwargs)

class Button(Control):
    def __init__(self, rect: p.Rect, surf:p.Surface, press_function, **kwargs) -> None:
        
        self.unpressed_surf = surf.copy()
        self.highlighted_surf, self.pressed_surf = self.create_surface_variants(surf)

        self.press_function = press_function
        self.highlighted = False
        self.pressed = False

        super().__init__(rect, **kwargs)

    def create_surface_variants(self, surf:p.Surface):
        temp_surf = p.Surface((surf.get_width(), surf.get_height()), p.SRCALPHA)

        highlighted_surf = surf.copy()
        temp_surf.fill((64, 64, 64, 64))
        #temp_surf.set_alpha(64)
        highlighted_surf.blit(temp_surf, (0,0))

        pressed_surf = surf.copy()
        temp_surf.fill((128, 128, 128, 128))
        #temp_surf.set_alpha(128)
        pressed_surf.blit(temp_surf, (0,0))

        return highlighted_surf, pressed_surf

    def update(self):
        if self.rect.collidepoint((g.mx, g.my)):
            if not self.highlighted:
                sounds.play_sound('highlight')
            self.highlighted = True
        else:
            self.highlighted = False

        if g.ml and self.highlighted:
            if not self.pressed:
                g.pressed_buttons.append(self)
                self.pressed = True
        else:
            self.pressed = False
        return super().update()

    def press(self):
        sounds.play_sound('button_click')
        self.press_function()

    def draw(self):

        if self.highlighted:
            if self.pressed:
                self.surf = self.pressed_surf
            else:
                self.surf = self.highlighted_surf
        else:
            self.surf = self.unpressed_surf

        super().draw()

class Switch(Button):
    """
    Control that can be clicked to switch between states
    """
    def __init__(self, rect: p.Rect, on_surf: p.Surface, off_surf: p.Surface, press_function, start_state=True, **kwargs) -> None:
        self.on_unpressed_surf = on_surf
        self.on_highlighted_surf, self.on_pressed_surf = self.create_surface_variants(self.on_unpressed_surf)

        self.off_unpressed_surf = off_surf
        self.off_highlighted_surf, self.off_pressed_surf = self.create_surface_variants(self.off_unpressed_surf)

        self.start_state = start_state
        

        super().__init__(rect, on_surf, press_function, **kwargs)

        self._state = self.start_state
        self.state = self.start_state

    def reset(self):
        super().reset()
        self.state = self.start_state

    def press(self):
        sounds.play_sound('button_switch')
        self.state = not self.state
        
    @property
    def state(self):
        return self._state
    @state.setter
    def state(self, val):
        self._state = val

        if self._state == True:
            self.unpressed_surf = self.on_unpressed_surf
            self.highlighted_surf = self.on_highlighted_surf
            self.pressed_surf = self.on_pressed_surf
        else:
            self.unpressed_surf = self.off_unpressed_surf
            self.highlighted_surf = self.off_highlighted_surf
            self.pressed_surf = self.off_pressed_surf

        self.press_function(self._state)

class Measure(Control):
    """
    Control that displays a certain number of objects based on a variable value
    """
    def __init__(self, rect:p.Rect, on_surf: p.Surface, off_surf: p.Surface, obj:object, val_name:str, max_val:int, padding=4, **kwargs) -> None:
        self.padding = padding

        self.on_surf = on_surf
        self.off_surf = off_surf

        self.obj = obj
        self.val_name = val_name

        self.icon_width, self.icon_height = self.on_surf.get_size()

        self.max_val = max_val
        icon_rect = p.Rect(rect.x, rect.y, (self.icon_width+self.padding)*self.max_val, self.icon_height )

        rect.union_ip(icon_rect)

        super().__init__(rect, None, **kwargs)

    def draw(self):
        val = int(round(self.obj.__getattribute__(self.val_name)))

        x = self.rect.x
        for i in range(val):
            g.screen.blit(self.on_surf, (x,self.rect.y))
            x += self.icon_width+self.padding

        if self.off_surf:
            for j in range(val,self.max_val):
                g.screen.blit(self.off_surf, (x,self.rect.y))
                x += self.icon_width+self.padding

class View3D(Control):
    """
    Where we draw our 3D stuff
    We only expect to have one
    """
    def __init__(self, rect: p.Rect, **kwargs) -> None:
        super().__init__(rect, **kwargs)

        g.viewport = self

        self.target_cursor = gfx.li('target_cursor')
        self.target_cursor_width = self.target_cursor.get_width()
        self.target_cursor_height = self.target_cursor.get_height()

        #TODO: baked properties

    @property
    def x(self):
        return self.rect.x
    @property
    def y(self):
        return self.rect.y
    
    @property
    def w(self):
        return self.rect.w
    @property
    def half_w(self):
        return self.rect.w/2
    
    @property
    def h(self):
        return self.rect.h
    @property
    def half_h(self):
        return self.rect.h/2


    @property
    def vec(self):
        return p.Vector3(self.rect.x, self.rect.y, 0)

    def draw(self):
        if g.player.selected_mouse_control == 'target':
            if self.rect.collidepoint((g.mx, g.my)):
            
            
                p.mouse.set_visible(False)
                g.screen.blit(self.target_cursor, (g.mx-(self.target_cursor_width/2), g.my-(self.target_cursor_height/2)) )
            else:
                p.mouse.set_visible(True)

        p.draw.rect(g.screen, 'gray', self.rect, 1)

class TextBox(Control):
    """
    Control for showing text
    """
    def __init__(self, rect: p.Rect, font:p.Font, text_function, text_colour='black', padding=4, **kwargs) -> None:
        self.text_function = text_function

        self._text = ''
        self._old_text = '-'

        self.font = font
        self.line_h = self.font.size('I')[1]
        self.text_colour = text_colour

        self._surf = p.Surface((rect.w, rect.h), p.SRCALPHA)
        self.padding = padding
        self.rect = rect #hack to avoid issues with text property
        self.text
        
        self.bound_text = True

        super().__init__(rect, self.surf, **kwargs)

    @property
    def text(self) -> str:
        self._text = self.text_function()
        return self._text

    @property
    def surf(self) -> p.Surface:
        if self.text != self._old_text:
            self._old_text = self._text

            pad_rect = self.rect.inflate(-self.padding*2, -self.padding*2)
            #text has changed so render it again
            self._surf.fill((0,0,0,0))
            #self._surf = self.font.render(self._text, False, self.text_colour)

            if not self._text:
                return self._surf

            words = self._text.split()
            current_line = ''
            x = self.padding
            y = self.padding
            i = 0
            if len(words) == 1:
                line = self.font.render(current_line, False, self.text_colour)
                self._surf.blit(line, (x,y))
                return self._surf

            for word in words:
                line_w = self.font.size(current_line + ' ' + word)[0]
                if line_w > pad_rect.w:
                    line = self.font.render(current_line, False, self.text_colour)
                    self._surf.blit(line, (x,y))

                    y += self.line_h

                    current_line = word
                else:
                    current_line = current_line + ' ' + word

                if current_line:
                    line = self.font.render(current_line, False, self.text_colour)
                    self._surf.blit(line, (x,y))

                i += 1

            
        return self._surf
    @surf.setter
    def surf(self, val):
        pass

class TutorialManager():
    """
    Not really a control, but used by infobox
    """
    def __init__(self):
        
        self.dirty_state = True
        self.states = ['start1', 'start2', 'tool', 'look', 'move', 'power', 'health', 'final1', 'end', 'end']
        self.state = 'None'

        self.state_change_timestamp = 0

    def can_progress(self, state:str) -> bool:
        """
        Check if we can progress onto the next state
        """

        min_time = 4

        if self.state == 'end':
            return False

        if self.state == 'start1' or self.state == 'start2':
            if self.time_since_state_change() >= 5.0:
                return True
            
        elif self.state == 'tool':
            if self.time_since_state_change() >= min_time and g.player.selected_tool:
                return True
            
        elif self.state == 'look':
            if self.time_since_state_change() >= min_time and g.player.selected_mouse_control == 'look':
                return True
        
        elif self.state == 'move':
            if self.time_since_state_change() >= min_time and g.keys[p.K_w] or g.keys[p.K_a] or g.keys[p.K_s] or g.keys[p.K_d]:
                return True
            
        elif self.state == 'power':
            if g.info_box.displayed_current_info() and self.time_since_state_change() >= 8.0:
                return True

        elif self.state == 'health':
            if g.info_box.displayed_current_info() and self.time_since_state_change() >= 8.0:
                return True
            
        elif self.state == 'final1':
            if g.info_box.displayed_current_info() and self.time_since_state_change() >= 8.0:
                return True

            
        return False

    def progress(self):
        """
        Go to next state
        """
        if self.state not in self.states:
            self.state = self.states[0]
        else:
            i = self.states.index(self.state)
            if i >= len(self.states)-1:
                return
            i += 1
            self.state = self.states[i]

        self.dirty_state = True
        self.state_change_timestamp = p.time.get_ticks()

    def time_since_state_change(self) -> float:
        return (p.time.get_ticks() - self.state_change_timestamp)/1000

    def reset(self):
        self.state = self.states[0]
        self.dirty_state = True
        self.state_change_timestamp = 0

    def get_text(self, state:str):
        """
        Get the text that should be shown for this state
        """

        text = ''
        if self.state == 'start1':
            text = 'PREPARING INSTRUCTION SEQUENCE...'

        elif self.state == 'start2':
            text = 'Welcome operator. Your objective is to locate and retrieve the lost cargo at the bottom of this cave.'

        elif self.state == 'tool':
            text = 'Due to the extreme depths, there is insufficient natural light to help you navigate.\
                  Please instead select one of the LiDAR viewers on the top left of your control panel.'
            
        elif self.state == 'look':
            text = 'Well done. Please get acquainted with the LiDAR view by pressing [SPACE] and looking \
            around with the mouse.'
            
        elif self.state == 'move':
            text = 'Move around and get your bearings with [W A S D]. Be careful to avoid colliding with any walls or obstacles.'
        
        elif self.state == 'power':
            text = 'You only have a limited amount of power, so please act quickly to avoid its depletion. \
                Your current power, and its rate of depletion, is shown at the top left. If you wish, you may disable \
                    certain navigation tools to conserve power.'
            
        elif self.state == 'health':
            text = 'Please also pay attention to the structural integrity of this craft. It is also displayed at the top left.'

        elif self.state == 'final1':
            text = 'Please proceed through the cave as quickly as possible. Good luck. (Toggle fullscreen with [ESCAPE].)'

        return text

    def update(self):
        if self.dirty_state and g.info_box.displayed_current_info():
            g.info_box.info = self.get_text(self.state)
            self.dirty_state = False

        if self.can_progress(self.state):
            self.progress()


class InfoBox(TextBox):
    """
    Textbox for showing info to the player
    """
    def __init__(self, rect:p.Rect):
        self._info = ''
        self.new_info_timestamp = 0
        self.info_reveal_speed = 32
        self.old_char_count = 0
        
        super().__init__(rect, g.fonts['info1'], self.get_current_info)

        g.info_box = self
        
        

        self.background = gfx.li('info_box_background')

        self.info = ''

    @property
    def info(self):
        return self._info
    
    def displayed_current_info(self) -> bool:
        """
        Whether or not this info box has finished revealing all of current information
        """
        if self.revealed_chars == len(self.info):
            return True
        else:
            return False
        
    def set_info_if_finished(self, val:str):
        """
        Update the info in this info box, but only if it's finished revealing it's current information
        """
        if self.displayed_current_info():
            self.info = val

    @info.setter
    def info(self, val:str):
        self.new_info_timestamp = p.time.get_ticks()
        self._info = val
        if 'main' in g.states:
            sounds.play_sound('info_notification')

    @property
    def revealed_chars(self) -> int:
        """
        How many characters of the current info are being displayed
        """
        time_diff = (p.time.get_ticks() - self.new_info_timestamp)/1000
        chars = min(len(self.info), int(time_diff*self.info_reveal_speed) )

        if chars != self.old_char_count:
            self.old_char_count = chars
            sounds.play_sound('text_char')
        return chars

    def get_current_info(self):
        """
        Text function that gets the shown portion of the current text
        """

        return self.info[:self.revealed_chars]
    
    def draw(self):
        g.screen.blit(self.background, self.rect)
        super().draw()

class Compass(Control):
    """
    Control for showing direction
    """
    def __init__(self, rect:p.Rect, **kwargs):
        background = gfx.li('compass_base')
        super().__init__(rect, background, **kwargs)

    def draw(self):
        super().draw()

        ang = g.camera.ay
        ex = self.rect.centerx + m.cos(ang)*(self.rect.w*0.4)
        ey = self.rect.centery + m.sin(ang)*(self.rect.h*0.4)

        p.draw.line(g.screen, 'red', self.rect.center, (ex,ey), 2 )

class TwoState(Control):
    """
    Control for showing different graphics based on a boolean condition
    """
    def __init__(self, rect:p.Rect, on_gfx:p.Surface, off_gfx:p.Surface, eval_function):
        self.on_gfx = on_gfx
        self.off_gfx = off_gfx
        self.eval_function = eval_function
        super().__init__(rect, self.surf)

    @property
    def surf(self) -> p.Surface:
        if self.eval_function():
            return self.on_gfx
        else:
            return self.off_gfx

    @surf.setter
    def surf(self, val):
        pass

class Radar(Control):
    """
    Radar which reveals the rough location of certain objects
    """
    def __init__(self, rect:p.Rect):
        super().__init__(rect, gfx.li('radar_background'))

        self.h_range = 60
        self.v_range = 40

        self.tagged_objects = []
        self.refresh_cooldown = 0.5
        self.last_refresh = 0

        self.padding = 3

    def refresh(self):
        """
        Update some info
        """
        self.tagged_objects.clear()

        for obj in g.model_instances:
            if obj.colour:# != 'white'
                if abs(obj.y - g.player.y) <= self.v_range:
                    h_diff = p.Vector2(obj.x - g.player.x, obj.z - g.player.z).magnitude()
                    if h_diff <= self.h_range:
                        self.tagged_objects.append(obj)

        
    def update(self):
        if p.time.get_ticks() - self.last_refresh >= self.refresh_cooldown:
            self.last_refresh = p.time.get_ticks()
            self.refresh()
        return super().update()
    
    def draw(self):
        super().draw()

        scale = (self.rect.w/2) / self.h_range
        for obj in self.tagged_objects:
            h_diff = p.Vector2(obj.x - g.player.x, obj.z - g.player.z)*scale
            h_diff.rotate_ip(-m.degrees(g.camera.ay))


            size = 4*scale #obj.bounding_radius

            if h_diff.magnitude()+size >= self.rect.w/2 - self.padding:
                h_diff.scale_to_length(self.rect.w/2 - size - self.padding)

            dx = self.rect.centerx - h_diff.x
            dy = self.rect.centery - h_diff.y

            dh = abs(obj.y - g.player.y)

            #todo, pg draw?
            colour = p.Color(obj.colour)
            colour.a = int(255* (1-(dh/self.v_range)))
            pg.filled_circle(g.screen, int(dx), int(dy), int(size), colour)

        if g.player.selected_point_spawner:
            spawner = g.player.selected_point_spawner
            #todo optimise
            for i in range(spawner.point_count):
                point = spawner.points_list[i]
                
                h_diff = p.Vector2(point.x - g.player.x, point.z - g.player.z)*scale
                

                if h_diff.magnitude()+size >= self.rect.w/2 - self.padding:
                    continue
                
                h_diff.rotate_ip(-m.degrees(g.camera.ay))
                dx = int(self.rect.centerx - h_diff.x)
                dy = int(self.rect.centery - h_diff.y)

                g.screen.set_at((dx,dy), point.colour)
