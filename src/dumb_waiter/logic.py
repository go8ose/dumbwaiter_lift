import asyncio
import logging
import time
logger = logging.getLogger(__name__)

from .io import Input,Output
from .util import run_later

LIFT_UP = 1
LIFT_DOWN = 2
LIFT_STOP = 0

SLEEP_TIME=0.1
SAFETY_TIME=23

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


        start_time = time.time()
        while True:

            # log a message once every so often
            if self.loop_count % (15*60 / SLEEP_TIME) == 1:
                logger.info(f"Lift logic still running, for {(time.time() - start_time)/60:0.2} minutes")

            self.loop_count += 1

            # For each time we loop around we will assume we will not be making
            # a change to the current lift direction
            send_lift = None

            if self.estop.value:
                if self.motor_state != LIFT_STOP:
                    self.stop_lift(reason="ESTOP activated")
                await asyncio.sleep(SLEEP_TIME)
                continue
            
            # If a limit has been hit, and it's a limit we might hit if we are
            # going in that direction, stop the motor.
            if (self.limit_top.value and self.motor_state == LIFT_UP): 
                self.stop_lift(reason="Top limit being reached")
                await asyncio.sleep(SLEEP_TIME)
                continue

            if (self.limit_bottom.value and self.motor_state == LIFT_DOWN):

                self.stop_lift(reason="Bottom limit being reached")
                await asyncio.sleep(SLEEP_TIME)
                continue

            # Work out if it is safe to move the lift
            safe_to_move = self.door_closed_level1.value \
                and self.door_closed_ground.value \
                and not self.estop.value
            
            if not safe_to_move and self.motor_state != LIFT_STOP:
                self.stop_lift(reason="It's not safe!")
                await asyncio.sleep(SLEEP_TIME)
                continue

            # Check if the calll button was pressed. This code assumes that the value property only
            # returns true once for each time the button is pressed.
            call_pressed = self.call_button.value

            # Every second log a debug message about current state of IO inputs
            if self.loop_count % (1 / SLEEP_TIME) == 0:
                logging.debug(f"Is it safe to move? {safe_to_move}. Door level 1 {self.door_closed_level1.value} Door ground {self.door_closed_ground.value} Estop {self.estop.value}")
                logging.debug(f"Lower limit {self.limit_bottom.value} top limit {self.limit_top.value}")

            if call_pressed and not safe_to_move:
                logger.info("Call pressed when not safe to move")
            elif call_pressed:
                # If the motor is running, the user probably wants us to stop the motor
                if self.motor_state != LIFT_STOP:
                    self.stop_lift(reason="Call pressed")
                    await asyncio.sleep(SLEEP_TIME)
                    continue

                else:
                    if self.limit_bottom.value and self.limit_top.value:
                        # oh no. This likely means a limit is stuck.
                        # TODO: emit a warning.
                        logger.warning("Both limits are active, likely one is stuck")
                    # If on a limit, go away from it.
                    elif self.limit_bottom.value:
                        send_lift = LIFT_UP
                        logger.info("Call pressed to send lift up")
                    elif self.limit_top.value:
                        send_lift = LIFT_DOWN
                        logger.info("Call pressed to send lift down")
                    # If we don't know where the lift is, send it down.
                    else:
                        send_lift = LIFT_DOWN
                        logger.info("Call pressed. Don't know where lift is, send down.")

            if send_lift:
                self.motor_state = send_lift
                self.move_lift(send_lift)

            await asyncio.sleep(SLEEP_TIME)


    def stop_lift(self, reason=''):
        if reason != '':
            logger.info(f"Stop the lift: {reason}")
        else:
            logger.info("Stop the lift, probably because of safety timer")

        if self.motor_state != LIFT_STOP:
            self.motor_state = LIFT_STOP
            self.raise_lift.off()
            self.lower_lift.off()
            if self.safety_timer_stop:
                self.safety_timer_stop.cancel()
                self.safety_timer_stop = None
            asyncio.create_task(run_later(delay=0.2,callback=self.lock_doors.off))

    def move_lift(self, direction):
        asyncio.create_task(run_later(delay=0.2,callback=self.lock_doors.on))
        if direction == LIFT_UP:
            logger.info("Raise the lift")
            self.lower_lift.off()
            asyncio.create_task(run_later(delay=0.8,callback=self.raise_lift.on))
        if direction == LIFT_DOWN:
            logger.info("Lower the lift")
            self.raise_lift.off()
            asyncio.create_task(run_later(delay=0.8,callback=self.lower_lift.on))
        
        # Setup a safety timer to stop the lift if it takes to long before a limit stops it.
        self.safety_timer_stop = asyncio.create_task(run_later(delay=SAFETY_TIME,callback=self.stop_lift))
