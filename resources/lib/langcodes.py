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

# string_ID | English Name | ISO 639-3 Code (for 95%)
LANGUAGES = [
[32901, "Albanian", "sqi"],
[32902, "Arabic", "ara"],
[32903, "Armenian", "hye"],
[32904, "Basque", "eus"],
[32905, "Belarusian", "bel"],
[32906, "Bosnian", "bos"],
[32907, "Bulgarian", "bul"],
[32908, "Catalan", "cat"],
[32909, "Chinese", "zho"],
[32910, "Croatian", "hrv"],
[32911, "Czech", "ces"],
[32912, "Danish", "dan"],
[32913, "Dutch", "nld"],
[32914, "Dutch (Flemish)", "vls"],
[32915, "English", "eng"],
[32916, "Estonian", "est"],
[32917, "Farsi", "fas"],
[32918, "Finnish", "fin"],
[32919, "French", "fra"],
[32920, "German", "deu"],
[32921, "German (Austrian)", "d-at"],
[32922, "German (Swiss)", "gsw"],
[32923, "Greek", "ell"],
[32924, "Hebrew", "heb"],
[32925, "Hindi", "hin"],
[32926, "Hungarian", "hun"],
[32927, "Icelandic", "isl"],
[32928, "Indonesian", "ind"],
[32929, "Italian", "ita"],
[32930, "Japanese", "jpn"],
[32931, "Korean", "kor"],
[32932, "Latvian", "lav"],
[32933, "Lithuanian", "lit"],
[32934, "Macedonian", "mkd"],
[32935, "Malay", "msa"],
[32936, "Norwegian", "nor"],
[32937, "Polish", "pol"],
[32938, "Portuguese", "por"],
[32939, "Portuguese (Brazil)", "p-br"],
[32940, "Romanian", "ron"],
[32941, "Russian", "rus"],
[32942, "Serbian", "srp"],
[32943, "Slovak", "slk"],
[32944, "Slovenian", "slv"],
[32945, "Spanish", "spa"],
[32946, "Spanish (Latin America)", "s-la"],
[32947, "Swedish", "swe"],
[32948, "Tagalog", "tgl"],
[32949, "Thai", "tha"],
[32950, "Turkish", "tur"],
[32951, "Ukrainian", "ukr"],
[32952, "Vietnamese", "vie"],
[32953, "Any", "-a-"],
[32954, "None", "---"]]

def LanguageSelected(index):
  langcode = LANGUAGES[index][2]
  return langcode
