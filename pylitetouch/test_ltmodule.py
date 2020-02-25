
import LiteTouch 
import time

host = '192.168.1.65'
port = 10001

def callback(msg, args):
    """Show the message are arguments."""
    print(msg, args)



LT = LiteTouch.LiteTouch(host,port,callback)

load = 81

lvl = 90

#LT.set_loadlevel(load,lvl)

LT.set_loadon(load)
#LT.set_loadoff(load)

#LT.toggleSwitch(16,2)

print('Waiting for Messages')
time.sleep(10.)

print('Close Connection')
LT.close()

