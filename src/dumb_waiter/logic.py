import logging
from dataclasses import dataclass
from typing import Optional

from asyncio import Task, create_task

from statemachine import State
from statemachine import StateMachine

from .io import Input, Output
from .util import run_later

logger = logging.getLogger(__name__)


@dataclass
class LiftLogicModel:
    estop1: Input 
    estop2: Input 
    lower_limit: Input
    upper_limit: Input
    upper_door_closed: Input
    lower_door_closed: Input

    raise_lift: Output
    lower_lift: Output
    lock_door_top: Output
    lock_door_bottom: Output

    safety_time: int = 23
    
    def __post_init__(self):
        self.safety_timer=None


class LiftLogicMachine(StateMachine):
    "A simple lift, that moves between two floors, ground floor and level1."

    # Define the states
    turned_on = State(initial=True, enter="lock_door", exit="stop")
    stopped = State()
    stopped_at_top = State(enter="unlock_door", exit="lock_door")
    stopped_at_bottom = State()
    rising = State(enter="start_rising", exit="stop")
    lowering = State(enter="start_lowering", exit="stop")

    # Define the transitions
    initialise = turned_on.to(stopped)
    # call, i.e. the call button was pushed.
    call = stopped.to.itself(cond="not safe_to_move", after='log_unsafe_to_move') \
        | stopped.to(lowering, cond="safe_to_move") \
        | stopped_at_top.to(lowering, cond="is_top_limit_active and safe_to_move") \
        | stopped_at_bottom.to(rising, cond="is_bottom_limit_active and safe_to_move") \
        | lowering.to(stopped) \
        | rising.to(stopped)
    # stop_rising, i.e. the upper limit was pressed
    stop_rising = rising.to(stopped_at_top, cond="is_top_limit_active")
    # stop_lowering, i.e. the lower limit was pressed
    stop_lowering = lowering.to(stopped_at_bottom, cond="is_bottom_limit_active")
    door_opens = rising.to(stopped) \
        | lowering.to(stopped) \
        | stopped.to.itself(internal=True) \
        | stopped_at_top.to.itself(internal=True) \
        | stopped_at_bottom.to.itself(internal=True)
    estop_pressed = rising.to(stopped) \
        | lowering.to(stopped) \
        | stopped.to.itself(internal=True) \
        | stopped_at_top.to.itself(internal=True) \
        | stopped_at_bottom.to.itself(internal=True)
    safety_timeout = rising.to(stopped) \
        | lowering.to(stopped)

    

    def on_enter_state(self, event, state):
        logging.info(f"Entering '{state.id}' state from '{event}' event.")

    def is_top_limit_active(self):
        return self.model.upper_limit()

    def is_bottom_limit_active(self):
        return self.model.lower_limit()

    def safe_to_move(self):
        if self.model.estop1() == True:
            return False
        if self.model.estop2() == True:
            return False
        if self.model.lower_door_closed() == False:
            return False
        if self.model.upper_door_closed() == False:
            return False
        return True

    def log_unsafe_to_move(self):
        logger.info(f"Not safe to move. Estops=[{self.model.estop1()} {self.model.estop2()}] lower_door_closed={self.model.lower_door_closed()}, upper_door_closed={self.model.upper_door_closed()}")

    def start_rising(self):
        self.model.safety_timer = create_task(run_later(delay=self.model.safety_time, callback=self.safety_timeout))
        self.model.raise_lift.on()

    def start_lowering(self):
        self.model.safety_timer = create_task(run_later(delay=self.model.safety_time,callback=self.safety_timeout))
        self.model.lower_lift.on()

    def stop(self):
        if self.model.safety_timer is not None:
            self.model.safety_timer.cancel()
            self.model.safety_timer = None
        self.model.lower_lift.off()
        self.model.raise_lift.off()

    def lock_door(self):
        logger.info("Lock the door")
        self.model.lock_door_top.on()
        self.model.lock_door_bottom.on()

    def unlock_door(self):
        logger.info("Unlock the door")
        self.model.lock_door_top.off()
        self.model.lock_door_bottom.off()


