#!/usr/bin/env python
import urllib2, re, datetime, ConfigParser,time
from gps_tools import *


Config = ConfigParser.ConfigParser()
Config.read("settings.ini")
settings = ConfigSectionMap("Settings",Config)

system_type =  settings['system_type']

if polling():
    if system_type == 'trbonet' or system_type == 'smartptt':
        getKML()

    if system_type == 'wave':
        getWave()
        
    if system_type == 'smartptt_db':
        readDatabaseSPTT()
        
print 0
