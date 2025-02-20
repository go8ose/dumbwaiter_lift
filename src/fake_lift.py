import asyncio
import sys
import logging

from dumb_waiter.logic import LiftLogicMachine, LiftLogicModel
from dumb_waiter.io import Input, Output

async def main():

    logging.basicConfig(level=logging.DEBUG)
    inputs = {
        'lower_limit': FakeDigitalInput(),
        'upper_limit': FakeDigitalInput(),
        'estop1': FakeDigitalInput(),
        'estop2': FakeDigitalInput(),
        'upper_door_closed': FakeDigitalInput(),
        'lower_door_closed': FakeDigitalInput(),
    }
    outputs = {
        'raise': FakeDigitalOutput('raise'),
        'lower': FakeDigitalOutput('lower'),
        'lock_door_top': FakeDigitalOutput('lock_door_top'),
        'lock_door_bottom': FakeDigitalOutput('lock_door_bottom'),
    }

    model=LiftLogicModel(
        estop1=inputs['estop1'], 
        estop2=inputs['estop2'], 
        lower_limit=inputs['lower_limit'], 
        upper_limit=inputs['upper_limit'], 
        upper_door_closed=inputs['upper_door_closed'], 
        lower_door_closed=inputs['lower_door_closed'],
        raise_lift=outputs['raise'],
        lower_lift=outputs['lower'],
        lock_door_top=outputs['lock_door_top'],
        lock_door_bottom=outputs['lock_door_bottom'],
        safety_time=23,
        )
    llm = LiftLogicMachine(model)
    #inputs['estop'].rising_edge_callback = lambda: llm.estop_pressed()
    inputs['estop1'].rising_edge_callback = llm.estop_pressed
    inputs['estop2'].rising_edge_callback = llm.estop_pressed
    inputs['lower_limit'].rising_edge_callback = lambda: llm.stop_lowering()
    inputs['upper_limit'].rising_edge_callback = lambda: llm.stop_rising()
    inputs['upper_door_closed'].falling_edge_callback = lambda: llm.door_opens()
    inputs['lower_door_closed'].falling_edge_callback = lambda: llm.door_opens()
    inputs['upper_door_closed'].on()
    inputs['lower_door_closed'].on()
    llm.initialise()


    while True:
        input_s = ' '.join(f'{s}={v.var}' for s,v in inputs.items())
        print(f"Inputs: {input_s}")
        answer = await ainput('Next command. Either "(t/h/on/off) Input" or "(c/q)": \n')
        try:
            command, input_ = answer.split()
        except ValueError:
            command = answer
            input_ = None

        if command == 'h':
            print("Commands are 't' for toggle, 'h' for this help, 'on' to turn an input on and 'off' to turn an input off. Or if you do 'c' it will trigger the call event. If you do 'q' it will quit")
            continue

        if command =='q':
            break

        if command =='c':
            llm.call()
            continue

        if input_ is None:
            print("input needed")
            continue

        if command == 't':
            inputs[input_].toggle()
            continue

        if command == 'on':
            inputs[input_].on()
            continue

        if command == 'off':
            inputs[input_].off()
            continue

async def ainput(string: str) -> str:
    await asyncio.to_thread(sys.stdout.write, f'{string} ')
    return (await asyncio.to_thread(sys.stdin.readline)).rstrip('\n')

class FakeDigitalInput(Input):
    def __init__(self, initial=False):
        self.var = initial

    def __call__(self):
        return self.var

    
    # I need a wait to change the fake input, hence below methods.
    def toggle(self):
        old_var = self.var
        self.var = not self.var
        if self.falling_edge_callback is not None:
            if old_var == True:
                self.falling_edge_callback()
        if self.rising_edge_callback is not None:
            if old_var == False:
                self.rising_edge_callback()

    def on(self):
        if self.var == True:
            return
        self.var = True
        if self.rising_edge_callback is not None:
            self.rising_edge_callback()

    def off(self):
        if self.var == False:
            return
        self.var = False
        if self.falling_edge_callback is not None:
            self.falling_edge_callback()

class FakeDigitalOutput(Output):
    def __init__(self, name):
        self.name = name
        self.var = False

    @property
    def value(self):
        return self.var

    def on(self):
        self.var = True

    def off(self):
        self.var = False


if __name__ == "__main__":
    asyncio.run(main())
