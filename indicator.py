import asyncio
from const import CRC16, BUTTON, CMD_TYPE, COMMAND, ERROR, SOF, ZERO
import logging
import serial_asyncio
import struct

debug = True
if debug:
    logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)

class Frame:
    mtype = ZERO
    cmd = ZERO
    seq = ZERO
    data = bytearray()
    
    def __init__(self, seq:bytes(1)=ZERO, msg:bytearray=None):
        if len(seq) > 1:
            LOGGER.critical("Size of seq must be 1 byte only")
        if msg:
            self.unpack(msg)
        else:
            self.seq = seq
 
    def build(self, mtype:bytes(1), cmd:bytes(1), data:bytearray=ZERO):
        self.mtype = mtype
        self.cmd = cmd
        self.data = data

    #can call multiple times, but no checking for duplicate idx's
    def led(self, idx:int, effect:int, rgb:tuple):
        #need input validation checking on rgb tuple?
        self.cmd = COMMAND["CONTROL_LED"]
        self.data += struct.pack(">cc3s", idx.to_bytes(), effect.to_bytes(), bytearray(rgb))

    def pack(self) -> bytearray:
        N=len(self.data)
        frame = struct.pack(f">cHccc{N}s", SOF, N+8, self.mtype, self.cmd, self.seq, self.data )
        frame += CRC16(frame).to_bytes(2)
        return frame

    def unpack(self, packet:bytearray) -> None:
        N = len(packet) - 8
        tuple = struct.unpack(f">cHccc{N}sH", packet)
        sof, plen, self.mtype, self.cmd, self.seq, self.data, crc = tuple
        #check crc here?

    def unpack_button(self):
        # double and long press dont seem supported
        if self.cmd == COMMAND['REPORT_EVENT']:
            idx, event, param = struct.unpack(">ccH", self.data)
            if idx == BUTTON['PAIRING']:
                print('Zigbee Pairing')
            return idx

class ycProtocol:
    g_seq = 0
    listeners = []

    def __init__(self, reader = None, writer = None):
        if reader or writer:
            self.reader = reader
            self.writer = writer

    async def serial_init(self):
        self.reader, self.writer = await serial_asyncio.open_serial_connection(url='/dev/ttyS3', baudrate=115200)
        try:
            asyncio.create_task(self.readSerial(self.reader))
        except asyncio.CancelledError:
            pass

    async def readSerial(self, serial:asyncio.StreamReader):
        while True:
            # Read until the start of frame is found
            header = await serial.readuntil(SOF)
            if not header:
                continue

            f_bytes = await serial.readexactly(2)
            f_size = int.from_bytes(f_bytes)
            frame = SOF + f_bytes + await serial.readexactly(f_size - 3)

            if self.checkCRC(frame):
                asyncio.create_task(self.frame_callback(frame))
            else:
                LOGGER.warning("CRC Error in frame")

            await asyncio.sleep(0.25)

    def checkCRC(self, packet:bytearray) -> bool:
        crc_size = 2
        calc_crc = CRC16(packet[:-crc_size]).to_bytes(crc_size)
        return calc_crc == packet[-crc_size:]

    async def frame_callback(self, packet:bytearray):
        frame = Frame(msg=packet)
        self.logFrame(frame)
        if frame.mtype == CMD_TYPE["REQUEST"]:
            self.sendAck(frame)
        elif frame.mtype == CMD_TYPE["RESPONSE"]:
            #first byte of data is error code (0x00 success)
            error_code = frame.data[0:1]
            if error_code == ERROR["SUCCESS"]:
                if frame.seq in self.listeners:
                    self.listeners.remove(frame.seq)
            else:
                LOGGER.warning(f"Response is error: {error_code}")
        else:
            #Notification type not implemented
            pass

    def logFrame(self, frame:Frame, title:str=None):
        if not title:
            title = "res" if frame.mtype == CMD_TYPE["RESPONSE"] else "req"
        packet = frame.pack()
        LOGGER.debug(f"[{title}] " + ' '.join(format(x, '02x') for x in packet))

    def nextSeq(self) -> bytes:
        self.g_seq = (self.g_seq + 1) % 255
        return self.g_seq.to_bytes(1)
    
    def sendAck(self, frame:Frame) -> None:
        ct_r = CMD_TYPE["RESPONSE"]

        if frame.mtype == CMD_TYPE["REQUEST"]:
            response = Frame(frame.seq)
            if frame.cmd == COMMAND["VERSION_RK"]:
                version = b'\x00\x00\x01'
                response.build(ct_r, COMMAND["VERSION_RK"], version)
            else:
                response.build(ct_r, frame.cmd)

            self.sendFrame(response)

    def sendFrame(self, frame):
        self.logFrame(frame)
        if frame.mtype == CMD_TYPE["REQUEST"]:
            self.listeners.append(frame.seq)
        asyncio.create_task(self.writeSerial(self.writer, frame))

    async def writeSerial(self, serial:asyncio.StreamWriter, frame:Frame):
        packet = frame.pack()
        serial.write(packet)
        await serial.drain()

async def main():
    #async init stream reader/writers in ycProtocol (or maybe HA)
    # reader, writer = await serial_asyncio.open_serial_connection(url='/dev/ttyS3', baudrate=115200)
    # yc = ycProtocol(reader, writer)
    yc = ycProtocol()
    await yc.serial_init()

    try:
        # asyncio.create_task(yc.readSerial(reader))
        #test code to remove from library
        indicator = Frame(yc.nextSeq())
        rgb =  (0,0,255)
        indicator.led(4, 1, rgb)
        yc.sendFrame(indicator)

        for i in range(5):
            await asyncio.sleep(1)
            LOGGER.info(f"main looping: {5-i}")
    except asyncio.CancelledError:
        pass

if __name__ == "__main__":
    asyncio.run(main())

