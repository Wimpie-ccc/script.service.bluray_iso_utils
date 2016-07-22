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
import resources.lib.utils as utils
from resources.lib.utils import log
from resources.lib.utils import settings
import sys, re, json, time

ADDON        = utils.ADDON
ADDONVERSION = utils.ADDONVERSION
ADDONNAME    = utils.ADDONNAME
ADDONPATH    = utils.ADDONPATH
ICON         = utils.ICON

# Global vars.
Global_BIU_vars = {"Default_stop_time": 9999999,    # No video is that long
                   "Stop_time": 9999999,            # Init
                   "Start_time": 0,                 # Offset in video where we start playing
                   "Current_video_time": 0,         # Current time location in video
                   "Duration": 0,                   # Time length of the video
                   "PlayCount": 0,                  # 0 = Not watched, 1 = watched
                   "Title": "",                     # Of the movie or tv episode
                   "Episode": "",                   # Episode number (as string)
                   "Season": "",                    # Season number (as string)
                   "Video_Type": "",                # movie, episode, unknown
                   "Video_ID": -1,                  # Needed for JSON calls
                   "Resume_Time": 0}                # In seconds where we can resume
Global_video_dict = {}
    
# Our monitor class
class BIUmonitor(xbmc.Monitor):
    def __init__(self):
        xbmc.Monitor.__init__(self)
        # Init settings
        settings.init()
        settings.readSettings()
        

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

    # This routine will check if the video has played long enough to set the watched flag in
    # Kodi. This is done through the JSON interface.
    def SetWatchedFlagIfNeeded(self):
        global Global_BIU_vars
        
        log('Checking if Wachted flag needs to be set.')

        Percent_played = (100 * (Global_BIU_vars["Current_video_time"] - Global_BIU_vars["Start_time"])) / Global_BIU_vars["Duration"]
        log('Percent played = %s' % str(Percent_played))
        if Percent_played > 95:
            # Increase playcount with 1
            Global_BIU_vars["PlayCount"] = Global_BIU_vars["PlayCount"] + 1
            
        # Update the Kodi library through JSON
        if Global_BIU_vars["Video_Type"] == 'movie':
            jsonmethod = "VideoLibrary.SetMovieDetails"; idfieldname = "movieid"
        elif Global_BIU_vars["Video_Type"] == 'episode':
            jsonmethod = "VideoLibrary.SetEpisodeDetails"; idfieldname = "episodeid"
        JSON_req = {"jsonrpc": "2.0",
                    "method": jsonmethod,
                    "params": {idfieldname: Global_BIU_vars["Video_ID"],
                               "playcount": Global_BIU_vars["PlayCount"],
                               "lastplayed": utils.TimeStamptosqlDateTime(int(time.time()))},
                    "id": 1}
        JSON_result = utils.executeJSON(JSON_req)
        if (JSON_result.has_key('result') and JSON_result['result'] == 'OK'):
            log('Updated Kodi DB with new lastplayed and playcount!')
        else:
            log('Error updating Kodi DB with new lastplayed and playcount!')
	
    # This event handler gets called when the video is played all the way to the end.
    # Check here if we need to set the watched flag for this video.
    def onPlayBackEnded(self):
        if settings.service_enabled == 'true':
            log('Playback ended.')

            # Check  if the watched flag needs to be set
            self.SetWatchedFlagIfNeeded()

    # This event handler gets called when the user or a script stops the video.
    # Check here if we need to set the watched flag for this video.
    def onPlayBackStopped(self):
        if settings.service_enabled == 'true':
            # Needed for watched state and resumepoint
            global Global_BIU_vars
            log('Playback stopped by user/service')
        
            # Check  if the watched flag needs to be set
            self.SetWatchedFlagIfNeeded()
            # Set stoptime for later use as resumepoint
    
    def onPlayBackStarted(self):
        # Needed to get stoptime to the deamon, and for the watched state
        global Global_BIU_vars
        global Global_video_dict
		
        # See what file we are now playing. 
        Nowplaying = self.getPlayingFile()
        if settings.service_enabled == 'true':
            log('Playing File : %s'% Nowplaying)
        # If it is our special video, then we need to redirect xbmc.player to the correct bluray playlist.
        if ((settings.service_enabled == 'true') and Nowplaying == "special://home/addons/script.service.bluray_iso_utils/resources/media/BIU_Black_Animation.720p.mp4"):
        #if True:
            # We are playing a .strm file!!
            #self.stop()
            # This is the first pass of our service script
            log('First pass of the service script')
            Global_BIU_vars["Current_video_time"] = 0	    # Init
            Global_BIU_vars["Video_ID"] = -1	            # Init
            Global_BIU_vars["PlayCount"] = 0	            # Init
            Global_video_dict = {}                          # Init

            JSON_req = {"jsonrpc": "2.0", "method": "JSONRPC.Introspect", "params": { "filter": { "id": "VideoLibrary.GetMovieDetails", "type": "method" } }, "id": 1 }
            JSON_result = utils.executeJSON(JSON_req)
            log('JSON syntax query = %s' % JSON_result)                




            # Sometimes getInfoLabel returns "" for ListItem.Path or ListItem.FileName.
            # I don't know why (Helper thread is blocked??). Try again until succes.
            # ListItem always returns blank from a homescreen/recently added episode/movie (no list)
            ListItem_Path_unicode = ""            # Init
            ListItem_FileName_unicode = ""        # Init
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
                xbmc.sleep(25)
                mycounter = mycounter + 1
            # 10 times should be enough, if not break
            if (ListItem_Path_unicode == "" or ListItem_FileName_unicode == ""):
                log('Error receiving getInfoLabel info!!')
                # Stop playing our black video
                self.stop()
                return

            # First validatepath to get the slashes OK,
            # then translatepath to get all the paths working.
            strmfile_unicode = xbmc.validatePath(ListItem_Path_unicode + ListItem_FileName_unicode).decode("utf-8")
            strmfile_unicode = xbmc.translatePath(strmfile_unicode).decode("utf-8")
            log('Strmfile = %s ' % strmfile_unicode)

            # Use Files.GetFileDetails to see if it is a movie or a tv episode video
            # Also gives us the DBID.
            try:
                JSON_req = {"jsonrpc": "2.0",
                            "method": "Files.GetFileDetails",
                            "params": {"file": strmfile_unicode,
                                       "media": "video",},
                            "id": "1"}
                log('JSON_req string = %s' % json.dumps(JSON_req))
                JSON_result = utils.executeJSON(JSON_req)
                log('JSON Files.GetFileDetails result = %s' % JSON_result)
                # Is it a movie or a tv show?
                Global_BIU_vars["Video_Type"] = JSON_result["result"]["filedetails"]["type"]
                if Global_BIU_vars["Video_Type"] not in [u'unknown', u'movie', u'episode']:
                    log('Error receiving JSON Files.GetFileDetails info!!')
                    return
                # We can extract the DBID from this request
                Global_BIU_vars["Video_ID"] = JSON_result["result"]["filedetails"]["id"]
                log('DBID = %s' % str(Global_BIU_vars["Video_ID"]))
                

                # Now get all properties, needs seperate call for movie or episode
                if Global_BIU_vars["Video_Type"] ==  u'episode': # we have a tv show
                    log('We play a episode.')
                    # Get all the properties of the tv show
                    JSON_req = {"jsonrpc": "2.0",
                                "method": "VideoLibrary.GetEpisodeDetails",
                                "params": {"episodeid": Global_BIU_vars["Video_ID"],
                                           "properties": ["title", "plot", "votes", "rating", "writer", "streamdetails",
                                                          "firstaired", "playcount", "runtime", "director",
                                                          "productioncode", "season", "episode", "cast", 
                                                          "originaltitle", "showtitle", "lastplayed",
                                                          "thumbnail", "file", "resume", "tvshowid", "userrating",
                                                          "dateadded", "uniqueid", "art", "fanart"]},
                                "id": "1"}
                    log('JSON_req string = %s' % json.dumps(JSON_req))
                    JSON_result = utils.executeJSON(JSON_req)
                    log('JSON VideoLibrary.GetEpisodeDetails result = %s' % JSON_result)
                    # Extract the needed info from JSON_result and put it in our video_dict
                    Global_video_dict["ListItem_Art_Thumb_unicode"] = JSON_result["result"]["episodedetails"]["thumbnail"]
                    Global_video_dict["ListItem_Art_Poster_unicode"] =  JSON_result["result"]["episodedetails"]["art"]["tvshow.poster"]
                    log('poster: %s' % Global_video_dict["ListItem_Art_Poster_unicode"])
                    Global_video_dict["ListItem_Cast_unicode"] = JSON_result["result"]["episodedetails"]["cast"]
                    Global_video_dict["ListItem_Title_unicode"] = JSON_result["result"]["episodedetails"]["title"]
                    Global_video_dict["ListItem_TVShowTitle_unicode"] = JSON_result["result"]["episodedetails"]["showtitle"]
                    Global_video_dict["ListItem_Season_unicode"] = JSON_result["result"]["episodedetails"]["season"]
                    Global_video_dict["ListItem_Episode_unicode"] = JSON_result["result"]["episodedetails"]["episode"]
                    Global_video_dict["ListItem_UserRating_unicode"] =  JSON_result["result"]["episodedetails"]["userrating"]
                    Global_video_dict["ListItem_Plot_unicode"] = JSON_result["result"]["episodedetails"]["plot"]
                    Global_video_dict["ListItem_RunTime_unicode"] = JSON_result["result"]["episodedetails"]["runtime"]
                    Global_video_dict["ListItem_FirstAired_unicode"] = JSON_result["result"]["episodedetails"]["firstaired"]
                    Global_video_dict["ListItem_DateAdded_unicode"] = JSON_result["result"]["episodedetails"]["dateadded"]
                    Global_video_dict["ListItem_LastPlayed_unicode"] = JSON_result["result"]["episodedetails"]["lastplayed"]
                    Global_video_dict["ListItem_Votes_unicode"] = JSON_result["result"]["episodedetails"]["votes"]
                    Global_video_dict["ListItem_OriginalTitle_unicode"] = JSON_result["result"]["episodedetails"]["originaltitle"]
                    Global_video_dict["ListItem_Rating_unicode"] = JSON_result["result"]["episodedetails"]["rating"]
                    Global_video_dict["ListItem_Writer_unicode"] = JSON_result["result"]["episodedetails"]["writer"]
                    Global_video_dict["ListItem_Director_unicode"] = JSON_result["result"]["episodedetails"]["director"]
                    Global_video_dict["ListItem_StreamDetails_unicode"] = JSON_result["result"]["episodedetails"]["streamdetails"]
                    # If playcount = 0 then the video is not watched, if playcount > 0 then the video is watched
                    Global_BIU_vars["PlayCount"] = JSON_result["result"]["episodedetails"]["playcount"]
                    # These properties are not yet used:
                    # , , productioncode, ratings, resume, file, tvshowid, uniqueid, art, fanart 
                    log('Streamdetails are %s' % Global_video_dict["ListItem_StreamDetails_unicode"])
                elif Global_BIU_vars["Video_Type"] ==  u'movie': # we have a movie
                    log('We play a movie.')
                    # Get all the properties of the movie
                    JSON_req = {"jsonrpc": "2.0",
                                "method": "VideoLibrary.GetMovieDetails",
                                "params": {"movieid": Global_BIU_vars["Video_ID"],
                                           "properties": ["title", "plot", "votes", "rating", "streamdetails",
                                                          "studio", "playcount", "runtime", "director",
                                                          "genre", "trailer", "tagline", "plotoutline",
                                                          "mpaa", "imdbnumber", "sorttitle", "setid",
                                                          "originaltitle", "lastplayed", "writer", "premiered",
                                                          "thumbnail", "file", "resume", "userrating",
                                                          "dateadded", "art", "fanart", "cast"]},
                                "id": "1"}
                    log('JSON_req string = %s' % json.dumps(JSON_req))
                    JSON_result = utils.executeJSON(JSON_req)
                    log('JSON VideoLibrary.GetMovieDetails result = %s' % JSON_result)
                    Global_video_dict["ListItem_Cast_unicode"] = JSON_result["result"]["moviedetails"]["cast"]
                    Global_video_dict["ListItem_Title_unicode"] = JSON_result["result"]["moviedetails"]["title"]
                    Global_video_dict["ListItem_Plot_unicode"] = JSON_result["result"]["moviedetails"]["plot"]
                    Global_video_dict["ListItem_Votes_unicode"] = JSON_result["result"]["moviedetails"]["votes"]
                    Global_video_dict["ListItem_Rating_unicode"] = JSON_result["result"]["moviedetails"]["rating"]
                    Global_video_dict["ListItem_StreamDetails_unicode"] = JSON_result["result"]["moviedetails"]["streamdetails"]
                    Global_video_dict["ListItem_Studio_unicode"] = JSON_result["result"]["moviedetails"]["studio"]
                    Global_video_dict["ListItem_Director_unicode"] =  JSON_result["result"]["moviedetails"]["director"]
                    Global_video_dict["ListItem_Genre_unicode"] =  JSON_result["result"]["moviedetails"]["genre"]
                    log('genre = %s' % Global_video_dict["ListItem_Genre_unicode"])
                    Global_video_dict["ListItem_Trailer_unicode"] =  JSON_result["result"]["moviedetails"]["trailer"]
                    Global_video_dict["ListItem_Tagline_unicode"] =  JSON_result["result"]["moviedetails"]["tagline"]
                    Global_video_dict["ListItem_mpaa_unicode"] =  JSON_result["result"]["moviedetails"]["mpaa"]
                    Global_video_dict["ListItem_PlotOutline_unicode"] = JSON_result["result"]["moviedetails"]["plotoutline"]
                    Global_video_dict["ListItem_imdbNumber_unicode"] =  JSON_result["result"]["moviedetails"]["imdbnumber"]
                    Global_video_dict["ListItem_SortTitle_unicode"] =  JSON_result["result"]["moviedetails"]["sorttitle"]
                    Global_video_dict["ListItem_setID_unicode"] =  JSON_result["result"]["moviedetails"]["setid"]
                    Global_video_dict["ListItem_RunTime_unicode"] =  JSON_result["result"]["moviedetails"]["runtime"]
                    Global_video_dict["ListItem_OriginalTitle_unicode"] =  JSON_result["result"]["moviedetails"]["originaltitle"]
                    Global_video_dict["ListItem_LastPlayed_unicode"] =  JSON_result["result"]["moviedetails"]["lastplayed"]
                    Global_video_dict["ListItem_Writer_unicode"] =  JSON_result["result"]["moviedetails"]["writer"]
                    Global_video_dict["ListItem_Premiered_unicode"] =  JSON_result["result"]["moviedetails"]["premiered"]
                    Global_video_dict["ListItem_UserRating_unicode"] =  JSON_result["result"]["moviedetails"]["userrating"]
                    Global_video_dict["ListItem_DateAdded_unicode"] =  JSON_result["result"]["moviedetails"]["dateadded"]
                    Global_video_dict["ListItem_Art_Thumb_unicode"] =  JSON_result["result"]["moviedetails"]["thumbnail"]
                    Global_video_dict["ListItem_Art_Poster_unicode"] =  JSON_result["result"]["moviedetails"]["art"]["poster"]
                    # If playcount = 0 then the video is not watched, if playcount > 0 then the video is watched
                    Global_BIU_vars["PlayCount"] = JSON_result["result"]["moviedetails"]["playcount"]
                    # These properties are not yet used:
                    # , file, resume, art , fanart
                    
            except:
                log('Error getting JSON response, media is probably unknown!!')
                Global_video_dict["ListItem_Art_Thumb_unicode"] = ""
                Global_video_dict["ListItem_Art_Poster_unicode"] = ""
                Global_video_dict["ListItem_Title_unicode"] = ""
                Global_video_dict["ListItem_Plot_unicode"] = ""
                Global_video_dict["ListItem_Votes_unicode"] = ""
                Global_video_dict["ListItem_DateAdded_unicode"] = ""
                Global_video_dict["ListItem_OriginalTitle_unicode"] = ""
                Global_video_dict["ListItem_UserRating_unicode"] = ""
                Global_video_dict["ListItem_Rating_unicode"] = ""
                Global_video_dict["ListItem_Writer_unicode"] = ""
                Global_video_dict["ListItem_Director_unicode"] = ""
                Global_video_dict["ListItem_StreamDetails_unicode"] = ""
                Global_video_dict["ListItem_LastPlayed_unicode"] = ""
                Global_video_dict["ListItem_Cast_unicode"] = ""
                Global_BIU_vars["PlayCount"] = 0
                Global_BIU_vars["Video_ID"] = -1

            # Was this video played already?
            log('Playcount = %s' % Global_BIU_vars["PlayCount"])

            # Read the entire contents of the .strm file.
            try:
                mystrmfile = xbmcvfs.File(strmfile_unicode)
                data_unicode = mystrmfile.read().decode("utf-8")
            except Exception:
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
            Global_BIU_vars["Start_time"] = 0                       # We are playing a new video, so init self.Starttime
            if mystarttime_unicode != "":               # A starttime was specified in the .strm file.
                try:
                    Global_BIU_vars["Start_time"] = self.ConvertTimeToSecs(mystarttime_unicode)
                except Exception:
                    log('Error converting starttime. Using 0 sec instead.')
                    Global_BIU_vars["Start_time"] = 0 
            log('Starttime = %s seconds' % Global_BIU_vars["Start_time"])

            # Get the stoptime (if specified)
            # We use a globel var because we need to check time outside this class.
            mystoptime_unicode = my_list_unicode[4][2:].strip()
            Global_BIU_vars["Stop_time"] = Global_BIU_vars["Default_stop_time"] # We are playing a new video, so init Global_stop_time 
            if mystoptime_unicode != "":                # A stoptime was specified in the .strm file.
                try:
                    Global_BIU_vars["Stop_time"] = self.ConvertTimeToSecs(mystoptime_unicode)
                except Exception:
                    log('Error converting stoptime. Using 9999999 sec instead.')
                    Global_BIU_vars["Stop_time"] = Global_BIU_vars["Default_stop_time"]            
            log('Stoptime = %s seconds' % Global_BIU_vars["Stop_time"])

            # Get the audiostream from the .strm file (if any)
            # and put this in self.reqaudio
            self.reqaudio = -1                          # Init var
            try:
                self.reqaudio = int(my_list_unicode[5][2:])
                log('Reqaudiochannel = %s' % self.reqaudio)
            except Exception:
                log('No valid audiostream specified in the .strm file!')

            # Get the subtitlestream from the .strm file (if any)
            # and put this is self.reqsubtitle
            self.reqsubtitle = -1                       # Init var
            try:
                self.reqsubtitle = int(my_list_unicode[6][2:])
                log('Reqsubtitlestream = %s' % self.reqsubtitle)
            except Exception:
                log('No valid subtitlestream specified in the .strm file!')

            # Play the correct bluray playlist
            # Fill first a listitem with the values of the .strm file. This way we get the correct mediainfo
            # while playing our bluray playlist. Otherwise this is empty (thumb picture) or 00800.mpls as name...
            # Could be that we need to copy more later, other skins might want to display other listitems.infolabels
            mylistitems = xbmcgui.ListItem (Global_video_dict["ListItem_Title_unicode"])
            mylistitems.setArt({'thumb': Global_video_dict["ListItem_Art_Thumb_unicode"]})
            mylistitems.setArt({'poster': Global_video_dict["ListItem_Art_Poster_unicode"]})
            # If Global_start_time <> 0 then start the video with the correct starttime (StartOffset).
            if Global_BIU_vars["Start_time"] != 0:
                mylistitems.setProperty('StartOffset', str(Global_BIU_vars["Start_time"]))  # Is alternative to seek

            # Convert "cast" [{thumbnail, role, name, order}, {thumbnail, role, name, order}] to
            # [(name, role), (name, role)].
            actor_list = []
            for item in Global_video_dict["ListItem_Cast_unicode"]:
                log('Role: %s' % item["role"])
                log('Name: %s' % item["name"])
                actor_list.append((item["name"], item["role"]))

            # Set the player/videoplayer infolabels
            # First infolabels used for both movie and tv shows
            mylistitems.setInfo('video', {'mediatype': Global_BIU_vars["Video_Type"],
                                          'votes': Global_video_dict["ListItem_Votes_unicode"], 
					  'rating': Global_video_dict["ListItem_Rating_unicode"], 
					  'title': Global_video_dict["ListItem_Title_unicode"], 
					  'plot': Global_video_dict["ListItem_Plot_unicode"], 
                                          'writer' : Global_video_dict["ListItem_Writer_unicode"],
                                          'director': Global_video_dict["ListItem_Director_unicode"],
                                          'lastplayed': Global_video_dict["ListItem_LastPlayed_unicode"],
                                          'runtime': Global_video_dict["ListItem_RunTime_unicode"],
                                          'dateadded': Global_video_dict["ListItem_DateAdded_unicode"],
                                          'userrating': Global_video_dict["ListItem_UserRating_unicode"],
                                          'playcount': Global_BIU_vars["PlayCount"],
                                          'castandrole': actor_list,
                                          'originaltitle': Global_video_dict["ListItem_OriginalTitle_unicode"]})
            # Movie specific infolabels
            if Global_BIU_vars["Video_Type"] ==  u'movie':
                # Convert genre list "[u'Comedy', u'Drama', u'Music', u'Mystery']" into string
                # like: "Comedy / Drama / Music / Mystery"
                Genre_string = ""
                for item in Global_video_dict["ListItem_Genre_unicode"]:
                    Genre_string = Genre_string + item + ' / '
                Genre_string = Genre_string[:-3]
                log('Genre = %s' % Genre_string)
                
                mylistitems.setInfo('video', { 'plotoutline': Global_video_dict["ListItem_PlotOutline_unicode"],
                                               'mpaa': Global_video_dict["ListItem_mpaa_unicode"],
                                               'studio': Global_video_dict["ListItem_Studio_unicode"],
                                               'genre': Genre_string,
                                               'premiered': Global_video_dict["ListItem_Premiered_unicode"],
                                               'tagline': Global_video_dict["ListItem_Tagline_unicode"],
                                               'sorttitle': Global_video_dict["ListItem_SortTitle_unicode"],
                                               'trailer': Global_video_dict["ListItem_Trailer_unicode"],
                                               'code': Global_video_dict["ListItem_imdbNumber_unicode"]})
                # Global_video_dict["ListItem_setID_unicode"] not used yet
            # TV show specific infolabels
            elif Global_BIU_vars["Video_Type"] ==  u'episode':
                mylistitems.setInfo('video', { 'season': Global_video_dict["ListItem_Season_unicode"],
                                               'tvshowtitle': Global_video_dict["ListItem_TVShowTitle_unicode"],
                                               'aired': Global_video_dict["ListItem_FirstAired_unicode"],
                                               'episode': Global_video_dict["ListItem_Episode_unicode"]})

            # Now play the bluray playlist with the correct infolabels/starttime...
            self.play(myescapedisofile_UTF8, mylistitems)
            # Temporary 'the end' for onPlayBackStarted.
            # Now it's waiting for the second pass, where we extract subtitle
            # and audio info from the correct bluray playlist.



        # Here we have the second pass of our service.
        # We detect this by looking at the filename of the current playing file.
        # If it includes ".BIUfiles" then we have a hit.
        if ((settings.service_enabled == 'true') and ('.BIUfiles' in Nowplaying)):
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
                except Exception:
                    log('No valid subtitlestream specified in the .strm file!')         

            # Calculate the video duration, needed for watched flag
            if Global_BIU_vars["Stop_time"] != Global_BIU_vars["Default_stop_time"]:
                # We have a non default stoptime
                Global_BIU_vars["Duration"] = Global_BIU_vars["Stop_time"] - Global_BIU_vars["Start_time"]
            else:
                # Duration is from video duration
                Global_BIU_vars["Duration"] = self.getTotalTime() - Global_BIU_vars["Start_time"]
            log('Video duration = %s' % str(Global_BIU_vars["Duration"]))
            

            temmpmmp = xbmc.getInfoLabel('VideoPlayer.Genre')
            log('genre player = %s' % temmpmmp)






            # Extract data from the videoplayer that we use to update the Kodi DB (through JSON)
            #run_time = int(self.getTotalTime())
            #log('runtime = %s' % run_time)
            #run_time = TimeStamptosqlDateTime(run_time)










            '''JSON_req = {"jsonrpc": "2.0",
                        "method": "VideoLibrary.SetEpisodeDetails",
                        "params": {"episodeid": Global_BIU_vars["Video_ID"],
                                   "runtime": run_time},
                        "id": 1}
            log('VideoLibrary.SetEpisodeDetails sends: %s' % JSON_req)
            JSON_result = utils.executeJSON(JSON_req)
            log('JSON VideoLibrary.GetEpisodeDetails result = %s' % JSON_result)'''                










            # This is used to make playcount again 0 for the playing video
            # Uncomment en run to reset watched state
            '''JSON_req = {"jsonrpc": "2.0",
                        "method": "VideoLibrary.SetEpisodeDetails",
                        "params": {"episodeid": Global_BIU_vars["Video_ID"],
                                   "playcount": 0},
                        "id": 1}
            JSON_result = utils.executeJSON(JSON_req)
            log('JSON VideoLibrary.GetEpisodeDetails result = %s' % JSON_result)'''                





# Main loop 
class Main:
    def __init__(self):
        self._init_vars()
        if settings.service_enabled == 'false':
            xbmc.log('%s: Service not enabled' % ADDONNAME, level=xbmc.LOGDEBUG)
        self._daemon()

    def _init_vars(self):
        self.monitor = BIUmonitor()
        self.player = BIUplayer()

    def _daemon(self):
	    # Needed for watched state en resumepoint
        global Global_BIU_vars
		
        while not self.monitor.abortRequested():
            # Sleep/wait for abort for 1 second
            if self.monitor.waitForAbort(1):
                # Abort was requested while waiting. We should exit
                break
            # This code is needed for checking if we need to stop the player because we
            # reached the stoptime (end of video).
            if ((settings.service_enabled == 'true') and (BIUplayer().isPlayingVideo())):
                # We play a video, track current time for watched state
                Global_BIU_vars["Current_video_time"] = BIUplayer().getTime()
                log('Daemon: Current video time:  = %s' % str(Global_BIU_vars["Current_video_time"]))
                # We have a custom stoptime, stop when current time > stoptime
                if (Global_BIU_vars["Stop_time"] != Global_BIU_vars["Default_stop_time"]):
                    if (Global_BIU_vars["Current_video_time"] > Global_BIU_vars["Stop_time"]):
                        log('Time to stop playing video - Stopping player.')
                        BIUplayer().stop()


# Real start of the program
if (__name__ == "__main__"):
    xbmc.log('%s: version %s started' % (ADDONNAME, ADDONVERSION), level=xbmc.LOGDEBUG)
    main = Main()
    xbmc.log('%s: version %s stopped' % (ADDONNAME, ADDONVERSION), level=xbmc.LOGDEBUG)
