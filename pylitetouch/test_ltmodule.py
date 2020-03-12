
from pylitetouch import LiteTouch
import time

host = '192.168.1.65'
port = 10001

load = 105
lvl = 20
kp = 14
but = 9

def callback(msg, args):
    """Show the message are arguments."""
    print(msg, args)



LT = LiteTouch(host,port,callback)
LT
time.sleep(.3)
#LT.toggle_switch(kp,but)

#LT.set_loadlevel(load,lvl)

#LT.set_loadon(load)
LT.get_led_state(kp,but)
#LT.set_loadoff(load)



print('Waiting for Messages')
time.sleep(315)

print('Close Connection')
LT.close()

