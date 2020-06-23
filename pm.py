#!/usr/bin/python

#
# Control logitech media server with the Powermate bluetooth
# 
# Press powermate to connect it to a player.
# From any player other players can be controlled using the LMSTools library which calls the LMS API.
#
# The following commands are recognized:
# - press powermate     send play/pause to logitech media server
# - turn clockwise      volume up
# - turn anticlockwie   volume down
#
# Press powermate for 10 seconds to turn it off.
#
# LED n the powermate is currently not supported.
#

from powermate import Powermate, PowermateDelegate
import argparse
import time

# default LED value
led_value = 0xA0

# Logitech media player definitions
SERVER_IP = "lms"
PLAYER_NAME = "woonkamer"

# signal pressing Control-C to stop (you have to press it twice)
control_c_pressed = False

from LMSTools import LMSServer
import logging
import signal
import sys
import time

def signal_handler(signal, frame):
    global control_c_pressed
    logging.debug('You pressed Ctrl+C!')
    controls_c_pressed = True
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
#logging.getLogger('pygatt').setLevel(logging.DEBUG)
logging.getLogger('bgapi').setLevel(logging.DEBUG)
logging.info('Powermate volume control for a Logitech Media Server player.')
logging.info('Default Logitech media server: %s', SERVER_IP)
logging.info('Default music player: %s', PLAYER_NAME)

server= LMSServer(SERVER_IP)
logging.info(server)

# Find the player by name
myplayer = None;
players = server.get_players()
nrOfPlayers = 0
curPlayer   = 0
logging.debug(players)
for player in players:
    nrOfPlayers += 1
    logging.info("Player : %s", player);
    if player.name==PLAYER_NAME:
        myplayer = player
        curPlayer = nrOfPlayers
logging.info('Detected  %d players.', nrOfPlayers)
logging.info('Current player %d.', curPlayer)
if myplayer is None:
    logging.info('Player %s is not detected.', PLAYER_NAME)
    sys.exit(0)

def change_player():
    global myplayer, nrOfPlayers, curPlayer
    myplayer = None;
    players = server.get_players()
    nextPlayer = (curPlayer + 1) % (nrOfPlayers + 1)
    if nextPlayer == 0:
        nextPlayer = 1
    logging.info("Next player : %d", nextPlayer);
    nrOfPlayers = 0
    logging.debug(players)
    for player in players:
        nrOfPlayers += 1
        logging.info("Player : %s", player);
        if nextPlayer == nrOfPlayers:
            myplayer = player;
            curPlayer = nrOfPlayers
    logging.info('Detected  %d players.', nrOfPlayers)
    logging.info('Now controlling %s.', myplayer.name)
    return

def get_volume(zone):
    "get current volume"
    try:
        result = zone.volume
        logging.debug("%s, volume: %d", zone.name, result)
    except:
        logging.warning("%s, Cannot read volume", zone.name)
        result = 0;
        pass;
    return result

def play_previous(zone):
    "skip to previous track"
    logging.info("Previous track")
    try:
        zone.prev()
    except:
        logging.warning("%s, Cannot play previous track", zone.name)
        pass;
    return

def play_next(zone):
    "skip to next track"
    logging.info("Next track")
    try:
        zone.next()
    except:
        logging.warning("%s, Cannot play next track", zone.name)
        pass;
    return

def play_pause(zone):
    "toggle play/pause"
    logging.info("Play/pause track")
    try:
        zone.toggle()
    except:
        logging.warning("%s, Cannot play/pause", zone.name)
        pass;
    return

def change_volume(zone, new_vol):
    "set volumne"
    logging.info("Volume: %d", new_vol)
    try:
        zone.volume = new_vol
    except:
        logging.warning("%s, Cannot play/pause", zone.name)
        pass;
    return


def update_led(led_value_change):
    global led_value
    led_value = led_value + led_value_change
    if led_value > 0xFF:
        led_value = 0xFF
    elif led_value < 0x00:
        led_value = 0x00
    #logging.debug("LED: %02X" % led_value)
    #device.char_write(uuid_led, bytearray([led_value]), False)
    return

def led_off():
    #device.char_write(uuid_led, bytearray([0x80]), False)
    return

def handle_notify(handle, value):
    logging.debug("Received notification data: %s" % binascii.hexlify(value))
    return


class PrintEvents(PowermateDelegate):
    def __init__(self, addr):
        self.addr = addr

    def on_connect(self):
        print('Connected to %s' % self.addr)

    def on_disconnect(self):
        print('Disconnected from %s' % self.addr)

    def on_battery_report(self, val):
        print('Battery: %d%%' % val)

    def on_press(self):
        print('Press')
        play_pause(myplayer)

    def on_long_press(self, t):
        print('Long press: %d seconds' % t)
        change_player()

    def on_clockwise(self):
        print('Clockwise')
        update_led(5)
        logging.debug("clockwise turn")
        new_vol = get_volume(myplayer)
        new_vol = new_vol + 3
        if new_vol < 0:
            new_vol=0
        elif new_vol > 100:
            new_vol=100
        change_volume(myplayer, new_vol)
        led_off();

    def on_counterclockwise(self):
        print('Counterclockwise')
        update_led(-5)
        logging.debug("counter clockwise turn")
        new_vol = get_volume(myplayer)
        new_vol = new_vol - 3
        if new_vol < 0:
            new_vol=0
        elif new_vol > 100:
            new_vol=100
        change_volume(myplayer, new_vol)
        led_off();

    def on_press_clockwise(self):
        print('Press clockwise')

    def on_press_counterclockwise(self):
        print('Press counterclockwise')


def main():
    global p, control_c_pressed
    parser = argparse.ArgumentParser(description='Print Powermate events')
    parser.add_argument('address', metavar='bluetooth_addr', type=str,
                        help='Bluetooth address of Powermate')
    args = parser.parse_args()

    p = Powermate(args.address, PrintEvents(args.address))
    while not control_c_pressed:
        time.sleep(5)
    p.stop()

main()
