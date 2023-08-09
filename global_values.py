import os
import pygame as p

WIDTH, HEIGHT = 900, 500
SCREEN_RECT = p.Rect(0,0,WIDTH,HEIGHT)

DIR_FILES = 'files'
DIR_GFX = os.path.join(DIR_FILES, 'gfx')
DIR_SOUND = os.path.join(DIR_FILES, 'sound')
DIR_MODELS = os.path.join(DIR_FILES, 'models')

states = set(('start',))
fullscreen = False

game_clock = None
dt = 0
events = []
keys = {}

fonts = {'info1':p.font.SysFont('consolas', 16)}

models = {}

model_instances = []
hints = []
goal = None

camera = None
player = None
level = None

point_spawners = []

controls = []
info_box = None
pressed_buttons = []

viewport = None

sound_dict:dict[p.mixer.Sound] = {}
world_sounds = []

mx, my = 0, 0
ml, mm, mr = False, False, False