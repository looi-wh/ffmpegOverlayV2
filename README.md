# ffmpegOverlay v2
Designed with care and concern for best automation

## Designed to extract subtitles and transcode large amount of files without user interactions

Recently I have started to explore Jackett, Sonarr, Radarr and Bazarr. These tools are useful, but whats more useful is what if I can have those files processed to optimise compability with more devices/browsers. And so I created this.

## Features
- Identify specifed languages and extract them accordingly
- Sync subtitles to audio using ffsubsync (made mainly due to bazarr)
- Transcode video and audio codecs to proper requirements
- Stop script if conversion folder/queue reached a certain limit
- Stop script if input folder has a size differences between one minute (can be adjusted)
- Anti fail system (Continue script even if one file fails) - [double edged sword, does not respect ctrl + c]
- Designed to run without maintenance for a long period of time

## Warning
- You should always run this script inside a screen
- Edit the script first before running (else it will exit unconditionally)
- DO NOT CTRL C THIS SCRIPT. There are try functions in this script and it will delete your files if you try to stop it without caution
- To stop script, you can either reboot the entire system, close the window or invalid the pathing by renaming the files to something else

## Installation/Setting up
Script requires [python3](https://www.python.org/downloads/), [ffmpeg](https://www.ffmpeg.org/) and [ffubsysnc](https://github.com/smacke/ffsubsync) to run.
Install the dependencies first.

```sh
sudo apt-get update
sudo apt install python3 python3-pip ffmpeg
sudo pip3 install ffsubsync
```
ffsubsync is not really required but it is recommended to help reduce subtitle timing mistakes. must first enable in script

Ideally, you can insert this line to run the script every 30 minutes as a cronjob.
This will run the script inside a screen so you can use screen-dr to view the progress.
Script will exit immediately if working folder is full or input folder is empty.
```sh
*/30 * * * * screen -dm bash -c 'sudo python3 path_to_script; exit'
```

Else you can also start a normal instance which will only run once.
```sh
sudo python3 path_to_script
```

## Deciding your workflow
The script is designed to have 3 folders:
- input (can also be sonarr/radarr root folder - which the script will check for files ready for conversion)
- working folder (should be an empty folder - the script will move files from input folder to this folder for conversion)
- output (can be jellyfin library folder - finished files will be moved to this folder once everything is ready)

So the script will run in this order:
- check input folder for files. if empty, exit
- check working folder for existing conversion. if a certain limit is reached, exit
- script will then process the files
- once completed, script will move them to output folder and exit
- script can also be adjusted to send a refresh library signal to Jellyfin
