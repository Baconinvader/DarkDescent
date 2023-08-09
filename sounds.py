import pygame as p
import os
import warnings

import global_values as g

#sound_reserves = {}

#def get_reserved_for_sound(sound_name:str):
#    return 3

def load_sounds(sound_dir:str=None):
    """
    Load all the sounds in a directory into the sound dict
    """
    if not sound_dir:
        sound_dir = g.DIR_SOUND

    for file_name in os.listdir(sound_dir):
        file_name_no_ext,ext = file_name.split('.')

        if ext != 'wav' and ext != 'ogg':
            continue

        sound = p.mixer.Sound(os.path.join(sound_dir,file_name))

        g.sound_dict[file_name_no_ext] = sound

def play_sound(sound_name:str):
    """
    Convinience function for playing sounds
    """
    sound = g.sound_dict.get(sound_name)
    #print(sound_name)
    if sound:
        sound.play()
    else:
        warnings.warn(f'Could not find sound "{sound_name}"')


class StartEndSound():
    """
    Sound that's actually composed as three sounds, a start, a middle and an end sound
    """
    def __init__(self, start_sound_name:str, middle_sound_name:str, end_sound_name:str) -> None:
        self.start_sound:p.mixer.Sound = g.sound_dict[start_sound_name]
        self.middle_sound:p.mixer.Sound = g.sound_dict[middle_sound_name]
        self.end_sound:p.mixer.Sound = g.sound_dict[end_sound_name]

        self.playing_sound = 0
        self.channel:p.mixer.Channel = None

    def play(self):
        if self.playing_sound == 0:
            self.channel = p.mixer.find_channel(True)
            self.channel.play(self.start_sound)
            self.playing_sound = 1

        elif self.playing_sound == 1:
            if not self.channel.get_busy():
                self.channel.play(self.middle_sound, -1)
                self.playing_sound == 2

    def stop(self):
        if self.playing_sound > 0:
            self.channel.stop()
            self.channel.play(self.end_sound)
            self.playing_sound = 0


class WorldSound(p.Vector3):
    def __init__(self, origin:p.Vector3, sound_name, vol=1):
        super().__init__(origin)

        self.sound_name = sound_name
        self.channel = p.mixer.find_channel(False)

        if not self.channel:
            warnings.warn(f'Failed to find channel to play sound "{self.sound_name}"')

        self.sound = g.sound_dict[self.sound_name]
        self.vol = vol

        

        self.creation_timestamp = p.time.get_ticks()

        self.deleted = False
        g.world_sounds.append(self)

        self.update()
        self.channel.play(self.sound)    

    def update(self):
        dist = (self.xyz - g.player.xyz).magnitude()

        if abs(dist) <= 0.2:
            vol = 4
        else:
            #no inverse square law here
            vol = 1/dist
        vol *= self.vol

        #todo add an option for set_source_location here?
        self.channel.set_volume(vol)

        if p.time.get_ticks() - self.creation_timestamp > self.sound.get_length()*1000:
            self.delete()

    def delete(self):
        if not self.deleted:
            self.deleted = True
            self.sound.stop()
            g.world_sounds.remove(self)

        