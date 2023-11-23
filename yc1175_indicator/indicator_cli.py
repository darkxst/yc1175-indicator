#!/usr/bin/python3
import argparse
import asyncio
from .const import EFFECT_LIST, LED_LIST
import serial_asyncio
from .indicator import Frame, ycProtocol
import logging

_LOGGER = logging.getLogger(__name__)

def validate_effect(value):
    value = int(value)
    if not value in range(9):
        raise argparse.ArgumentTypeError('Effect must be in the range 0 to 8')
    return value

def validate_index(value):
    value = int(value)
    if not value in range(5):
        raise argparse.ArgumentTypeError('LED index must be in the range 0 to 4')
    return value

def validate_rgb(value):
    value = int(value)
    if not value in range(256):
        raise argparse.ArgumentTypeError('RGB values must be in the range 0 to 255')
    return value

def parser_opt():
    parser = argparse.ArgumentParser(description='LED command parser')
    main_group = parser.add_mutually_exclusive_group(required=True)
    main_group.add_argument('index', type=validate_index, nargs='?', help='LED index (0-4)')
    main_group.add_argument('--list', action='store_true', help='print leds and available effects')
    parser.add_argument('--init', action='store_true', help='Ensure init of yc1175')
    parser.add_argument('--effect', type=validate_effect, default=1, help='LED effect (0-8)')
    parser.add_argument('--rgb', type=validate_rgb, nargs=3, default=(255,0,0), metavar=('R', 'G', 'B'), help='RGB values (0-255)')
    parser.add_argument('--debug', action='store_true', help='enable debug output')

    return parser

def led(yc, index, effect, rgb):
    rgb_str = rgb
    if index != 4:
        rgb_str = "n/a"
    print(f"Index: {index} Effect: {effect}, Color: {rgb_str}")

    indicator_frame = Frame()
    indicator_frame.led(index, effect, rgb)
    yc.send_frame(indicator_frame)

def print_list():
    print("LEDs:")
    for i in range(5):
        print(f"{i} - {LED_LIST[i]}")
    print("---")
    print("Effects:")
    for i in range(8):
        print(f"{i} - {EFFECT_LIST[i]}")
    print("---")

async def run():
    parser = parser_opt()
    args = parser.parse_args()
    rgb = tuple(args.rgb)

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    if args.list:
        print_list()
        return
    elif args.index is None:
        parser.error("led index is required for all other options")

    comm = ycProtocol()
    try:
        await comm.serial_init()

        if args.init:
            _LOGGER.info("Waiting for yc1175 indicator init")
            await asyncio.sleep(1)
        
        led(comm, args.index, args.effect, rgb)
        await asyncio.sleep(0.25)

    except asyncio.CancelledError:
        pass
    except Exception as e:
        _LOGGER.error(f"An error occurred: {e}")

def main():
    asyncio.run(run())

if __name__ == '__main__':
    main()