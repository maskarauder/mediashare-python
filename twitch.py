#!/usr/bin/env python3

# Twitch API
from twitchAPI.twitch import Twitch
from twitchAPI.oauth import CodeFlow
from twitchAPI.helper import first
from twitchAPI.pubsub import PubSub
from uuid import UUID

# App Specific
from config import *
from classes import *
from obs import *
import threading
import webbrowser

obs_thread = None

async def add_to_queue(forced_end:int, message:str) -> None:
    global obs_thread

    link = None
    start_time = -1
    end_time = -1

    tokens = message.split()
    for token in tokens:
        if token.startswith('cheer'):
            continue
        elif link is not None and end_time != -1:
            break

        if link is None and 'youtube' in token or 'youtu.be' in token:
            link = token

        if end_time != -1:
            continue

        ncolon = token.count(':')
        if ncolon > 2:
            continue

        time_vals = token.split(':')
        time_vals.reverse()
        if time_vals is None:
            time_vals = [token]

        time = 0
        try:
            time = int(time_vals[0])
            if ncolon == 1:
                time += int(time_vals[1]) * 60
            if ncolon == 2:
                time = int(time_vals[2]) * 60 * 60
        except ValueError:
            continue

        if start_time == -1:
            start_time = time
        elif end_time == -1:
            end_time = time

    if link is not None:
        if start_time == -1:
            start_time = 0

        forced_end_time = start_time + forced_end
        if end_time == -1:
            end_time = forced_end

        if end_time < start_time:
            end_time = start_time + end_time

        end_time = end_time - start_time
            
        if end_time > forced_end_time:
            end_time = forced_end_time

        try:
            entry = MediaShareEntry(link, start_time, end_time)
            queue.put(entry)
            print(f'Added {entry._link}, start_time = {entry._start_time}, duration = {entry._duration}')
        except Exception as e:
            print(f'Failed to add MediaShare entry.\nlink = {link}, start_time = {start_time}, end_time = {end_time}, exception = {e}')

        if obs_thread is None or not obs_thread.is_alive():
            obs_thread = threading.Thread(target=play_media, args=[])
            obs_thread.start()


async def callback_bits(uuid: UUID, data: dict) -> None:
    nbits = data['data']['bits_used']
    link = None
    start_time = -1
    end_time = -1
    if nbits >= TRIGGER_BIT_VALUE:
        forced_end = MIN_DURATION + ((nbits - TRIGGER_BIT_VALUE) / BITS_PER_SECOND)
        if forced_end > MAX_DURATION:
            forced_end = MAX_DURATION
        await add_to_queue(forced_end, data['data']['chat_message'])


async def callback_channelpoints(uuid:UUID, data:dict) -> None:
    if not CHANNELPOINTS_MEDIASHARE:
        return

    reward = data['data']['redemption']['reward']['title']
    if reward.lower() != CHANELLPOINTS_REWARD_NAME.lower():
        return
    
    user_input = data['data']['redemption']['user_input']
    if user_input is None or user_input == '':
        return
    
    forced_end = MAX_DURATION
    if 'CHANNELPOINTS_REWARD_MAX_DURATION' in vars() or 'CHANNELPOINTS_REWARD_MAX_DURATION' in globals():
        forced_end = CHANNELPOINTS_REWARD_MAX_DURATION
        if forced_end > MAX_DURATION:
            forced_end = MAX_DURATION
    
    await add_to_queue(forced_end, user_input)

async def setup_twitch_listener():
    #twitch = await Twitch(APP_TOKEN, APP_SECRET)
    twitch = await Twitch(APP_TOKEN, None, authenticate_app=False)
    
    target_scope = TARGET_SCOPE

    #auth = UserAuthenticator(twitch, target_scope, force_verify=False)
    auth = CodeFlow(twitch, target_scope)

    code, url = await auth.get_code()
    browser = webbrowser.get(None)
    browser.open(url, new=2)

    print(f'Please enter code {code} in the browser to continue.')
    token, refresh_token = await auth.wait_for_auth_complete()

    #add User authentication
    await twitch.set_user_authentication(token, target_scope, refresh_token)
    user = await first(twitch.get_users(logins=[TARGET_CHANNEL]))

    # Start PubSub
    pubsub = PubSub(twitch)
    pubsub.start()

    if AuthScope.BITS_READ in target_scope:
        bits_uuid = await pubsub.listen_bits(user.id, callback_bits)
    if CHANNELPOINTS_MEDIASHARE and AuthScope.CHANNEL_READ_REDEMPTIONS in target_scope:
        channel_points_uuid = await pubsub.listen_channel_points(user.id, callback_channelpoints)
    input('Awaiting bits. press Enter to close...')

    if AuthScope.BITS_READ in target_scope:
        await pubsub.unlisten(bits_uuid)
    if AuthScope.CHANNEL_READ_REDEMPTIONS in target_scope:
        await pubsub.unlisten(channel_points_uuid)
    pubsub.stop()
    await twitch.close()