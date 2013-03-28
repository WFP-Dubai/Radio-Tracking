import _mssql, decimal, uuid,pymssql

import urllib2, re, datetime, ConfigParser,time
import  gps_tools


gps_tools.settings = gps_tools.ConfigSectionMap("Settings")
# gps_tools.debug = True

trackMeServer = gps_tools.settings['trackme_server']
foodsat_prefix = gps_tools.settings['foodsat_prefix']
system_type =  gps_tools.settings['system_type']

if system_type == 'wave':
    wave_server_address = gps_tools.settings['radio_server_address']
    wave_server_port = gps_tools.settings['radio_server_port']
    server_url =  wave_server_address +':'+wave_server_port

db_name = gps_tools.settings['database_name']
server_name = gps_tools.settings['server_name']

if system_type == 'trbonet' or system_type == 'smartptt':
    kml_file =  gps_tools.settings['kml_file']



    


def polling():
    poll_url = 'http://'+trackMeServer+ '/trackme/api/update/' + settings['server_name'] +'/'
    poll_response = urllib2.urlopen(poll_url)
    poll_data = poll_response.read()
    print poll_data
    
#polling()
gps_tools.readDatabaseSPTT()