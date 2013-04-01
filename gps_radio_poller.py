#!/usr/bin/env python
''' needs BeautifulSoup '''
import urllib2, re, datetime, ConfigParser,time
from xml.dom.minidom import parse, parseString
from xml.dom import Node
import _mssql, decimal, uuid,pymssql


def report_issues(issue):
    # make connection to trackme server to report any issues
    poll_url = 'http://'+trackMeServer+ '/radio_error/' + settings['server_name'] +'?error_message='+issue
    poll_response = urllib2.urlopen(poll_url)
    poll_data = poll_response.read()
    print issue

def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

Config = ConfigParser.ConfigParser()
Config.read("settings.ini")
settings = ConfigSectionMap("Settings")

trackMeServer = settings['trackme_server']
foodsat_prefix = settings['foodsat_prefix']
system_type =  settings['system_type']
server_name = settings['server_name']

if system_type == 'wave':
    wave_server_address = settings['radio_server_address']
    wave_server_port = settings['radio_server_port']
    server_url =  wave_server_address +':'+wave_server_port

#if system_type == 'smartptt_db'or system_type == 'trbonet_db':
#    db_name=settings['wave_server']

if system_type == 'trbonet' or system_type == 'smartptt':
    kml_file =  settings['kml_file']


def update_trbonet(dataTable):
    outputData = []
    p = re.compile('\d+')
    ptime =re.compile('\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d')
    #print dataTable
    for i in dataTable:
        
        timetable = i.getElementsByTagName('text')[0].childNodes[0].nodeValue
        devicePosition = {}
        devicePosition['Timestamp']=  ptime.findall(timetable)[0]
        devicePosition['Name'] = i.getElementsByTagName('name')[0].childNodes[0].nodeValue
        coord = i.getElementsByTagName('coordinates')[0].childNodes[0].nodeValue
        devicePosition['Lon'] = coord.split(',')[0]
        devicePosition['Lat'] = coord.split(',')[1]
        
        send_data(devicePosition)


def update_smartptt_kml(dataTable):

    p = re.compile('\[(\d+)\]')
    r = re.compile('(\d+)')
    for i in dataTable:
        timetable = i.getElementsByTagName('description')[0].childNodes[0].nodeValue
        devicePosition = {}
        devicePosition['Timestamp']=  timetable

        try:
            devicePosition['ID']=p.findall(  i.getElementsByTagName('name')[0].childNodes[0].nodeValue)[0]
        except:
            devicePosition['ID']=r.findall(  i.getElementsByTagName('name')[0].childNodes[0].nodeValue)[0]
        coord = i.getElementsByTagName('coordinates')[0].childNodes[0].nodeValue
        devicePosition['Lon'] = coord.split(',')[0]
        devicePosition['Lat'] = coord.split(',')[1]
        send_data(devicePosition)   
        


def update_wave(dataTable):
    p = re.compile('\((\d+)\)')
    r = re.compile('#(\d+)')
    for i in dataTable:
        try:
            timetable = i.getElementsByTagName('value')[0].childNodes[0].nodeValue
            devicePosition = {}
            devicePosition['Name'] = i.getElementsByTagName('name')[0].childNodes[0].nodeValue
            coord = i.getElementsByTagName('coordinates')[0].childNodes[0].nodeValue
            devicePosition['Lon'] = coord.split(',')[0]
            devicePosition['Lat'] = coord.split(',')[1]
            try:
                devicePosition['ID']=p.findall(  i.getElementsByTagName('name')[0].childNodes[0].nodeValue)[0]
            except:
                devicePosition['ID']=r.findall(  i.getElementsByTagName('name')[0].childNodes[0].nodeValue)[0]
            devicePosition['Timestamp']= datetime.datetime.fromtimestamp(float(timetable))
       
            send_data(devicePosition)
        except Exception as e:
            report_issues( e )


def readDatabaseSPTT():
    conn = pymssql.connect(server=settings['database_name'], user=settings['server_user'],password=settings['server_pw'],database=settings['server_database'], as_dict=True)
    query = """
    select * from (
    SELECT radioid, dt, latitude, longitude, speed, radius, rssi, ROW_NUMBER() OVER (PARTITION BY radioid ORDER BY dt DESC) as rn
    FROM (SELECT ((id & 0xFF) * 65536 + (id / 256 & 0xFF) * 256) + (id / 65536 & 0xFF) AS radioid, dt, latitude, longitude, speed, radius, rssi
     FROM (SELECT CAST(CASE WHEN msuid < 0 THEN (4294967296 + msuid) ELSE msuid END / 256 AS int) AS id, dt, latitude, longitude, speed, radius, rssi
    FROM <DATABASE>.dbo.LocationData) AS xLocationData) AS yLocationData 
    ) a where rn = 1 order by dt"""
    
    query = query.replace("<DATABASE>",settings['server_database'])
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
        


def update_kml_file(dataTable):

    if system_type == 'trbonet':
        update_trbonet(dataTable)
    if system_type == 'smartptt':
        update_smartptt_kml(dataTable)
                

def send_data(devicePosition):
        pushUrl = "/trackme/requests.php?a=upload&id=%s%s&lat=%s&long=%s&do=%s&tn="%(foodsat_prefix,devicePosition['ID'],devicePosition['Lat'],devicePosition['Lon'],devicePosition['Timestamp'])
        pushUrl_new = "/trackme/radio_update/%s/%s%s/%s/%s/?date=%s&device_type=%s"%(settings['server_name'],foodsat_prefix,devicePosition['ID'],devicePosition['Lat'],devicePosition['Lon'],devicePosition['Timestamp'],system_type)
        import urllib
        pushUrl = urllib.quote(pushUrl,'\&/?=')
        pushUrl_new = urllib.quote(pushUrl_new,'\&/?=')
        try:
            urllib2.urlopen('http://'+trackMeServer+ pushUrl)
        except Exception as e:
            urllib2.urlopen('http://'+trackMeServer+ pushUrl_new)
            report_issues( e )

def polling():
    try:
        poll_url = 'http://'+trackMeServer+ '/trackme/radio_check/' + settings['server_name'] 
        poll_response = urllib2.urlopen(poll_url)
        poll_data = poll_response.read()
        if poll_data == '1':
            return True
        else:
            return False
    except:
            return True

if polling():
    if system_type == 'trbonet' or system_type == 'smartptt':
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


    if system_type == 'wave':
        try:
        
            fh = urllib2.urlopen('http://'+ server_url +'/all-subscribers.kml')
            html = fh.read()
            #print html
            fh.close()
            soup = parseString(html)
            devicePosition = dict();
            dataTable = soup.getElementsByTagName('Placemark')
            update_wave(dataTable)
        except Exception as e:
            report_issues( e )
        
    if system_type == 'smartptt_db':
        readDatabaseSPTT()
        #connect to db using python

print 0
