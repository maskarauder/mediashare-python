#!/usr/bin/env python3

# OBS API
import obsws_python as obs

# App Specific
from config import *
from classes import *
from pprint import pprint
from time import sleep

scene = None
source = None
inputobj = None

def play_media():
    global scene
    global source
    global inputobj

    cl = None
    while not queue.empty():
        cl = connect_to_obs()
        if scene is None or source is None or inputobj is None:
            sleep(1)
            continue
    
        next = queue.get()
        print('Playing ' + str(next) + ' for ' + str(next._duration) + 's')
        settings = cl.get_input_settings(inputobj['inputName'])
        settings.input_settings['url'] = str(next)
        cl.set_input_settings(inputobj['inputName'], settings.input_settings, True)
        cl.set_input_mute(inputobj['inputName'], False)

        cl.set_scene_item_enabled(scene, source['sceneItemId'], True)
        sleep(next._duration)
        cl.set_scene_item_enabled(scene, source['sceneItemId'], False)

        if cl is not None:
            cl.disconnect()


def connect_to_obs() -> obs.ReqClient:
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
        return None

    sceneitems = cl.get_scene_item_list(scene)
    if sceneitems is None:
        cl.disconnect()
        return None

    inputs = cl.get_input_list()
    if inputs is None:
        cl.disconnect()
        return None

    for i in inputs.inputs:
        if i['inputName'] == OBS_SCENEITEM_NAME:
            inputobj = i
            break

    if inputobj is None:
        cl.disconnect()
        return None

    for sceneitem in sceneitems.scene_items:
        if sceneitem['sourceName'] == OBS_SCENEITEM_NAME:
            source = sceneitem
            break
        
    if source is None:
        cl.disconnect()

    return cl