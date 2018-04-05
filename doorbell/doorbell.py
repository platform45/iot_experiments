#!/usr/bin/env python3

import sys
import os
import subprocess

import pyaudio
import threading
import wave
import time
from slackclient import SlackClient 

flicstuff_dir = os.path.abspath(os.path.join(os.path.realpath(__file__), '../../'))
fliclib_dir = os.path.join(flicstuff_dir, 'fliclib-linux-hci')
flicstuff_doorbell_dir = os.path.join(flicstuff_dir, 'doorbell')
fliclib_python_dir = os.path.join(fliclib_dir, 'clientlib/python/')
sys.path.append(fliclib_python_dir)
import fliclib

import logging
logger = logging.getLogger('doorbell')
hdlr = logging.FileHandler(os.path.join(flicstuff_doorbell_dir, 'doorbell.log'))
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.INFO)

ps_grep_output = subprocess.check_output("ps x | grep flicd | grep -v grep | wc -l", shell=True).decode('utf-8').strip()
if (int(ps_grep_output) <= 0):
    logger.info('Starting flic daemon')
    subprocess.call([os.path.join(fliclib_dir, 'bin/armv6l/flicd'), "-d", "-f", os.path.join(flicstuff_dir, 'flic.sqlite3')])
else:
    logger.info('flic daemon already running')

button_mac = "xx:xx:xx:xx:xx:xx"
slack_channel_id = "CXXXXXXXX"

paudio = pyaudio.PyAudio()

class PlaybackStream(threading.Thread):
    def __init__(self, path):
        threading.Thread.__init__(self)
        self.path = os.path.join(flicstuff_doorbell_dir, path)

    def run(self):
        self.wf = wave.open(self.path, 'rb')

        def callback(in_data, frame_count, time_info, status):
            data = self.wf.readframes(frame_count)
            return (data, pyaudio.paContinue)

        stream = paudio.open(format=paudio.get_format_from_width(self.wf.getsampwidth()),
            channels=self.wf.getnchannels(),
            rate=self.wf.getframerate(),
            output=True,
            stream_callback=callback)

        stream.start_stream()

        while stream.is_active():
            time.sleep(0.1)

        stream.stop_stream()
        stream.close()

        self.wf.close()

slack_token = ""
with open(os.path.join(flicstuff_doorbell_dir, "slacktoken.txt"), "r") as f:
    slack_token = f.read()

slack_client = SlackClient(slack_token)

slacking = False
last_slack = 0

class DingDong(threading.Thread):
    def run(self):
        global slacking

        logger.info("sending message to slack...")
        response = slack_client.api_call(
                                    "chat.postMessage",
                                    channel=slack_channel_id,
                                    text="<!here> Someone is at the door"
                                    )
        logger.info(response)
        slacking = False

flic_client = fliclib.FlicClient("localhost")

cc = fliclib.ButtonConnectionChannel(button_mac)

def button_callback(channel, click_type, was_queued, time_diff):
    if was_queued:
        return
    global slacking
    global last_slack
    logger.info(channel.bd_addr + " " + str(click_type) + " queued: " + ("yes" if was_queued  else "no") + ", time_diff: " + str(time_diff))
    if (click_type == fliclib.ClickType.ButtonDown):
        PlaybackStream('door_bell_1.wav').start()
    else:
        PlaybackStream('door_bell_2.wav').start()

    if (click_type == fliclib.ClickType.ButtonUp and not slacking and time.time() - last_slack > 10):
        logger.info("doing it!")
        last_slack = time.time()
        slacking = True
        DingDong().start()
    else:
        logger.info("not doing it :(")

cc.on_button_up_or_down = button_callback

flic_client.add_connection_channel(cc)

logger.info("Okay, press a button!")
PlaybackStream('startup.wav').start()
flic_client.handle_events()
paudio.terminate()
