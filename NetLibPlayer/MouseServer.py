import socket
import pyautogui as pag
from os import system as run_shell
from NetLibPlayer import config
from NetLibPlayer.common import log

__author__ = 'johng'

pag.FAILSAFE = False


class MouseServer:
    """Creates a TCP socket listener and handles client requests"""

    # Variables for handling errors and communicating to/from clients
    sock_error = False
    input_error = False

    ERROR_BIND = 1
    ERROR_CON_DIED = 2
    ERROR_CON_LOST = 3
    ERROR_BAD_COMMAND = 4
    ERROR_BAD_ARGS = 5

    RESPONSE_START = b'110'
    RESPONSE_GOOD = b'0'
    RESPONSE_BAD = b'1'
    RESPONSE_CLOSE = b'2'

    def __init__(self, host=config.ip_address, port=config.mouse_server_port, mouse_speed=0.1):
        """Entry point of MouseServer, initializes the socket listener and contains the main loop"""

        self.MOUSE_MOVE_SPEED = mouse_speed
        self.sock = socket.socket()

        # Attempts to bind socket
        try:
            self.sock.bind((host, port))
        except OSError:
            self.sock_error = self.ERROR_BIND
            return

        # Listens for one connection attempt at a time
        self.sock.listen(1)
        log("Listening on interface: " + host + ":" + str(port))

        # Continuously listen for connection attempts, and calls _on_connect() when one is made
        while True:
            conn, addr = self.sock.accept()
            log("Connection with " + addr[0] + ":" + str(addr[1]) + " established")
            self._on_connect(conn, addr)

    def _on_connect(self, conn, remote):
        """Connection with client has been established"""

        # Initialize connection error value and send a connection start response
        conn_error = False
        conn.send(self.RESPONSE_START)

        while True:
            self.input_error = False
            msg_queue = ""

            # Waits for client to send something...
            try:
                data = conn.recv(1024)
            except socket.error:
                conn_error = self.ERROR_CON_DIED
                break

            # No data received, terminate connection
            if not data:
                conn_error = self.ERROR_CON_LOST
                break

            # Splits data by space character. command = data[0], args = data[1:]
            data = str(data, "utf-8").strip().split(" ")
            command = data[0]

            if len(data) == 2:
                args = data[1]
            else:
                args = None

            if command == "GOTO":
                if args is None:
                    self.input_error = self.ERROR_BAD_ARGS
                else:
                    coords = self.parse_coords(args)
                    pag.moveTo(coords[0], coords[1], self.MOUSE_MOVE_SPEED) \
                        if type(coords[0]) is float else self._set_input_error(self.ERROR_BAD_ARGS)

            elif command == "MOVE":
                if args is None:
                    self.input_error = self.ERROR_BAD_ARGS
                else:
                    coords = self.parse_coords(args)
                    pag.moveRel(coords[0], coords[1], self.MOUSE_MOVE_SPEED) \
                        if type(coords[0]) is float else self._set_input_error(self.ERROR_BAD_ARGS)

            elif command == "CLICK":
                pag.click()

            elif command == "DOWN":
                pag.mouseDown()

            elif command == "UP":
                pag.mouseUp()

            elif command == "VDOWN":
                if args is None:
                    args = 1
                pag.press("volumedown", int(args))

            elif command == "VUP":
                if args is None:
                    args = 1
                pag.press("volumeup", int(args))

            elif command == "VMUTE":
                pag.press("volumemute")

            elif command == "EXIT":
                pag.hotkey("alt", "f4")

            elif command == "SLEEP":
                log("Terminating connection with " + remote[0] + "\nGoing to sleep...")
                conn.send(self.RESPONSE_CLOSE)
                conn.close()
                run_shell("{} -d -f -t 0".format(config.psshutdown))
                break

            elif command == "RCLICK":
                pag.click(button="right")

            elif command == "SEND":
                if args is None:
                    self.input_error = self.ERROR_BAD_ARGS
                else:
                    if args == "8":
                        key = "backspace"
                    else:
                        key = chr(int(args))
                    pag.press(key)

            elif command == "HELP":
                msg_queue = """\
Mouse Server v0.1
Available Commands:
GOTO
MOVE
CLICK
RCLICK
SEND
CLOSE
HELP
"""

            elif command == "CLOSE":
                log("Connection ended per client request")
                conn.send(self.RESPONSE_CLOSE)
                conn.close()
                break

            # Invalid command
            else:
                self.input_error = self.ERROR_BAD_COMMAND

            # Responds to client request with a 0 for OKAY and 1 for ERROR
            if self.input_error is not False:
                conn.send(self.RESPONSE_BAD + bytes(self._get_error(self.input_error)))
            else:
                conn.send(self.RESPONSE_GOOD + bytes(msg_queue))

        # Connection ended, if there was an error report it
        if conn_error is not False:
            log("Input error: " + self._get_error(conn_error))

    def _set_input_error(self, errno):
        self.input_error = errno

    @staticmethod
    def parse_coords(coords):
        """Given a string in format of XXX,YYY returns a tuple of X and Y float coordinates,
            or (None, None) if not valid coordinates"""
        try:
            x, y = coords.split(",")
            return float(x), float(y)
        except ValueError:
            return None, None

    def _get_error(self, errno):
        """Returns the appropriate error message for the given error number"""
        error_messages = {
            self.ERROR_BIND: "Failed to bind to the socket address.",
            self.ERROR_CON_DIED: "Connection terminated by client.",
            self.ERROR_CON_LOST: "Lost connection to the client.",
            self.ERROR_BAD_COMMAND: "No such command.",
            self.ERROR_BAD_ARGS: "Malformed arguments received, please see HELP."
        }
        return error_messages[errno]

    def __del__(self):
        """Server termination house-keeping"""
        if self.sock_error:
            log("Exiting with error: " + self._get_error(self.sock_error))
        else:
            try:
                self.sock.send(self.RESPONSE_CLOSE)
            except OSError:
                log("Failed to send.")
                pass
        self.sock.close()


if __name__ == "__main__":
    MouseServer()
