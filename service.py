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
import sys, re, os, json, time, ntpath
import xml.etree.ElementTree as ET
import sqlite3
#import mysql.connector

ADDON        = utils.ADDON
ADDONVERSION = utils.ADDONVERSION
ADDONNAME    = utils.ADDONNAME
ADDONPATH    = utils.ADDONPATH
ICON         = utils.ICON
ADDONPROFILE = utils.ADDONPROFILE

# Create the table
QUERY_CREATE_SQLITE = "CREATE TABLE IF NOT EXISTS video_resume (filename TEXT PRIMARY KEY, resumepoint INTEGER)"
# query the wanted video out of the db
QUERY_SELECT_SQLITE = "SELECT * FROM video_resume WHERE filename = ?"
# insert new entry
QUERY_INSERT_SQLITE = "INSERT OR IGNORE INTO video_resume (filename, resumepoint) VALUES (?, ?)"
# update entry
QUERY_UPDATE_SQLITE = "UPDATE video_resume SET resumepoint = ? WHERE filename  = ?"
# delete entry
QUERY_CLEAR_SQLITE = "DELETE FROM video_resume WHERE filename = ?"

# Global vars.
Global_BIU_vars = {"Default_stop_time": 9999999,    # No video is that long
                   "Stop_time": 9999999,            # Init
                   "Start_time": 0,                 # Offset in video where we start playing
                   "Current_video_time": 0,         # Current time location in video
                   "Duration": 0,                   # Time length of the video
                   "PlayCount": 0,                  # 0 = Not watched, 1 = watched
                   "Video_Type": "",                # movie, episode, unknown
                   "Update_Streamdetails": False,   # streamdetails in Kodi library != []
                   "Video_ID": -1,                  # Needed for JSON calls
                   "BIU_videofile_unicode": "",     # ID used in resume db
                   "playcountminimumpercent": 90,   # Init, for watched (Kodi default)
                   "ignoresecondsatstart": 180,     # Init, for resumepoint (Kodi default)
                   "ignorepercentatend": 8,         # Init, for resumepoint (Kodi default)
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
        self.isPlayingBIUBluRay = False     # Flag that indicates if we are (or just have) playing a BIUfile type video
        self.ExtSubFile = ''
        self.dbPath = os.path.join(ADDONPROFILE, "BIU.db")

    # Convert the seektime in the filename (format: uu_mm_ss) to seconds.
    # result = (3600 * uu) + (60 * mm) + ss
    def ConvertTimeToSecs(self, file_time):
        hours = int(file_time[0:2])
        mins = int(file_time[3:5])
        secs = int(file_time[6:])
        result_int = (3600 * hours) + (60 * mins) + secs
        return result_int

    # Convert the secs time to normal hh:mm:ss time
    def ConvertSecsToTime(self, secs):
        hours = secs / 3600
        mins = (secs - (3600 * hours)) / 60
        secs = secs - (3600 * hours) - (60 * mins)
        return str(hours) + ":" + str(mins) + ":" + str(secs)

    # This is the exit handler, if something goes wrong.
    # Make function so I forget nothing...
    def BIU_ExitHandler(self, ExitString):
        log(ExitString)
        self.isPlayingBIUBluRay = False
 
    # This routine will check if the video has played long enough to set the watched flag in
    # Kodi. Also lastplayed and resumepoint is done here. We use the JSON interface.
    def UpdateDBIfNeeded(self):
        global Global_BIU_vars
        
        # Calculate how far we are in the video when we stopped
        log('Checking if watched flag needs to be set.')
        try:
            Percent_played = (100 * (Global_BIU_vars["Current_video_time"] - Global_BIU_vars["Start_time"])) / Global_BIU_vars["Duration"]
        except Exception: # Could divide by zero
            Percent_played = 1
        log('Percent played = %s' % str(Percent_played))
        # Check if we have to increase playcount (watched flag)
        if Percent_played > Global_BIU_vars["playcountminimumpercent"]:
            # Increase playcount with 1
            Global_BIU_vars["PlayCount"] = Global_BIU_vars["PlayCount"] + 1
            log('Playcount increased by 1 to: %s' % Global_BIU_vars["PlayCount"])
        
        # Check if resumepoint needs to be set
        try:
            # Open db
            sqlcon_wl = sqlite3.connect(self.dbPath);
            sqlcursor_wl = sqlcon_wl.cursor()

            # Check if a resume for this video already exist
            values = list([Global_BIU_vars["BIU_videofile_unicode"]])
            sqlcursor_wl.execute(QUERY_SELECT_SQLITE, values)
            db_ret = sqlcursor_wl.fetchall()

            if ((Global_BIU_vars["ignoresecondsatstart"] < Global_BIU_vars["Current_video_time"]) and (Percent_played < (100 - Global_BIU_vars["ignorepercentatend"]))):
                # Resume point is needed
                resume_point_int = Global_BIU_vars["Current_video_time"]
                log('Set resumepoint to: %s' % resume_point_int)
            
                # Check if we need to UPDATE or INSERT
                if db_ret != []:
                    # Already an entry in the db, UPDATE
                    values = list([resume_point_int, Global_BIU_vars["BIU_videofile_unicode"]])
                    sqlcursor_wl.execute(QUERY_UPDATE_SQLITE, values)
                    log('Resumepoint updated.')
                else:
                    # New entry in db needed, INSERT
                    values = list([Global_BIU_vars["BIU_videofile_unicode"], resume_point_int])
                    sqlcursor_wl.execute(QUERY_INSERT_SQLITE, values)
                    log('New resumepoint inserted.')
 
            else:
                # No resume point needs to be set (=0)
                log('Resumepoint is not needed.')

                # Delete resume point (if needed)
                if db_ret != []:
                    # An entry in the db exists, DELETE
                    values = list([Global_BIU_vars["BIU_videofile_unicode"]])
                    sqlcursor_wl.execute(QUERY_CLEAR_SQLITE, values)
                    log('Resumepoint deleted.')
                    
            # Commit changes
            sqlcon_wl.commit()
            
        except Exception:
            log('Error accessing db! (Saving resume point)')

        finally:
            # Close db
            sqlcon_wl.close()
        
               
        # if Global_video_dict["BIU_StreamDetails_unicode"]["video"] == []:
        # No stream details in the Kodi library, add them now
            
        if Global_BIU_vars["Video_Type"] == 'movie':
            jsonmethod = "VideoLibrary.SetMovieDetails"; idfieldname = "movieid"
        elif Global_BIU_vars["Video_Type"] == 'episode':
            jsonmethod = "VideoLibrary.SetEpisodeDetails"; idfieldname = "episodeid"

        # Update the Kodi library through JSON
        JSON_req = {"jsonrpc": "2.0",
                    "method": jsonmethod,
                    "params": {idfieldname: Global_BIU_vars["Video_ID"],
                               "lastplayed": utils.TimeStamptosqlDateTime(int(time.time())),
                               "playcount": Global_BIU_vars["PlayCount"]},
                    "id": 1}
        JSON_result = utils.executeJSON(JSON_req)
        if (JSON_result.has_key('result') and JSON_result['result'] == 'OK'):
            log('Updated Kodi DB with new lastplayed and playcount!')
        else:
            log('Error updating Kodi DB with new lastplayed and playcount!')
	
    # This event handler gets called when the video is played all the way to the end.
    # Check here if we need to set the watched flag for this video.
    def onPlayBackEnded(self):
        if self.isPlayingBIUBluRay:
            log('Playback ended.')
            # Update data in Kodi DB if needed
            if self.isPlayingBIUBluRay:
                self.UpdateDBIfNeeded()
            # Set flag to False
            self.isPlayingBIUBluRay = False

    # This event handler gets called when the user or a script stops the video.
    # Check here if we need to set the watched flag for this video.
    def onPlayBackStopped(self):
        if self.isPlayingBIUBluRay:
            log('Playback stopped by user/service')
            # Update data in Kodi DB if needed
            if self.isPlayingBIUBluRay:
                self.UpdateDBIfNeeded()
            # Set flag to False
            self.isPlayingBIUBluRay = False

    # Test
    def onPlayBackPaused(self):
        log('Playback paused by user')
        
    def onPlayBackResumed(self):
        log('Playback resumed by user')
    
    
    def onPlayBackStarted(self):
        # Needed to get stoptime to the deamon, and for the watched state
        global Global_BIU_vars
        global Global_video_dict

        '''JSON_req = {"jsonrpc": "2.0", "method": "JSONRPC.Introspect", "params": { "filter": { "id": "VideoLibrary.SetMovieDetails", "type": "method" } }, "id": 1 }
        JSON_result = utils.executeJSON(JSON_req)
        log('JSON syntax query = %s' % JSON_result)'''              

	BIU_videofile_unicode = ""	    # Init
        # See what file we are now playing. 
        Nowplaying = self.getPlayingFile()
	# This part of code checks if we are starting a BR with the help of a .strm file.
	if (Nowplaying == "special://home/addons/script.service.bluray_iso_utils/resources/media/BIU_Black_Animation.720p.mp4"):
            # Sometimes getInfoLabel returns "" for ListItem.Path or ListItem.FileName.
            # I don't know why (Helper thread is blocked??). Try again until succes.
            # ListItem always returns blank from a homescreen/recently added episode/movie (no list)
            BIU_FolderPath_unicode = ""     # Init
            BIU_FileName_unicode = ""       # Init
            mycounter = 0                   # Needed to prevent deadlock when user wants to play video
                                            # from wrong location (result of getinfolabel is always empty).                                            
            while ((BIU_FolderPath_unicode == "" or BIU_FileName_unicode == "") and (mycounter < 10)):
                # Get Name and Path of this .strm file.
                # We can not use player.path because this returns the file INSIDE the .strm file.
                # This is a hack, but there is no other way..
                # Would love a player.StrmPath and a player.StrmFileName infolabel!!!
                BIU_FolderPath_unicode = xbmc.getInfoLabel('ListItem.Path').decode("utf-8")
                log('ListItem.Path = %s ' % BIU_FolderPath_unicode)
                BIU_FileName_unicode = xbmc.getInfoLabel('ListItem.FileName').decode("utf-8")
                log('ListItem.FileName (.strm) = %s ' % BIU_FileName_unicode)
                xbmc.sleep(25)
                mycounter = mycounter + 1
            # 10 times should be enough, if not return to Kodi
            if (BIU_FolderPath_unicode == "" or BIU_FileName_unicode == ""):
                log('Error receiving getInfoLabel info!!')
                # Stop playing our black video
                self.stop()
                return
            # First validatepath to get the slashes OK,
            # then translatepath to get all the paths working.
            BIU_videofile_unicode = xbmc.validatePath(BIU_FolderPath_unicode + BIU_FileName_unicode).decode("utf-8")
            BIU_videofile_unicode = xbmc.translatePath(BIU_videofile_unicode).decode("utf-8")
            log('BIU_videofile_unicode = %s ' % BIU_videofile_unicode)
	# This part of code checks if we are starting a BR with the help of a our dummy video file.
	if (".BIUvideo.mp4" in Nowplaying):
            # Split into filename and directory (later needed).
            # ntpath should be OS agnostic (stackoverflow).
            BIU_FolderPath_unicode = ntpath.dirname(Nowplaying) + '\\'
            log('BIU_FolderPath_unicode = %s ' % BIU_FolderPath_unicode)
            BIU_FileName_unicode = ntpath.basename(Nowplaying)
            log('BIU_FileName_unicode = %s ' % BIU_FileName_unicode)
            # First validatepath to get the slashes OK,
            # then translatepath to get all the paths working.
            BIU_videofile_unicode = xbmc.validatePath(BIU_FolderPath_unicode + BIU_FileName_unicode).decode("utf-8")
            BIU_videofile_unicode = xbmc.translatePath(BIU_videofile_unicode).decode("utf-8")
            log('BIU_videofile_unicode (.mp4) = %s ' % BIU_videofile_unicode)
            
		    
        # If it is our special video, then we need to redirect xbmc.player to the correct bluray playlist.
        if (settings.service_enabled and (BIU_videofile_unicode != "")):
            # We are playing a .BIUvideo file!!
            log('Playing BIUvideo File : %s'% BIU_videofile_unicode)
            # This is the first pass of our service script
            log('First pass of the service script')
            Global_BIU_vars["Current_video_time"] = 0	    # Init
            Global_BIU_vars["BIU_videofile_unicode"] = BIU_videofile_unicode	    # Init
            Global_BIU_vars["Video_ID"] = -1	            # Init
            Global_BIU_vars["PlayCount"] = 0	            # Init
            Global_BIU_vars["Update_Streamdetails"] = False # Init
            Global_video_dict = {}                          # Init
		
            # Use Files.GetFileDetails to see if it is a movie or a tv episode video
            # Also gives us the DBID.
            try:
                JSON_req = {"jsonrpc": "2.0",
                            "method": "Files.GetFileDetails",
                            "params": {"file": BIU_videofile_unicode,
                                       "media": "video",},
                            "id": "1"}
                log('JSON_req string = %s' % json.dumps(JSON_req))
                JSON_result = utils.executeJSON(JSON_req)
                log('JSON Files.GetFileDetails result = %s' % JSON_result)
                # Is it a movie or a tv show?
                Global_BIU_vars["Video_Type"] = JSON_result["result"]["filedetails"]["type"]
                if Global_BIU_vars["Video_Type"] not in [u'unknown', u'movie', u'episode']:
                    self.BIU_ExitHandler('Error receiving JSON Files.GetFileDetails info!!')
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
                                           "properties": ["art",
                                                          "cast",
                                                          "dateadded", "director",
                                                          "episode",
                                                          "fanart", "file", "firstaired",
                                                          "lastplayed",
                                                          "originaltitle",
                                                          "playcount", "plot", "productioncode",
                                                          "rating", "runtime", "resume",
                                                          "season", "showtitle", "streamdetails",
                                                          "thumbnail", "title", "tvshowid",
                                                          "uniqueid", "userrating",
                                                          "votes",
                                                          "writer"]},
                                "id": "1"}
                    log('JSON_req string = %s' % json.dumps(JSON_req))
                    JSON_result = utils.executeJSON(JSON_req)
                    log('JSON VideoLibrary.GetEpisodeDetails result = %s' % JSON_result)
                    # A
                    Global_video_dict["BIU_Art_Poster_unicode"] = JSON_result["result"]["episodedetails"]["art"]["tvshow.poster"]
                    # C
                    Global_video_dict["BIU_Cast_unicode"] = JSON_result["result"]["episodedetails"]["cast"]
                    # D
                    Global_video_dict["BIU_DateAdded_unicode"] = JSON_result["result"]["episodedetails"]["dateadded"]
                    Global_video_dict["BIU_Director_unicode"] = JSON_result["result"]["episodedetails"]["director"]
                    # E
                    Global_video_dict["BIU_Episode_unicode"] = JSON_result["result"]["episodedetails"]["episode"]
                    # F (fanart, file)
                    Global_video_dict["BIU_FirstAired_unicode"] = JSON_result["result"]["episodedetails"]["firstaired"]
                    # L
                    Global_video_dict["BIU_LastPlayed_unicode"] = JSON_result["result"]["episodedetails"]["lastplayed"]
                    # O
                    Global_video_dict["BIU_OriginalTitle_unicode"] = JSON_result["result"]["episodedetails"]["originaltitle"]
                    # P (productioncode)
                    Global_BIU_vars["PlayCount"] = JSON_result["result"]["episodedetails"]["playcount"]
                    Global_video_dict["BIU_Plot_unicode"] = JSON_result["result"]["episodedetails"]["plot"]
                    # R (resume)
                    Global_video_dict["BIU_Rating_unicode"] = JSON_result["result"]["episodedetails"]["rating"]
                    Global_video_dict["BIU_RunTime_unicode"] = JSON_result["result"]["episodedetails"]["runtime"]
                    # S
                    Global_video_dict["BIU_Season_unicode"] = JSON_result["result"]["episodedetails"]["season"]
                    Global_video_dict["BIU_TVShowTitle_unicode"] = JSON_result["result"]["episodedetails"]["showtitle"]
                    Global_video_dict["BIU_StreamDetails_unicode"] = JSON_result["result"]["episodedetails"]["streamdetails"]
                    # T (tvshowid)
                    Global_video_dict["BIU_Art_Thumb_unicode"] = JSON_result["result"]["episodedetails"]["thumbnail"]
                    Global_video_dict["BIU_Title_unicode"] = JSON_result["result"]["episodedetails"]["title"]
                    # U (uniqueid)
                    Global_video_dict["BIU_UserRating_unicode"] = JSON_result["result"]["episodedetails"]["userrating"]
                    # V
                    Global_video_dict["BIU_Votes_unicode"] = JSON_result["result"]["episodedetails"]["votes"]
                    # W
                    Global_video_dict["BIU_Writer_unicode"] = JSON_result["result"]["episodedetails"]["writer"]
                elif Global_BIU_vars["Video_Type"] ==  u'movie': # we have a movie
                    log('We play a movie.')
                    # Get all the properties of the movie
                    JSON_req = {"jsonrpc": "2.0",
                                "method": "VideoLibrary.GetMovieDetails",
                                "params": {"movieid": Global_BIU_vars["Video_ID"],
                                           "properties": ["art",
                                                          "cast",
                                                          "dateadded", "director",
                                                          "fanart", "file",
                                                          "genre",
                                                          "imdbnumber",
                                                          "lastplayed",
                                                          "mpaa",
                                                          "originaltitle",
                                                          "playcount", "plot", "plotoutline", "premiered",
                                                          "rating", "runtime", #"resume",
                                                          "setid", "sorttitle", "streamdetails", "studio",
                                                          "tagline", "thumbnail", "title", "trailer",
                                                          "userrating",
                                                          "votes",
                                                          "writer"]},
                                "id": "1"}
                    log('JSON_req string = %s' % json.dumps(JSON_req))
                    JSON_result = utils.executeJSON(JSON_req)
                    log('JSON VideoLibrary.GetMovieDetails result = %s' % JSON_result)
                    # A
                    Global_video_dict["BIU_Art_Poster_unicode"] = JSON_result["result"]["moviedetails"]["art"]["poster"]
                    # C
                    Global_video_dict["BIU_Cast_unicode"] = JSON_result["result"]["moviedetails"]["cast"]
                    # D
                    Global_video_dict["BIU_DateAdded_unicode"] = JSON_result["result"]["moviedetails"]["dateadded"]
                    Global_video_dict["BIU_Director_unicode"] = JSON_result["result"]["moviedetails"]["director"]
                    # F (fanart, file)
                    # G
                    Global_video_dict["BIU_Genre_unicode"] =  JSON_result["result"]["moviedetails"]["genre"]
                    # I
                    Global_video_dict["BIU_imdbNumber_unicode"] = JSON_result["result"]["moviedetails"]["imdbnumber"]
                    # L
                    Global_video_dict["BIU_LastPlayed_unicode"] = JSON_result["result"]["moviedetails"]["lastplayed"]
                    # M
                    Global_video_dict["BIU_mpaa_unicode"] = JSON_result["result"]["moviedetails"]["mpaa"]
                    # O
                    Global_video_dict["BIU_OriginalTitle_unicode"] = JSON_result["result"]["moviedetails"]["originaltitle"]
                    # P
                    Global_BIU_vars["PlayCount"] = JSON_result["result"]["moviedetails"]["playcount"]
                    Global_video_dict["BIU_Plot_unicode"] = JSON_result["result"]["moviedetails"]["plot"]
                    Global_video_dict["BIU_PlotOutline_unicode"] = JSON_result["result"]["moviedetails"]["plotoutline"]
                    Global_video_dict["BIU_Premiered_unicode"] = JSON_result["result"]["moviedetails"]["premiered"]
                    # R (resume)
                    Global_video_dict["BIU_Rating_unicode"] = JSON_result["result"]["moviedetails"]["rating"]
                    Global_video_dict["BIU_RunTime_unicode"] = JSON_result["result"]["moviedetails"]["runtime"]
                    #Global_video_dict["BIU_Resume_unicode"] = JSON_result["result"]["moviedetails"]["resume"]
                    # S
                    Global_video_dict["BIU_setID_unicode"] = JSON_result["result"]["moviedetails"]["setid"]
                    Global_video_dict["BIU_SortTitle_unicode"] = JSON_result["result"]["moviedetails"]["sorttitle"]
                    Global_video_dict["BIU_StreamDetails_unicode"] = JSON_result["result"]["moviedetails"]["streamdetails"]
                    Global_video_dict["BIU_Studio_unicode"] = JSON_result["result"]["moviedetails"]["studio"]
                    # T
                    Global_video_dict["BIU_Tagline_unicode"] = JSON_result["result"]["moviedetails"]["tagline"]
                    Global_video_dict["BIU_Art_Thumb_unicode"] = JSON_result["result"]["moviedetails"]["thumbnail"]
                    Global_video_dict["BIU_Title_unicode"] = JSON_result["result"]["moviedetails"]["title"]
                    Global_video_dict["BIU_Trailer_unicode"] = JSON_result["result"]["moviedetails"]["trailer"]
                    # U
                    Global_video_dict["BIU_UserRating_unicode"] = JSON_result["result"]["moviedetails"]["userrating"]
                    # V
                    Global_video_dict["BIU_Votes_unicode"] = JSON_result["result"]["moviedetails"]["votes"]
                    # W
                    Global_video_dict["BIU_Writer_unicode"] = JSON_result["result"]["moviedetails"]["writer"]
                    
            except Exception:
                log('Error getting JSON response, media is probably unknown!!')
                Global_video_dict["BIU_Art_Thumb_unicode"] = ""
                Global_video_dict["BIU_Art_Poster_unicode"] = ""
                Global_video_dict["BIU_Title_unicode"] = ""
                Global_video_dict["BIU_Plot_unicode"] = ""
                Global_video_dict["BIU_Votes_unicode"] = ""
                Global_video_dict["BIU_DateAdded_unicode"] = ""
                Global_video_dict["BIU_OriginalTitle_unicode"] = ""
                Global_video_dict["BIU_UserRating_unicode"] = ""
                Global_video_dict["BIU_Rating_unicode"] = ""
                Global_video_dict["BIU_Writer_unicode"] = ""
                Global_video_dict["BIU_Director_unicode"] = ""
                Global_video_dict["BIU_StreamDetails_unicode"] = ""
                Global_video_dict["BIU_LastPlayed_unicode"] = ""
                Global_video_dict["BIU_Cast_unicode"] = ""
                Global_BIU_vars["PlayCount"] = 0
                Global_BIU_vars["Video_ID"] = -1
                
            # Check if the video streamdetails are empty, if they are then we need to update the Kodi library
            log('Streamdetails are %s' % Global_video_dict["BIU_StreamDetails_unicode"])
            if Global_video_dict["BIU_StreamDetails_unicode"]["video"] == []:
                Global_BIU_vars["Update_Streamdetails"] = True

            # Was this video played already?
            # If playcount = 0 then the video is not watched, if playcount > 0 then the video is watched
            log('Playcount = %s' % Global_BIU_vars["PlayCount"])
		
            # First validatepath to get the slashes OK,
            # then translatepath to get all the paths working.
            BIU_file_unicode = xbmc.validatePath(BIU_FolderPath_unicode + 'BIUinfo.xml').decode("utf-8")
            BIU_file_unicode = xbmc.translatePath(BIU_file_unicode).decode("utf-8")
            log('BIUfile.xml = %s ' % BIU_file_unicode)

            # Read the entire contents of the BIUfile.xml file.
            try:
                tree_XML = ET.parse(BIU_file_unicode)
                directorydetails_XML = tree_XML.getroot()
                log('BIUfile.xml file has been read.')
            except:
                self.BIU_ExitHandler('Error reading BIUfile.xml!!')
                return

            # Init
            backpathiso_UTF8 = None
            myplaylistnumber_UTF8 = None
            mystarttime_UTF8 = None
            mystoptime_UTF8 = None
            myaudiostream_UTF8 = None
            mysubtitlestream_UTF8 = None
            # Extract all settings from the BIUfile.xml file.
            for video_XML in directorydetails_XML:                              # for every video node
                log('Videofile = %s' % (video_XML.attrib['filename']))
                # check if the filename attrib contains the correct filename
                if (video_XML.attrib['filename'] == BIU_FileName_unicode): 
                    log('Videofile and xml record match.')                      # if yes: We have a winner!!!
                    # Location of the iso file
                    backpathiso = video_XML.find('isofile')
                    if backpathiso is not None:
                        backpathiso_UTF8 = backpathiso.text
                        log('isofile = %s' % backpathiso_UTF8)
                    # Playlist number
                    myplaylistnumber = video_XML.find('playlist')
                    if myplaylistnumber is not None:
                        myplaylistnumber_UTF8 = myplaylistnumber.text
                        log('playlist = %s' % myplaylistnumber_UTF8)
                    # Starttime
                    mystarttime = video_XML.find('starttime')
                    if mystarttime is not None:
                        mystarttime_UTF8 = mystarttime.text
                        log('starttime = %s' % mystarttime_UTF8)
                    # Stoptime
                    mystoptime = video_XML.find('stoptime')
                    if mystoptime is not None:
                        mystoptime_UTF8 = mystoptime.text
                        log('stoptime = %s' % mystoptime_UTF8)
                    # Audiostream
                    myaudiostream = video_XML.find('audiochannel')
                    if myaudiostream is not None:
                        myaudiostream_UTF8 = myaudiostream.text
                        log('audiochannel = %s' % myaudiostream_UTF8)
                    # Subtitlestream
                    mysubtitlestream = video_XML.find('subtitlechannel')
                    if mysubtitlestream is not None:
                        mysubtitlestream_UTF8 = mysubtitlestream.text
                        log('subtitlechannel = %s' % mysubtitlestream_UTF8)
                    break               # No need to check the other entries, we found our match.

            # The base path is "BIU_Path_unicode". Normally the user would place the iso file
            # in a subdirectory of the base path. However, with the following code section it is also
            # possible to up 1 or more parent directories and place there the iso file.
            # This is usefull for movie iso's with different 'cuts'.
            backpathdir_unicode = BIU_FolderPath_unicode
            log("BIU_Backpathdir = %s" % backpathdir_unicode)
            if backpathiso_UTF8 != None:
                backpathiso_unicode = backpathiso_UTF8.decode("utf-8")
            else:
                self.BIU_ExitHandler('Backpathiso_UTF8 is empty.')
                return
            log("Backpathiso = %s" % backpathiso_unicode)
             # Cut of the trailing slash, we will add it again after the while loop
            backpathdir_unicode = backpathdir_unicode[:-1]    
            # As long as the iso dir in the .xml file has "../" (or "..\")in front,
            # cut off the last dir in backpathdir_unicode (same as "cd .." in the shell)
            while ((backpathiso_unicode[:3] == "../") or (backpathiso_unicode[:3] == "..\\")):
                backpathiso_unicode = backpathiso_unicode[3:]
                # We don't know if this system uses "/" or "\".
                # Take care of both possibilities
                myindex_1 = backpathdir_unicode.rfind("\\")     # Dual slash needed
                myindex_2 = backpathdir_unicode.rfind("/")
                # Result of myindex will be -1 if not found, or a number if found
                # Both "/" and "\" are not mixed in one and the same path (I hope)
                if myindex_1 != -1:
                    log('Myindex_1 = %s' % myindex_1)
                    backpathdir_unicode = backpathdir_unicode[:myindex_1]
                if myindex_2 != -1:                              
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
            log("Mystreamnumber = %s" % myplaylistnumber_UTF8)
            if myplaylistnumber_UTF8 == None:
                self.BIU_ExitHandler('No valid playlist number in BIUfiles.xml!')
                return
            # Aaargh!!! urllib.quote does not work with unicode strings!! Great!!!
            # Encode first to UTF-8. Luckely UTF-8 works...
            myescapedisofile_UTF8 = myisofile_unicode.encode("utf-8")
            myescapedisofile_UTF8 = urllib.quote(myescapedisofile_UTF8, safe='!')
            myescapedisofile_UTF8 = 'udf://' + myescapedisofile_UTF8 + '/'
            myescapedisofile_UTF8 = urllib.quote(myescapedisofile_UTF8, safe='()!')
            myescapedisofile_UTF8 = 'bluray://' + myescapedisofile_UTF8 + '/BDMV/PLAYLIST/' + myplaylistnumber_UTF8 + '.mpls'
            log("Myescapedisofile_UTF8 = %s" % myescapedisofile_UTF8)

            # Get resume info from the db
            try:
                # Open db
                sqlcon_wl = sqlite3.connect(self.dbPath);
                sqlcursor_wl = sqlcon_wl.cursor()
                # Check if a resume point for this video exist
                values = list([Global_BIU_vars["BIU_videofile_unicode"]])
                sqlcursor_wl.execute(QUERY_SELECT_SQLITE, values)
                db_ret = sqlcursor_wl.fetchall()
                # Is there a valid resume point in the db?
                if db_ret != []:
                    # Yes
                    Global_BIU_vars["Resume_Time"] = int(db_ret[0][1])
                    log("Valid resumepoint in the db for this video is: %s" % str(Global_BIU_vars["Resume_Time"]))

                    # Check if the user wants to resume this video
                    dialog = xbmcgui.Dialog()
                    dialog_ret = dialog.yesno('Kodi', 'Do you want this video to resume from %s ?'% self.ConvertSecsToTime(Global_BIU_vars["Resume_Time"]))
                    if not dialog_ret:
                        # User doesn't want to resume, set resumetime to 0
                        log("User does not want to resume this video.")
                        Global_BIU_vars["Resume_Time"] = 0
                else:
                    # No
                    log("No resume point in the db for this video.")
            except Exception:
                log("Error accessing db! (Getting resume point)")
            finally:
                # Close db
                sqlcon_wl.close()
            
            # Get the starttime (if specified)
            Global_BIU_vars["Start_time"] = 0        # We are playing a new video, so init self.Starttime
            if mystarttime_UTF8 != None:             # A starttime was specified in the .xml file.
                try:
                    Global_BIU_vars["Start_time"] = self.ConvertTimeToSecs(mystarttime_UTF8)
                except Exception:
                    log('Error converting starttime. Using 0 sec instead.')
                    Global_BIU_vars["Start_time"] = 0
            log('Starttime = %s seconds' % Global_BIU_vars["Start_time"])

            # Get the stoptime (if specified)
            # We use a globel var because we need to check time outside this class.
            # We are playing a new video, so init Stop_time 
            Global_BIU_vars["Stop_time"] = Global_BIU_vars["Default_stop_time"] 
            if mystoptime_UTF8 != None:              # A stoptime was specified in the .xml file.
                try:
                    Global_BIU_vars["Stop_time"] = self.ConvertTimeToSecs(mystoptime_UTF8)
                except Exception:
                    log('Error converting stoptime. Using 9999999 sec instead.')
                    Global_BIU_vars["Stop_time"] = Default_stop_time            
            log('Stoptime = %s seconds' % Global_BIU_vars["Default_stop_time"])

            # Get the audiostream from the .xml file (if any)
            # and put this in self.reqaudio
            self.reqaudio = -1                          # Init var
            try:
                self.reqaudio = int(myaudiostream)      # Will except if myaudiostream == None
                log('Reqaudiochannel = %s' % self.reqaudio)
            except Exception:
                log('No valid audiostream specified in the .xml file!')

            # Get the subtitlestream from the .xml file (if any)
            # and put this is self.reqsubtitle
            self.reqsubtitle = -1                           # Init var
            try:
                self.reqsubtitle = int(mysubtitlestream)    # Will except if mysubtitlestream == None
                log('Reqsubtitlestream = %s' % self.reqsubtitle)
                if self.reqsubtitle == 0:
                    log('External subtitle file wanted.')
                    # Get the external subtitle filename.
                    # Could be: '.srt'; ...
                    temp_string = BIU_FileName_unicode[:-3]
                    BIU_subtitlefile_unicode = xbmc.validatePath(BIU_FolderPath_unicode + temp_string).decode("utf-8")
                    BIU_subtitlefile_unicode = xbmc.translatePath(BIU_subtitlefile_unicode).decode("utf-8")
                    # Check if subtitle file is a .srt file.
                    if xbmcvfs.exists(BIU_subtitlefile_unicode + 'srt'):
                        self.ExtSubFile = BIU_subtitlefile_unicode + 'srt'
                        log('Subtitlefile is : %s' % self.ExtSubFile)
                    # No valid subtitle file found!
                    else:
                        self.reqsubtitle = -1 # Use whatever default the user has
                        raise
            except Exception:
                log('No valid subtitlestream specified in the .xml file!')

            # Play the correct bluray playlist
            # Fill first a listitem with the values of the .BIUfile.mp3 file. This way we get the correct mediainfo
            # while playing our bluray playlist. Otherwise this is empty (thumb picture) or 00800.mpls as name...
            # Could be that we need to copy more later, other skins might want to display other listitems.infolabels
            mylistitems = xbmcgui.ListItem (Global_video_dict["BIU_Title_unicode"])
            mylistitems.setArt({'thumb': Global_video_dict["BIU_Art_Thumb_unicode"]})
            mylistitems.setArt({'poster': Global_video_dict["BIU_Art_Poster_unicode"]})
            # Add the resumetime to the starttime
            startplayingfrom = Global_BIU_vars["Start_time"] + Global_BIU_vars["Resume_Time"]
            # If startplayingfrom <> 0 then start the video with the correct starttime (StartOffset).
            if startplayingfrom != 0:
                mylistitems.setProperty('StartOffset', str(startplayingfrom))  # Is better alternative to 'start and then seek'
            # Convert "cast" [{thumbnail, role, name, order}, {thumbnail, role, name, order}] to
            # [(name, role), (name, role)].
            myactor_list = []
            for item in Global_video_dict["BIU_Cast_unicode"]:
                log('Name: %s as role: %s' % (item["name"], item["role"]))
                myactor_list.append((item["name"], item["role"]))

            # Set the player/videoplayer infolabels
            # First infolabels used for both movie and tv shows
            mylistitems.setInfo('video', {'castandrole': myactor_list,
                                          'dateadded': Global_video_dict["BIU_DateAdded_unicode"],
                                          'director': Global_video_dict["BIU_Director_unicode"],
                                          'lastplayed': Global_video_dict["BIU_LastPlayed_unicode"],
                                          'mediatype': Global_BIU_vars["Video_Type"],
                                          'originaltitle': Global_video_dict["BIU_OriginalTitle_unicode"],
                                          'playcount': Global_BIU_vars["PlayCount"],
					  'plot': Global_video_dict["BIU_Plot_unicode"], 
					  'rating': Global_video_dict["BIU_Rating_unicode"], 
                                          'runtime': Global_video_dict["BIU_RunTime_unicode"],
					  'title': Global_video_dict["BIU_Title_unicode"], 
                                          'userrating': Global_video_dict["BIU_UserRating_unicode"],
                                          'votes': Global_video_dict["BIU_Votes_unicode"], 
                                          'writer' : Global_video_dict["BIU_Writer_unicode"]})
            # Movie specific infolabels
            if Global_BIU_vars["Video_Type"] ==  u'movie':
                # Convert genre list "[u'Comedy', u'Drama', u'Music', u'Mystery']" into string
                # like: "Comedy / Drama / Music / Mystery"
                Genre_string = ""
                for item in Global_video_dict["BIU_Genre_unicode"]:
                    Genre_string = Genre_string + item + ' / '
                Genre_string = Genre_string[:-3]
                log('Genre = %s' % Genre_string)
                
                mylistitems.setInfo('video', {'code': Global_video_dict["BIU_imdbNumber_unicode"],
                                              'genre': Genre_string,
                                              'mpaa': Global_video_dict["BIU_mpaa_unicode"],
                                              'plotoutline': Global_video_dict["BIU_PlotOutline_unicode"],
                                              'premiered': Global_video_dict["BIU_Premiered_unicode"],
                                              'sorttitle': Global_video_dict["BIU_SortTitle_unicode"],
                                              'studio': Global_video_dict["BIU_Studio_unicode"],
                                              'tagline': Global_video_dict["BIU_Tagline_unicode"],
                                              'trailer': Global_video_dict["BIU_Trailer_unicode"]})
                # Global_video_dict["ListItem_setID_unicode"] not used yet
            # TV show specific infolabels
            elif Global_BIU_vars["Video_Type"] ==  u'episode':
                mylistitems.setInfo('video', {'aired': Global_video_dict["BIU_FirstAired_unicode"],
                                              'episode': Global_video_dict["BIU_Episode_unicode"],
                                              'season': Global_video_dict["BIU_Season_unicode"],
                                              'tvshowtitle': Global_video_dict["BIU_TVShowTitle_unicode"]})

            # Now play the bluray playlist with the correct infolabels/starttime...
            self.play(myescapedisofile_UTF8, mylistitems)
            # Set flag to true, doing this earlier could set a video as watched (12 sec black video ends)
            self.isPlayingBIUBluRay = True
            # Temporary 'the end' for onPlayBackStarted.
            # Now it's waiting for the second pass, where we extract subtitle
            # and audio info from the correct bluray playlist.



        # Here we have the second pass of our service.
        # We detect this by looking at the filename of the current playing file.
        # If it includes ".BIUfiles" then we have a hit.
        if (self.isPlayingBIUBluRay and ('.BIUfiles' in Nowplaying)):
            log('Second pass of the service script')

            # If a audiostream number is set in the .xml file,
            # then we enable that audiostream here
            audiostreams = self.getAvailableAudioStreams()
            log('Available audiostreams = %s' % audiostreams)
            numberofaudiostreams = len(audiostreams)
            log('Number of audiostreams = %s' % numberofaudiostreams)
            log('Reqaudiochannel = %s' % self.reqaudio)
            if self.reqaudio != -1:
                # The .xml file contains a valid (?) audio stream number
                if ((self.reqaudio > 0) and (self.reqaudio <= numberofaudiostreams)):
                    reqaudiochannel = self.reqaudio - 1 # Goes from 0 to count-1 in Kodi
                    self.setAudioStream(reqaudiochannel)
                    log('Audiostream %s set' % (reqaudiochannel + 1))
                else:
                    log('No valid audiostream specified in the .xml file!')
                    
            # If a subtitlestream number is set in the .xml file,
            # then we enable that subtitlestream here                
            subtitlestreams = self.getAvailableSubtitleStreams()
            log('Available subtitlestreams = %s' % subtitlestreams)
            numberofsubtitlestreams = len(subtitlestreams)
            log('Number of subtitlestreams = %s' % numberofsubtitlestreams)
            log('Reqsubtitlestream = %s' % self.reqsubtitle)
            if self.reqsubtitle != -1:
                # The .xml file contains a valid (?) subtitle stream number
                try:
                    log('1')
                    if self.reqsubtitle == 0:               # Use an external subtitle stream file.
                        log('External subtitlestream enabled')
                        log('Subtitle file = %s ' % self.ExtSubFile)
                        self.setSubtitles(self.ExtSubFile)
                    elif ((self.reqsubtitle > 0) and (self.reqsubtitle <= numberofsubtitlestreams)): # Use internal subtitles
                        log('Internal subtitlestream %s enabled' % self.reqsubtitle)
                        reqsubtitlestream = self.reqsubtitle - 1   # Goes from 0 to count-1 in Kodi
                        self.setSubtitleStream(reqsubtitlestream)
                        self.showSubtitles(True)
                except Exception:
                    log('No valid subtitlestream specified in the .xml file!')         

            # Calculate the video duration, needed for watched flag
            if Global_BIU_vars["Stop_time"] != Global_BIU_vars["Default_stop_time"]:
                # We have a non default stoptime
                Global_BIU_vars["Duration"] = Global_BIU_vars["Stop_time"] - Global_BIU_vars["Start_time"]
            else:
                # Duration is from video duration
                Global_BIU_vars["Duration"] = self.getTotalTime() - Global_BIU_vars["Start_time"]
            log('Video duration = %s' % str(Global_BIU_vars["Duration"]))

            # Set all streamdetails so we can save
            if Global_BIU_vars["Update_Streamdetails"] == True:
                pass


            

            BIU_videoresolution = xbmc.getInfoLabel('VideoPlayer.VideoResolution').decode("utf-8")
            log('VideoPlayer.VideoResolution = %s ' % BIU_videoresolution)
            BIU_videoaspect = xbmc.getInfoLabel('VideoPlayer.VideoAspect').decode("utf-8")
            log('VideoPlayer.VideoAspect = %s ' % BIU_videoaspect)
            BIU_audiocodec = xbmc.getInfoLabel('VideoPlayer.AudioCodec').decode("utf-8")
            log('VideoPlayer.AudioCodec = %s ' % BIU_audiocodec)
            BIU_audiochannels = xbmc.getInfoLabel('VideoPlayer.AudioChannels').decode("utf-8")
            log('VideoPlayer.AudioChannels = %s ' % BIU_audiochannels)
            BIU_audiolanguage = xbmc.getInfoLabel('VideoPlayer.AudioLanguage').decode("utf-8")
            log('VideoPlayer.AudioLanguage = %s ' % BIU_audiolanguage)
            BIU_subtitleslanguage = xbmc.getInfoLabel('VideoPlayer.SubtitlesLanguage').decode("utf-8")
            log('VideoPlayer.SubtitlesLanguage = %s ' % BIU_subtitleslanguage)
            BIU_duration = xbmc.getInfoLabel('VideoPlayer.Duration').decode("utf-8")
            log('VideoPlayer.Duration = %s ' % BIU_duration)
            BIU_videocodec = xbmc.getInfoLabel('VideoPlayer.VideoCodec').decode("utf-8")
            log('VideoPlayer.VideoCodec = %s ' % BIU_videocodec)
            BIU_DBID = xbmc.getInfoLabel('VideoPlayer.DBID').decode("utf-8")
            log('VideoPlayer.DBID = %s ' % BIU_DBID)





                








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
            # Always logged, user should know the addon is not enabled while debugging turned off.
            xbmc.log('%s: Service not enabled' % ADDONNAME, level=xbmc.LOGDEBUG)
        self._daemon()

    def _init_vars(self):
	# Needed for watched state en resumepoint
        global Global_BIU_vars
        
        self.monitor = BIUmonitor()
        self.player = BIUplayer()

        # Read the entire contents of the advancedsettings.xml file.
        # I don't know any other way to get these user setings.
        # And if a user set's these, then my addon should honour those settings.
        # If there is a better/approved way, let me know and I change the addon.
        try:
            tree_XML = ET.parse(xbmc.translatePath("special://masterprofile/advancedsettings.xml"))
            advancedsettings_XML = tree_XML.getroot()
            log('advancedsettings.xml file has been read.')
            # Get all values
            for video_XML in advancedsettings_XML:            
                Temp = advancedsettings_XML.find("video/playcountminimumpercent")
                if Temp is not None:
                    Global_BIU_vars["playcountminimumpercent"] = int(Temp.text)
                Temp = advancedsettings_XML.find("video/ignoresecondsatstart")
                if Temp is not None:
                    Global_BIU_vars["ignoresecondsatstart"] = int(Temp.text)
                Temp = advancedsettings_XML.find("video/ignorepercentatend")
                if Temp is not None:
                    Global_BIU_vars["ignorepercentatend"] = int(Temp.text)
        except Exception:
            log('Error reading advancedsettings.xml!!')
        # Log all values
        log('playcountminimumpercent = %s' % str(Global_BIU_vars["playcountminimumpercent"]))
        log('ignoresecondsatstart = %s' % str(Global_BIU_vars["ignoresecondsatstart"]))
        log('ignorepercentatend = %s' % str(Global_BIU_vars["ignorepercentatend"]))

        try:
            # Init db
            sqlcon_wl = sqlite3.connect(os.path.join(ADDONPROFILE, "BIU.db"));
            sqlcursor_wl = sqlcon_wl.cursor()

            # create tables if they don't exist
            sqlcursor_wl.execute(QUERY_CREATE_SQLITE)
            sqlcon_wl.commit()
        except Exception:
            log("Error accessing db! (Init)")
        finally:
            log("Init - Closing DB.")
            sqlcon_wl.close()


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
            if ((settings.service_enabled == 'true') and (BIUplayer().isPlayingVideo()) and (self.player.isPlayingBIUBluRay)):
                # We play a BIU video, track current time for watched state
                Global_BIU_vars["Current_video_time"] = BIUplayer().getTime()
                log('Daemon: Current video time:  = %s' % str(Global_BIU_vars["Current_video_time"]))
                # We have a custom stoptime, stop when current time > stoptime
                if (Global_BIU_vars["Stop_time"] != Global_BIU_vars["Default_stop_time"]):
                    if (Global_BIU_vars["Current_video_time"] > Global_BIU_vars["Stop_time"]):
                        log('Time to stop playing video - Stopping player.')
                        BIUplayer().stop()


# Real start of the program
if (__name__ == "__main__"):
    # Always logged, user should know addon is installed while debugging turned off.
    xbmc.log('%s: version %s started' % (ADDONNAME, ADDONVERSION), level=xbmc.LOGDEBUG)
    main = Main()
    # Always logged, user should know addon is installed while debugging turned off.
    xbmc.log('%s: version %s stopped' % (ADDONNAME, ADDONVERSION), level=xbmc.LOGDEBUG)
