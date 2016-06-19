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

TV Shows                  <<Source folder, Content: TV shows>>  
   |----TV Show 1  
   |       |----Season 1  
   |            |--.BIUfiles  
   |                  |----my show.s01d01.iso  
   |                  |----my show.s01d02.iso  
   |                  |----my show.s01d03.iso  
   |            |--s01e01.strm  
   |            |--s01e02.strm  
   |            |--s01e03.strm  
   |            |--s01e04.strm  
   |            |--s01e04.strm  
   |            |--s01e06.strm  
   |            |--s01e07.strm  
   |       |----Season 2  
   |            |--.BIUfiles  
   |                  |----my show.s02d01.iso  
   |                  |----my show.s02d02.iso  
   |                  |----my show.s02d03.iso  
   |            |--s02e01.strm  
   |            |--s02e02.strm  
   |            |--s02e03.strm  
   |            |--s02e04.strm  
   |            |--s02e04.strm  
   |            |--s02e06.strm  
   |            |--s02e07.strm  




