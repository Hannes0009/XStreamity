#!/usr/bin/python
# -*- coding: utf-8 -*-

from . import _

from Plugins.Plugin import PluginDescriptor
from enigma import eTimer, getDesktop, addFont
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigDirectory, ConfigYesNo, ConfigSelectionNumber, ConfigClock, configfile

import twisted.python.runtime

try:
    from multiprocessing.pool import ThreadPool
    hasMultiprocessing = True
except:
    hasMultiprocessing = False

try:
    from concurrent.futures import ThreadPoolExecutor
    if twisted.python.runtime.platform.supportsThreads():
        hasConcurrent = True
    else:
        hasConcurrent = False
except:
    hasConcurrent = False

import os
import shutil
import sys

pythonFull = float(str(sys.version_info.major) + "." + str(sys.version_info.minor))
pythonVer = sys.version_info.major

isDreambox = False
if os.path.exists("/usr/bin/apt-get"):
    isDreambox = True

autoStartTimer = None


with open("/usr/lib/enigma2/python/Plugins/Extensions/XStreamity/version.txt", 'r') as f:
    version = f.readline()

screenwidth = getDesktop(0).size()

dir_etc = "/etc/enigma2/xstreamity/"
dir_tmp = "/tmp/xstreamity/"
dir_plugins = "/usr/lib/enigma2/python/Plugins/Extensions/XStreamity/"

if screenwidth.width() > 1280:
    skin_directory = "%sskin/fhd/" % (dir_plugins)
else:
    skin_directory = "%sskin/hd/" % (dir_plugins)


folders = os.listdir(skin_directory)
if "common" in folders:
    folders.remove("common")

languages = [
    ('en', 'English'),
    ('de', 'Deutsch'),
    ('es', 'Español'),
    ('fr', 'Français'),
    ('it', 'Italiano'),
    ('nl', 'Nederlands'),
    ('tr', 'Türkçe'),
    ('cs', 'Český'),
    ('da', 'Dansk'),
    ('hr', 'Hrvatski'),
    ('hu', 'Magyar'),
    ('no', 'Norsk'),
    ('pl', 'Polski'),
    ('pt', 'Português'),
    ('ro', 'Română'),
    ('ru', 'Pусский'),
    ('sh', 'Srpski'),
    ('sk', 'Slovenčina'),
    ('fi', 'suomi'),
    ('sv', 'svenska'),
    ('uk', 'Український'),
    ('ar', 'العربية'),
    ('bg', 'български език'),
    ('el', 'ελληνικά'),
    ('sq', 'shqip')
]
config.plugins.XStreamity = ConfigSubsection()

cfg = config.plugins.XStreamity

streamtype_choices = [('1', 'DVB(1)'), ('4097', 'IPTV(4097)')]

if os.path.exists("/usr/bin/gstplayer"):
    streamtype_choices.append(('5001', 'GStreamer(5001)'))

if os.path.exists("/usr/bin/exteplayer3"):
    streamtype_choices.append(('5002', 'ExtePlayer(5002)'))

if os.path.exists("/usr/bin/apt-get"):
    streamtype_choices.append(('8193', 'GStreamer(8193)'))


cfg.livetype = ConfigSelection(default='1', choices=streamtype_choices)
cfg.vodtype = ConfigSelection(default='4097', choices=streamtype_choices)
cfg.downloadlocation = ConfigDirectory(default='/media/hdd/movie/')
cfg.location = ConfigDirectory(default=dir_etc)
cfg.main = ConfigYesNo(default=True)
cfg.livepreview = ConfigYesNo(default=False)
cfg.stopstream = ConfigYesNo(default=False)
cfg.skin = ConfigSelection(default='default', choices=folders)
cfg.parental = ConfigYesNo(default=False)
cfg.timeout = ConfigSelectionNumber(1, 20, 1, default=10)
cfg.TMDB = ConfigYesNo(default=True)
cfg.TMDBLanguage = ConfigSelection(default='en', choices=languages)
cfg.catchupstart = ConfigSelectionNumber(0, 30, 1, default=0)
cfg.catchupend = ConfigSelectionNumber(0, 30, 1, default=0)
cfg.subs = ConfigYesNo(default=False)
cfg.skipplaylistsscreen = ConfigYesNo(default=False)
cfg.wakeup = ConfigClock(default=((9 * 60) + 9) * 60)  # 7:00

skin_path = '%s%s/' % (skin_directory, cfg.skin.value)
common_path = '%scommon/' % (skin_directory)
playlists_json = "%sx-playlists.json" % (dir_etc)
downloads_json = "%sdownloads.json" % (dir_etc)
playlist_file = "%splaylists.txt" % (dir_etc)

if cfg.location.value:
    playlist_file = "%s/playlists.txt" % (cfg.location.value)

font_folder = "%sfonts/" % (dir_plugins)
icon_folder = "%sicons/" % (dir_plugins)
image_folder = "%s/images/" % (skin_path)


"""
hdr = {
'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0',
'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
'Accept-Language': 'en-GB,en;q=0.5',
'Accept-Encoding': 'gzip, deflate',
}
"""


hdr = {'User-Agent': 'Enigma2 - XStreamity Plugin'}


# create folder for working files
if not os.path.exists(dir_etc):
    os.makedirs(dir_etc)

# delete temporary folder and contents
if os.path.exists(dir_tmp):
    shutil.rmtree('/tmp/xstreamity')

# create temporary folder for downloaded files
if not os.path.exists(dir_tmp):
    os.makedirs(dir_tmp)

# check if playlists.txt file exists in specified location
if not os.path.isfile(playlist_file):
    open(playlist_file, 'a').close()

# check if x-playlists.json file exists in specified location
if not os.path.isfile(playlists_json):
    open(playlists_json, 'a').close()

# check if x-downloads.json file exists in specified location
if not os.path.isfile(downloads_json):
    open(downloads_json, 'a').close()


def main(session, **kwargs):
    from . import mainmenu
    session.open(mainmenu.XStreamity_MainMenu)
    return


def mainmenu(menu_id, **kwargs):
    if menu_id == 'mainmenu':
        return [(_('XStreamity'), main, 'XStreamity', 50)]
    else:
        return []


def extensionsmenu(session, **kwargs):
    from . import mainmenu
    session.open(mainmenu.XStreamity_MainMenu)
    return


class AutoStartTimer:
    def __init__(self, session):
        self.session = session
        self.timer = eTimer()
        try:  # DreamOS fix
            self.timer_conn = self.timer.timeout.connect(self.onTimer)
        except:
            self.timer.callback.append(self.onTimer)
        self.update()

    def getWakeTime(self):
        import time
        clock = cfg.wakeup.value
        nowt = time.time()
        now = time.localtime(nowt)
        return int(time.mktime((now.tm_year, now.tm_mon, now.tm_mday, clock[0], clock[1], 0, now.tm_wday, now.tm_yday, now.tm_isdst)))

    def update(self, atLeast=0):
        import time
        self.timer.stop()
        wake = self.getWakeTime()
        nowtime = time.time()
        if wake > 0:
            if wake < nowtime + atLeast:
                # Tomorrow.
                wake += 24 * 3600
            next = wake - int(nowtime)
            if next > 3600:
                next = 3600
            if next <= 0:
                next = 60
            self.timer.startLongTimer(next)
        else:
            wake = -1
        return wake

    def onTimer(self):
        import time
        self.timer.stop()
        now = int(time.time())
        wake = self.getWakeTime()
        atLeast = 0
        if abs(wake - now) < 60:
            self.runUpdate()
            atLeast = 60
        self.update(atLeast)

    def runUpdate(self):
        print('\n *********** Updating XStreamity EPG ************ \n')
        from . import update
        epg = update.XStreamity_Update()


def autostart(reason, session=None, **kwargs):
    global autoStartTimer
    if reason == 0:
        if session is not None:
            if autoStartTimer is None:
                autoStartTimer = AutoStartTimer(session)
    return


def Plugins(**kwargs):
    addFont(font_folder + 'm-plus-rounded-1c-regular.ttf', 'xstreamityregular', 100, 0)
    addFont(font_folder + 'm-plus-rounded-1c-medium.ttf', 'xstreamitybold', 100, 0)

    iconFile = 'icons/plugin-icon_sd.png'
    if screenwidth.width() > 1280:
        iconFile = 'icons/plugin-icon.png'
    description = (_('IPTV Xtream Codes playlists player by KiddaC'))
    pluginname = (_('XStreamity'))

    main_menu = PluginDescriptor(name=pluginname, description=description, where=PluginDescriptor.WHERE_MENU, fnc=mainmenu, needsRestart=True)

    extensions_menu = PluginDescriptor(name=pluginname, description=description, where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=extensionsmenu, needsRestart=True)

    result = [PluginDescriptor(name=pluginname, description=description, where=[PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART], fnc=autostart),
              PluginDescriptor(name=pluginname, description=description, where=PluginDescriptor.WHERE_PLUGINMENU, icon=iconFile, fnc=main)]

    result.append(extensions_menu)

    if cfg.main.getValue():
        result.append(main_menu)

    return result
