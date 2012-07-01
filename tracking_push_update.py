#!/usr/bin/env python
''' needs BeautifulSoup '''
import urllib2, re, datetime, ConfigParser
from xml.dom.minidom import parse, parseString
from xml.dom import Node

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
Config.read("tracking.ini")
trackMeServer = ConfigSectionMap("Settings")['trackme_server']
wave_server = ConfigSectionMap("Settings")['wave_server']
wave_server_port = ConfigSectionMap("Settings")['wave_server_port']
foodsat_prefix = ConfigSectionMap("Settings")['foodsat_prefix']


listOfServers = [
    wave_server +':'+wave_server_port
    ]
#trackMeServer = '87.201.216.107'

def update(dataTable):
    outputData = []
    p = re.compile('\d\d\d\d')
    for i in dataTable:
        
        timetable = i.getElementsByTagName('value')[0].childNodes[0].nodeValue
        devicePosition = {}
        devicePosition['Name'] = i.getElementsByTagName('name')[0].childNodes[0].nodeValue
        coord = i.getElementsByTagName('coordinates')[0].childNodes[0].nodeValue
        devicePosition['Lon'] = coord.split(',')[0]
        devicePosition['Lat'] = coord.split(',')[1]
        devicePosition['ID']=p.findall(  i.getElementsByTagName('name')[0].childNodes[0].nodeValue)[0]
        devicePosition['Timestamp']= datetime.datetime.fromtimestamp(float(timetable))
        pushUrl = "/trackme/requests.php?a=upload&id=%s%s&lat=%s&long=%s&do=%s&tn="%(foodsat_prefix,devicePosition['ID'],devicePosition['Lat'],devicePosition['Lon'],devicePosition['Timestamp'])
        #try:
        import urllib
        pushUrl = urllib.quote(pushUrl,'\&/?=')
        #print 'http://'+trackMeServer+ pushUrl
        
        urllib2.urlopen('http://'+trackMeServer+ pushUrl)
        #except:
        outputData.append(devicePosition)

for server in listOfServers:
    try:
        fh = urllib2.urlopen('http://'+ server +'/all-subscribers.kml')
        html = fh.read()
        fh.close()
        soup = parseString(html)
        devicePosition = dict();
        dataTable = soup.getElementsByTagName('Placemark')
        update(dataTable)
    except Exception as e:
        print e

urllib2.urlopen('http://'+trackMeServer+'/trackme/trackme/update/')

print 0
