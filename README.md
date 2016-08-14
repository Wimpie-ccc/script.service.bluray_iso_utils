# script.service.bluray_iso_utils
Kodi addon - Used to make all videos in a bluray iso file available and scrapeable to Kodi

## Description
This addon will enable the Kodi user to access all videos on a bluray iso file.

With this addon you are able to:
- import tv shows and movies on bluray iso's in the Kodi library (as if they are .mkv files)
- use the video extras addon with all the extras on the bluray iso
- can set default audio and subtitle streams (usefull when kodi shows 'Unknown' as language)
- enter a multiple movie iso file correctly in the Kodi library, each movie will have it's own entrypoint
- enter different cut's of a movie correctly in the Kodi library (from 1 bluray iso file), each movie will have it's own entrypoint
- skip the recap ("Previously on ...") on your tv shows
- should work with a mix of Kodi devices (win 7, Openelec, ...)

This is done through the use of .xml and dummy video files. No symlinks need to be made. 

## Installing
Use install from [zip](https://github.com/Wimpie-ccc/script.service.bluray_iso_utils/archive/master.zip) file (rename the zipfile to: "script.service.bluray_iso_utils.zip" AND rename root dir in zip file to "script.service.bluray_iso_utils" before installing.). At the moment you need no settings to edit (inside Kodi). Requires Kodi 17 min. 

A dummy, 12 seconds long, animation can be downloaded [here](https://github.com/Wimpie-ccc/helperfiles/blob/master/BIU_Black_Animation.720p.mp4?raw=true).
[Here](https://raw.githubusercontent.com/Wimpie-ccc/helperfiles/master/BIUinfo.xml) you can get a example BIUinfo.xml file.

## Usage
### Directory structure
This addon is developed with the "default" directory layout of Kodi in mind  [see: "1.1 Simple" for tv shows](http://kodi.wiki/view/Naming_video_files/TV_shows) and [see: "Movies stored in individual folders" for movies](http://kodi.wiki/view/Naming_video_files/Movies)

You need to add a directory where the bluray iso files are stored. This directory NEEDS to be named ".BIUfiles" (in windows name this dir ".BIUfiles."). Add in this directory an ".nomedia" file (for windows: ".nomedia.") so that Kodi wil NOT scan these iso files (Alternatively: use [advancedsettings.xml (2.3.11 & 2.3.13)](http://kodi.wiki/view/advancedsettings.xml)). The iso files can have any name.

Every episode/movie is a small dummy video (get one [here](https://github.com/Wimpie-ccc/helperfiles/blob/master/BIU_Black_Animation.720p.mp4?raw=true)). The filename of the dummy video is the name of the episode or movie. It MUST end with ".BIUvideo.mp4", but otherwise has no limitations. I advice to name it such that the scraper has no problem scraping it. Also filetags like ".bluray." are possible.

Each directory containing these dummy videos need a "BIUinfo.xml" file. This file contains the relevent info to link the '.BIUvideo.mp4' video file to the corresponding playlist in the blu-ray iso. [See example](https://raw.githubusercontent.com/Wimpie-ccc/helperfiles/master/BIUinfo.xml)

TV show example
```
Tv Shows
   |-----TV Show 1
   |         |----Season 1
   |         |       |-----.BIUfiles
   |         |       |         |-----MyShow.s01e01.s01e02.s01e03.s01e04.BluRay.iso
   |         |       |         |-----MyShow_S01D02.iso
   |         |       |         |-----.nomedia
   |         |       |-----Extras
   |         |       |       |---BIUinfo.xml
   |         |       |       |---Making of MyShow.BIUvideo.mp4
   |         |       |       |---Interview with the cast.BIUvideo.mp4
   |         |       |-----BIUinfo.xml
   |         |       |-----s01e01.BluRay.BIUvideo.mp4
   |         |       |-----s01e02.BIUvideo.mp4
   |         |       |-----s01e03.BluRay.BIUvideo.mp4
   |         |       |-----s01e07.BluRay.BIUvideo.mp4
   |         |       |-----s01e07.BluRay.BIUvideo.srt
   |         |----Season 2
   |         |       |-----.BIUfiles
...
```
Movie example
```
Movies
   |-----mymovie (1985)
   |        |-----.BIUfiles
   |        |         |-----mymovie.BluRay.iso
   |        |         |-----.nomedia
   |        |-----Extras
   |        |       |---BIUinfo.xml
   |        |       |---Making of mymovie.BIUvideo.mp4
   |        |       |---Delete scenes.BIUvideo.mp4
   |        |-----BIUinfo.xml
   |        |-----mymovie (1985).BluRay.BIUvideo.mp4
   |        |-----mymovie (1985).BluRay.BIUvideo.srt
   |-----myothermovie (1995)
   |        |-----.BIUfiles
   |        |         |-----myothermovie.iso
   |        |         |-----.nomedia
   |        |-----BIUinfo.xml
   |        |-----myothermovie (1995).BluRay.BIUvideo.mp4
...
```

### BIUinfo.xml file structure
This file is used to link the dummy video with the correct playlist on the blu-ray disc.

It is a .xml file. The root element is "directorydetails", and each video is contained in a "video" element. 

The video element has an attribute "filename=myvideofile", where myvideofile is the name of the dummy video. This is required, it won't work without it.

Inside the video element are child elements. Optional elements can be left out. They are: 
   - <isofile>  NEEDED, link to the iso file, relative from the directory that contains this .xml file. Can be "../myothermovie (1995)/.BIUfiles/myothermovie.iso". This means go back 1 directory level into the myothermovie directory, think of this as if you do "cd .." in the CLI. It is used for multiple cuts on 1 blu-ray disc, or for extras.
   - <playlist>  NEEDED, MUST be 5 numbers. The correct playlist on the bluray disc for this video.
   - <starttime>  Optional, start time of the video. Can be blank if not needed. Can be used to skip past the "previously on ..." recaps. format: hh:mm:ss, eg : 00:00:47
   - <stoptime>  Optional, stop time of the video. Can be blank if not needed. Is usefull for those discs were all tv episodes are linked to 1 big video (use together with <starttime>). format: hh:mm:ss, eg : 01:32:47
   - <audiochannel> Optional, used when kodi does not recognise the language (Kodi shows "Unknown" as language). Can be blank if not needed. When you look at the languages in Kodi, the top one is number 1, second from top is number 2, etc...
   - <subtitlechannel> Optional, used when kodi does not recognise the language (Kodi shows "Unknown" as language). Can be blank if not needed. When you look at the languages in Kodi, the top one is number 1, second from top is number 2, etc... If you put in here 0, then the addon will use an external .srt file for subtitiles. This external .srt file NEEDS to be named the same as the video file, but with extension ".srt".

TV show example
```xml
<?xml version="1.0" encoding="utf-8"?>
<directorydetails>
  <video filename="s01e01.BluRay.BIUvideo.mp4">
    <isofile>.BIUfiles/MyShow.s01e01.s01e02.s01e03.s01e04.BluRay.iso</isofile>
    <playlist>00001</playlist>
    <starttime></starttime>
    <stoptime></stoptime>
    <audiochannel></audiochannel>
    <subtitlechannel></subtitlechannel>
  </video>
  <video filename="s01e02.BIUvideo.mp4">
    <isofile>.BIUfiles/MyShow.s01e01.s01e02.s01e03.s01e04.BluRay.iso</isofile>
    <playlist>00002</playlist>
  </video>
  <video filename="s01e03.BluRay.BIUvideo.mp4">
    <isofile>.BIUfiles/MyShow.s01e01.s01e02.s01e03.s01e04.BluRay.iso</isofile>
    <playlist>00003</playlist>
    <starttime>00:01:00</starttime>
  </video>
  <video filename="s01e07.BluRay.BIUvideo.mp4">
    <isofile>.BIUfiles/MyShow_S01D02.iso</isofile>
    <playlist>00004</playlist>
    <starttime>00:45:42</starttime>
    <stoptime>01:31:02</stoptime>
    <audiochannel></audiochannel>
    <subtitlechannel>0</subtitlechannel>
  </video>
</directorydetails>
```
Example "Extras" BIUinfo.xml file:
```xml
<?xml version="1.0" encoding="utf-8"?>
<directorydetails>
  <video filename="Making of MyShow.BIUvideo.mp4">
    <isofile>../Extras/.BIUfiles/MyShow.s01e01.s01e02.s01e03.s01e04.BluRay.iso</isofile>
    <playlist>00053</playlist>
  </video>
  <video filename="Interview with the cast.BIUvideo.mp4">
    <isofile>../Extras/.BIUfiles/MyShow_S01D02.iso</isofile>
    <playlist>00011</playlist>
  </video>
</directorydetails>
```
## Questions / Contact
Please use the [Kodi forum](http://forum.kodi.tv/showthread.php?tid=280247).
