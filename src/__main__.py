from gpiozero import DigitalInputDevice, OutputDevice, Button
import asyncio
import logging

import dumb_waiter


class LiftSetupError(Exception):
    pass

class OutPin:
    def __init__(self, pin, initial_value=False):
        self.dev = OutputDevice(pin=pin, initial_value=initial_value)

    def __call__(self, value):
        self.dev.value = value

class InPin:
    def __init__(self, pin):
        self.dev = DigitalInputDevice(pin=pin, bounce_time=0.01)

    def __call__(self):
        return self.dev.value

class InPinFalling(InPin):
    '''A class that has a call back to be called then the input has a falling edge. It remembers that state.
    The "pressed" property will return True once after a falling edge'''

    def __init__(self, pin):
        self.dev = Button(pin=pin, bounce_time=0.01)
        self._activated = False
        self.dev.when_deactivated = self.pressed_cb

    def pressed_cb(self):
        self._activated = True

    @property
    def pressed(self):
        if self._activated:
            self._activated = False
            return True
        return False

def main():

    logging.basicConfig(level=logging.INFO)

    pinO_lift_up_button = OutPin("BOARD7")
    pinO_lift_down_button = OutPin("BOARD11")
    
    # TODO: Rename "lock_doors" to lock upper door. Add a lock button door.
    lock_doors = OutPin("BOARD31")


    comms = dumb_waiter.Comms('localhost')
    OutputFactory = dumb_waiter.io.OutputFactory(comms=comms)
    InputFactory = dumb_waiter.io.InputFactory(comms=comms)

    
    # TODO: Do I need all these call back functions? Or can I just past the bound methods?
    pinI_call_pb = InPinFalling("BOARD13")
    def call_pressed():
        return pinI_call_pb.pressed

    pinI_lower_limit = InPin("BOARD15")
    def lower_limit_cb():
        return pinI_lower_limit()

    pinI_upper_limit = InPin("BOARD16")
    def upper_limit_cb():
        return pinI_upper_limit()

    pinI_door_closed_level1 = InPin("BOARD18")
    def door_closed_level1_cb():
        return pinI_door_closed_level1()

    pinI_door_closed_ground = InPin("BOARD22")
    def door_closed_ground_cb():
        return pinI_door_closed_ground()

    pinI_estop = InPin("BOARD29")
    def estop_cb():
        return pinI_estop()

    lift = dumb_waiter.lift(
        raise_lift = OutputFactory(name='Raise', callback=pinO_lift_up_button),
        lower_lift = OutputFactory(name='Lower', callback=pinO_lift_down_button),
        lock_doors = OutputFactory(name='LockDoors', callback=lock_doors),
        call_button = InputFactory(name='Call Button', callback=call_pressed),
        limit_top = InputFactory(name='Limit Top', callback=upper_limit_cb),
        limit_bottom = InputFactory(name='Limit Bottom', callback=lower_limit_cb),
        door_closed_level1 = InputFactory(name='Door Closed Level1', callback=door_closed_level1_cb),
        door_closed_ground = InputFactory(name='Door Closed Ground', callback=door_closed_ground_cb),
        estop = InputFactory(name='EStop', callback=estop_cb),
    )

    asyncio.run(lift.main())



if __name__ == '__main__':
    main()