# Flic button Doorbell

A doorbell using a flic button that makes a doorbell sound and sends a message to slack.

# What you will need:

1. A [flic button](https://flic.io/)
2. A Raspberry Pi with a Bluetooth LE chip (or some similar sort of setup)
3. [fliclib-linux-hci](https://github.com/50ButtonsEach/fliclib-linux-hci)
4. Python 3.5+
5. `pyaudio` and `slackclient` python libraries (install with pip)

# Installation

## Basic Setup

1. Set up `fliclib-linux-hci` (follow their instructions) to pair a flic button and make note of the MAC address.
2. Put the MAC address of your flic button in `doorbell.py` as the `button_mac` variable.
3. Put your slack bot's auth token in a file called `slacktoken.txt` in the root of this directory.
4. Place this directory in the same directory as `fliclib-linux-hci`.
5. Set your slack channel ID in the variable `slack_channel_id`.

## Running as a service

1. Edit `init.d/doorbell` and make sure it refers to the correct location of `doorbell.py` (by default it is `/home/pi/flicstuff/doorbell/doorbell.py`).
2. Copy `init.d/doorbell` to `/etc/init.d` (you may need to use `sudo`).
3. Run `sudo update.d doorbell defaults`.
4. Then you can start the service with `sudo service doorbell start`.
5. When you hear the startup sound (`startup.wav`), the doorbell is listening.

# Notes

1. `door_bell_1.wav` and `door_bell_2.wav` are the button-down and button-up sounds respectively.
2. The slack bot will post `@here Someone is at the door` which could be annoying for some people. Consider using a separate channel or remove the `@here`.
3. There is a 10-second "debounce" on the slack message, meaning that it will not post a message more than once every ten seconds.
4. Pressing the doorbell really fast causes a lot of threads to spin up, and the sound will start sounding slow and stretched out.
5. Logs are output to `doorbell.log` in this directory.