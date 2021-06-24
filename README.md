# ffmpegOverlay v2
## Designed to extract subtitles and transcode large amount of files without user interactions

Recently I have started to explore Jackett, Sonarr, Radarr and Bazarr. These tools are useful, but whats more useful is what if I can have those files processed to optimise compability with more devices/browsers. And so I created this.

## Features
- Identify specifed languages and extract them accordingly
- Sync subtitles to audio using ffsubsync (made mainly due to bazarr)
- Transcode video and audio codecs to proper requirements
- Stop script if conversion folder/queue reached a certain limit
- Stop script if input folder has a size differences between one minute (can be adjusted)
- Anti fail system (Continue script even if one file fails)

## Warning
- You should always run this script inside a screen
- Edit the script first before running (else it will exit unconditionally)

## Installation
Script requires [python3](https://www.python.org/downloads/), [ffmpeg](https://www.ffmpeg.org/) and [ffubsysnc](https://github.com/smacke/ffsubsync) to run.
Install the dependencies first.

```sh
sudo apt-get update
sudo apt install python3 python3-pip ffmpeg
sudo pip3 install ffsubsync
```

Ideally, you can insert this line to run the script every 10 minutes as a cronjob.
This will run the script inside a screen so you can use screen-dr to view the progress.
Script will exit if working folder is full or input folder is empty.
```sh
*/10 * * * * screen -dm bash -c 'sudo python3 path_to_script; exit'
```

Else you can also start a normal instance which will only run once.
```sh
sudo python3 path_to_script
```

## Deciding your workflow
The script is designed to have 3 folders:
- input (can also be sonarr/radarr root folder)
- working (should be an empty folder)
- output (can be jellyfin library folder)

So the script will run in this order:
- check input folder for files. if empty, exit
- check working folder for existing conversion. if a certain limit is reached, exit
- script will then process the files
- once completed, script will move them to output folder and exit
