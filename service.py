# -*- coding: utf-8 -*-
#
#     Copyright (C) 2016 Wimpie
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import unicode_literals
import urllib
import xbmc, xbmcgui, xbmcaddon, xbmcvfs
import resources.lib.utils
from resources.lib.utils import log

ADDON        = resources.lib.utils.ADDON
ADDONVERSION = resources.lib.utils.ADDONVERSION
ADDONNAME    = resources.lib.utils.ADDONNAME
ADDONPATH    = resources.lib.utils.ADDONPATH
ICON         = resources.lib.utils.ICON

# Needed to be able to stop the playback after a user requested time.
Default_stop_time = 9999999
Global_stop_time = Default_stop_time
Global_start_time = 0

# This class is the interface between the internal default settings and the user.
# The user adjust the settings to his/her likings in Kodi. This class will make
# sure that the addon knows that the user changed a setting.
class Mysettings():
    # Init with some default values for the addon
    def init(self):
        self.service_enabled = ADDON.getSetting('enabled') == 'true'
        log('Init - enabled: %s' % self.service_enabled)
    
    def __init__(self):
        self.init()

    # Read setting that user can change from within Kodi    
    def readSettings(self):
        self.service_enabled = ADDON.getSetting('enabled')
        log('enabled: %s' % self.service_enabled)

# Needed so we can use it in the next class.
settings = Mysettings()

# Our monitor class
class BIUmonitor(xbmc.Monitor):
    def __init__(self):
        xbmc.Monitor.__init__(self)

    # This is the function that signals that the user just changed a setting.
    # First default settings will be loaded, then we read the user-defined settings and
    # overwrite these default settings if needed.   
    def onSettingsChanged(self):
        settings.init()
        settings.readSettings()
        
# Our player class
class BIUplayer(xbmc.Player):
    def __init__(self):
        xbmc.Player.__init__(self)
        # Here comes some variables that need to get from the first to the second pass,
        # but are not needed outside the player class
        self.reqaudio = -1
        self.reqsubtitle = -1

    # Convert the seektime in the filename (format: uu_mm_ss) to seconds.
    # result = (3600 * uu) + (60 * mm) + ss
    def ConvertTimeToSecs(self, file_time):
        hours = int(file_time[0:2])
        mins = int(file_time[3:5])
        secs = int(file_time[6:])
        result_int = (3600 * hours) + (60 * mins) + secs
        return result_int                  

    # This event handler gets called when the video is played all the way to the end.
    # Check here if we need to set the watched flag for this video.
    def onPlayBackEnded(self):
        log('Playback ended.')

    # This event handler gets called when the user or a script stops the video.
    # Check here if we need to set the watched flag for this video.
    def onPlayBackStopped(self):
        log('Playback stopped by user/script')
    
    def onPlayBackStarted(self):
        # Needed to get stoptime to the deamon, and for the watched state
        global Global_stop_time
        global Global_start_time
        
        # See what file we are now playing. 
        Nowplaying = self.getPlayingFile()
        log('Playing File : %s'% Nowplaying)
        # If it is our special video, then we need to redirect xbmc.player to the correct bluray playlist.
        if (settings.service_enabled and Nowplaying == "special://home/addons/script.service.bluray_iso_utils/resources/media/BIU_Black_Animation.720p.mp4"):
            # We are playing a .strm file!!
            #self.stop()
            # This is the first pass of our service script
            log('First pass of the service script')

            # Sometimes getInfoLabel returns "" for ListItem.Path or ListItem.FileName.
            # I don't know why (Helper thread is blocked??). Try again until succes.
            ListItem_Path_unicode = ""            # Init
            ListItem_FileName_unicode = ""        # Init
            ListItem_Art_Thumb_unicode = ""       # Init
            ListItem_Art_Poster_unicode = ""      # Init
            ListItem_Prop_TotalSeasons_unicode = ""       # Init
            ListItem_Prop_TotalEpisodes_unicode = ""      # Init
            ListItem_Prop_WatchedEpisodes_unicode = ""    # Init
            ListItem_Prop_UnWatchedEpisodes_unicode = ""  # Init
            ListItem_Prop_NumEpisodes_unicode = ""        # Init
            ListItem_Title_unicode = ""           # Init
            ListItem_TVShowTitle_unicode = ""     # Init
            ListItem_Season_unicode = ""          # Init
            ListItem_Episode_unicode = ""         # Init
            ListItem_Plot_unicode = ""            # Init
            ListItem_Votes_unicode = ""           # Init
            ListItem_RatingAndVotes_unicode = ""  # Init
            ListItem_Mpaa_unicode = ""            # Init
            ListItem_PlotOutline_unicode = ""     # Init
            mycounter = 0                   # Needed to prevent deadlock when user wants to play video
                                            # from wrong location (result of getinfolabel is always empty).                                            
            while ((ListItem_Path_unicode == "" or ListItem_FileName_unicode == "") and (mycounter < 10)):
                # Get Name and Path of this .strm file.
                # We can not use player.path because this returns the file INSIDE the .strm file.
                # This is a hack, but there is no other way..
                # Would love a player.StrmPath and a player.StrmFileName infolabel!!!
                ListItem_Path_unicode = xbmc.getInfoLabel('ListItem.Path').decode("utf-8")
                log('ListItem.Path = %s ' % ListItem_Path_unicode)
                ListItem_FileName_unicode = xbmc.getInfoLabel('ListItem.FileName').decode("utf-8")
                log('ListItem.FileName = %s ' % ListItem_FileName_unicode)
                # Get all infotags that could be shown on the OSD by the skin.
                # If I 'forget' one, then a simple request will add the missing infotag here.
                ListItem_Art_thumb_unicode = xbmc.getInfoLabel('ListItem.Art(thumb)').decode("utf-8")
                log('ListItem.Art(thumb) = %s ' % ListItem_Art_thumb_unicode)
                ListItem_Art_poster_unicode = xbmc.getInfoLabel('ListItem.Art(poster)').decode("utf-8")
                log('ListItem.Art(poster) = %s ' % ListItem_Art_poster_unicode)
                ListItem_Prop_TotalSeasons_unicode = xbmc.getInfoLabel('ListItem.Property(TotalSeasons)').decode("utf-8")
                log('ListItem.Property(TotalSeasons) = %s ' % ListItem_Prop_TotalSeasons_unicode)
                ListItem_Prop_TotalEpisodes_unicode = xbmc.getInfoLabel('ListItem.Property(TotalEpisodes)').decode("utf-8")
                log('ListItem.Property(TotalEpisodes) = %s ' % ListItem_Prop_TotalEpisodes_unicode)
                ListItem_Prop_WatchedEpisodes_unicode = xbmc.getInfoLabel('ListItem.Property(WatchedEpisodes)').decode("utf-8")
                log('ListItem.Property(WatchedEpisodes) = %s ' % ListItem_Prop_WatchedEpisodes_unicode)
                ListItem_Prop_UnWatchedEpisodes_unicode = xbmc.getInfoLabel('ListItem.Property(UnWatchedEpisodes)').decode("utf-8")
                log('ListItem.Property(UnWatchedEpisodes) = %s ' % ListItem_Prop_UnWatchedEpisodes_unicode)
                ListItem_Prop_NumEpisodes_unicode = xbmc.getInfoLabel('ListItem.Property(NumEpisodes)').decode("utf-8")
                log('ListItem.Property(NumEpisodes) = %s ' % ListItem_Prop_NumEpisodes_unicode)
                ListItem_Title_unicode = xbmc.getInfoLabel('ListItem.Title').decode("utf-8")
                log('ListItem.Title = %s ' % ListItem_Title_unicode)
                ListItem_TVShowTitle_unicode = xbmc.getInfoLabel('ListItem.TVShowTitle').decode("utf-8")
                log('ListItem.TVShowTitle = %s ' % ListItem_TVShowTitle_unicode)
                ListItem_Season_unicode = xbmc.getInfoLabel('ListItem.Season').decode("utf-8")
                log('ListItem.Season = %s ' % ListItem_Season_unicode)
                ListItem_Episode_unicode = xbmc.getInfoLabel('ListItem.Episode').decode("utf-8")
                log('ListItem.Episode = %s ' % ListItem_Episode_unicode)
                ListItem_Plot_unicode = xbmc.getInfoLabel('ListItem.Plot').decode("utf-8")
                log('ListItem.Plot = %s ' % ListItem_Plot_unicode)
                ListItem_Votes_unicode = xbmc.getInfoLabel('ListItem.Votes').decode("utf-8")
                log('ListItem.Votes = %s ' % ListItem_Votes_unicode)
                ListItem_RatingAndVotes_unicode = xbmc.getInfoLabel('ListItem.RatingAndVotes').decode("utf-8")
                log('ListItem.RatingAndVotes = %s ' % ListItem_RatingAndVotes_unicode)
                ListItem_Mpaa_unicode = xbmc.getInfoLabel('ListItem.Mpaa').decode("utf-8")
                log('ListItem.Mpaa = %s ' % ListItem_Mpaa_unicode)
                ListItem_PlotOutline_unicode = xbmc.getInfoLabel('ListItem.PlotOutline').decode("utf-8")
                log('ListItem.PlotOutline = %s ' % ListItem_PlotOutline_unicode)
                xbmc.sleep(25)
                mycounter = mycounter + 1
            # 10 times should be enough, if not break
            if (ListItem_Path_unicode == "" or ListItem_FileName_unicode == ""):
                log('Error receiving getInfoLabel info!!')
                return

            # First validatepath to get the slashes OK,
            # then translatepath to get all the paths working.
            strmfile_unicode = xbmc.validatePath(ListItem_Path_unicode + ListItem_FileName_unicode).decode("utf-8")
            strmfile_unicode = xbmc.translatePath(strmfile_unicode).decode("utf-8")
            log('Strmfile = %s ' % strmfile_unicode)

            # Read the entire contents of the .strm file.
            try:
                mystrmfile = xbmcvfs.File(strmfile_unicode)
                data_unicode = mystrmfile.read().decode("utf-8")
            except:
                log('Error reading .strm file!!')
                mystrmfile.close()
                return
            else:
                mystrmfile.close()

            # Split the .strm file in lines so we can easely extract the bluray settings
            my_list_unicode = data_unicode.splitlines()
            log('Entire .strm file has been read.')
            log('Line 0 = %s' % my_list_unicode[0]) # The dummy animation file
            log('Line 1 = %s' % my_list_unicode[1]) # Location of the bluray iso file
            log('Line 2 = %s' % my_list_unicode[2]) # Playlist number in the iso file
            log('Line 3 = %s' % my_list_unicode[3]) # Starttime
            log('Line 4 = %s' % my_list_unicode[4]) # Stoptime
            log('Line 5 = %s' % my_list_unicode[5]) # Audio channel, starts from 1
            log('Line 6 = %s' % my_list_unicode[6]) # Subtitle, internal starts from 1, 0 means use external subtitles
            log('Line 7 = %s' % my_list_unicode[7]) # Reserved
            log('Line 8 = %s' % my_list_unicode[8]) # Reserved
            log('Line 9 = %s' % my_list_unicode[9]) # Reserved

            # The base path is "ListItem_Path_unicode". Normally the user would place the iso file
            # in a subdirectory of the base path. However, with the following code section it is also
            # possible to up 1 or more parent directories and place there the iso file.
            # This is usefull for movie iso's with different 'cuts'.
            backpathdir_unicode = ListItem_Path_unicode
            log("Backpathdir = %s" % backpathdir_unicode)                
            backpathiso_unicode = my_list_unicode[1][2:]
            log("Backpathiso = %s" % backpathiso_unicode)
            # Cut of the trailing slash, we will add it again after the while loop
            backpathdir_unicode = backpathdir_unicode[:-1]    
            # As long as the iso dir in the .strm file has "../" (or "..\")in front,
            # cut off the last dir in backpathdir_unicode (same as "cd .." in the shell)
            while ((backpathiso_unicode[:3] == "../") or (backpathiso_unicode[:3] == "..\\")):
                backpathiso_unicode = backpathiso_unicode[3:]
                # We don't know if this system uses "/" or "\".
                # Take care of both possibilities
                myindex_1 = backpathdir_unicode.rfind("\\")     # Dual slash needed
                myindex_2 = backpathdir_unicode.rfind("/")
                # Result of myindex will be -1 if not found, or a number if found
                # Both "/" and "\" are not mixed in one and the same path (I hope)
                if myindex_1 <> -1:
                    log('Myindex_1 = %s' % myindex_1)
                    backpathdir_unicode = backpathdir_unicode[:myindex_1]
                if myindex_2 <> -1:                              
                    log('Myindex_2 = %s' % myindex_2)
                    backpathdir_unicode = backpathdir_unicode[:myindex_2]
            # Restore the trailing slash we removed before the while loop
            backpathdir_unicode = backpathdir_unicode + "/"
            myisofile_unicode =  backpathdir_unicode + backpathiso_unicode
            # First validatepath to get the slashes OK,
            # then translatepath to get all the paths working.
            # Only translatepath didn't work here...
            myisofile_unicode = xbmc.validatePath(myisofile_unicode).decode("utf-8")
            myisofile_unicode = xbmc.translatePath(myisofile_unicode).decode("utf-8")
            log("Myisofile = %s" % myisofile_unicode)

            # URL escape the filename so that it works with xbmc.player.play
            # Needs following format: bluray://[udf://[path to iso]/]/BDMV/PLAYLIST/12345.mpls
            # with [path to iso] eg: 'M:/testdir/test_movie.bluray.iso'
            # and 12345 the playlist number to play. Playlist number needs to be 5 digits.
            myplaylistnumber_UTF8 = my_list_unicode[2][2:].encode("utf-8")
            log("Mystreamnumber = %s" % myplaylistnumber_UTF8)
            # Aaargh!!! urllib.quote does not work with unicode strings!! Great!!!
            # Encode first to UTF-8. Luckely UTF-8 works...
            myescapedisofile_UTF8 = myisofile_unicode.encode("utf-8")
            myescapedisofile_UTF8 = urllib.quote(myescapedisofile_UTF8)
            myescapedisofile_UTF8 = 'udf://' + myescapedisofile_UTF8 + '/'
            myescapedisofile_UTF8 = urllib.quote(myescapedisofile_UTF8, safe='()')
            myescapedisofile_UTF8 = 'bluray://' + myescapedisofile_UTF8 + '/BDMV/PLAYLIST/' + myplaylistnumber_UTF8 + '.mpls'
            log("Myescapedisofile_UTF8 = %s" % myescapedisofile_UTF8)

            # Get the starttime (if specified)
            mystarttime_unicode = my_list_unicode[3][2:].strip()
            Global_start_time = 0                       # We are playing a new video, so init self.Starttime
            if mystarttime_unicode != "":               # A starttime was specified in the .strm file.
                try:
                    Global_start_time = self.ConvertTimeToSecs(mystarttime_unicode)
                except:
                    log('Error converting starttime. Using 0 sec instead.')
                    Global_start_time = 0 
            log('Starttime = %s seconds' % Global_start_time)

            # Get the stoptime (if specified)
            # We use a globel var because we need to check time outside this class.
            mystoptime_unicode = my_list_unicode[4][2:].strip()
            Global_stop_time = Default_stop_time        # We are playing a new video, so init Global_stop_time 
            if mystoptime_unicode != "":                # A stoptime was specified in the .strm file.
                try:
                    Global_stop_time = self.ConvertTimeToSecs(mystoptime_unicode)
                except:
                    log('Error converting stoptime. Using 9999999 sec instead.')
                    Global_stop_time = Default_stop_time            
            log('Stoptime = %s seconds' % Global_stop_time)

            # Get the audiostream from the .strm file (is any)
            # and put this in self.reqaudio
            self.reqaudio = -1                          # Init var
            try:
                self.reqaudio = int(my_list_unicode[5][2:])
                log('Reqaudiochannel = %s' % self.reqaudio)
            except:
                log('No valid audiostream specified in the .strm file!')

            # Get the subtitlestream from the .strm file (if any)
            # and put this is self.reqsubtitle
            self.reqsubtitle = -1                       # Init var
            try:
                self.reqsubtitle = int(my_list_unicode[6][2:])
                log('Reqsubtitlestream = %s' % self.reqsubtitle)
            except:
                log('No valid subtitlestream specified in the .strm file!')

            # Play the correct bluray playlist
            # Fill first a listitem with the values of the .strm file. This way we get the correct mediainfo
            # while playing our bluray playlist. Otherwise this is empty (thumb picture) or 00800.mpls as name...
            # Could be that we need to copy more later, other skins might want to display other listitems.infolabels
            mylistitems = xbmcgui.ListItem (ListItem_Title_unicode)
            mylistitems.setArt({'thumb': ListItem_Art_thumb_unicode})
            mylistitems.setArt({'poster': ListItem_Art_poster_unicode})
            # If Global_start_time <> 0 then start the video with the correct starttime (StartOffset).
            if Global_start_time != 0:
                mylistitems.setProperty('StartOffset', str(Global_start_time))
            mylistitems.setProperty('TotalSeasons', ListItem_Prop_TotalSeasons_unicode)
            mylistitems.setProperty('TotalEpisodes', ListItem_Prop_TotalEpisodes_unicode)
            mylistitems.setProperty('WatchedEpisodes', ListItem_Prop_WatchedEpisodes_unicode)
            mylistitems.setProperty('UnWatchedEpisodes', ListItem_Prop_UnWatchedEpisodes_unicode)
            mylistitems.setProperty('NumEpisodes', ListItem_Prop_NumEpisodes_unicode)
            mylistitems.setInfo('video', {'PlotOutline': ListItem_PlotOutline_unicode, 
			                              'Votes': ListItem_Votes_unicode, 
										  'Mpaa': ListItem_Mpaa_unicode, 
										  'RatingAndVotes': ListItem_RatingAndVotes_unicode, 
										  'Title': ListItem_Title_unicode, 
										  'Plot': ListItem_Plot_unicode, 
										  'Season': ListItem_Season_unicode, 
										  'TVShowTitle': ListItem_TVShowTitle_unicode, 
										  'Episode': ListItem_Episode_unicode})
            # Now play the bluray playlist with the correct infotags/starttime...
            self.play(myescapedisofile_UTF8, mylistitems)
            # Temporary 'the end' for onPlayBackStarted.
            # Now it's waiting for the second pass, where we extract subtitle
            # and audio info from the correct bluray playlist.


        # Here we have the second pass of our service.
        # We detect this by looking at the filename of the current playing file.
        # If it includes ".BIUfiles" then we have a hit.
        if (settings.service_enabled and ('.BIUfiles' in Nowplaying)):
            log('Second pass of the service script')

            # If a audiostream number is set in the .strm file,
            # then we enable that audiostream here
            audiostreams = self.getAvailableAudioStreams()
            log('Available audiostreams = %s' % audiostreams)
            numberofaudiostreams = len(audiostreams)
            log('Number of audiostreams = %s' % numberofaudiostreams)
            log('Reqaudiochannel = %s' % self.reqaudio)
            if self.reqaudio <> -1:
                # The .strm file contains a valid (?) audio stream number
                if ((self.reqaudio > 0) and (self.reqaudio <= numberofaudiostreams)):
                    reqaudiochannel = self.reqaudio - 1 # Goes from 0 to count-1 in Kodi
                    self.setAudioStream(reqaudiochannel)
                    log('Audiostream %s set' % (reqaudiochannel + 1))
                else:
                    log('No valid audiostream specified in the .strm file!')
                    
            # If a subtitlestream number is set in the .strm file,
            # then we enable that subtitlestream here                
            subtitlestreams = self.getAvailableSubtitleStreams()
            log('Available subtitlestreams = %s' % subtitlestreams)
            numberofsubtitlestreams = len(subtitlestreams)
            log('Number of subtitlestreams = %s' % numberofsubtitlestreams)
            log('Reqsubtitlestream = %s' % self.reqsubtitle)
            if self.reqsubtitle <> -1:
                # The .strm file contains a valid (?) subtitle stream number
                try:
                    if self.reqsubtitle == 0:               # Use an external subtitle stream file.
                        self.setSubtitles()
                        self.showSubtitles(True)
                        log('External subtitlestream enabled')
                    elif ((self.reqsubtitle > 0) and (self.reqsubtitle <= numberofsubtitlestreams)): # Use internal subtitles
                        reqsubtitlestream = self.reqsubtitle - 1   # Goes from 0 to count-1 in Kodi
                        self.setSubtitleStream(reqsubtitlestream)
                        self.showSubtitles(True)
                        log('Internal subtitlestream %s enabled' % (reqsubtitlestream + 1))
                except:
                    log('No valid subtitlestream specified in the .strm file!')
                                   

# Main loop 
class Main:
    def __init__(self):
        self._init_vars()
        if (not settings.service_enabled):
            log('Service not enabled')
        self._daemon()

    def _init_vars(self):
        self.monitor = BIUmonitor()
        self.player = BIUplayer()

    def _daemon(self):
        while not self.monitor.abortRequested():
            # Sleep/wait for abort for 1 second
            if self.monitor.waitForAbort(1):
                # Abort was requested while waiting. We should exit
                break
            # This code is needed for checking if we need to stop the player because we
            # reached the stoptime (end of video).
            if ((BIUplayer().isPlayingVideo()) and (Global_stop_time != Default_stop_time)):
                Current_video_time = BIUplayer().getTime()
                log('Daemon: Current video time:  = %s' % str(Current_video_time))
                if (Current_video_time > Global_stop_time):
                    log('Time to stop playing video - Stopping player.')
                    BIUplayer().stop()


# Real start of the program
if (__name__ == "__main__"):
    log('version %s started' % ADDONVERSION)
    main = Main()
    log('version %s stopped' % ADDONVERSION)
