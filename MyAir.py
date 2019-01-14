#!/usr/bin/python3

import sys
import argparse
import site
path=''
path=site.getsitepackages()
for i in path:
    sys.path.append(i)

import miio.airqualitymonitor

parser = argparse.ArgumentParser(description='Script which comunicate with AirPurfier.')
parser.add_argument('IPaddress', help='IP address of AirPurfier' )
parser.add_argument('token', help='token to login to device')
parser.add_argument('--debug', action='store_true', help='if define more output is printed')

# MyAir.set_mode(miio.airpurifier.OperationMode.Silent)

args = parser.parse_args()
if args.debug:
    print(args)
MyAir = miio.airqualitymonitor.AirQualityMonitor(args.IPaddress, args.token)

print(MyAir.status())
