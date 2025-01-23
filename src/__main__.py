try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO! You may need to pip install it, or you may need superuser privileges.  You can achieve this by using 'sudo' to run your script")

import asyncio

import dumb_waiter

GPIO.setmode(GPIO.BOARD)

class LiftSetupError(Exception):
    pass

class OutPin:
    def __init__(self, channel, initial_value=GPIO.LOW):
        self.channel = channel
        GPIO.setup(channel, GPIO.OUT, initial=initial_value)

    def __call__(self, value):
        gpio.output(self.channel, value)

class InPin:
    def __init__(self, channel):
        self.channel = channel
        GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def __call__(self):
        return gpio.input(self.channel)

class InPinEdge(InPin):
    def __init__(self, channel, edge, callback):
        if edge not in (GPIO.RISING, GPIO.FALLING, GPIO.BOTH):
            raise LiftSetupError
        self.channel = channel
        GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(channel, edge, callback=callback, bouncetime=50)

def main():

    pinO_lift_up_button = OutPin(7)
    pinO_lift_down_button = OutPin(11)
    
    # TODO: Rename "lock_doors" to lock upper door. Add a lock button door.
    lock_doors = OutPin(31)


    # Or I could either have a lift class that does take arguments for all the
    # I/O.
    comms = dumb_waiter.Comms('localhost')
    OutputFactory = dumb_waiter.io.OutputFactory(comms=comms)
    InputFactory = dumb_waiter.io.InputFactory(comms=comms)

    def call_pressed(channel):
        lift.call_button(True)
    pinI_call_pb = InPinEdge(13, GPIO.FALLING, callback=call_pressed)

    pinI_lower_limit = InPin(15)
    def lower_limit_cb():
        return pinI_lower_limit()

    pinI_upper_limit = InPin(16)
    def upper_limit_cb():
        return pinI_upper_limit()

    pinI_door_closed_level1 = InPin(18)
    def door_closed_level1_cb():
        return pinI_door_closed_level1()

    pinI_door_closed_ground = InPin(22)
    def door_closed_ground_cb():
        return pinI_door_closed_ground()

    pinI_estop = InPin(29)
    def estop_cb():
        return pinI_estop()

    lift = dumb_waiter.lift(
        raise_lift = OutputFactory(name='Raise', callback=pinO_lift_up_button),
        lower_lift = OutputFactory(name='Lower', callback=pinO_lift_down_button),
        lock_doors = OutputFactory(name='LockDoors', callback=lock_doors),
        call_button = InputFactory(name='Call Button', callback='Button'),
        limit_top = InputFactory(name='Limit Top', callback=upper_limit_cb),
        limit_bottom = InputFactory(name='Limit Bottom', callback=lower_limit_cb),
        door_closed_level1 = InputFactory(name='Door Closed Level1', callback=door_closed_level1_cb),
        door_closed_ground = InputFactory(name='Door Closed Ground', callback=door_closed_ground_cb),
        estop = InputFactory(name='EStop', callback=estop_cb),
    )

    asyncio.run(lift.main())



if __name__ == '__main__':
    try:
        main()
    finally:
        GPIO.cleanup()
