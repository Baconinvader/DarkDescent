import pygame as p
p.font.init()
import math as m
import os

import global_values as g

import models
import gameobjects
import GJK
import cameras
import players
import controls
import gfx
import obstacles
import pickups
import sounds


#box_model = models.Box((0,0,0), 3, 'red')
#box_model2 = models.Box((0,0,5), 4, 'blue')
#box_model3 = models.Box((13,0,0), 6, 'yellow')

p.mixer.init()
p.display.set_caption('Dark Descent')
import random
if random.randint(1,5) == 5:
    p.display.set_caption('Sub-Optimal')


sounds.load_sounds()

cube_model = models.load('cube2.ply', is_convex=True)
#tri1_model = models.load('tri1.ply')
#tri_instance = gameobjects.GameObj((10, 0, 0), 'tri1')
#tri2_model = models.load('tri2.ply')
fish_model = models.load('shark.ply')
sphere_model = models.load('sphere1.ply', is_convex=True)



level_model = models.load('level.ply')
g.level = gameobjects.GameObj((15, -10, 20), 'level', octree_depth=4, do_convex_check=False)

g.screen = p.display.set_mode((g.WIDTH, g.HEIGHT))
p.display.set_icon(gfx.li('icon'))
controls.View3D(p.Rect(200,0,500,500))


g.fullscreen = False
def toggle_fullscreen():
    """
    Toggle between fullscreen and not fullscreen
    """
    g.fullscreen = not g.fullscreen

    if g.fullscreen:
        g.screen = p.display.set_mode((g.WIDTH, g.HEIGHT), p.FULLSCREEN|p.SCALED)
    else:
        g.screen = p.display.set_mode((g.WIDTH, g.HEIGHT))


g.game_clock = p.time.Clock()

g.player = players.Player((20, 0, 20))


#BACKGROUNDS
controls.Background(p.Rect(0,0,g.WIDTH,g.HEIGHT), gfx.li('win_background'), active_state='win')
controls.Background(p.Rect(0,0,g.WIDTH,g.HEIGHT), gfx.li('gameover_background'), active_state='gameover')
controls.Background(p.Rect(0,0,g.WIDTH,g.HEIGHT), gfx.li('start_background'), active_state='start')

controls.Background(p.Rect(0,0,200,500), gfx.li('background_left'))
controls.Background(p.Rect(700,0,200,500), gfx.li('background_right'))

#SELECTABLE CONTROLS
#controls.Button(p.Rect(g.viewport.rect.right+10,10,32,32), gfx.li('button_target'), lambda :  g.player.select_tool('missile') )
viewport_right = g.viewport.rect.right
rect = p.Rect(viewport_right+48,40,96,48)
controls.Button(rect, gfx.li('button_look'), lambda : g.player.select_tool('Beam') )
rect = rect.move(0, 52)
controls.Button(rect, gfx.li('button_radar'), lambda : g.player.select_tool('Vertical Scanner') )
rect = rect.move(0, 52)
controls.Button(rect, gfx.li('button_beam'), lambda : g.player.select_tool('Horizontal Scanner') )
rect = rect.move(0, 52)
controls.Button(rect, gfx.li('button_none'), lambda : (g.player.select_tool(None), g.player.select_point_spawner(None)) )


#POWER BAR
rect = p.Rect(20,42,164,15)
c_power_bar = controls.Measure(rect, gfx.li('power_bar_segment_on'), gfx.li('power_bar_segment_off'), g.player, 'power', g.player.max_power)
c_power_usage_bar = controls.Measure(rect.move(0,20), gfx.li('power_usage'), None, g.player, 'current_drain', 14)

#POWERED CONTROLS

rect = p.Rect(20,116,162,27)
c_health_bar = controls.Measure(rect, gfx.li('light_on'), gfx.li('light_off'), g.player, 'health', g.player.max_health)
controls.Switch(p.Rect(16,rect.y-30,32,16), gfx.li('switch_on'), gfx.li('switch_off'), lambda s:c_health_bar.set_visible(s), True)
#controls.TwoState( p.Rect(16,rect.y+32,32,32), gfx.li('collision_light_on'), gfx.li('collision_light_off'), lambda: g.player.just_collided)

#rect = p.Rect(0,128+32,200,64)
#def get_coord_info():
#    if g.goal:
#        goal_dist = str(round( (g.goal-g.player).magnitude(), 1)).zfill(1)
#    else:
#        goal_dist = '???'
#    return f'''
#    X {str(round(g.player.x,1)).zfill(1)} Y {str(round(g.player.y,1)).zfill(1)} Z {str(round(g.player.z,1)).zfill(1)}
#     Target: {goal_dist} units away.
#    '''
#c_coords = controls.TextBox(rect, g.fonts['info1'], get_coord_info, padding=0, text_colour='white')
#controls.Switch(p.Rect(16,rect.y-16,32,16), gfx.li('switch_on'), gfx.li('switch_off'), lambda s:c_coords.set_visible(s), True)

rect = p.Rect(64, 198, 64, 64)
c_compass = controls.Compass(rect)
controls.Switch(p.Rect(16,rect.y-38,32,16), gfx.li('switch_on'), gfx.li('switch_off'), lambda s:c_compass.set_visible(s), True)

rect = p.Rect(24+16, 336+8, 128, 128)
c_radar = controls.Radar(rect)
controls.Switch(p.Rect(16,rect.y-52,32,16), gfx.li('switch_on'), gfx.li('switch_off'), lambda s:c_radar.set_visible(s), True)

powered_controls = {
    'health_bar':c_health_bar,
    #'coords':c_coords,
    'compass':c_compass,
    'radar':c_radar
}
g.player.powered_controls = powered_controls

#MENU BUTTONS
controls.Button(p.Rect(g.WIDTH*0.9, g.HEIGHT*0.83, 64, 64), gfx.li('fullscreen_toggle'), toggle_fullscreen, active_state='start')


rect= p.Rect(g.WIDTH*0.5 - 128, g.HEIGHT*0.75, 256, 64)
controls.Button(rect, gfx.li('button_start'), lambda: start_game(), active_state='start')
controls.Button(rect.move(0,-64), gfx.li('button_menu'), lambda: go_to_start(), active_state='gameover')
controls.Button(rect.move(0,-64), gfx.li('button_menu'), lambda: go_to_start(), active_state='win')



tutorial_manager = controls.TutorialManager()
controls.InfoBox(p.Rect(702, 284, 196, 212))

def reset_game():
    """
    Clear all old game state and data
    """
    for model_instance in g.model_instances[:]:
        if model_instance == g.level:
            #no need to reset level itself
            continue
        if model_instance == g.player:
            continue

        model_instance.delete()

    g.player.reset()
    #tutorial_manager.reset()


    #FIRST ROOM
    pickups.Health(p.Vector3(12, -13, 92))

    #TIGHT TURN
    #pickups.Battery(p.Vector3(100, -13, 104))
    pickups.Battery(p.Vector3(-11, -13, 102))
    pickups.Health(p.Vector3(-11, -13, 100))

    #RIGHT TUNE
    pickups.Battery(p.Vector3(-67, -12, 67))

    #BONUS ROOM
    obstacles.Mine(p.Vector3(-111, -13, 91))
    pickups.Health(p.Vector3(-121, -17, 100))

    #DROP 1
    obstacles.Mine(p.Vector3(-67, -24, 20))
    obstacles.Mine(p.Vector3(-57, -64, 20))

    obstacles.Mine(p.Vector3(-90 -80 -45))

    obstacles.Mine(p.Vector3(-84, -88, -48))

    #FORK
    obstacles.Mine(p.Vector3(-129, -84, -43))
    pickups.Health(p.Vector3(-123, -84, -40))

    #LEFT FORK
    obstacles.Mine(p.Vector3(-193, -84, -10))
    pickups.Health(p.Vector3(-208, -87, -4.5))
    pickups.Battery(p.Vector3(-209, -86, -3.5))

    #RIGHT FORK
    #-238 -102 -45
    obstacles.Fish(p.Vector3(-238 -102 -45))

    #JOIN
    obstacles.Mine(p.Vector3(-397, -122, 16))

    #DROP 2
    pickups.Battery(p.Vector3(-107, -83, -41))

    #DROP 3
    obstacles.Mine(p.Vector3(-341, -158, 88))
    obstacles.Mine(p.Vector3(-345, -164, 105))

    #FINAL CAVE 1
    pickups.Battery(p.Vector3(-296, -168, 97))
    pickups.Health(p.Vector3(-235, -152, 80))

    #FINAL CAVE 2
    obstacles.Mine(p.Vector3(-169, -160, 81))

    #FINAL
    pickups.Goal(p.Vector3(-77, -195-10, 75))

p.mixer_music.load(os.path.join(g.DIR_SOUND, 'music_main.ogg'))

def go_to_start():
    g.states = set(('start',))

def start_game():
    """
    Start the game from the start menu
    """
    print('start!')
    reset_game()
    controls.Overlay(g.SCREEN_RECT, 'black', 255, 0, 2.0)
    g.states = set(('main',))
    tutorial_manager.progress()
    p.mixer_music.play()

def win():
    print('WIN!')
    reset_game()
    controls.Overlay(g.SCREEN_RECT, 'black', 255, 0, 1.0)
    g.states = set(('win',))

def lose():
    print('lose')
    reset_game()
    g.states = set(('gameover',))
    controls.Overlay(g.SCREEN_RECT, 'black', 255, 0, 4.0)

def handle_events():
    for ev in g.events:
        if ev == 'win':
            win()

        if ev == 'lose':
            lose()

    g.events.clear()



def handle_input():
    g.mx, g.my = p.mouse.get_pos()
    g.ml, g.mm, g.mr = p.mouse.get_pressed()

    camera_move_speed = m.pi*0.3 *g.dt
    
    mouse_move_events = 0
    for ev in p.event.get():
        if ev.type == p.KEYDOWN:
            if ev.key == p.K_SPACE and 'main' in g.states:
                if g.player.selected_mouse_control == 'look':
                    g.player.selected_mouse_control = 'target'
                else:
                    g.player.selected_mouse_control = 'look'
            
            if ev.key == p.K_ESCAPE:
                toggle_fullscreen()

        if ev.type == p.QUIT:
            g.running = False

        if ev.type == p.MOUSEMOTION and mouse_move_events < 5:
            if g.player.selected_mouse_control == 'look' and 'main' in g.states:
                mouse_move_events += 1

                mx, my = ev.rel

                g.camera.ay += mx*camera_move_speed
                g.camera.ax -= my*camera_move_speed

                g.camera.ax = max(min(g.camera.ax,1.4),-1.4)


    g.keys = p.key.get_pressed()
    move_speed = 20 * g.dt
    
    dt = min(g.dt, 0.5)

    if 'main' in g.states:
        if g.keys[p.K_LEFT]:
            g.camera.ay -= camera_move_speed

        if g.keys[p.K_RIGHT]:
            g.camera.ay += camera_move_speed

        if g.keys[p.K_UP]:
            g.camera.ax += camera_move_speed

        if g.keys[p.K_DOWN]:
            g.camera.ax -= camera_move_speed


        move_vec = p.Vector3(0.0, 0.0, 0.0)
        if g.keys[p.K_w]:   
            move_vec.x -= m.sin(g.camera.ay)
            move_vec.y += m.sin(g.camera.ax)
            move_vec.z += m.cos(g.camera.ay)
        if g.keys[p.K_s]:
            move_vec.x += m.sin(g.camera.ay)
            move_vec.y -= m.sin(g.camera.ax)
            move_vec.z -= m.cos(g.camera.ay)
            

        if g.keys[p.K_a]:
            move_vec.x -= m.sin(g.camera.ay -(m.pi/2) )
            move_vec.z += m.cos(g.camera.ay -(m.pi/2))
        if g.keys[p.K_d]:
            move_vec.x += m.sin(g.camera.ay -(m.pi/2) )
            move_vec.z -= m.cos(g.camera.ay -(m.pi/2))

        move_vec *= move_speed
        g.player.velocity += move_vec

        if g.keys[p.K_SPACE]:
            if g.player.selected_tool:
                g.player.selected_tool.use()

def update():
    for model_instance in g.model_instances[:]:
        model_instance.update()

    if g.player.selected_tool:
        g.player.selected_tool.update()

    #todo only update one spawner
    for point_spawner in g.point_spawners:
        point_spawner.update()

    for hint in g.hints[:]:
        hint.update()

    for control in g.controls:
        if control.active_state in g.states:
            control.update()

    for world_sound in g.world_sounds:
        world_sound.update()

    for button in g.pressed_buttons:
        button.press()

    tutorial_manager.update()

    g.pressed_buttons.clear()

    g.camera.update_matrices()

def draw():
    #for model in g.model_instances:
    #    if model != g.level:
    #        g.camera.draw_model_instance(model)

    if g.player.selected_point_spawner:
        g.player.selected_point_spawner.draw()

    g.camera.finish_draw()

    for control in g.controls:
        if control.visible and control.active_state in g.states:
            control.draw()

    

g.dt = 0

g.running = True
#start_game()
#g.player.select_tool('Vertical Scanner')
while g.running:
    g.screen.fill('black')
    handle_events()
    handle_input()
    update()
    draw()

    if not g.dt and g.player.selected_tool:
        g.player.selected_tool.use()

    g.dt = min(g.game_clock.tick(60)/1000, 0.4)

    
    #if p.time.get_ticks() > 10*1000:
    #    break

    p.display.flip()