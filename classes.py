#!/usr/bin/env python3
from config import *
from urllib.parse import urlparse, parse_qs
from pprint import pprint
from time import sleep

import requests
from bs4 import BeautifulSoup

class MediaShareEntry(object):
    _link: str = ''
    _start_time: int = 0
    _duration: int = 0

    def __init__(self, link, start_time, duration) -> None:
        if 'youtube' in link:
            u = urlparse(link)
            if u.query == '':
                raise Exception('Invalid YouTube URL! (Missing params.)')
            p = parse_qs(u.query)
            if 'v' not in p:
                raise Exception('Invalid YouTube URL! (Failed to parse video id.)')
            self._link = 'https://www.youtube.com/watch?v=' + p['v'][0]
        elif 'youtu.be' in link:
            u = urlparse(link)
            if u.path == '':
                raise Exception('Invalid YouTube URL! (Missing video ID.)')
            self._link = 'https://www.youtube.com/watch?v=' + str(u.path).strip('/')
            print(u.path)
            if u.query != '':
                p = parse_qs(u.query)
            else:
                p = []
        else:
            raise Exception(f'Invalid link {link}')



        end_of_video = MediaShareEntry.check_view_count(self._link)
        
        if start_time == 0 and 't' in p:
            self._start_time = int(p['t'][0].rstrip('s'))

        if (start_time + duration) > end_of_video:
            duration = end_of_video - start_time

        self._start_time = start_time
        self._duration = duration
        self._link = self._link.replace('youtube', 'yout-ube', 1)

    def __str__(self) -> str:
        if self._start_time == 0:
            return self._link
        return self._link + '&t=' + str(self._start_time)

    @classmethod
    def check_view_count(cls, link: str) -> int:
        resp = requests.get(link)
        if resp.status_code != 200:
            raise Exception('Failed to retrieve YouTube video!')

        soup = BeautifulSoup(resp.content, 'html.parser')
        
        views = soup.select_one('meta[itemprop="interactionCount"][content]')['content']
        end_of_video = soup.select_one('meta[itemprop="duration"][content]')['content']

        if views is None or end_of_video is None:
            raise Exception('Failed to retrieve YouTube view count!')

        if int(views) < MIN_VIEWS:
            raise Exception('YouTube video did not have sufficient views!')
        
        end_of_video = end_of_video.lstrip('PT')
        days = 0
        hours = 0
        minutes = 0
        seconds = 0
        if 'D' in end_of_video:
            dlist = end_of_video.split('D', 1)
            days = int(dlist[0])
            end_of_video = dlist[1]
        if 'H' in end_of_video:
            dlist = end_of_video.split('H', 1)
            hours = int(dlist[0])
            end_of_video = dlist[1]
        if 'M' in end_of_video:
            dlist = end_of_video.split('M', 1)
            minutes = int(dlist[0])
            end_of_video = dlist[1]
        if 'S' in end_of_video:
            end_of_video = end_of_video.rstrip('S')
            seconds = int(end_of_video)
        
        if days > 0:
            hours += days * 24
        if hours > 0:
            minutes += hours * 60
        if minutes > 0:
            seconds += minutes * 60

        return seconds