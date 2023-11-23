import crcmod
from typing import Dict

CRC16 = crcmod.mkCrcFun(0x11021, initCrc=0)
SOF = b'\xFE'
ZERO = b'\x00'

BUTTON: Dict[str, str] = {
    'POWER': b'\x00',
    'PAIRING': b'\x01',
    'SECURITY': b'\x02',
    'MUSIC': b'\x03',
    'RESET': b'\x04',
}

BUTTON_TRIGGER: Dict[str, str] = {
    'SINGLE': b'\x00',
    'DOUBLE': b'\x01',
    'LONG': b'\x02',
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

EFFECT_LIST: list[str] = [
    'off',
    'on',
    'fast_flashing',
    'double_flashing',
    'breathing',
    'marquee',
    'single_shot_flasher',
    'test_mode',
]

ERROR: Dict[str, str] = {
	'SUCCESS': b'\x00',
	'FRAME_LENGTH': b'\x01',
	'CRC': b'\x02',
	'COMMAND': b'\x03',
	'FORMAT': b'\x04',
	'CONTENT': b'\x05',
	'TIMEOUT': b'\x06',
}

LED_LIST: list[str] = [
    'power',
    'pairing',
    'security',
    'music',
    'indicator',
]
