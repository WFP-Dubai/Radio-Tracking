import urllib2, re, datetime, ConfigParser,time
from xml.dom.minidom import parse, parseString
from xml.dom import Node
import _mssql, decimal, uuid,pymssql

debug = False
def report_issues(issue):
    # make connection to trackme server to report any issues
    print issue

def ConfigSectionMap(section):
    Config = ConfigParser.ConfigParser()
    Config.read("settings.ini")
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


def report_issues(issue):
    # make connection to trackme server to report any issues
    print issue

def send_data(devicePosition):
        pushUrl = "/requests.php?a=upload&id=%s%s&lat=%s&long=%s&do=%s&tn="%(foodsat_prefix,devicePosition['ID'],devicePosition['Lat'],devicePosition['Lon'],devicePosition['Timestamp'])
        pushUrl_new = "/trackme/api/radio_update/%s%s/%s/%s/?date=%s&device_type=%s&server_name=%s"%(foodsat_prefix,devicePosition['ID'],devicePosition['Lat'],devicePosition['Lon'],devicePosition['Timestamp'],"smartptt",settings['server_name'])
        import urllib
        #print pushUrl
        pushUrl = urllib.quote(pushUrl,'\&/?=')
        try:
            urllib2.urlopen('http://'+trackMeServer+ pushUrl)
        except Exception as e:
            report_issues( e )
        
def readDatabaseSPTT():
    #global settings
    conn = pymssql.connect(server=settings['database_name'], user=settings['server_user'],password=settings['server_pw'],database=settings['server_database'], as_dict=True)
    query = """
    select * from (
    SELECT radioid, dt, latitude, longitude, speed, radius, rssi, ROW_NUMBER() OVER (PARTITION BY radioid ORDER BY dt DESC) as rn
    FROM (SELECT ((id & 0xFF) * 65536 + (id / 256 & 0xFF) * 256) + (id / 65536 & 0xFF) AS radioid, dt, latitude, longitude, speed, radius, rssi
     FROM (SELECT CAST(CASE WHEN msuid < 0 THEN (4294967296 + msuid) ELSE msuid END / 256 AS int) AS id, dt, latitude, longitude, speed, radius, rssi
    FROM RadioServer1.dbo.LocationData) AS xLocationData) AS yLocationData 
    ) a where rn = 1 order by dt"""
    
    cur = conn.cursor()
    cur.execute(query)
    for radio in cur:
        try:
            
            devicePosition = {}
            devicePosition['Name']  = radio['radioid']
            devicePosition['Lon']   = radio['latitude']
            devicePosition['Lat']   = radio['longitude']
            devicePosition['ID']    = radio['radioid']
            devicePosition['Timestamp'] = radio['dt']
            if debug:
                print devicePosition
            else:
                print "ND" + devicePosition
            #send_data(devicePosition)

        except Exception as e:
            report_issues( e )

def polling():
    poll_url = 'http://'+trackMeServer+ '/trackme/api/update/' + settings['server_name'] +'/'
    poll_response = urllib2.urlopen(poll_url)
    poll_data = poll_response.read()
    print poll_data