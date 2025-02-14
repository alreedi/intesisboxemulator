"""
Emulates an IntesisBox device on TCP port 3310 
"""
import asyncio
import socket
 
# Function to display hostname and
# IP address
def get_Host_name_IP():
    try:
        host_name = socket.gethostname()
        host_ip = socket.gethostbyname(host_name)
        print("Hostname :  ",host_name)
        print("IP : ",host_ip)
    except:
        print("Unable to get Hostname and IP")
 
# Driver code
get_Host_name_IP()

MODE_AUTO = 'AUTO'
MODE_DRY = 'DRY'
MODE_FAN = 'FAN'
MODE_COOL = 'COOL'

FUNCTION_ONOFF = 'ONOFF'
FUNCTION_MODE = 'MODE'
FUNCTION_SETPOINT = 'SETPTEMP'
FUNCTION_FANSP = 'FANSP'
FUNCTION_VANEUD = 'VANEUD'
FUNCTION_VANELR = 'VANELR'
FUNCTION_AMBTEMP = 'AMBTEMP'
FUNCTION_ERRSTATUS = 'ERRSTATUS'
FUNCTION_ERRCODE = 'ERRCODE'

RW_FUNCTIONS = [FUNCTION_ONOFF, FUNCTION_MODE, FUNCTION_SETPOINT,
                FUNCTION_VANELR, FUNCTION_VANEUD, FUNCTION_FANSP]

class IntesisBoxEmulator(asyncio.Protocol):
    def __init__(self):
        self.mode = 'AUTO'
        self.setpoint = '210'
        self.power = 'ON'
        self.devices = {'1': {FUNCTION_MODE: MODE_AUTO,
                            FUNCTION_SETPOINT: '210',
                            FUNCTION_ONOFF: 'ON',
                            FUNCTION_FANSP: 'AUTO',
                            FUNCTION_AMBTEMP: '180',
                            FUNCTION_VANEUD: 'AUTO',
                            FUNCTION_VANELR: 'AUTO',
                            FUNCTION_ERRSTATUS: 'OK',
                            FUNCTION_ERRCODE: ''
                            }
                        }

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        linesReceived = data.decode('ascii').splitlines()
        for line in linesReceived:
            request = line.rstrip().split(',')
            response = ''
            if request[0] == 'ID':
                response = 'ID:IS-IR-WMP-1,001DC9A2C911,192.168.100.246,ASCII,v0.0.1,-44'
            elif request[0] == 'GET':
                acNum = request[1].split(':')[0]
                function = request[1].split(':')[1]
                if acNum in self.devices and function == '*':
                    for function, value in self.devices[acNum].items():
                        response += 'CHN,{}:{},{}\r\n'.format(acNum, function, value)
                elif acNum in self.devices and function in self.devices[acNum]:
                    current_value = self.devices[acNum][function]
                    response = 'CHN,{}:{},{}'.format(acNum, function, current_value)
                else:
                    response = 'ERR'

            elif request[0] == 'SET':
                acNum = request[1].split(':')[0]
                function = request[1].split(':')[1]
                if acNum in self.devices and function in RW_FUNCTIONS and len(request) >= 3:
                    value = request[2]
                    if self.devices[acNum][function] != value:
                        self.devices[acNum][function] = value
                        response = 'ACK\r\nCHN,{}:{},{}'.format(acNum, function, value)
                    else:
                        response = 'ACK'
                else:
                    response = 'ERR'

            elif request[0].split(':')[0] == 'LIMITS':
                limit = request[0].split(':')[1]
                if limit == 'FANSP':
                    response = 'LIMITS:FANSP,[AUTO,1,2,3,4]'
                elif limit == 'VANEUD':
                    response = 'LIMITS:VANEUD,[AUTO,1,2,3,SWING]'
                elif limit == 'VANELR':
                    response = 'LIMITS:VANELR,[AUTO,1,2,3,SWING]'
                elif limit == 'SETPTEMP':
                    response = 'LIMITS:SETPTEMP,[160,300]'
                elif limit == 'MODE':
                    response = 'LIMITS:MODE,[AUTO,HEAT,DRY,COOL,FAN]'

            response += '\r\n'
            self.transport.write(response.encode('ascii'))

async def main(host, port):
    loop = asyncio.get_running_loop()
    server = await loop.create_server(IntesisBoxEmulator, host, port)
    await server.serve_forever()

asyncio.run(main('0.0.0.0', 3310))
