# script.service.bluray_iso_utils
Kodi addon - Used to make all videos in a bluray iso file available and scrapeable to Kodi

# Description
This addon will enable the Kodi user to access all videos on a bluray iso file.

With this addon you are able to:
- give each tv show episode an individual entry in the Kodi library (as if they are .mkv files)
- are able to use video extras with all the extras on the bluray iso
- can set default audio and subtitle streams
- enter a multiple movie iso file correctly in the Kodi library, each movie will have it's own entrypoint
- enter different cut's of a movie correctly in the Kodi library (from 1 bluray iso file)
- skip the recap ("Previously on ...") on your tv shows
- should work with a mix of Kodi devices (win 7, Openelec, ...)

This is done through the use of .strm files. No symlinks need to be made. 

#Usage
Directory structure
--------------------
This addon is developed with the "default" directory layout of Kodi in mind  [see: 1.1 Simple](http://kodi.wiki/view/Naming_video_files/TV_shows)

You need to add a directory where the bluray iso files are stored. This directory NEEDS to be named ".BIUfiles" (in windows name this dir ".BIUfiles."). Kodi wil NOT scan these iso files. 

![alt text](https://raw.githubusercontent.com/Wimpie-ccc/helperfiles/master/TV-file-structure.png)

The .strm files have followinf structure:

special://home/addons/script.service.bluray_iso_utils/resources/media/BIU_Black_Animation.720p.mp4
# .BIUfiles/
#
#
#
#
#
#
#
# Comments can be put in the file from here
# Line 1: contains a link to our dummy animation file
# Line 2: Link to the bluray iso file, relative from the directory containing the '.strm' file. eg: "# .BIUfiles/myblurayiso.iso"
# Line 3: Playlist of the bluray we need to play, always needs to be 5 numbers. eg: "# 00005"
# line 4: Optional time from were we start playing, format uu:mm:ss. Can be blank if not needed. eg: "# 00:45:23"
# Line 5: optional time when we stop playing this playlist, format uu:mm:ssm. Can be blank if not needed. eg: "# 01:30:55"
# Line 6: Audio channel, starts from 1. Can be blank if not needed. eg: "# 2"
# Line 7: Subtitle, internal starts from 1, 0 means use external subtitles. Can be blank if not needed. eg: "# 2"
# Line 8: Reserved
# Line 9: Reserved

sdf
