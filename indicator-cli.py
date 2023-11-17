#!/usr/bin/python3
import argparse
import asyncio
import serial_asyncio
from indicator import Frame, ycProtocol
import logging

debug = True
if debug:
    logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)

def validate_effect(value):
    value = int(value)
    if value < 0 or value > 8:
        raise argparse.ArgumentTypeError('Effect must be in the range 0 to 8')
    return value

def validate_index(value):
    value = int(value)
    if value < 0 or value > 4:
        raise argparse.ArgumentTypeError('LED index must be in the range 0 to 4')
    return value

def parse_args():
    parser = argparse.ArgumentParser(description='LED command parser')
    parser.add_argument('index', type=validate_index, help='LED index (0-4)')
    parser.add_argument('--effect', type=validate_effect, default=1, help='LED effect (0-8)')
    parser.add_argument('--rgb', type=int, nargs=3, metavar=('R', 'G', 'B'), help='RGB values (0-255)')
    parser.add_argument('--init', action='store_true', help='Force init of yc1175')
    return parser.parse_args()

def led(yc, index, effect, rgb):
    print(f"Index: {index} Effect: {effect}, Color: {rgb}")
    indicator_frame = Frame(yc.nextSeq())
    indicator_frame.led(index, effect, rgb)
    yc.sendFrame(indicator_frame)

async def run():
    comm = ycProtocol()


    args = parse_args()
    try:
        await comm.serial_init()

        if args.init:
            LOGGER.info("Initialising yc1175 indicator")
            await asyncio.sleep(1)
        
        led(comm, args.index, args.effect, args.rgb)

        await asyncio.sleep(0.5)

    except asyncio.CancelledError:
        pass
    except Exception as e:
        LOGGER.error(f"An error occurred: {e}")
    
if __name__ == '__main__':
    asyncio.run(run())
