
import pylitetouch
import time

host = '192.168.1.65'
port = 10001

load = 105
lvl = 90
kp = 22
but = 1

def callback(msg, args, state=0):
    """Show the message are arguments."""
    print(msg, args, state)



LT = pylitetouch.LiteTouch(host,port,callback)



#LT.set_loadlevel(load,lvl)

#LT.set_loadon(load)
#LT.get_led_states(kp,but)
LT.set_loadoff(load)

#LT.toggle_switch(kp,but)

print('Waiting for Messages')
time.sleep(10.)

print('Close Connection')
LT.close()

