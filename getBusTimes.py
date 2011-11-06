#!/usr/bin/env python


# Copyright (C) 2011 Colum Walsh
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


"""
Gets the  time for the next 3 buses, then sends them to a ducksboard widget
re-checks every 90 seconds
"""

from BeautifulSoup import BeautifulSoup as BS
import base64
import json
import urllib2
import sys
import sched, time
import re

#api details
link1="12378"
link2="12380"
link3="12379"
api="6xp73lqdgk30ap2c72o9c4imsvtv5a03omwi8256mch1cbq6gp"

s = sched.scheduler(time.time, time.sleep)

def get_bus_times(bus, stop):
    busStr=str(bus)+'\\\\'
    times=[]
    f = urllib2.urlopen("http://www.dublinbus.ie/en/RTPI/Sources-of-Real-Time-Information/?searchtype=view&searchquery="+str(stop))
    soup = BS(f)
    if len(soup('p', text='Sorry, Real Time Information is currently unavailable for this bus stop.')):
        print 'no buses at this stop'
        return 0, 0, 0
    else:
        trs = soup.findAll(attrs={"class" : "odd"})
        eventrs=soup.findAll(attrs={"class" : "even"})
        for tr in eventrs:
            trs.append(tr)
        buses=[]
        for tr in trs:
            td = tr.findAll('td')
            #backslashes due to 'backslash plague'
            if re.search(busStr, str(td[0].contents)):
                timey = td[2].contents[0].strip()
                if timey=='due':
                    times.append(0)
                else:
                    hour = timey[0]+timey[1]
                    minute = timey[3]+timey[4]
                    hourmin = int(hour)*60+int(minute)
                    currtime=time.gmtime()[3]*60+time.gmtime()[4]
                    times.append(hourmin-currtime)
    if len(times)==0:
        print 'bus '+bus+' not found at stop ' + stop +' at ' + str(time.gmtime()[3]) +":" + str(time.gmtime()[4]) 
    times.sort()
    #to prevent list out of bounds, add 0 to the end of times
    times.append(0)
    times.append(0)
    times.append(0)
    return times[0], times[1], times[2]
        
def send_to_ducksboard(endpoint, apikey, source):
    """
    Send image to ducksboard custom image widget.
    """
    msg = {'value': int(source)}
    request = urllib2.Request("https://push.ducksboard.com/values/"+endpoint)
    auth = base64.encodestring('%s:x' % apikey)
    auth = auth.replace('\n', '')
    request.add_header('Authorization', 'Basic %s' % auth)
    urllib2.urlopen(request, json.dumps(msg))

def timerloop(sc, bus, stop):
    times = get_bus_times(bus, stop)
    send_to_ducksboard(link1, api, times[0])
    send_to_ducksboard(link2, api, times[1])
    send_to_ducksboard(link3, api, times[2])
    #timer recursion
    sc.enter(90, 1, timerloop, (sc, bus, stop,))
    sc.run()
    
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage: %s bus stop' % sys.argv[0]
        sys.exit(0)
    bus = sys.argv[1]
    stop = sys.argv[2]
    timerloop(s, bus, stop)
