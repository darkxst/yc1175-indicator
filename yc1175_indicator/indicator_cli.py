#!/usr/bin/python3
import argparse
import asyncio
from .const import EFFECT_LIST
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

def parse_args():
    parser = argparse.ArgumentParser(description='LED command parser')
    parser.add_argument('index', type=validate_index, help='LED index (0-4)')
    parser.add_argument('--init', action='store_true', help='Ensure init of yc1175')
    parser.add_argument('--effect', type=validate_effect, default=1, help='LED effect (0-8)')
    parser.add_argument('--list', action='store_true', help='print available effects')
    parser.add_argument('--rgb', type=validate_rgb, nargs=3, default=(255,0,0), metavar=('R', 'G', 'B'), help='RGB values (0-255)')
    parser.add_argument('--debug', action='store_true', help='enable debug output')

    return parser.parse_args()

def led(yc, index, effect, rgb):
    rgb_str = rgb
    if index != 4:
        rgb_str = "n/a"
    print(f"Index: {index} Effect: {effect}, Color: {rgb_str}")

    indicator_frame = Frame()
    indicator_frame.led(index, effect, rgb)
    yc.send_frame(indicator_frame)

def print_list():
    print("Effects:")
    for i in range(8):
        print(f"{i} - {EFFECT_LIST[i]}")
    print("---")

async def run():
    args = parse_args()
    rgb = tuple(args.rgb)
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    if args.list:
        print_list()

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