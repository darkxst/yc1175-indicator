import crcmod
from typing import Dict

CRC16 = crcmod.mkCrcFun(0x11021, initCrc=0)

BUTTON: Dict[str, str] = {
    'POWER': b'\x01',
    'PAIRING': b'\x02',
    'SECURITY': b'\x03',
    'MUSIC': b'\x04',
    'RESET': b'\x05',
}

CMD_TYPE: Dict[str, str] = {
    'REQUEST': b'\x00',
    'RESPONSE': b'\x40',
    'NOTIFY': b'\x80',
}

COMMAND: Dict[str, str] = {
	'VERSION_YC': b'\x01',
	'VERSION_RK': b'\x02',
	'REPORT_EVENT': b'\x03',
	'CONTROL_LED': b'\x04',
	'REPORT_LED': b'\x05',
	'BROADCAST_ID': b'\x06',
	'QUERY_LED': b'\x07',
}

ERROR: Dict[str, str] = {
	'SUCCESS': b'\x00',
	'FRAME_LENGTH': b'\x01',
	'CRC': b'\x02',
	'COMMAND': b'\x03',
	'FORMAT': b'\x04',
	'CONTENT': b'\x05',
	'TIMEOUT': b'\x06',
}

SOF = b'\xFE'
ZERO = b'\x00'