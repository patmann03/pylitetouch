# pylitetouch
Litetouch Integration library for interfacing with Savant SSL-P018 / 5000LC Controllers

Implemented Features:
  - Turn Load on by Load ID
  - Turn Load off by Load ID
  - Set Brightness Level by Load ID
  - Receive LED updates by keypad and button (events to determine if a load associated to the button is turned on or off)


In Development:
  - Request LED States by Keypad


SAMPLE:
-----------------------------------------
    import pylitetouch 
    import time

    host = '192.168.1.65'
    port = 10001
    load = 105

    lvl = 90

    def callback(msg, args):

        """Show the message are arguments."""
    
        print(msg, args)



    LT = pylitetouch.LiteTouch(host,port,callback)



    LT.set_loadlevel(load,lvl)

    LT.set_loadon(load)
    LT.get_LEDStates(22,1)
    LT.set_loadoff(load)

    LT.toggleSwitch(16,2)

    print('Waiting for Messages')
    time.sleep(10.)

    print('Close Connection')
    LT.close()
