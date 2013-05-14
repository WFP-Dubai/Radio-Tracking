#!/usr/bin/env python
import ConfigParser
from gps_tools import *



Config = ConfigParser.ConfigParser()
Config.read("settings.ini")
settings = config_section_map("Settings",Config)

system_type =  settings['system_type']

def main():
    status = 0
    try:
        if polling():
            if system_type == 'trbonet' or system_type == 'smartptt':
                get_kml()

            if system_type == 'wave':
                get_wave()
        
            if system_type == 'smartptt_db':
                 get_database_sptt()
    except:
        status = -1       
    print status


if __name__ == '__main__':
    main()
