import serlcd
import RPi.GPIO as GPIO


from time import sleep, gmtime, strftime
import random
import subprocess
import os
import atexit
import select
import ConfigParser
import glib

from pyudev import Context, Monitor
import pyudev
from pyudev.glib import GUDevMonitorObserver as MonitorObserver
import threading

# for finding files in usb device
import fnmatch
import os.path
import re

import glib, gio, gobject

###### HIER GEHTS LOS!!!

# configure hardware
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

BTN_UP  = 20
BTN_DWN = 13
BTN_SET = 5

GPIO.setup(BTN_UP, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(BTN_DWN, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(BTN_SET, GPIO.IN, pull_up_down = GPIO.PUD_UP)

LED_ON = 0
LED_TX = 1


# load config file
config = ConfigParser.ConfigParser()
config.read("/home/pi/pfm.conf")

# define runtime constants
locked      = True
pin_target  = config.get('keylock', 'pin')
pin_pos     = 0
pin_input   = [0,0,0,0]

print pin_target


# initially open the fifo for writing
mplayer_fifo = open("/home/pi/.mplayer_control", "w")

# initialize display
lcd = serlcd.SerLCD()


# pin lock functions

def pinlock():

    # prepare screen for pin input
    lcd.clear()
    lcd.cursor(1,3)
    lcd.write('Unlock Pocket FM')

    pin_pos_offset = 7
    for i in range(4):
        lcd.cursor(3,pin_pos_offset+i*2)
        lcd.write(str(pin_input[i]))

    # enable cursor for input
    lcd.cursor(3,pin_pos_offset)
    lcd.show_cursor()

    while locked:
        pass

    # hide cursor when done
    lcd.show_cursor(False)

def update_pin_screen():
    pin_pos_offset = 7
    for i in range(4):
        lcd.cursor(3,pin_pos_offset+i*2)
        lcd.write(str(pin_input[i]))

    # enable cursor for input
    lcd.cursor(3,pin_pos_offset+pin_pos*2)

def increase_digit(pin):
    if pin_input[pin_pos] < 9:
        pin_input[pin_pos] += 1
    else:
        pin_input[pin_pos] = 0

    update_pin_screen()

def decrease_digit(pin):
    if pin_input[pin_pos] > 0:
        pin_input[pin_pos] -= 1
    else:
        pin_input[pin_pos] = 9

    update_pin_screen()

def set_digit(pin):
    global pin_pos, pin_input, pin_target
    
    # next digit
    if pin_pos < 3:
        pin_pos += 1
        update_pin_screen()
    else:

        # compare strings
        pin = "".join( map(str, pin_input) )
        
        if pin == pin_target:
            print "Hurra"
            locked = False
            #pin_success()
        else:
            print "noe"
            # reset and cycle
            pin_pos = 0
            pin_input = [0,0,0,0]
            update_pin_screen()

# initially bound inputs to pinlock
GPIO.add_event_detect(BTN_UP,  GPIO.RISING, callback = increase_digit, bouncetime = 100)
GPIO.add_event_detect(BTN_DWN, GPIO.RISING, callback = set_digit, bouncetime = 100)
GPIO.add_event_detect(BTN_SET, GPIO.RISING, callback = set_digit, bouncetime = 100)




# Handling USB events
def add_to_playlist(files_array, playlist_file):
    playlist = playlist_file
    usb_path = '/media/usb'
    f = open(playlist, 'w')
    for item in files_array:
        f.write("%s/%s\n" % (usb_path,item))
    f.close()
    return playlist

def list_audio_files(dir):
    print "Scan dir: " + dir
    audio_files = []
    for ROOT,DIR,FILES in os.walk(dir):
        for file in FILES:
            if file.endswith(('.mp3','.MP3')) and not file.startswith(('.')):
                audio_files.append(file)
    return audio_files

def device_event(observer, action, device):

    dev_type = device.get('DEVTYPE')
    proc = None

    # there are two events, another for usb_interface - drop it
    if dev_type == 'usb_device':

        if action == 'add':
            print 'USB attached. Play files from USB.'
            mount_point = '/media/usb' # always mounted there get_mount_point(dev_name)
            
            while len(os.listdir(mount_point)) == 0:
                # wait for usb to mount
                sleep(.1)

            # create playlist in writable area (/media/)
            playlist_file = '/media/usb-playlist.txt'
            files_array = list_audio_files('/media/usb')
            add_to_playlist(files_array, playlist_file)

            # send command to mplayer fifo
            cmd = "loadlist %s\n" % playlist_file
            print(cmd)
	    mplayer_fifo.write(cmd)
            mplayer_fifo.flush()

        elif action == 'remove':
            print 'USB removed. Switch to local playlist'
            mplayer_fifo.write("loadlist /home/pi/audio/playlist.txt\n")
            mplayer_fifo.flush()            


# Main program loop
def update_loop():
    print "In the loop. Wait 1s"
    sleep(1)
    return True

# Initial program
try:
    # Ask for correct pin first
    if locked:
        print "Pinlock is active"
        pinlock()
	
	exit()
    
    context = Context()
    monitor = Monitor.from_netlink(context)

    monitor.filter_by(subsystem='usb')
    observer = MonitorObserver(monitor)

    observer.connect('device-event', device_event)
    monitor.start()
    
    gobject.threads_init()
    glib.idle_add(update_loop)
    glib.MainLoop().run() 
        
finally:
    # close the fifo
    mplayer_fifo.close()
    GPIO.cleanup()
