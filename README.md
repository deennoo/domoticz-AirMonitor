# domoticz-AirMonitor
Domoticz Python Plugin for Xiaomi PM 2.5 Monitor


Since FW : 1.4.3_8103 this device need a token to be read, This plugin is the solution.

Fully base on kofec and his AirPurifier Plugin : https://github.com/kofec/domoticz-AirPurifier

-------------------------------------------------------------------------------------------------------------------------------------
Domoticz plugin for Xiaomi AirMonitor PM2.5

Based on repository https://github.com/lrybak/domoticz-airly/
and script for Samsung TV: https://www.domoticz.com/wiki/Plugins/SamsungTV.html
and base on repository https://github.com/rytilahti/python-miio
Installation
pip3 install -U python-miio
Make sure your Domoticz instance supports Domoticz Plugin System - see more https://www.domoticz.com/wiki/Using_Python_plugins

Get plugin data into DOMOTICZ/plugins directory

cd YOUR_DOMOTICZ_PATH/plugins
git clone https://github.com/deennoo/domoticz-AirMonitor/

First use script "MyAir.py" to verify if you have needed python modules e.g:

./MyAir.py 192.168.1.1 850000000000000000000000002 --debug
./MyAir.py -h
usage: MyAir.py [--debug]
                IPaddress token

Script which comunicate with AirMonitor.

positional arguments:
  IPaddress             IP address of AirPurfier
  token                 token to login to device

optional arguments:
  -h, --help            show this help message and exit
  --debug               if define more output is printed
  
check where modules was installed and in file plugin.py find and correct below variable (in my case 2 instances) if needed pathOfPackages = '/usr/local/lib/python3.5/dist-packages'

Restart Domoticz

Go to Setup > Hardware and create new Hardware with type: AirPurfier
Enter name (it's up to you), user name and password if define. If not leave it blank
Update
cd YOUR_DOMOTICZ_PATH/plugins/domoticz-AirMonitor
git pull
Restart Domoticz
Troubleshooting
In case of issues, mostly plugin not visible on plugin list, check logs if plugin system is working correctly. See Domoticz wiki for resolution of most typical installation issues http://www.domoticz.com/wiki/Linux#Problems_locating_Python
