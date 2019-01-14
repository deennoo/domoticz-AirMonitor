 # A Python plugin for Domoticz to access AXiaomi Air Monitor
#
# Author: kofec
#
# TODO: Update text sensors only when changed
#
#
# v0.1.0 - initial version,
# fetching data Air Monitor print(MyAir.status()) <AirPurifierStatus power=on,
# aqi=10 temperature=22.9, humidity=35%, mode=OperationMode.Silent, led=True, led_brightness=LedBrightness.Bright,
# buzzer=False, child_lock=False, brightness=None, favorite_level=10, filter_life_remaining=79,
# filter_hours_used=717, use_time=2581642, motor_speed=352>

# v0.1.1 - Add initial version of switches, update to nie version of python-miio
#
"""
<plugin key="AirMonitor" name="AirMonitor" author="Deennoo" version="0.1.1" wikilink="https://github.com/rytilahti/python-miio" externallink="https://github.com/kofec/domoticz-AirPurifier">
    <params>
		<param field="Address" label="IP Address" width="200px" required="true" default="127.0.0.1"/>
		<param field="Mode1" label="AirMonitor Token" default="" width="400px" required="true"  />
        <param field="Mode3" label="Check every x minutes" width="40px" default="5" required="true" />
		<param field="Mode6" label="Debug" width="75px">
			<options>
				<option label="True" value="Debug"/>
				<option label="False" value="Normal" default="true" />
			</options>
		</param>
    </params>
</plugin>
"""
import Domoticz
import sys
import datetime
import socket
import subprocess
import site
path=''
path=site.getsitepackages()
for i in path:
    sys.path.append(i)

import miio.airqualitymonitor

L10N = {
    'pl': {
        "Air Quality Index":
            "Jakość powietrza",
        "Avarage Air Quality Index":
            "Średnia wartość AQI",
        "Air pollution Level":
            "Zanieczyszczenie powietrza",
        "Temperature":
            "Temperatura",
        "Humidity":
            "Wilgotność",
        "Fan Speed":
            "Prędkość wiatraka",
        "Favorite Fan Level":
            "Ulubiona prędkość wiatraka",
        "Sensor information":
            "Informacje o stacji",
        "Device Unit=%(Unit)d; Name='%(Name)s' already exists":
            "Urządzenie Unit=%(Unit)d; Name='%(Name)s' już istnieje",
        "Creating device Name=%(Name)s; Unit=%(Unit)d; ; TypeName=%(TypeName)s; Used=%(Used)d":
            "Tworzę urządzenie Name=%(Name)s; Unit=%(Unit)d; ; TypeName=%(TypeName)s; Used=%(Used)d",
        "%(Vendor)s - %(Address)s, %(Locality)s<br/>Station founder: %(sensorFounder)s":
            "%(Vendor)s - %(Address)s, %(Locality)s<br/>Sponsor stacji: %(sensorFounder)s",
        "%(Vendor)s - %(Locality)s %(StreetNumber)s<br/>Station founder: %(sensorFounder)s":
            "%(Vendor)s - %(Locality)s %(StreetNumber)s<br/>Sponsor stacji: %(sensorFounder)s",
        "Great air quality":
            "Bardzo dobra jakość powietrza",
        "Good air quality":
            "Dobra jakość powietrza",
        "Average air quality":
            "Przeciętna jakość powietrza",
        "Poor air quality":
            "Słaba jakość powietrza",
        "Bad air quality":
            "Zła jakość powietrza",
        "Really bad air quality":
            "Bardzo zła jakość powietrza",
        "Sensor id (%(sensor_id)d) not exists":
            "Sensor (%(sensor_id)d) nie istnieje",
        "Not authorized":
            "Brak autoryzacji",
        "Starting device update":
            "Rozpoczynanie aktualizacji urządzeń",
        "Update unit=%d; nValue=%d; sValue=%s":
            "Aktualizacja unit=%d; nValue=%d; sValue=%s",
        "Bad air today!":
            "Zła jakość powietrza",
        "Enter correct airly API key - get one on https://developer.airly.eu":
            "Wprowadź poprawny klucz api -  pobierz klucz na stronie https://developer.airly.eu",
        "Awaiting next pool: %s":
            "Oczekiwanie na następne pobranie: %s",
        "Next pool attempt at: %s":
            "Następna próba pobrania: %s",
        "Connection to airly api failed: %s":
            "Połączenie z airly api nie powiodło się: %s",
        "Unrecognized error: %s":
            "Nierozpoznany błąd: %s"
    },
    'en': { }
}

def _(key):
    try:
        return L10N[Settings["Language"]][key]
    except KeyError:
        return key

class UnauthorizedException(Exception):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message

class SensorNotFoundException(Exception):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message

class ConnectionErrorException(Exception):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message

# temporery class

class AirStatus:
    """Container for status reports from the air purifier."""

    def __init__(self, AddressIP, token):
        """
        Response of script:

               "<AirPurifierStatus power=on, aqi=10,average_aqi=8,temperature=21.9, humidity=36%," \
               "mode=OperationMode.Silent,led=True,led_brightness=LedBrightness.Bright,buzzer=False, " \
               "child_lock=False,favorite_level=10,filter_life_remaining=70, filter_hours_used=1044, " \
               "use_time=3748042, purify_volume=38007, motor_speed=354> "
        """

        addressIP = str(AddressIP)
        token = str(token)
        data = subprocess.check_output(['bash', '-c', './MyAir.py ' + addressIP + ' ' + token], cwd=Parameters["HomeFolder"])
        data = str(data.decode('utf-8'))
        if Parameters["Mode6"] == 'Debug':
            Domoticz.Debug(data[:30] + " .... " + data[-30:])
        data = data[19:-2]
        data = data.replace(' ', '')
        data = dict(item.split("=") for item in data.split(","))
        self.aqi = data["aqi"]
        for item in data.keys():
            Domoticz.Debug(str(item) + " => " + str(data[item]))

class BasePlugin:
    enabled = False

    def __init__(self):
        # Consts
        self.version = "0.1.1"

        self.EXCEPTIONS = {
            "SENSOR_NOT_FOUND":     1,
            "UNAUTHORIZED":         2,
        }

        self.debug = False
        self.inProgress = False

        # Do not change below UNIT constants!
        self.UNIT_AIR_QUALITY_INDEX     = 1
        self.UNIT_AIR_POLLUTION_LEVEL   = 2
        self.nextpoll = datetime.datetime.now()
        return


    def onStart(self):
        Domoticz.Debug("onStart called")
        if Parameters["Mode6"] == 'Debug':
            self.debug = True
            Domoticz.Debugging(1)
            DumpConfigToLog()
        else:
            Domoticz.Debugging(0)

        Domoticz.Heartbeat(20)
        self.pollinterval = int(Parameters["Mode3"]) * 60


        self.variables = {
            self.UNIT_AIR_QUALITY_INDEX: {
                "Name":     _("Air Quality Index"),
                "TypeName": "Custom",
                "Options":  {"Custom": "1;%s" % "AQI"},
                "Image":    7,
                "Used":     1,
                "nValue":   0,
                "sValue":   None,
            },

            self.UNIT_AIR_POLLUTION_LEVEL: {
                "Name":     _("Air pollution Level"),
                "TypeName": "Alert",
                "Image":    7,
                "Used":     0,
                "nValue":   0,
                "sValue":   None,
            },

        }



    def onStop(self):
        Domoticz.Log("onStop called")
        Domoticz.Debugging(0)

    def onConnect(self, Status, Description):
        Domoticz.Log("onConnect called")

    def onMessage(self, Data, Status, Extra):
        Domoticz.Log("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log(
            "onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

        # Parameters["Address"] - IP address, Parameters["Mode1"] - token
        commandToCall = './MyAir.py ' + Parameters["Address"] + ' ' + Parameters["Mode1"] + ' '
        

        if Parameters["Mode6"] == 'Debug':
            Domoticz.Debug("Call command: " + commandToCall)
        data = subprocess.check_output(['bash', '-c', commandToCall], cwd=Parameters["HomeFolder"])
        data = str(data.decode('utf-8'))
        if Parameters["Mode6"] == 'Debug':
            Domoticz.Debug(data)
        self.onHeartbeat(fetch=True)

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(
            Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self):
        Domoticz.Log("onDisconnect called")

    def postponeNextPool(self, seconds=3600):
        self.nextpoll = (datetime.datetime.now() + datetime.timedelta(seconds=seconds))
        return self.nextpoll

    def createDevice(self, key=None):
        """create Domoticz virtual device"""

        def createSingleDevice(key):
            """inner helper function to handle device creation"""

            item = self.variables[key]
            _unit = key
            _name = item['Name']

            # skip if already exists
            if key in Devices:
                Domoticz.Debug(_("Device Unit=%(Unit)d; Name='%(Name)s' already exists") % {'Unit': key, 'Name': _name})
                return

            try:
                _options = item['Options']
            except KeyError:
                _options = {}

            _typename = item['TypeName']

            try:
                _used = item['Used']
            except KeyError:
                _used = 0

            try:
                _image = item['Image']
            except KeyError:
                _image = 0

            Domoticz.Debug(_("Creating device Name=%(Name)s; Unit=%(Unit)d; ; TypeName=%(TypeName)s; Used=%(Used)d") % {
                               'Name':     _name,
                               'Unit':     _unit,
                               'TypeName': _typename,
                               'Used':     _used,
                           })

            Domoticz.Device(
                Name=_name,
                Unit=_unit,
                TypeName=_typename,
                Image=_image,
                Options=_options,
                Used=_used
            ).Create()

        if key:
            createSingleDevice(key)
        else:
            for k in self.variables.keys():
                createSingleDevice(k)


    def onHeartbeat(self, fetch=False):
        Domoticz.Debug("onHeartbeat called")
        now = datetime.datetime.now()

        if fetch == False:
            if self.inProgress or (now < self.nextpoll):
                Domoticz.Debug(_("Awaiting next pool: %s") % str(self.nextpoll))
                return

        # Set next pool time
        self.postponeNextPool(seconds=self.pollinterval)

        try:
            # check if another thread is not running
            # and time between last fetch has elapsed
            self.inProgress = True

            res = self.sensor_measurement(Parameters["Address"], Parameters["Mode1"])



            try:
                self.variables[self.UNIT_AIR_QUALITY_INDEX]['sValue'] = str(res.aqi)
            except KeyError:
                pass  # No airQualityIndex value

            #       AQI	Air Pollution - base on https://en.wikipedia.org/wiki/Air_quality_index
            #       Level	Health Implications
            #       0–50	    Excellent
            #       51–100	Good
            #       101–150	Lightly Polluted
            #       151–200	Moderately Polluted
            #       201–300	Heavily Polluted
            #       300+	Severely Polluted

            if int(res.aqi) < 50:
                pollutionLevel = 1  # green
                pollutionText = _("Great air quality")
            elif int(res.aqi) < 100:
                pollutionLevel = 1  # green
                pollutionText = _("Good air quality")
            elif int(res.aqi) < 150:
                pollutionLevel = 2  # yellow
                pollutionText = _("Average air quality")
            elif int(res.aqi) < 200:
                pollutionLevel = 3  # orange
                pollutionText = _("Poor air quality")
            elif int(res.aqi) < 300:
                pollutionLevel = 4  # red
                pollutionText = _("Bad air quality")
            elif int(res.aqi) >= 300:
                pollutionLevel = 4  # red
                pollutionText = _("Really bad air quality")
            else:
                pollutionLevel = 0

            self.variables[self.UNIT_AIR_POLLUTION_LEVEL]['nValue'] = pollutionLevel
            self.variables[self.UNIT_AIR_POLLUTION_LEVEL]['sValue'] = pollutionText
            self.doUpdate()
        except Exception as e:
            Domoticz.Error(_("Unrecognized error: %s") % str(e))
        finally:
            self.inProgress = False
        if Parameters["Mode6"] == 'Debug':
            Domoticz.Debug("onHeartbeat finished")
        return True


    def doUpdate(self):
        Domoticz.Log(_("Starting device update"))
        for unit in self.variables:
            nV = self.variables[unit]['nValue']
            sV = self.variables[unit]['sValue']

            # cast float to str
            if isinstance(sV, float):
                sV = str(float("{0:.0f}".format(sV))).replace('.', ',')

            # Create device if required
            if sV:
                self.createDevice(key=unit)
                if unit in Devices:
                    Domoticz.Log(_("Update unit=%d; nValue=%d; sValue=%s") % (unit, nV, sV))
                    Devices[unit].Update(nValue=nV, sValue=sV)

    def sensor_measurement(self, addressIP, token):
        """current sensor measurements"""
        return AirStatus(addressIP, token)
  


global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Status, Description):
    global _plugin
    _plugin.onConnect(Status, Description)

def onMessage(Data, Status, Extra):
    global _plugin
    _plugin.onMessage(Data, Status, Extra)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect():
    global _plugin
    _plugin.onDisconnect()

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return

def UpdateDevice(Unit, nValue, sValue):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    if (Unit in Devices):
        if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue):
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue))
            Domoticz.Log("Update " + str(nValue) + ":'" + str(sValue) + "' (" + Devices[Unit].Name + ")")
    return
 
