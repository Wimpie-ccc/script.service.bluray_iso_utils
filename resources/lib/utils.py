# -*- coding: utf-8 -*-
#
#     Copyright (C) 2013 Team-XBMC
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

import os, json, time
import xbmc
import xbmcaddon

# import xbmcgui
# import xbmcvfs

ADDON        = xbmcaddon.Addon()
ADDONVERSION = ADDON.getAddonInfo('version')
ADDONNAME    = ADDON.getAddonInfo('name')
ADDONPATH    = ADDON.getAddonInfo('path').decode('utf-8')
ADDONPROFILE = xbmc.translatePath( ADDON.getAddonInfo('profile') ).decode('utf-8')
ICON         = ADDON.getAddonInfo('icon')

# This class is the interface between the internal default settings and the user.
# The user adjust the settings to his/her likings in Kodi. This class will make
# sure that the addon knows that the user changed a setting.
class Mysettings():
    # Init with some default values for the addon
    def init(self):
        self.service_debug = ADDON.getSetting('debug') == 'false'
        self.service_enabled = ADDON.getSetting('enabled') == 'true'
    
    def __init__(self):
        self.init()

    # Read setting that user can change from within Kodi    
    def readSettings(self):
        #self.log_settings('user changed settings')
        self.service_debug = ADDON.getSetting('debug')
        self.log_settings('Setting.debug: %s' % self.service_debug)
        self.service_enabled = ADDON.getSetting('enabled')
        self.log_settings('Setting.enabled: %s' % self.service_enabled)

    def log_settings(self, txt):   # used only in settings, python does not know forward reference
        if self.service_debug == 'true':      # Only log when user addon setting is true
            if isinstance (txt,str):                        # if txt is an ASCII string
                txt = txt.decode("utf-8")                   # then make it unicode
            message = u'%s: %s' % (ADDONNAME, txt)
            xbmc.log(msg=message.encode("utf-8"), level=xbmc.LOGDEBUG)  # Kodi accepts UTF-8 strings, not unicode

# Needed so we can use it in the next class.
settings = Mysettings()

# Logging function here because pyhton doesn't know forward declaration
def log(txt):                       # loglevel is LOGDEBUG
    if settings.service_debug == 'true':      # Only log when user addon setting is 'true'
        if isinstance (txt,str):                        # if txt is an ASCII string
            txt = txt.decode("utf-8")                   # then make it unicode
        message = u'%s: %s' % (ADDONNAME, txt)
        xbmc.log(msg=message.encode("utf-8"), level=xbmc.LOGDEBUG)  # Kodi accepts UTF-8 strings, not unicode

# Fixes unicode problems
def string_unicode(text, encoding='utf-8'):     
    try:
        text = unicode( text, encoding )
    except:
        pass
    return text

def normalize_string(text):                  
    try:
        text = unicodedata.normalize('NFKD', string_unicode(text)).encode('ascii', 'ignore')
    except:
        pass
    return text

def localise(id):
    string = normalize_string(ADDON.getLocalizedString(id))
    return string

def executeJSON(request):
    """Execute JSON-RPC Command
    
    Args:
        request: Dictionary with JSON-RPC Commands

    Found code in xbmc-addon-service-watchedlist
    """
    rpccmd = json.dumps(request) # create string from dict
    json_query = xbmc.executeJSONRPC(rpccmd)
    json_query = unicode(json_query, 'utf-8', errors='ignore')
    json_response = json.loads(json_query)  
    return json_response

def TimeStamptosqlDateTime(TimeStamp):
    """Convert Unix Timestamp to SQLite DateTime
    
        Args: 
            timestamp: E.g. 1368213804
            
        Returns:
            sqlDateTime: E.g. "2013-05-10 21:23:24"

    Found code in xbmc-addon-service-watchedlist        
    """
    if TimeStamp == 0:
        return ""
    else:
        return time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(TimeStamp))    

