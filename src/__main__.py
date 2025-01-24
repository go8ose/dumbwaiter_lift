from gpiozero import DigitalInputDevice, OutputDevice
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
        self.dev = DigitalInputDevice(pin=pin, pull_up=False)

    def __call__(self):
        return self.dev.value

#class InPinEdge(InPin):
#    def __init__(self, channel, edge, callback):
#        if edge not in (GPIO.RISING, GPIO.FALLING, GPIO.BOTH):
#            raise LiftSetupError
#        self.channel = channel
#        GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
#        GPIO.add_event_detect(channel, edge, callback=callback, bouncetime=50)

def main():

    logging.basicConfig()

    pinO_lift_up_button = OutPin("BOARD7")
    pinO_lift_down_button = OutPin("BOARD11")
    
    # TODO: Rename "lock_doors" to lock upper door. Add a lock button door.
    lock_doors = OutPin("BOARD31")


    # Or I could either have a lift class that does take arguments for all the
    # I/O.
    comms = dumb_waiter.Comms('localhost')
    OutputFactory = dumb_waiter.io.OutputFactory(comms=comms)
    InputFactory = dumb_waiter.io.InputFactory(comms=comms)

    pinI_call_pb = InPin("BOARD13")
    def call_pressed():
        return pinI_call_pb()

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