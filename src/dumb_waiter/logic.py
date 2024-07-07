import asyncio

from .io import Input,Output
from .util import run_later

LIFT_UP = 1
LIFT_DOWN = 2
LIFT_STOP = 0

SLEEP_TIME=0.1
SAFETY_TIME=10000

class Logic:

    def __init__(self,
        raise_lift: Output,
        lower_lift: Output,
        lock_doors: Output,
        call_button: Input,
        limit_top: Input,
        limit_bottom: Input,
        door_closed_level1: Input,
        door_closed_ground: Input,
        estop: Input,
    ):
        self.raise_lift = raise_lift
        self.lower_lift = lower_lift
        self.lock_doors = lock_doors
        self.call_button = call_button
        self.limit_top = limit_top
        self.limit_bottom = limit_bottom
        self.door_closed_level1 = door_closed_level1
        self.door_closed_ground = door_closed_ground
        self.estop = estop


        # Some internal variables
        self.motor_state = LIFT_STOP
        self.safety_timer_stop = None

        self.loop_count = 0


    async def main(self):
        self.motor_state = LIFT_STOP


        while True:
            self.loop_count += 1

            # For each time we loop around we will assume we will not be making
            # a change to the current lift direction
            send_lift = None

            if self.estop.value:
                self.stop_lift()
                await asyncio.sleep(SLEEP_TIME)
                continue
            
            # If a limit has been hit, and it's a limit we might hit if we are
            # going in that direction, stop the motor.
            if (self.limit_top.value and self.motor_state == LIFT_UP) \
                or (self.limit_bottom.value and self.motor_state == LIFT_DOWN):

                self.stop_lift()
                await asyncio.sleep(SLEEP_TIME)
                continue

            # Work out if it is safe to move the lift
            safe_to_move = self.door_closed_level1.value \
                and self.door_closed_ground.value \
                and not self.estop.value
            

            # Clear the call variable if it is not safe to move.
            if self.call_button.value and not safe_to_move:
                self.call_button.value = False

            # TODO: Work out what to do in io.py to support a falling edge IRQ call.
            # If the button was pressed unset our call_button variable, and decided what to do.
            if self.call_button.value and safe_to_move:
                self.call_button.value = False

                # If the motor is running, the user probably wants us to stop the motor
                if self.motor_state != LIFT_STOP:
                    send_lift = LIFT_STOP

                else:
                    # If on a limit, go away from it.
                    if self.limit_bottom.value:
                        send_lift = LIFT_UP
                    elif self.limit_top.value:
                        send_lift = LIFT_DOWN
                    
                    elif self.limit_bottom.value and self.limit_top.value:
                        # oh no. This likely means a limit is stuck.
                        # TODO: emit a warning.
                        pass
                    
                    # If we don't know where the lift is, send it down.
                    else:
                        send_lift = LIFT_DOWN

            if send_lift:
                self.motor_state = send_lift
                self.move_lift(send_lift)

            await asyncio.sleep(SLEEP_TIME)


    def stop_lift(self):
        if self.motor_state != LIFT_STOP:
            self.motor_state = LIFT_STOP
            self.raise_lift.off()
            self.lower_lift.off()
            if self.safety_timer_stop:
                self.safety_timer_stop.deinit()
                self.safety_timer_stop = None

    def move_lift(self, direction):
        asyncio.create_task(run_later(delay=0.2,callback=self.lock_doors.on))
        if direction == LIFT_UP:
            self.lower_lift.off()
            asyncio.create_task(run_later(delay=0.8,callback=self.raise_lift.on))
        if direction == LIFT_DOWN:
            self.raise_lift.off()
            asyncio.create_task(run_later(delay=0.8,callback=self.lower_lift.on))
        
        # Setup a safety timer to stop the lift if it takes to long before a limit stops it.
        self.safety_timer_stop = asyncio.create_task(run_later(delay=SAFETY_TIME,callback=self.stop_lift))
