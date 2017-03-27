# -*- coding: utf-8 -*-
#
#     Copyright (C) 2017 Wimpie
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
import langcodes
import xml.dom.minidom

# import xbmcgui
# import xbmcvfs

ADDON        = xbmcaddon.Addon()
ADDONVERSION = ADDON.getAddonInfo('version')
ADDONNAME    = ADDON.getAddonInfo('name')
ADDONPATH    = ADDON.getAddonInfo('path').decode('utf-8')
ADDONPROFILE = xbmc.translatePath( ADDON.getAddonInfo('profile') ).decode('utf-8')
ICON         = ADDON.getAddonInfo('icon')

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

# This class is the interface between the internal default settings and the user.
# The user adjust the settings to his/her likings in Kodi. This class will make
# sure that the addon knows that the user changed a setting.
class Mysettings():
    # Init 
    def __init__(self):
        self.service_debug = ADDON.getSetting('debug') == 'true'            # Construct to get bool, getSetting returns a string of 'false'|'true'
        self.log_settings('Init settings')
        self.readSettings()

    def init(self):
        self.__init__

    def convertsubchoice(self, choice):
        # Subtitles, possible result values:
        # 0 : No (no)
        # 1 : Yes (yes)
        # 2 : Prefer subtitles for spoken foreign languagues (for_lang)
        # 3 : Yes, unless original language is user language (yes_no_orig) (only with original audio)
        if choice == "0":
            result = "no"
        elif choice == "1":
            result = "yes"
        elif choice == "2":
            result = "for_lang"
        else:
            result = "yes_no_orig"
        return result
            

    # Read setting that user can change from within Kodi    
    def readSettings(self):
        self.log_settings('User changed settings')
        self.service_debug = ADDON.getSetting('debug') == 'true'            # Construct to get bool, getSetting returns a string of 'false'|'true'
        self.log_settings('Setting.debug: %s' % self.service_debug)
        self.service_enabled = ADDON.getSetting('enabled') == 'true'
        self.log_settings('Setting.enabled: %s' % self.service_enabled)

        # Show recap with tv-shows?
        self.show_recap = ADDON.getSetting('show_recap') == 'true'

        # User languages
        self.UserLang01 = langcodes.LanguageSelected(int(ADDON.getSetting('UserLang01')))
        self.log_settings('User language 1 : %s' % self.UserLang01)
        self.UserLang02 = langcodes.LanguageSelected(int(ADDON.getSetting('UserLang02')))
        # Special case: if self.UserLang02 == "-a-" then self.UserLang02 = "---" (any comes before none in language list)
        if self.UserLang02 == "-a-":
            self.UserLang02 = "---"
        self.log_settings('User language 2 : %s' % self.UserLang02)

        # disc languages
        self.prim_disc_lang = langcodes.LanguageSelected(int(ADDON.getSetting('DiscLang01')))
        self.log_settings('Primary disc language: %s' % self.prim_disc_lang)
        self.sec_disc_lang = langcodes.LanguageSelected(int(ADDON.getSetting('DiscLang02')))
        self.log_settings('Secondary disc language: %s' % self.sec_disc_lang)
        self.other_disc_lang = langcodes.LanguageSelected(int(ADDON.getSetting('DiscLang03')))
        self.log_settings('Other disc language: %s' % self.other_disc_lang)

        # dubbed, or original audio; if dubbed, fall back to orig if not available
        # possible result values
        # 0 : Use original audio (orig)
        # 1 : Use dubbed audio (dubbed)
        self.prim_audio_lang = ("orig" if (ADDON.getSetting('AudioLang01') == "0") else "dubbed")
        self.log_settings('Primary language: %s' % self.prim_audio_lang)
        self.sec_audio_lang = ("orig" if (ADDON.getSetting('AudioLang02') == "0") else "dubbed")
        self.log_settings('Secondary language: %s' % self.sec_audio_lang)
        self.other_audio_lang = ("orig" if (ADDON.getSetting('AudioLang03') == "0") else "dubbed")
        self.log_settings('Other language: %s' % self.other_audio_lang)

        # Subtitles, possible result values:
        # 0 : No (no)
        # 1 : Yes (yes)
        # 2 : Prefer subtitles for spoken foreign languagues (for_lang)
        # 3 : Yes, unless original language is user language (yes_no_orig) (only with original audio)
        self.prim_SubDubbedLang = self.convertsubchoice(ADDON.getSetting('SubSubbedLang01'))
        self.log_settings('Subtitles when primary language is : Prefer Subbed: %s' % self.prim_SubDubbedLang)
        self.prim_SubOrigLang = self.convertsubchoice(ADDON.getSetting('SubOrigLang01'))
        self.log_settings('Subtitles when primary language is : Original: %s' % self.prim_SubOrigLang)
        self.sec_SubDubbedLang = self.convertsubchoice(ADDON.getSetting('SubSubbedLang02'))
        self.log_settings('Subtitles when secondary language is : Prefer Subbed: %s' % self.sec_SubDubbedLang)
        self.sec_SubOrigLang = self.convertsubchoice(ADDON.getSetting('SubOrigLang02'))
        self.log_settings('Subtitles when secondary language is : Original: %s' % self.sec_SubOrigLang)
        self.other_SubDubbedLang = self.convertsubchoice(ADDON.getSetting('SubSubbedLang03'))
        self.log_settings('Subtitles when other language is : Prefer Subbed: %s' % self.other_SubDubbedLang)
        self.other_SubOrigLang = self.convertsubchoice(ADDON.getSetting('SubOrigLang03'))
        self.log_settings('Subtitles when other language is : Original: %s' % self.other_SubOrigLang)
        
        # Accessibility : Use Kodi settings
        # Prefer the audio stream for the visually impaired to other audio streams of the same language
        self.Prefer_aud_vis_imp = False
        JSON_req = {"jsonrpc": "2.0",
                    "method": "Settings.GetSettingValue",
                    "params": {"setting": "accessibility.audiovisual"},
                    "id": 1}
        JSON_result = executeJSON(JSON_req)
        self.Prefer_aud_vis_imp = JSON_result["result"]["value"]
        self.log_settings('Prefer Audio Language for the visually impaired : %s' % ("True" if self.Prefer_aud_vis_imp else "False"))
        
        # Prefer the audio stream for the hearing impaired to other audio streams of the same language
        self.Prefer_aud_hear_imp = False
        JSON_req = {"jsonrpc": "2.0",
                    "method": "Settings.GetSettingValue",
                    "params": {"setting": "accessibility.audiohearing"},
                    "id": 1}
        JSON_result = executeJSON(JSON_req)
        self.Prefer_aud_hear_imp = JSON_result["result"]["value"]
        self.log_settings('Prefer the audio stream for the hearing impaired : %s' % ("True" if self.Prefer_aud_hear_imp else "False"))
        
        # Prefer the subtitle stream for the hearing impaired to other subtitle streams of the same language
        self.Prefer_sub_hear_imp = False
        JSON_req = {"jsonrpc": "2.0",
                    "method": "Settings.GetSettingValue",
                    "params": {"setting": "accessibility.subhearing"},
                    "id": 1}
        JSON_result = executeJSON(JSON_req)
        self.Prefer_sub_hear_imp = JSON_result["result"]["value"]
        self.log_settings('Prefer the subtitle stream for the hearing impaired : %s' % ("True" if self.Prefer_sub_hear_imp else "False"))
        
        


    def log_settings(self, txt):   # used only in settings, python does not know forward reference
        if self.service_debug:     # Only log when user addon setting is true
            if isinstance (txt,str):                        # if txt is an ASCII string
                txt = txt.decode("utf-8")                   # then make it unicode
            message = u'%s: %s' % (ADDONNAME, txt)
            xbmc.log(msg=message.encode("utf-8"), level=xbmc.LOGDEBUG)  # Kodi accepts UTF-8 strings, not unicode       

# Needed so we can use it in the next class.
settings = Mysettings()

# Logging function here because pyhton doesn't know forward declaration
def log(txt):                       # loglevel is LOGDEBUG
    if settings.service_debug:      # Only log when user addon setting is 'true'
        if isinstance (txt,str):                        # if txt is an ASCII string
            txt = txt.decode("utf-8")                   # then make it unicode
        message = u'%s: %s' % (ADDONNAME, txt)
        xbmc.log(msg=message.encode("utf-8"), level=xbmc.LOGDEBUG)  # Kodi accepts UTF-8 strings, not unicode

def GetXML_TagValue(my_element, tagname):
    '''
    Returns None if tag could not be found, or was empty, or has children
    Returns TagValue if tag exists
    '''
    try:
        TagValue_elem = my_element.getElementsByTagName(tagname)[0]
        TagValue = TagValue_elem.firstChild.data
        if TagValue_elem.firstChild.nodeType != xml.dom.minidom.Element.TEXT_NODE:
            TagValue = None
        if len(TagValue_elem.childNodes) != 1:
            TagValue = None
        if TagValue.strip() == "":
            TagValue = None
    except (IndexError, AttributeError) as e:
        TagValue = None
    return TagValue

def GetXML_hasChildren(my_element, tagname):
    '''
    Returns True if tag has children, else false
    '''
    try:
        TagValue = False
        TagValue_elem = my_element.getElementsByTagName(tagname)[0]
        if len(TagValue_elem.childNodes) > 1:
            TagValue = True
    except (IndexError, AttributeError) as e:
        TagValue = False
    return TagValue



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

