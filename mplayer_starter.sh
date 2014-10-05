#!/bin/bash -

if pidof -x "pulseaudio" >/dev/null; then
  # wait a seconds for process to be ready to receive audio
  sleep 2
  # run as pi user
  /bin/su - pi -c "/usr/bin/mplayer -ao pulse -vo null -nolirc -framedrop -slave -input file=/home/pi/.mplayer_control -playlist /home/pi/audio/playlist.txt"
fi

# sleep for some time otherwise process will be disabled for 5min
sleep 2
