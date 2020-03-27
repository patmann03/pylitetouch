import socket
from threading import Thread
import select
import logging
import time


_LOGGER = logging.getLogger(__name__)

POLLING_FREQ = 1.0


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
            print("Connection Successful")
            # Setup interface and subscribe to events
            self._send("R,SIEVN,4")  # subscribe to led events

            _LOGGER.info("Connected to %s:%d", self._host, self._port)
        except (BlockingIOError, ConnectionError, TimeoutError) as error:
            pass

    def _send(self, command, ltcmd=None, keypad=None, button=None):
        """Send and Encode Message to LiteTouch Controller"""
        _LOGGER.debug("send: %s", command)
        try:

            self._socket.sendall((command + "\r").encode("utf-8"))

            if ltcmd in ("CGLES", "CGLED"):
                """
                Handle LED requests.  Needed for LED state for specific 
                keypad as keypad # isn't returned in response.
                """
                data = self._socket.recv(1024)
                resp = data.decode().strip("\r")
                self._handle_request(resp, keypad, button)
            else:
                data = ""
            return True

        except (ConnectionError, AttributeError):
            self._socket = None
            return False

    def set_loadlevel(self, loadid, level):
        """Send Brightness level to Controller for specific load id"""
        loadid = str(loadid - 1)
        level = str(level)
        _LOGGER.debug("pylt set brightness: %s, %s", (loadid, level))
        self._send(f"R,CINLL, {loadid}, {level}")

    def set_loadon(self, loadid: str):
        """Turn Load on."""
        loadid = str(loadid - 1)
        self._send(f"R,CSLON,{loadid}")

    def set_loadoff(self, loadid):
        """Turn load off."""
        # Loads are 0 based, reduce load by 1.
        loadid = str(loadid - 1)
        self._send(f"R,CSLOF, {loadid}")

    def toggle_switch(self, keypad, button):
        """Toggle button on Keypad"""
        keypad = str(keypad).zfill(3).upper()
        # button's are zero based, reduce input by 1.
        button = str(button - 1)
        kb = keypad + button
        msg = "R,CTGSW," + kb
        self._send(msg, keypad=keypad, button=button)

    def get_led_states(self, keypad, button=1):
        """Get Keypad LED States"""
        try:
            if "_" in keypad:
                button = keypad.split("_")[1]
                keypad = keypad.split("_")[0]
                keypad = str(keypad).zfill(3).upper()
                msg = f"R,CGLES,{keypad}"
                time.sleep(0.2)
                self._send(msg, ltcmd="CGLES", keypad=keypad, button=button)

        except:
            msg = f"R,CGLES,{keypad}"
            self._send(msg, ltcmd="CGLES", keypad=keypad, button=button)

    def get_led_state(self, keypad, button=1):
        """Get Keypad LED States"""
        # zero based buttons
        
        try:
            if "_" in keypad:
                button = keypad.split("_")[1]
                button = int(button) - 1
                keypad = keypad.split("_")[0]
                keypad = str(keypad).zfill(3).upper()
                msg = f"R,CGLED,{keypad}{button}"
                #time.sleep(0.2)
                self._send(msg, ltcmd="CGLED", keypad=keypad, button=button + 1)

        except:
            keypad = str(keypad).zfill(3).upper()
            button = int(button) - 1
            msg = f"R,CGLED,{keypad}{button}"
            self._send(msg, ltcmd="CGLED", keypad=keypad, button=button + 1)

    def run(self):
        """Read and dispatch messages from the controller."""
        self._running = True
        chk = 0
        data = ""
        while self._running:
            if self._socket == None:
                time.sleep(POLLING_FREQ)
                _LOGGER.debug(f"socket: {self._socket}.  Reconnecting")
                self._connect()
            else:
                try:
                    readable, _, _ = select.select([self._socket], [], [], POLLING_FREQ)
                    if len(readable) != 0:
                        byte = self._socket.recv(1)
                        if byte == b"\r":
                            if len(data) > 0:
                                self._processReceivedData(data)
                                data = ""
                        elif byte != b"\n":
                            data += byte.decode("utf-8")
                    elif chk > 120:
                        self._send("R,SIEVN,4")
                        _LOGGER.debug("Litetouch: Keep Alive")
                        chk = 0
                    else:
                        chk = chk + 1


                except (ConnectionError, AttributeError, TimeoutError):
                    _LOGGER.warning(
                        "Lost connection to litetouch controller, will attempt to reconnect."
                    )
                    self._socket = None
                except UnicodeDecodeError:
                    data = ""

    def _processReceivedData(self, data):
        _LOGGER.debug(f"Raw: {data}")
        try:
            raw_args = data.split(",")
            cmd = raw_args[1]

            if cmd == ("RLEDU" or "RMODU" or "REVNT"):

                if cmd == "RLEDU":
                    keypad = raw_args[2]
                    blist = list(str(raw_args[3][0:9]))
                    bnum = 0
                    for b in blist:
                        bnum = bnum + 1
                        kb = keypad + "_" + str(bnum)  # Build keypad address:
                        kb = [kb, b]
                        # Return LED Event and keypad/button status (binary):
                        self._callback("RLEDU", kb)
                elif cmd == "RMODU":
                    _LOGGER.warning(f"Event: {cmd}, not handled")
                else:
                    _LOGGER.warning(f"Event: {cmd}, not handled")

            elif cmd == "RCACK":
                data = ""
                # _LOGGER.warning(f"Not handling: {cmd}")
            else:
                data = ""
                # _LOGGER.warning(f'Not handling:  {cmd}')

        except ValueError:
            _LOGGER.warning("Weird data: %s", data)

    def _handle_request(self, resp, keypad, button):
        """handle specific controller query"""
        resplist = resp.split(",")
        cmd = resplist[2]

        # Need to fix to return all buttons instead of single button
        if cmd == "CGLES":
            status = int(resplist[3])
            status = bin(status)[2:]
            final = len(status) - int(button)
            final = str(status)[final:][0:1]
            kb = str(keypad) + "_" + str(button)
            if len(status) == 1 and len(status) < int(button):
                status = "0"
                kb = [kb, status]
                self._callback("CGLES", kb)
            elif len(status) < int(button):
                status = "0"
                kb = [kb, status]
                self._callback("CGLES", kb)
            elif final == "1":
                status = "1"
                kb = [kb, status]
                self._callback("CGLES", kb)
            else:
                status = "0"
                kb = [kb, status]
                self._callback("CGLES", kb)
        else:
            status = int(resplist[3])
            
            kb = str(keypad) + "_" + str(button)
            kb = [kb, status]
            self._callback("CGLED", kb)

    def close(self):
        """Close the connection to the controller."""
        self._running = False
        if self._socket:
            time.sleep(POLLING_FREQ)
            self._socket.close()
            self._socket = None
