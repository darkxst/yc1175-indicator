# YC1175 Indicator - Sonoff iHost

A library that implements the serial protocol for communication with the
indicator module on the Sonoff iHost. This module controls the 4 buttons
and the main RGB indicator.

**WARNING: This is only useful if you have flashed linux or HAOS on your iHost.**

## Installation

`pip install yc1175-indicator`


## CLI Usage
For convience you can control the LED's from the CLI Wrapper.  
`indicator-cli <led_index> --effect <effect_num> --rgb <rgb tuple>`

example:  
`indicator-cli 4 --effect 2 --rgb 0 0 255`

## Library Usage
```python
import asyncio
from yc1175_indicator import indicator

async def test_callback(idx, event):
    print(f"Button press: {idx}, type: {event}")

async def main():
    my_yc = indicator.HassAPI()
    await my_yc.setup()
    my_yc.register_event_callback(test_callback)

    rgb =  (0,0,255)
    yc.light_on(4, 1, rgb)
    try:
        # wait for button press
        await asyncio.sleep(30)
    except asyncio.CancelledError:
        pass
    yc.light_off(4)

if __name__ == "__main__":
    asyncio.run(main())
```