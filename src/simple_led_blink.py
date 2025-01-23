import sys
import argparse
from gpiozero import LED
from time import sleep

def main(argv):
    parser = argparse.ArgumentParser(
                    prog='simple_led_blink',
                    description='Makes a LED blink on a raspberry PI (turns a gpio pin on and off)',
    parser.add_argument('channel', type=int)
    args = parser.parse_args(argv)
    
    led = LED(args.channel)

    while True:
        led.on()
        sleep(1)
        led.off()
        sleep(1)

if __name__ == '__main__':
    main(sys.argv)