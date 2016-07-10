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

import os
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

def log(txt):                                       # loglevel is LOGDEBUG
    if isinstance (txt,str):                        # if txt is an ASCII string
        txt = txt.decode("utf-8")                   # then make it unicode
    message = u'%s: %s' % (ADDONNAME, txt)
    xbmc.log(msg=message.encode("utf-8"), level=xbmc.LOGDEBUG)  # Kodi accepts UTF-8 strings, not unicode

