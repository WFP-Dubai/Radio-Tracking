from xml.dom.minidom import parse, parseString
from xml.dom import Node
import _mssql
import decimal
import uuid
import pymssql
import urllib2
import re
import datetime
import ConfigParser
import time


def config_section_map(section,config):
    dict1 = {}
    options = config.options(section)
    for option in options:
        try:
            dict1[option] = config.get(section, option)

        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1


config = ConfigParser.ConfigParser()
config.read("settings.ini")
settings = config_section_map("Settings",config)

trackMeServer = settings['trackme_server']
foodsat_prefix = settings['foodsat_prefix']
system_type =  settings['system_type']
server_name = settings['server_name']
if system_type == 'wave':
    wave_server_address = settings['radio_server_address']
    wave_server_port = settings['radio_server_port']
    server_url =  wave_server_address +':'+wave_server_port

if system_type == 'trbonet' or system_type == 'smartptt':
    kml_file =  settings['kml_file']


def report_issues(issue):
    # make connection to trackme server to report any issues
    try:
        try:
            issueString = issue.reason
        except:
            issueString = str(issue)
        poll_url = 'http://'+trackMeServer+ '/trackme/radio_error/' +           settings['server_name'] +'?error_message='+            issueString
        poll_response = urllib2.urlopen(poll_url)
        poll_data = poll_response.read()
    except Exception as e:
        print "Unknown Error: %s"%str(e)

    raise Exception('System Error')
        


def polling():
    try:
        poll_url = 'http://' +            trackMeServer +           '/trackme/radio_check/' +            settings['server_name'] 
        poll_response = urllib2.urlopen(poll_url)
        poll_data = poll_response.read()
        if poll_data == '1':
            return True
        else:
            return False
    except:
        return True


def update_trbonet(dataTable):
    outputData = []
    p = re.compile(r'\d+')
    ptime =re.compile(r'\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d')
    for i in dataTable:
        timetable = i.getElementsByTagName('text')[0].childNodes[0].nodeValue
        devicePosition = {}
        devicePosition['Timestamp']=  ptime.findall(timetable)[0]
        devicePosition['Name'] =             i.getElementsByTagName('name')[0].childNodes[0].nodeValue
        coord = i.getElementsByTagName('coordinates')[0].childNodes[0].nodeValue
        devicePosition['Lon'] = coord.split(',')[0]
        devicePosition['Lat'] = coord.split(',')[1]
        
        send_data(devicePosition)


def update_smartptt_kml(dataTable):

    p = re.compile(r'\[(\d+)\]')
    r = re.compile(r'(\d+)')
    for i in dataTable:
        timetable =             i.getElementsByTagName('description')[0].childNodes[0].nodeValue
        devicePosition = {}
        devicePosition['Timestamp']=  timetable

        try:
            devicePosition['ID'] = p.findall( 
                 i.getElementsByTagName('name')[0].childNodes[0].nodeValue
                 )[0]
        except:
            devicePosition['ID']= r.findall(
                i.getElementsByTagName('name')[0].childNodes[0].nodeValue)[0]
        coord = i.getElementsByTagName('coordinates')[0].childNodes[0].nodeValue
        devicePosition['Lon'] = coord.split(',')[0]
        devicePosition['Lat'] = coord.split(',')[1]
        send_data(devicePosition)   
        


def update_wave(dataTable):
    p = re.compile(r'\((\d+)\)')
    r = re.compile(r'#(\d+)')
    for i in dataTable:
        try:
            timetable =                 i.getElementsByTagName('value')[0].childNodes[0].nodeValue
            devicePosition = {}
            devicePosition['Name'] = i.getElementsByTagName('name')[0].childNodes[0].nodeValue
            coord = i.getElementsByTagName('coordinates')[0].childNodes[0].nodeValue
            devicePosition['Lon'] = coord.split(',')[0]
            devicePosition['Lat'] = coord.split(',')[1]
            try:
                devicePosition['ID']=p.findall(
                   i.getElementsByTagName('name')[0].childNodes[0].nodeValue
                   )[0]
            except:
                devicePosition['ID']=r.findall(
                  i.getElementsByTagName('name')[0].childNodes[0].nodeValue
                  )[0]
            devicePosition['Timestamp']=                 datetime.datetime.fromtimestamp(float(timetable))
       
            send_data(devicePosition)
        except Exception as e:
            report_issues( e )
            
def get_kml():
    try:
        fh = open(kml_file,'r')
        data = fh.read()
        soup = parseString(data)
        fh.close()
        devicePosition = dict()
        dataTable = soup.getElementsByTagName('Placemark')
        update_kml_file(dataTable)
    except Exception as e:
        report_issues( e )

def get_wave():
    try:
        fh = urllib2.urlopen('http://'+ server_url +'/all-subscribers.kml')
        html = fh.read()

        fh.close()
        soup = parseString(html)
        devicePosition = dict()
        dataTable = soup.getElementsByTagName('Placemark')
        update_wave(dataTable)
    except Exception as e:
        report_issues( e )

def get_database_sptt():
    try:
        db_server =         "%s:%s"%(settings['radio_server_address'],settings['radio_server_port'])
        conn = pymssql.connect(
            server=db_server,user=settings['server_user'], 
            password=settings['server_pw'],
            database=settings['server_database'],
            as_dict=True)
        query = """
        select * from (
        SELECT radioid, dt, latitude, longitude, speed, radius, rssi, 
        ROW_NUMBER() OVER (PARTITION BY radioid ORDER BY dt DESC) as rn
        FROM (SELECT ((id & 0xFF) * 65536 + (id / 256 & 0xFF) * 256) + 
        (id / 65536 & 0xFF) AS 
        radioid, dt, latitude, longitude, speed, radius, rssi
         FROM (SELECT CAST(CASE WHEN msuid < 0 THEN (4294967296 + msuid) 
         ELSE msuid END / 256 AS int) AS
          id, dt, latitude, longitude, speed, radius, rssi
        FROM <DATABASE>.dbo.LocationData) AS xLocationData) AS yLocationData 
        ) a where rn = 1 AND (GETUTCDATE() - dt < <PERIOD>) order by dt"""
    
        query = query.replace("<DATABASE>",settings['server_database'])
        query = query.replace("<PERIOD>",settings['period'])
        cur = conn.cursor()
        cur.execute(query)
        for radio in cur:
            try:
            
                devicePosition = {}
                devicePosition['Name']  = radio['radioid']
                devicePosition['Lon']   = radio['longitude']
                devicePosition['Lat']   = radio['latitude']
                devicePosition['ID']    = radio['radioid']
                devicePosition['Timestamp'] = radio['dt']
                send_data(devicePosition)
            except Exception as e:
                report_issues( e )
    except Exception as e:
        report_issues( e )
        


def update_kml_file(dataTable):

    if system_type == 'trbonet':
        update_trbonet(dataTable)
    if system_type == 'smartptt':
        update_smartptt_kml(dataTable)
                

def send_data(devicePosition):
    pushUrl_new =         "/trackme/radio_update/%s/%s%s/%s/%s/?date=%s&device_type=%s" %         (server_name,
        foodsat_prefix,devicePosition['ID'],
        devicePosition['Lat'],
        devicePosition['Lon'],
        devicePosition['Timestamp'],
        system_type)
    #pushUrl = urllib2.quote(pushUrl,'\&/?=')
    pushUrl_new = urllib2.quote(pushUrl_new,r'\&/?=')
    try:
        urllib2.urlopen('http://'+trackMeServer+ pushUrl_new)
    except Exception as e:
        report_issues( e )



