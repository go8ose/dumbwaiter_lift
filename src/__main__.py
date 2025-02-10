import asyncio
import logging
import argparse
import sys
from typing import Callable
from signal import pause

from gpiozero import DigitalInputDevice, OutputDevice, Button

from dumb_waiter.logic import LiftLogicMachine, LiftLogicModel
from dumb_waiter.io import Input,Output


class OutPin(Output):
    def __init__(self, pin, initial_value=False):
        self.dev = OutputDevice(pin=pin, initial_value=initial_value)

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
    args = parser.parse_args(argv[1:])

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    
    # Output pins
    pinO_drive_lift_up = OutPin("BOARD7")
    pinO_drive_lift_down = OutPin("BOARD11")
    pinO_lock_door = OutPin("BOARD31")


    # Input pins
    pinI_call_pb = InPin("BOARD13", pull_up=True)
    pinI_lower_limit = InPin("BOARD15", pull_up=True)
    pinI_upper_limit = InPin("BOARD16", pull_up=True)
    pinI_door_closed_level1 = InPin("BOARD18", pull_up=True)
    pinI_door_closed_ground = InPin("BOARD22", pull_up=True)
    pinI_estop = InPin("BOARD29", pull_up=True)

    model = LiftLogicModel(
        estop=pinI_estop,
        lower_limit=pinI_lower_limit,
        upper_limit=pinI_upper_limit,
        upper_door_closed=pinI_door_closed_level1,
        lower_door_closed=pinI_door_closed_ground,
        raise_lift=pinO_drive_lift_up,
        lower_lift=pinO_drive_lift_down,
        lock_door=pinO_lock_door,
        #TODO: use argparser paramter
        safety_time=args.safety_timer,
    )
    llm = LiftLogicMachine(model)
    
    # Wire up the triggers to the lift logic
    pinI_call_pb.falling_edge_callback = lambda: llm.call()
    pinI_lower_limit.rising_edge_callback = lambda: llm.stop_lowering()
    pinI_upper_limit.rising_edge_callback = lambda: llm.stop_rising()
    pinI_door_closed_level1.falling_edge_callback = lambda: llm.door_opens()
    pinI_door_closed_ground.falling_edge_callback = lambda: llm.door_opens()
    pinI_estop.rising_edge_callback = lambda: llm.estop_pressed()

    llm.initialise()
    

    while True:
        await asyncio.sleep(10)


if __name__ == '__main__':
    asyncio.run(main(sys.argv))
