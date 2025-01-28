import sys
import argparse
from gpiozero import Button, DigitalInputDevice
from time import sleep
import asyncio

async def run(button):
    while True:
        print(f"{button.value}")
        await asyncio.sleep(1)

def main(argv):
    parser = argparse.ArgumentParser(
                    prog='simple_led_blink',
                    description='Makes a LED blink on a raspberry PI (turns a gpio pin on and off)',)
    parser.add_argument('channel', type=int)
    args = parser.parse_args(argv[1:])
    
    #button = Button(args.channel, pull_up=True)
    button = DigitalInputDevice(args.channel, pull_up=True)

    asyncio.run(run(button))


if __name__ == '__main__':
    main(sys.argv)
