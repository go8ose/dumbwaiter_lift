import asyncio
import logging
import argparse
import sys
from typing import Callable
from signal import pause

from gpiozero import DigitalInputDevice, OutputDevice, Button

from dumb_waiter.logic import LiftLogicMachine, LiftLogicModel
from dumb_waiter.io import Input,Output
from dumb_waiter.util import ainput


class OutPin(Output):
    def __init__(self, pin, initial_value=False, active_high=True):
        self.dev = OutputDevice(pin=pin, initial_value=initial_value, active_high=active_high)

    @property
    def value(self):
        return self.dev.value

    def on(self):
        self.dev.on()

    def off(self):
        self.dev.off()

class InPin(Input):
    def __init__(self, pin, pull_up = False):
        self.dev = Button(pin=pin, bounce_time=0.01, pull_up=pull_up)
        self.main_loop = asyncio.get_running_loop()

    def __call__(self):
        return self.dev.value

    @property
    def falling_edge_callback(self):
        return self.dev.when_deactivated

    @falling_edge_callback.setter
    def falling_edge_callback(self, value: Callable):
        
        # If the callback is set, we need to store it somewhere, and then setup the gpio device
        # to fire a callback when the event occurs. But gpio creates a new thread which executes 
        # the callback. I want the callback to occur in the main thread.
        self.callable_to_fire_on_falling_edge = value
        self.dev.when_deactivated = self._falling_call_soon_wrapper

    def _falling_call_soon_wrapper(self):
        self.main_loop.call_soon_threadsafe(self.callable_to_fire_on_falling_edge)

    @property
    def rising_edge_callback(self):
        return self.dev.when_activated

    @rising_edge_callback.setter
    def rising_edge_callback(self, value: Callable):
        
        # If the callback is set, we need to store it somewhere, and then setup the gpio device
        # to fire a callback when the event occurs. But gpio creates a new thread which executes 
        # the callback. I want the callback to occur in the main thread.
        self.callable_to_fire_on_rising_edge = value
        self.dev.when_activated = self._rising_call_soon_wrapper

    def _rising_call_soon_wrapper(self):
        self.main_loop.call_soon_threadsafe(self.callable_to_fire_on_rising_edge)

async def main(argv):

    parser = argparse.ArgumentParser(prog='lift control logic')
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('--safety-timer', action='store_true', default=23)
    parser.add_argument('--check-io', action='store_true', default=False,
        help="""Before starting the logic to drive the lift prompt the user and check each input""")
    args = parser.parse_args(argv[1:])

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    
    # Output pins
    pinO_drive_lift_up = OutPin("BOARD7", active_high=False)
    pinO_drive_lift_down = OutPin("BOARD11", active_high=False)
    pinO_lock_door_top = OutPin("BOARD31")
    pinO_lock_door_bottom = OutPin("BOARD33")


    # Input pins
    pinI_call_pb_top = InPin("BOARD13", pull_up=True)
    pinI_call_pb_bottom = InPin("BOARD38", pull_up=True)
    pinI_lower_limit = InPin("BOARD15", pull_up=True)
    pinI_upper_limit = InPin("BOARD16", pull_up=True)
    pinI_door_closed_level1 = InPin("BOARD18", pull_up=True)
    pinI_door_closed_ground = InPin("BOARD22", pull_up=True)
    pinI_estop_top = InPin("BOARD29", pull_up=True)
    pinI_estop_bottom = InPin("BOARD40", pull_up=True)

    if args.check_io:

        print("For this test both doors will be unlocked")
        pinO_lock_door_top.off()
        pinO_lock_door_bottom.off()
        answer = await ainput('Please confirm both doors are unlocked: (Enter "y" or "n"):')
        if answer.lower() not in ('y', 'yes'):
            raise SystemExit('Abandoning --check-io run')

        input_was_activated = False
        def input_fired():
            input_was_activated = True
        print("Let's check all the inputs")

        inputs = [
            (pinI_estop_top, "EStop top"),
            (pinI_estop_bottom, "EStop bottom"),
            (pinI_call_pb_top, "Call button top"),
            (pinI_call_pb_bottom, "Call button bottom"),
            (pinI_lower_limit, "Lower Limit"),
            (pinI_upper_limit, "Upper Limit"),
            (pinI_door_closed_level1, "Door Closed Level 1"),
            (pinI_door_closed_ground, "Door Closed Ground"),
        ]

        for (pin, message) in inputs:
            pin.falling_edge_callback = input_fired
            print(f'Please activate and then deactivate {message}')
            while not input_was_activated:
                # TODO: It would be nice if the input_fired() interrupted this sleep. Then I 
                # could make the sleep longer, and each time through the loop post a new message so
                # the operator knows the script is still running.
                await asyncio.sleep(0.5)
            pinI_call_pb_top.falling_edge_callback = None
            input_was_activated = False

        print("We will soon check the motor.")
        while pinI_door_closed_ground() == False:
            print("Please shut the ground door")
            await asyncio.sleep(3.5)
        while pinI_door_closed_level1() == False:
            print("Please shut the level 1 door")
            await asyncio.sleep(3.5)


        answer = ''
        # todo loop for right answer?
        while answer.lower() not in ('u', 'd', 'up', 'down'):
            answer = await ainput('We will move the lift for 1 second. Do you want it to move up or down? (Please enter "u" or "d") ')

        direction = 'up' if answer in ['u', 'up'] else 'down'
        print(f"About to move lift {direction}")
        await asyncio.sleep(1)
        if direction == 'up':
            pinO_drive_lift_up.on()
            await asyncio.sleep(1)
            pinO_drive_lift_up.off()
        else:
            pinO_drive_lift_down.on()
            await asyncio.sleep(1)
            pinO_drive_lift_down.off()

        print("Now we will move the lift in the other direction for 1 second")
        direction = 'up' if direction == 'down' else 'down'
        print(f"Move lift {direction}")
        await asyncio.sleep(1)
        if direction == 'up':
            pinO_drive_lift_up.on()
            await asyncio.sleep(1)
            pinO_drive_lift_up.off()
        else:
            pinO_drive_lift_down.on()
            await asyncio.sleep(1)
            pinO_drive_lift_down.off()

        print("Testing finished, exiting")
        raise SystemExit()

    model = LiftLogicModel(
        estop1=pinI_estop_top,
        estop2=pinI_estop_bottom,
        lower_limit=pinI_lower_limit,
        upper_limit=pinI_upper_limit,
        upper_door_closed=pinI_door_closed_level1,
        lower_door_closed=pinI_door_closed_ground,
        raise_lift=pinO_drive_lift_up,
        lower_lift=pinO_drive_lift_down,
        lock_door_top=pinO_lock_door_top,
        lock_door_bottom=pinO_lock_door_bottom,
        #TODO: use argparser paramter
        safety_time=args.safety_timer,
    )
    llm = LiftLogicMachine(model)
    
    # Wire up the triggers to the lift logic
    pinI_call_pb_top.falling_edge_callback = lambda: llm.call()
    pinI_call_pb_bottom.falling_edge_callback = lambda: llm.call()
    pinI_lower_limit.rising_edge_callback = lambda: llm.stop_lowering()
    pinI_upper_limit.rising_edge_callback = lambda: llm.stop_rising()
    pinI_door_closed_level1.falling_edge_callback = lambda: llm.door_opens()
    pinI_door_closed_ground.falling_edge_callback = lambda: llm.door_opens()
    pinI_estop_top.rising_edge_callback = lambda: llm.estop_pressed()
    pinI_estop_bottom.rising_edge_callback = lambda: llm.estop_pressed()

    llm.initialise()
    

    while True:
        await asyncio.sleep(10)


if __name__ == '__main__':
    asyncio.run(main(sys.argv))
