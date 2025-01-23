try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO! You may need to pip install it, or you may need superuser privileges.  You can achieve this by using 'sudo' to run your script")


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
        GPIO.setup(channel, GPIO.IN)

    def __call__(self):
        return gpio.input(self.channel)

class InPinEdge(InPin):
    def __init__(self, channel, edge, callback):
        if edge not in (GPIO.RISING, GPIO.FALLING, GPIO.BOTH):
            raise LiftSetupError
        self.channel = channel
        GPIO.setup(channel, GPIO.IN)
        GPIO.add_event_detect(channel, edge, callback=callback, bouncetime=50)

def main():

    pinO_lift_up_button = OutPin(7)
    pinO_lift_down_button = OutPin(11)


    # Or I could either have a lift class that does take arguments for all the
    # I/O.
    comms = dumb_waiter.Comms('localhost')
    OutputFactory = dumb_waiter.io.OutputFactory(comms=comms)
    InputFactory = dumb_waiter.io.InputFactory(comms=comms)
    lift = dump_waiter.lift(
        raise_lift = OutputFactory(name='Raise', callback=pinO_lift_up_button),
        lower_lift = OutputFactory(name='Lower', callback=pinO_lift_down_button),
        lock_doors = OutputFactory(name='LockDoors', callback=lock_doors),
        call_button=InputFactory(name='Call Button', kind='Button'),
        limit_top=InputFactory(name='Limit Top', default=pinI_upper_limit.value),
        limit_bottom=InputFactory(name='Limit Bottom', default=pinI_lower_limit.value),
        door_closed_level1=InputFactory(name='Door Closed Level1', default=pinI_door_closed_level1.value),
        door_closed_ground=InputFactory(name='Door Closed Ground', default=pinI_door_closed_ground.value),
        estop=InputFactory(name='EStop', default=pinI_estop.value),
    )


    pinI_call_pb = InPinEdge(13, GPI.FALLING, handler=call_pressed)
    def call_pressed(channel):
        lift.call_button(True)
    pinI_call_pb.irq(handler=call_pressed, trigger=Pin.IRQ_FALLING)

    pinI_lower_limit = InPin(15)
    def lower_limit_handler(p):
        lift.limit_bottom(p)
    pinI_call_pb.irq(handler=lower_limit_handler)

    pinI_upper_limit = InPin(16)
    def upper_limit_handler(p):
        lift.limit_top(p)
    pinI_upper_limit.irq(handler=upper_limit_handler)

    pinI_door_closed_level1 = InPin(18)
    def door_closed_level1_handler(p):
        lift.door_closed_level1(p)
    pinI_door_closed_level1.irq(handler=door_closed_level1_handler)

    pinI_door_closed_ground = InPin(22)
    def door_closed_ground_handler(p):
        lift.door_closed_ground(p)
    pinI_door_closed_ground.irq(handler=door_closed_level1_handler)


    pinI_estop = InPin(29)
    def estop_handler(p):
        lift.estop(p)
    pinI_estop.irq(handler=door_closed_level1_handler)

    asyncio.run(lift.main())



if __name__ == '__main__':
    try:
        main()
    finally:
        GPIO.cleanup()
