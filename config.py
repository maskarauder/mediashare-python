#!/usr/bin/env python3
from twitchAPI.type import AuthScope
from queue import Queue
from typing import List

# Twitch Specific Settings
APP_TOKEN:str = 'n1na6w6icm414471lfjo06ep0q90ac'
TARGET_CHANNEL:str = 'SwiftIke'

# OBS Specific Settings
OBS_HOST:str = 'localhost'
OBS_PORT:int = 4455
OBS_WEBSOCKET_PASSWORD:str = ''
OBS_SCENE_NAME:str = 'alerts'
OBS_SCENEITEM_NAME:str = 'maskmediashare'

# App Specific Settings
TRIGGER_BIT_VALUE:int = 90                        # i.e. 90 bits says this is a mediashare request, message still must be formatted correctly.
MIN_DURATION:int = 30                             # Minimum duration to run
MAX_DURATION:int = 7 * 60                         # Maximum duration to run
MIN_VIEWS:int = 1000                              # Minimum views required to play the video

# Bits Settings
BITS_PER_SECOND:int = 3                           # How many bits are required per second of video

# Channel Point Settings
CHANNELPOINTS_MEDIASHARE:bool = True              # Allow running for free via Channel Points
CHANELLPOINTS_REWARD_NAME:str = 'MediaShare'      # The case-insensitive name of the Channel Points reward to listen for
CHANNELPOINTS_REWARD_MAX_DURATION:int = 7 * 60    # Maximum duration to run for the channel points reward (cannot exceed MAX_DURATION)

# Globals
queue:Queue = Queue()
TARGET_SCOPE:List[AuthScope] = [AuthScope.BITS_READ]
if CHANNELPOINTS_MEDIASHARE:
    TARGET_SCOPE.append(AuthScope.CHANNEL_READ_REDEMPTIONS)