import socket
from threading import Thread
import select
import logging
import time


_LOGGER = logging.getLogger(__name__)

POLLING_FREQ = 1.


class LiteTouch(Thread):

    """Interface with a LiteTouch 5000LC, Savant SSL P-018 system."""

    def __init__(self, host, port, callback):
        """Connect to controller using host, port."""
        Thread.__init__(self)
        self._host = host
        self._port = port
        self._callback = callback
        self._socket = None

        self._running = False
        self._connect()
        if self._socket == None:
            raise ConnectionError("Couldn't connect to '%s:%d'" % (host, port))
        self.start()
    
    def _connect(self):
        try:
            self._socket = socket.create_connection((self._host, self._port))
            print('Connection Successful')
            # Setup interface and subscribe to events
            self._send('R,SIEVN,7')     # subscribe to all events
            
            _LOGGER.info("Connected to %s:%d", self._host, self._port)
        except (BlockingIOError, ConnectionError, TimeoutError) as error:
            pass
    
    def _send(self, command, ltcmd=None, keypad=None, button=None):
        """Send and Encode Message to LiteTouch Controller"""
        _LOGGER.debug("send: %s", command)
        try:
            print(command)
            self._socket.sendall((command + '\r').encode("utf-8"))
            
            if ltcmd == ('CGLES'):
                """
                Handle LED requests.  Needed for LED state for specific 
                keypad as keypad # isn't returned in response.
                """
                data = self._socket.recv(1024)
                print(data)
                resp = data.decode().strip('\r')
                self._handle_request(resp, keypad, button)
            else:
                data = ''
            return True
        except (ConnectionError, AttributeError):
            self._socket = None
            return False
    
    def set_loadlevel(self, loadid, level):
        """Send Brightness level to Controller for specific load id"""
        loadid = str(loadid-1)
        level = str(level)
        self._send(f'R,CINLL, {loadid}, {level}')
    
    def set_loadon(self, loadid: str):
        """Turn Load on."""
        loadid = str(loadid-1)
        self._send(f'R,CSLON,{loadid}')

    def set_loadoff(self, loadid):
        """Turn load off."""
        # Loads are 0 based, reduce load by 1.
        loadid = str(loadid-1)
        self._send(f'R,CSLOF, {loadid}')
    
    def toggle_switch(self, keypad, button):
        """Toggle button on Keypad"""
        keypad = str(keypad).zfill(3)
        #button's are zero based, reduce input by 1.
        button = str(button-1)
        kb = keypad+button
        msg = 'R,CTGSW,' + kb
        self._send(msg, keypad=keypad, button=button)
    
    def get_led_states(self, keypad, button):
        """Get Keypad LED States"""
        keypad = str(keypad).zfill(3)
        msg = f"R,CGLES,{keypad}"
        time.sleep(.6)
        self._send(msg, ltcmd='CGLES', keypad=keypad, button=button)

    def run(self):
        """Read and dispatch messages from the controller."""
        self._running = True
        data = ''
        while self._running:
            if self._socket == None:
                time.sleep(POLLING_FREQ)
                self._connect()
            else:
                try:
                    readable, _, _ = select.select([self._socket], [], [], POLLING_FREQ)
                    if len(readable) != 0:
                        byte = self._socket.recv(1)
                        if byte == b'\r':
                            if len(data) > 0:
                                self._processReceivedData(data)
                                data = ''
                        elif byte != b'\n':
                            data += byte.decode('utf-8')
                except (ConnectionError, AttributeError):
                    _LOGGER.warning("Lost connection.")
                    self._socket = None
                except UnicodeDecodeError:
                    data = ''

    def _processReceivedData(self, data):
        _LOGGER.debug(f"Raw: {data}")
        try:
            raw_args = data.split(',')
            cmd = raw_args[1]
            
            if cmd == ('RLEDU' or 'RMODU' or 'REVNT'):
                
                if cmd == 'RLEDU':
                    keypad = raw_args[2]
                    blist = list(str(raw_args[3][0:9]))
                    bnum = 0
                    for b in blist:
                        bnum = bnum + 1
                        kb = keypad + '_' + str(bnum) # Build keypad address:
                        
                        # Return LED Event and keypad/button status (binary):
                        self._callback('RLEDU', kb, b)
                elif cmd == 'RMODU':
                    _LOGGER.warning(f'Event: {cmd}, not handled')
                else:
                    _LOGGER.warning(f'Event: {cmd}, not handled')
                #self._eventHandler(raw_args)
                
            elif cmd == 'RCACK':
                data = ''
                #_LOGGER.warning(f"Not handling: {cmd}")
            else:
                data = ''
                #_LOGGER.warning(f'Not handling:  {cmd}')
            

        except ValueError:
            _LOGGER.warning("Weird data: %s", data)
    
    def _handle_request(self, resp, keypad, button):
        #resplist = resp.split(',')
        print(resp, keypad, button)


    def close(self):
        """Close the connection to the controller."""
        self._running = False
        if self._socket:
            time.sleep(POLLING_FREQ)
            self._socket.close()
            self._socket = None






