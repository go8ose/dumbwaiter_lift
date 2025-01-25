import sys
import argparse
from gpiozero import Button
from time import sleep


press_count = 0
def button_pressed():
    global press_count
    press_count += 1
    print (f"button pressed {press_count} times")



def main(argv):
    parser = argparse.ArgumentParser(
                    prog='simple_led_blink',
                    description='Makes a LED blink on a raspberry PI (turns a gpio pin on and off)',)
    parser.add_argument('channel', type=int)
    args = parser.parse_args(argv[1:])

    
    button = Button(args.channel, bounce_time=0.01)
    button.when_deactivated = button_pressed

    while True:
        print(f"{button.is_pressed}")
        sleep(1)

if __name__ == '__main__':
    main(sys.argv)
