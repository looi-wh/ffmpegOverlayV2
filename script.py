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

arrayOfExtentions = [".avi", ".mkv", ".mov", ".mp4", ".wmv", ".flv", ".webm"] # specify the file extensions to look at
# cwd = os.getcwd() # sets current location [NOT RECOMMENDED - FOR DEBUGGING ONLY]
cwd = "/input_folder" #input folder
cwd_in_progress = "/conversion_folder" #transcoding folder (will create another sub folder to prevent conflicts)
cwd_completed = "/completed_folder" #finished files will come here, can be jellyfin library folder
targetContainer = ".mp4" # set target contatiner [IMPORTANT] - recommended: .mp4
arrayOfSubCodec = ["ass", "srt", "dvb_subtitle", "dvd_subtitle", "mov_text", "subt"] # ignore
arrayofSubExtentions = [".ass", ".srt"] # insert more if you think that your subtitle kept getting deleted or smthing
illegalCharacters = ["'", '"', "<", ">", "|"] # this is important as this script cannot exists with such characters involved
cleanUpList = [".txt", ".html", ".jpg", ".png", ".exe", ".bat", "._"]
removeOringalFile = 1 # delete original files after writing the output files
targetContainer = ".mp4" # set target contatiner [IMPORTANT]
videotarget = "h264" # target video codec
audiotarget = "aac" # target audio codec
audiochannelstTarget = 2 # target audio channels, based on ffmpeg.
removeSubtitles = 1 # removes subtitles from media, the goal of which is to avoid Jellyfin from extracting subtitles on the fly (better control over subtitles)
checkFolderSize = 1800 # abort script if folder size between intervals are not the same [change if you know what you are doing]
subtitleExt = ".srt" # target subtitle format
mediaTargetx = [".en", ".zh", ".ms", ".id", ".zt"] # any files which contain such words will be targeted
subsync = 0 # enable usage of ffsubsync [MUST INSTALL FIRST!]
jellyfinServerLink="http://127.0.0.1:8096" # http to your jellyfin host
jellyfinAPIKey="YOUR_OWN_API_KEY" # generate from your jellyfin > dashboard > API Keys. Generate an API key for this script and paste it here.

# chmod
command = "sudo chmod -R 777 " + cwd
os.system(command)

# check if theres files in cwd
if os.listdir(cwd) == []:
	print("exited due to cwd being empty")
	exit()
else:
	# prevent overlapping tasks by looking at cwd_in_progress
	# replace with a higher value if your system can handle
 	if len(os.listdir(cwd_in_progress)) > 3:
 		print("exited due to cwd_in_progress more than max processes")
 		exit()

# check folder size
if checkFolderSize > 0:
	print("[NOTICE] Checking folder size")
	size = os.path.getsize(cwd)
	print("folder size detected:", size)
	print("waiting for", checkFolderSize, "seconds")
	time.sleep(checkFolderSize)
	size2 = os.path.getsize(cwd)
	print("folder size second check detected", size2)
	if not size == size2:
		print("directory size is detected to be changing, exiting..")
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
	command = "ffmpeg -y -loglevel error -dump_attachment:t '' -i '" + mediaName + "' -map 0:" + streamNum + " -c:s srt -y '" + subtitleName + "'"
	os.system(command) # runs the command
	command = "rm -d -f -r *.ttf *.TTF *.otf *.OTF"
	os.system(command)
	if os.path.getsize(subtitleName)  < 9000:
		print("[WARNING] Subtitle size too small, deleting..")
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
	elif targetLanguage == "eng" and stream_value == 99:
		# runs extract at first stream anyways
		print("[WARNING] english subtitles not found, extracting first subs as english anyways")
		try:
			runExtract(target, target.replace(codecs, extraInfo), "s:0")
		except:
			print("[WARNING] title does not seem to have any subtitles in the first place")


def runFFMPEG(inputname, outputname, videoc, audioc, channels): # runs ffmpeg [configure your custom ffmpeg commands here]
	# the defaults are configured for:
	# made for maximum jellyfin compatibility
	# h264	(4M - 1920x1080 max)
	# aac	(320K - 2 channel audio)
	# full audio and subtitles pass through
	# faststart, profile main
	# -map '0:s?' -c:s mov_text 
	# command = "ffmpeg -i '" + inputname + "' -preset veryfast -c:v copy -c:a copy -y -map 0:v:0 -map 0:a -movflags +faststart -ac 2 -map '0:s?' -c:s mov_text '" + outputname + "' "
	command = "ffmpeg -y -i '" + inputname + "' -preset veryfast -c:v " + videoc +" -c:a " + audioc +" -pix_fmt yuv420p -map 0:v:0 -map 0:a:0 -hide_banner -loglevel panic -movflags +faststart -b:a 192k -ac " + str(channels) + " '" + outputname + "' "
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

def moveFiles(source, destination, rsync):
	global cwd_in_progress, illegalCharacters
	if rsync == 1:
		# uses rsync as the main function
		print("")
		print("running rsync to move files over")
		for file in os.listdir(source):
			d = os.path.join(source, file)
			if os.path.isdir(d):
				command = "rsync -aP '" + str(d) + "' '" + str(destination) + "'"
				os.system(command) # runs the command
				deleteDirectory(d)
		return 1
	else:
		allfiles = os.listdir(source)
		for f in allfiles:
			shutil.move(source + "/" + f, destination + "/" + f)
		return 1



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


def deleteDirectory(inputx):
	try:
		command = "sudo rm -d -r -f '" + str(inputx) + "'"
		os.system(command) # runs the command
		print("[NOTICE] deletion of", inputx, "is a success")
	except OSError as error:
		print(error)
		return 0

def jf_refresh():
	global jellyfinServerLink, jellyfinAPIKey
	command = "curl -v -H 'X-MediaBrowser-Token: " + jellyfinAPIKey + "' -d '' " + jellyfinServerLink + "/Library/Refresh"
	os.system(command)

# clean up extra files downloaded with torrent [remove to disable]
targetFiles = findFiles(cleanUpList, cwd) 
for target in targetFiles: # recursive scrap thru all files in searched list
	for codecs in cleanUpList: # helps with determining the codecs
		if not target.count(codecs) == 0: # prevent works on external
			os.remove(target)
print("[NOTICE] extra files removed from folders")

# move the files from cwd to cwd_in_progress
unique_folder = rog(20)
cwd_in_progress = cwd_in_progress + "/" + str(unique_folder) # create a random 20 chac folder
os.mkdir(cwd_in_progress)
print(cwd_in_progress, " will be the working directory for this session")
moveFiles(cwd, cwd_in_progress, 0)
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
						print("[WARNING] failed", subtitleOutput, " but file might also not exist")
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
						print(targetZero, "passed as the video file met the requirements")
				except OSError as error:
					print(error)
					print(targetZero, "is ignored as an error has occured")

print("[NOTICE] transcode job has been completed! now trying to move the files into", cwd_completed)

# move the files to final directory
try:
	moveFiles(cwd_in_progress, cwd_completed, 1)
	print("[NOTICE] moved files to", cwd_completed)
	print("deleting the rest of the working directory..")
	deleteDirectory(cwd_in_progress)
except:
	print("[FATAL] final process failure, stopping script")
	exit()

if not jellyfinServerLink == "":
	print("")
	print("[NOTICE] sending a post request to", jellyfinServerLink, "(jellyfin server) to refresh library")
	try:
		jf_refresh()
	except OSError as error:
		print(error)
		print("[WARNING] failure to send the refresh request, please refresh manually")

print("job done")