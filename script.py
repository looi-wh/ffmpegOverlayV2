# !/usr/bin/python3
import platform
import os
from os import system, name # clearScreen
from pathlib import Path
from os import listdir
from os.path import isfile, join
import subprocess
import shutil
import re
import datetime
import time
import sys
import glob
import re
import random
import string

# == script settings ==
arrayOfExtentions = [".avi", ".mkv", ".mov", ".mp4", ".wmv", ".flv", ".webm"] # which file extension to search for
# cwd = os.getcwd() # sets to current location of cd
cwd = "input folder dir" #input folder
cwd_in_progress = "working folder dir" #transcoding folder (will create another sub folder to prevent conflicts)
cwd_completed = "output folder dir" #finished files will come here
targetContainer = ".mp4" # set target contatiner [IMPORTANT]
arrayOfSubCodec = ["ass", "srt", "dvb_subtitle", "dvd_subtitle", "mov_text", "subt"]
cleanUpList = [".txt", ".html", ".jpg", ".png", ".exe", ".bat", "._"]
removeOringalFile = 1 # delete original files after writing the output files
targetContainer = ".mp4" # set target contatiner [IMPORTANT]
videotarget = "h264" # video codec
audiotarget = "aac" # audio codec
audiochannelstTarget = 2
removeSubtitles = 1 # avoid extraction
checkFolderSize = 60 # abort script if folder size between intervals are not the same
subtitleExt = ".srt"
mediaTargetx = [".en", ".zh", ".ms", ".id", "zt"] # any files which contain such words will be targeted by ffsubsync
subsync = 1 # enable usage of ffsubsync

if cwd == "input folder dir" or cwd_in_progress == "working folder dir" or cwd_completed == "output folder dir":
	print("[FATAL] please edit script settings inside the script first")
	exit()

# chmod
command = "sudo chmod -R 777 " + cwd
os.system(command)

# check if theres files in cwd
if os.listdir(cwd) == []:
	exit()
else:
	# prevent overlapping tasks by looking at cwd_in_progress
	# replace with a higher value if your system can handle
 	if len(os.listdir(cwd_in_progress)) > 2:
 		exit()

# check folder size
if checkFolderSize > 0:
	print("[NOTICE] Checking folder size")
	size = subprocess.check_output(['du','-sh', cwd]).split()[0].decode('utf-8')
	time.sleep(checkFolderSize)
	size2 = subprocess.check_output(['du','-sh', cwd]).split()[0].decode('utf-8')
	if not size == size2:
		exit()

def findFiles(arrayOfNames, workingDir): # file files in a given directory
	filtered = []
	for extension in arrayOfNames:
		path = cwd
		files = []
		for r, d, f in os.walk(path):
			for file in f:
				if extension in file:
					files.append(os.path.join(r, file))
		filtered.append(list(filter(lambda k: extension in k, files)))
		combinedFiltered = combineArray(filtered)
	return combinedFiltered

def combineArray(input): # converts two dimension array to one dimension
	combine = []
	for x in input:
		for y in x:
			combine.append(y)
	return combine

def runExtract(mediaName, subtitleName, streamNum): # runs ffmpeg [configure your ffmpeg here]
	# -map '0:s?'
	command = "ffmpeg -loglevel error -dump_attachment:t '' -i '" + mediaName + "' -map 0:" + streamNum + " -c:s srt -y '" + subtitleName + "'"
	os.system(command) # runs the command
	command = "rm -d -f -r *.ttf *.TTF *.otf *.OTF"
	os.system(command)
	if os.path.getsize(subtitleName)  < 9000:
		os.remove(subtitleName)
	return 0

def getLanStream(mediaName, language, streamType):
	global arrayOfSubCodec
	try:
		command = "ffprobe -loglevel error -select_streams " + streamType + " -show_entries stream=index:stream_tags=language -of csv=p=0 '" + mediaName + "' | grep '" + language + "'"
		output = str(subprocess.check_output(command, shell=True))
		numbers = re.findall(r'\d+', output)
	except:
		return 99
	final = 99
	for x in numbers:
		for y in arrayOfSubCodec:
			command = "ffprobe -loglevel error -select_streams " + x + " -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 '" + mediaName + "'"
			if y in str(subprocess.check_output(command, shell=True)):
				final = x
	return final

def extractSubsPackage(mediaName, targetLanguage, extraInfo):
	stream_value = getLanStream(target, targetLanguage, "s")
	if not stream_value == 99:
		runExtract(target, target.replace(codecs, extraInfo), stream_value)

def runFFMPEG(inputname, outputname, videoc, audioc, channels): # runs ffmpeg [configure your custom ffmpeg commands here]
	# the defaults are configured for:
	# made for maximum jellyfin compatibility
	# h264	(4M - 1920x1080 max)
	# aac	(320K - 2 channel audio)
	# full audio and subtitles pass through
	# faststart, profile main
	# -map '0:s?' -c:s mov_text 
	# command = "ffmpeg -i '" + inputname + "' -preset veryfast -c:v copy -c:a copy -y -map 0:v:0 -map 0:a -movflags +faststart -ac 2 -map '0:s?' -c:s mov_text '" + outputname + "' "
	command = "ffmpeg -i '" + inputname + "' -preset veryfast -c:v " + videoc +" -c:a " + audioc +" -pix_fmt yuv420p -map 0:v:0 -map 0:a:0 -hide_banner -loglevel panic -movflags +faststart -b:a 192k -ac " + str(channels) + " '" + outputname + "' "
	os.system(command) # runs the command
	return 0

def runFFPROBE(mediaName, codecsx): 
	global videotarget, audiotarget, audiochannelstTarget, videocTEMP, audiocTEMP, targetContainer, removeSubtitles
	currentVideoCodec = str(subprocess.check_output("ffprobe '" + target + "' 2>&1 >/dev/null |grep Stream.*Video | sed -e 's/.*Video: //' -e 's/[, ].*//'", shell = True))
	currentAudioCodec = str(subprocess.check_output("ffprobe '" + target + "' 2>&1 >/dev/null |grep Stream.*Audio | sed -e 's/.*Audio: //' -e 's/[, ].*//'", shell=True))
	currentSubtitleCheck = int(subprocess.check_output("ffmpeg -i '" + target + "' -c copy -map 0:s -f null - -v 0 -hide_banner && echo $? || echo $?", shell=True))
	try:
		currentAudioChannels = int(subprocess.check_output("ffprobe -i '" + target + "' -show_entries stream=channels -select_streams a:0 -of compact=p=0:nk=1 -v 0", shell = True))
	except:
		currentAudioChannels = 0 # Converts anyways
	skip = 0
	if videotarget in currentVideoCodec:
		videocTEMP = "copy"
		skip += 1
	if audiotarget in currentAudioCodec and int(audiochannelstTarget) == int(currentAudioChannels):
		audiocTEMP = "copy"
		skip += 1
	if str(codecsx) == str(targetContainer):
		skip += 1
	if currentSubtitleCheck == 1 and removeSubtitles == 1: # 0 means found, 1 means not found
		skip += 1
	if skip == 4 and int(removeSubtitles) == 1:
		return 0
	elif skip == 3 and int(removeSubtitles) == 0:
		return 0
	else:
		return 1
	return 1

def rog(length):
	lower = string.ascii_lowercase
	num = string.digits
	allx = lower + num
	temp = random.sample(allx,length)
	rogx = "".join(temp)
	return str(rogx)

def moveFiles(source, destination):
	allfiles = os.listdir(source)
	for f in allfiles:
		shutil.move(source + "/" + f, destination + "/" + f)

def getModifiedPath(originalPath):
	ctitle = originalPath
	illegal = ['NUL',':','*','"','<','>','|', "'"]
	for i in illegal:
		ctitle = ctitle.replace(i, '')
	return ctitle

def runFFSubsync(inputsubs, outputsubs, videofile):
	command = "ffsubsync '" + videofile + "' -i '" + inputsubs + "' --max-offset-seconds=6000000 -o '" + outputsubs + "'"
	os.system(command) # runs the command
	return 0

# remove illegal characters [remove to disable]
for x in range(0, 1):
	targetFiles = findFiles(arrayOfExtentions, cwd) # search for targets
	for target in targetFiles: # recursive scrap thru all files in searched list
		for codecs in arrayOfExtentions: # helps with determining the codecs
			if not target.count(codecs) == 0: # prevent works on external
				if not "._" in target:
					os.renames(target, getModifiedPath(target))
					shutil. rmtree(target) # delete original path
print("[NOTICE] illegal characters removed from filenames")
print("[HINT] removal of illegal characters helps to prevent any scripting issue later on")

# clean up extra files downloaded with torrent [remove to disable]
targetFiles = findFiles(cleanUpList, cwd) 
for target in targetFiles: # recursive scrap thru all files in searched list
	for codecs in cleanUpList: # helps with determining the codecs
		if not target.count(codecs) == 0: # prevent works on external
			os.remove(target)
    

# move the files from cwd to cwd_in_progress
unique_folder = rog(20)
cwd_in_progress = cwd_in_progress + "/" + str(unique_folder) # create a random 20 chac folder
os.mkdir(cwd_in_progress)
print(cwd_in_progress, " will be the working directory for this session")
moveFiles(cwd, cwd_in_progress)
cwd = cwd_in_progress

# search for targets
targetFiles = findFiles(arrayOfExtentions, cwd) 
print(len(targetFiles), "potential targets found")
print("[NOTICE] initial scan completed")

# smartly extract Subtitles [remove to disable]
print("[NOTICE] starting subtitle extraction job")
for target in targetFiles: # recursive scrap thru all files in searched list
	for codecs in arrayOfExtentions: # helps with determining the codecs
		if not target.count(codecs) == 0: # prevent works on external
			if not "._" in target:
				# customize this section according to your needs
				extractSubsPackage(target, "eng", ".english.default.srt")
				extractSubsPackage(target, "chi", ".chinese.srt")
				extractSubsPackage(target, "ind", ".indonesian.srt")
				print("extraction job done for", target)
print("[NOTICE] subtitle extraction completed")

# subtitle sync job using ffsubsync.
# works for media without any subtitles inside the video
print("[NOTICE] start subtitle syncing job")
if subsync == 1:
	print("[NOTICE] using ffsubsync to sync subtitles. this might take awhile")
	for mediaTarget in mediaTargetx:
		targetFiles = findFiles(arrayOfExtentions, cwd) # search for targets
		for target in targetFiles: # recursive scrap thru all files in searched list
			for codecs in arrayOfExtentions: # helps with determining the codecs
				if not target.count(codecs) == 0:
					subtitleOutput = target.replace(codecs, str(mediaTarget) + str(subtitleExt))
					subtitleTarget = subtitleOutput.replace(subtitleExt, str(".input") + str(subtitleExt))
					try:
						os.rename(subtitleOutput, subtitleTarget)
						runFFSubsync(subtitleTarget, subtitleOutput, target)
						if removeOringalFile == 1:
							os.remove(subtitleTarget)
					except:
						print("[WARNING] failed", subtitleOutput, ". please verify files manually")
	print("[NOTICE] subtitle syncing job done")
else:
	print("[ERROR] skipping sync job since subsync isnt enabled")
	print("[HINT] to install ffsubsync, view github.com/smacke/ffsubsync")
	print("[HINT] if you are still struggling, make sure you install ffsubsync with sudo")

# smartly convert video streams
print("[NOTICE] starting transcode job")
print("[HINT] the purpose of this job is to remove the need for future transcoding")
print("[NOTICE] this might take awhile..")
targetFiles = findFiles(arrayOfExtentions, cwd) # search for targets
for target in targetFiles: # recursive scrap thru all files in searched list
	for codecs in arrayOfExtentions: # helps with determining the codecs
		if not target.count(codecs) == 0: # prevent works on external
			if not "._" in target:
				targetZero = target # saves a backup of target filename for a clean output name
				videocTEMP = str(videotarget)
				audiocTEMP = str(audiotarget)
				try:
					if runFFPROBE(target, codecs) == 1:
						if targetContainer in str(target): # check if output filename will clash with input filename
							target = target.replace(codecs, str(".input") + str(codecs)) # new target filename
							os.renames(targetZero, target) # renames the file
						output = targetZero.replace(codecs, targetContainer)
						runFFMPEG(target, output, videocTEMP, audiocTEMP, audiochannelstTarget)
						print(targetZero, "completed successfully")
						if removeOringalFile == 1: # removes original file
							os.remove(target)
					else:
						print(targetZero, "passed")
				except:
					print(targetZero, "is ignored as an error has occured")

print("[NOTICE] transcode job has been completed! now trying to move the files into", cwd_completed)

# move the files to final directory
moveFiles(cwd_in_progress, cwd_completed)
print("[NOTICE] moved files to", cwd_completed)
# delete 
shutil.rmtree(cwd_in_progress)
print("[NOTICE] deleted the remains of", str(nique_folder))

print("job done")