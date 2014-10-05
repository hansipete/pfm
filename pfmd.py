
from time import sleep, gmtime, strftime
import random
import subprocess
import os
import atexit
import select

import ConfigParser

config = ConfigParser.ConfigParser()
config.read("/home/pi/pfm.conf")

keylock = True
pin = config.get('keylock', 'pin')

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

# FICK FACK


# initially open the fifo for writing
mplayer_fifo = open("/home/pi/.mplayer_control", "w")


def add_to_playlist(files_array, playlist_file):
    playlist = playlist_file
    usb_path = '/media/usb'
    f = open(playlist, 'w')
    for item in files_array:
        #print "Write: %s/%s\n" % (usb_path,item)
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
                #print file
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

def update_loop():
    print "In the loop. Wait 1s"
    sleep(1)
    return True

try:

    if keylock:
        print "Pinlock is active"
	print pin
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
