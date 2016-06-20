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
Installng
-----------
Use install from zip file. At the moment you need no settings to edit.

Directory structure
--------------------
This addon is developed with the "default" directory layout of Kodi in mind  [see: 1.1 Simple](http://kodi.wiki/view/Naming_video_files/TV_shows)

You need to add a directory where the bluray iso files are stored. This directory NEEDS to be named ".BIUfiles" (in windows name this dir ".BIUfiles."). Kodi wil NOT scan these iso files. 

![alt text](https://raw.githubusercontent.com/Wimpie-ccc/helperfiles/master/TV-file-structure.png)

The [.strm files](https://github.com/Wimpie-ccc/helperfiles/blob/master/s01e01.strm) have following structure:

![alt text](https://github.com/Wimpie-ccc/helperfiles/blob/master/example.strm-file.png)

Line 1:
- Do not touch, contains location of a helper video, needed for correct function of this addon.

Line 2:
- Contains the location of the bluray iso file, referenced from the directory that contains this .strm file
eg:
Lets say C:\Users\wimpie-ccc\Videos\MyMovies\ is the root were all my movies are.

![alt text](https://github.com/Wimpie-ccc/helperfiles/blob/master/movie-file-structure.png)

Then line 2 in 'movie_1_theatrical.strm' would be: "# .BIUfiles/movie1.iso"

Line 2 in movie_1_uncut.strm would be: "# ../Movie_1-Theatricalversion/.BIUfiles/movie1.iso" (Think this as if using cd .. in the shell)

Line 2 in 
