import sys
import argparse
from gpiozero import Button
from time import sleep

def main(argv):
    parser = argparse.ArgumentParser(
                    prog='simple_led_blink',
                    description='Makes a LED blink on a raspberry PI (turns a gpio pin on and off)',)
    parser.add_argument('channel', type=int)
    args = parser.parse_args(argv[1:])
    
    button = Button(args.channel)

    while True:
        print(f"{button.is_pressed}")
        sleep(1)

if __name__ == '__main__':
    main(sys.argv)