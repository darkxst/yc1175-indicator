import asyncio
from .const import (
    BUTTON,
    CRC16,
    CMD_TYPE,
    COMMAND,
    EFFECT_LIST,
    ERROR,
    SOF,
    ZERO)
import logging
import serial_asyncio
import struct
from typing import Tuple

_LOGGER = logging.getLogger(__name__)

class Frame:
    g_seq = 0
    def __init__(self, seq:bytes(1) = None, packet:bytearray = None) -> None:
        if packet:
            self.unpack(packet)
        else:
            self.cmd = ZERO
            self.data = bytearray()
            self.mtype = CMD_TYPE["REQUEST"]
            if seq:
                if len(seq) > 1:
                    _LOGGER.critical("Size of seq must be 1 byte only")
                    seq=0
                self.seq = seq
            else:
                self.seq = self.g_seq
                Frame.g_seq = (Frame.g_seq + 1) % 255
 
    def build(self, mtype:bytes(1), cmd:bytes(1), data:bytearray=b'') -> None:
        self.mtype = mtype
        self.cmd = cmd
        self.data = data

    def led(self, idx:int, effect:int, rgb:tuple) -> None:
        """Build data field to control led, can be called multiple times to add extra led commands."""
        if not self.validate_rgb(rgb):
            _LOGGER.warning("Invalid rgb tuple, using default value")
            rgb = (255,0,0)

        self.mtype = CMD_TYPE["REQUEST"]
        self.cmd = COMMAND["CONTROL_LED"]
        self.data += struct.pack(">cc3s", idx.to_bytes(), effect.to_bytes(), bytearray(rgb))

    def pack(self) -> bytearray | None:
        if self.cmd == ZERO:
            _LOGGER.warning("Command not set, Frame likely incomplete")
            return None

        seq = self.seq.to_bytes(1) if type(self.seq) is int else self.seq
        N=len(self.data)

        frame = struct.pack(f">cHccc{N}s", SOF, N+8, self.mtype, self.cmd, seq, self.data)
        frame += CRC16(frame).to_bytes(2)
        return frame

    def unpack(self, packet:bytes) -> None:
        N = len(packet) - 8
        tuple = struct.unpack(f">cHccc{N}sH", packet)
        sof, plen, self.mtype, self.cmd, self.seq, self.data, crc = tuple

    def unpack_button(self) -> Tuple[bytes, bytes]:
        if self.cmd == COMMAND['REPORT_EVENT']:
            idx, event, param = struct.unpack(">ccH", self.data)
            return idx, event

    def validate_rgb(self, rgb:tuple) -> bool:
        if isinstance(rgb, tuple) and len(rgb) == 3:
            if all(c in range(256) for c in rgb):
                return True
        return False

class ycProtocol:
    event_callback = None
    listeners = []

    def __init__(self, reader:asyncio.StreamReader=None, writer:asyncio.StreamWriter=None):
        if reader or writer:
            self.reader = reader
            self.writer = writer

    async def serial_init(self) -> None:
        self.reader, self.writer = await serial_asyncio.open_serial_connection(url='/dev/ttyS3', baudrate=115200)
        try:
            asyncio.create_task(self.read_serial(self.reader))
        except asyncio.CancelledError:
            pass

    async def read_serial(self, serial:asyncio.StreamReader) -> None:
        while True:
            # Read until the start of frame is found
            header = await serial.readuntil(SOF)
            if not header:
                continue

            f_bytes = await serial.readexactly(2)
            f_size = int.from_bytes(f_bytes)
            packet = SOF + f_bytes + await serial.readexactly(f_size - 3)

            if self.checkCRC(packet):
                asyncio.create_task(self.frame_callback(packet))
            else:
                _LOGGER.warning("CRC Error in frame")

            await asyncio.sleep(0.25)

    def checkCRC(self, packet:bytearray) -> bool:
        crc_size = 2
        calc_crc = CRC16(packet[:-crc_size]).to_bytes(crc_size)
        return calc_crc == packet[-crc_size:]

    async def frame_callback(self, packet:bytearray) -> None:
        frame = Frame(packet=packet)
        self.log_frame(frame)

        if frame.mtype == CMD_TYPE["REQUEST"]:
            self.send_ack(frame)
            if self.event_callback and frame.cmd == COMMAND["REPORT_EVENT"]:
                idx, event = frame.unpack_button()
                asyncio.create_task(self.event_callback(idx, event))
    
        elif frame.mtype == CMD_TYPE["RESPONSE"]:
            #first byte of response data is error code (0x00 success)
            error_code = frame.data[0:1]
            if error_code == ERROR["SUCCESS"]:
                if frame.seq in self.listeners:
                    self.listeners.remove(frame.seq)
            else:
                _LOGGER.warning(f"Response is error: {error_code}")
        else:
            #Notification type not implemented
            pass

    def log_frame(self, frame:Frame, title:str=None) -> None:
        if not title:
            title = "res" if frame.mtype == CMD_TYPE["RESPONSE"] else "req"
        packet = frame.pack()
        _LOGGER.debug(f"[{title}] " + ' '.join(format(x, '02x') for x in packet))
  
    def send_ack(self, frame:Frame) -> None:
        ct_r = CMD_TYPE["RESPONSE"]

        if frame.mtype == CMD_TYPE["REQUEST"]:
            response = Frame(seq=frame.seq)
            if frame.cmd == COMMAND["VERSION_RK"]:
                version = b'\x00\x00\x01'
                response.build(ct_r, COMMAND["VERSION_RK"], version)
            else:
                response.build(ct_r, frame.cmd, ZERO)

            self.send_frame(response)

    def send_frame(self, frame) -> None:
        self.log_frame(frame)
        if frame.mtype == CMD_TYPE["REQUEST"]:
            self.listeners.append(frame.seq)
        asyncio.create_task(self.write_serial(self.writer, frame))

    async def write_serial(self, serial:asyncio.StreamWriter, frame:Frame) -> None:
        packet = frame.pack()
        if packet:
            serial.write(packet)
            await serial.drain()

class HassAPI:
    """Provide API for use in Home Assistant Integration"""
    def __init__(self, yc:ycProtocol=None):
        if yc:
            self.comm = yc

    async def setup(self) -> None:
        """Setup asyncio serial connection to yc1175"""
        self.comm = ycProtocol()
        await self.comm.serial_init()

    def button_list(self) -> list:
        """Available buttons list"""
        buttons = [key.lower() for key in BUTTON.keys()]
        return buttons

    def effect_list(self) -> list:
        """Supported effects list"""
        return EFFECT_LIST

    def light_on(self, idx:int, effect:int=1, rgb:tuple=(0,0,255)) -> None:
        led_frame = Frame()
        led_frame.led(idx, effect, rgb)
        self.comm.send_frame(led_frame)

    def light_off(self, idx:int) -> None:
        rgb=(0,0,0)
        led_frame = Frame()
        led_frame.led(idx, 0, rgb)
        self.comm.send_frame(led_frame)

    def register_event_callback(self, callback) -> None:
        """Register callback to be fired on button press"""
        self.comm.event_callback = callback

    def remove_event_callback(self) -> None:
        self.comm.event_callback = None
