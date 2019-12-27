# python3.6+

"""
NORDVPN SERVER SWITCHER

reconnects to new server when www cannot be quickly reached
trends toward connection to low latency servers

litepresence 2019
"""

from subprocess import call
from random import random, randint, shuffle
import requests
import time
import json
from subprocess import PIPE, run

COUNTRY = "US" # list of server country codes
MIN_ID = 1 # min server id number
MAX_ID = 4500 # max server id number

# response time fine tuning
DEPTH = 50 # moving average of response time
DEVIATION = 7 # max coeff of deviation from mean

VERSION = 0.00000001

SITES = [
    "pastebin.com",
    "hastebin.com",
    "codebeautify.org",
    "jsonformatter.org",
    "unitconverters.net",
    "textmechanic.com",
    "paste.ee",
]

BLACKLIST = [0,
]

def connected():
    """
    Keyword check for 'disconnected' in status call via subprocess pipe
    """
    status = run(["nordvpn", "status"], stdout=PIPE, universal_newlines=True)
    print (status.stdout)
    connection = False
    if "disconnected" not in str(status.stdout).lower():
        connection = True

    return connection

def reconnect():
    """
    Repeatedly reconnect until connection is confirmed
    """
    while 1:
        location_id = 0
        while location_id in BLACKLIST:
            location_id = randint(MIN_ID, MAX_ID)
        site = COUNTRY.lower() + str(location_id)
        command = ["nordvpn", "connect", site]
        print(time.ctime())
        print(" ".join(command))
        call(command)
        if connected():
            city = ipapi()
            break

    return city

def ipapi():
    """
    Fetch city name from independent source
    """
    try:
        url = "http://ip-api.com/json/"
        ret = requests.get(url).json()
        ret = str(ret["city"]) + ", " + str(ret['country'])
    except:
        # allow null response as to not get hung by service failure
        ret = ""
    return ret


def main():
    """
    Maintain a VPN connection through adversity
    """
    # initialize variables
    begin = time.time()
    deviation = 7.00
    max_mean = 0.50
    max_time = 1.75
    ret = ""
    times = []
    blacklist = []
    sites = SITES[:]
    shuffle(sites)
    bad_response = 0
    exceptions = 0
    bad_status = 0
    mean_slow = 0
    spec_slow = 0
    too_slow = 0
    i = 0
    for _ in range(DEPTH):
        times.append(max_mean/2)
    # if the second while loop breaks then reconnect.
    while 1:
        # create a new nord connection
        city = reconnect()
        reconnected = time.time()
        # rotate list of websites to test
        sites.append(sites.pop(0))
        # test the quality of the connection
        while 1:
            # every second check if "connected" via nord status call
            if not connected():
                city = reconnect()
                reconnected = time.time()
                bad_status += 1
            # every 10 seconds test connection to an actual website
            if i % 3 == 0:
                try:
                    print("testing connection to %s..." % sites[0])
                    start = time.time()
                    ret = str(requests.get("https://" + sites[0]))
                    elapsed = time.time() - start
                    # calculate a moving average of elapsed time
                    times.append(elapsed)
                    times = times[-DEPTH:]
                    mean_ret = sum(times) / len(times)
                    
                    # check connection slow relative to running average
                    if (elapsed > deviation * mean_ret):
                        too_slow += 1
                        deviation *= 1.1
                        break
                    # check connection slow relative to max specification
                    if (elapsed > max_time):
                        spec_slow += 1
                        max_time *= 1.1
                        break
                    # check connection response code
                    if ret != "<Response [200]>":
                        bad_response += 1
                        break
                    # ensure running mean is not too slow
                    if (mean_ret > max_mean):
                        times = []
                        for _ in range(DEPTH):
                            times.append(max_mean/2)
                        mean_slow += 1
                        max_mean *= 1.1
                        break

                except Exception as e:
                    exceptions += 1
                    break
                deviation *= 0.9999
                max_time *= 0.9999
                max_mean *= 0.9999
            else:
                print("")
                
            print("elapsed: %.3f mean: %.3f" % (elapsed, mean_ret))
            i+=1
            print(
                "slow:", too_slow, 
                "spec:", spec_slow, 
                "mean:", mean_slow,
                "resp:", bad_response,
                "stat:", bad_status,
                "exce:", exceptions, 
                "\n",
            )
            print(
                "deviation: %.4f\n"% deviation,
                "max_mean: %.4f\n"% max_mean,
                "max_time: %.4f\n"% max_time,
            )
            time.sleep(4)
            runtime = int(time.time() - begin)
            contime = int(time.time() - reconnected)
            print("\033c")
            print(time.ctime(), "\n")
            print("NORDVPN SERVER SWITCHER %.8f\n" % VERSION)
            print("Run time: ", contime, "/", runtime, "\n")
            print("Geolocation: ", city, "\n")
            print("Response time: ", "%.3f\n" % mean_ret)
            


if __name__ == "__main__":

    main()
