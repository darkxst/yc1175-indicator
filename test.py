#!/usr/bin/python
from const import BUTTON, BUTTON_TRIGGER
import asyncio
import indicator
import logging

debug = True
if debug:
    logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)

async def test_callback(idx, event):
    button = idx
    trigger = event
    for k, v in BUTTON.items():
        if v == button:
            button = k
            break
    for k, v in BUTTON_TRIGGER.items():
        if v == trigger:
            trigger = k
            break

    _LOGGER.info(f"Button press: {button}, type: {trigger}")


async def main():
    """Emulate usage as per Home Assistant integration"""
    yc = indicator.HassAPI()
    await yc.setup()
    yc.register_event_callback(test_callback)

    rgb =  (0,0,255)
    yc.light_on(4, 1, rgb)
    try:
        for i in range(5):
            await asyncio.sleep(5)
            _LOGGER.info(f"main looping: {5-i}")
    except asyncio.CancelledError:
        pass
    yc.light_off(4)

if __name__ == "__main__":
    asyncio.run(main())