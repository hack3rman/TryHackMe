#/usr/bin/python
import ast 
import socket
import time

HOST = '10.10.131.53'  
PORT = 1337             
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST,PORT))
s.recv(10000)  #Initial banner 

for i in range(1001):
    data=""
    bt=s.recv(1)
    while True:
        data = data + bt
        if bt == ">":
            s.recv(10)
            break
        bt = s.recv(1)
    print ("Operation number {}".format(i))
    data = data.decode('utf8').splitlines()          #Interpret data as string and split it by lines
    op = data[len(data) - 2]                         #Take the second to last line which is our operation
    op = ast.literal_eval(op)                        #Turn the operation string into a tuple
    res = eval("{}{}{}".format(op[0],op[1],op[2]))   #Evaluate the operation
    s.send("{}\n".format(res))                       #Send the response 

#After we ar done with the 1000 responses get whatever the server is sending. 

time.sleep(5)
x = s.recv(1024)
while x:
    print x
    x= s.recv(1024)
