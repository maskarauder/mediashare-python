#!/usr/bin/env python3

# OBS API
import obsws_python as obs

# App Specific
from config import *
from classes import *
from pprint import pprint
from time import sleep
from typing import Tuple

scene = None
source = None
inputobj = None
pause = False
skip = False

def on_scene_item_enable_state_changed(data):
    global source
    global pause

    if data['sceneItemId'] == source['sceneItemId']:
        if data['sceneItemEnabled']:
            pause = False
        else:
            pause = True


def on_input_settings_changed(data):
    global inputobj

    if data.input_uuid == inputobj['inputUuid']:
        if data.input_settings['url'] is None or data.input_settings['url'] == '':
            skip = True


def play_media():
    global scene
    global source
    global inputobj
    global pause
    global skip

    cl = None
    while not queue.empty():
        cl, ecl = connect_to_obs()
        if scene is None or source is None or inputobj is None or cl is None or ecl is None:
            print('Failed to connect to OBS. Retrying in 1 sec...')
            sleep(1)
            continue
    
        next = queue.get()

        print('Playing ' + str(next) + ' for ' + str(next._duration) + 's')
        settings = cl.get_input_settings(inputobj['inputName'])
        settings.input_settings['url'] = str(next)
        cl.set_input_settings(inputobj['inputName'], settings.input_settings, True)
        cl.set_input_mute(inputobj['inputName'], False)

        cl.set_scene_item_enabled(scene, source['sceneItemId'], True)

        ecl.callback.register(on_scene_item_enable_state_changed)
        ecl.callback.register(on_input_settings_changed)
        
        counter = next._duration
        while counter > 0:
            sleep(1)
            counter -= 1
            if pause:
                counter = next._duration
                continue
            if skip:
                skip = False
                break

        ecl.callback.deregister(on_scene_item_enable_state_changed)
        ecl.callback.deregister(on_input_settings_changed)

        cl.set_scene_item_enabled(scene, source['sceneItemId'], False)

        cl.disconnect()


def connect_to_obs() -> Tuple:
    global scene
    global source
    global inputobj

    scene = None
    source = None
    inputobj = None

    cl = obs.ReqClient(host=OBS_HOST, port=OBS_PORT, password=OBS_WEBSOCKET_PASSWORD, timeout=3)

    if OBS_SCENE_NAME:
        scene = OBS_SCENE_NAME
    else:
        scene = cl.get_current_program_scene().scene_name
    if scene is None:
        cl.disconnect()
        return None, None

    sceneitems = cl.get_scene_item_list(scene)
    if sceneitems is None:
        cl.disconnect()
        return None, None

    inputs = cl.get_input_list()
    if inputs is None:
        cl.disconnect()
        return None, None

    for i in inputs.inputs:
        if i['inputName'] == OBS_SCENEITEM_NAME:
            inputobj = i
            break

    if inputobj is None:
        cl.disconnect()
        return None, None

    for sceneitem in sceneitems.scene_items:
        if sceneitem['sourceName'] == OBS_SCENEITEM_NAME:
            source = sceneitem
            break
        
    if source is None:
        cl.disconnect()
        return None, None

    ecl = obs.EventClient(host=OBS_HOST, port=OBS_PORT, password=OBS_WEBSOCKET_PASSWORD, timeout=3)

    return cl, ecl