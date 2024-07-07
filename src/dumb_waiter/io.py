# The io.py library is meant to bridge between the code that will be
# actually interacting with the hardware (and using micropython library
# calls) and the logic for the lift. In the lift logic I want to isolate 
# it from all the hardware calls itself. This is for two reasons
#  1) while developing I'm using normal python, so I don't want to depend on
#  micropython to work out the logic
#  2) I want to be able to test the logic.
# This should also be convenient, as it will give me a way to "hook" in for
# generating mqtt messages on IO changes.



# I would like to use dataclasses for these. Unfortunately I can't use a
# dataclass, as micropython doesn't support them :(


# Inputs in micropython have IRQ handlers. When an input pin changes state the
# IRQ is called. So my class needs a IRQ handler that records the new state
# of the input pin.
class Input:
    '''An Input object is an input on the lift. When the code that wraps the 
    lift works out a change in state of an input it will call that Input to set
    the new state'''
    def __init__(self, name, default, comms):
        self.name = name
        self.value = default

    # This __call__ is used in an IRQ handler, hence it needs to return as quickly
    # as possible, without doing any assignments.
    # As per
    # https://docs.micropython.org/en/latest/reference/isr_rules.html#isr-rules
    # I need to keep in mind the following points:
    #  - Keep the code as short and simple as possible.
    #  - Avoid memory allocation: no appending to lists or insertion into
    #  dictionaries, no floating point.
    #  - Consider using micropython.schedule to work around the above
    #  constraint.
    #  - Where an ISR returns multiple bytes use a pre-allocated bytearray.
    #  If multiple integers are to be shared between an ISR and the main
    #  program consider an array (array.array).
    #  - Where data is shared between the main program and an ISR, consider
    #  disabling interrupts prior to accessing the data in the main program
    #  and re-enabling them immediately afterwards.
    #  - Allocate an emergency exception buffer.
    def __call__(self, pin):
        self.value = pin.value

    def __str__(self):
        return f"Input: {self.name}={self.value}"
    def __repr__(self):
        return f'<dumb_waiter.lift_input {self.name}={self.value}'

class InputButton(Input):
    '''The InputButton is for when you have a Pin where you want to have the
    interrupt fire on a edge. In that case the pin.value will be the value after
    the edge, which might not be interesting. Instead you just want to record
    that the interrupt has fired. In this case we set an our value to True. We
    expect that the lift logic will clear that once it's inspected it.'''

    def __init__(self, name, default, comms):
        super().__init__(name=name, default=default, comms=comms)


    def __call__(self, pin):
        self.value=True


class InputFactory:
    def __init__(self, comms):
        self.comms = comms
    def __call__(self, name, default, kind='Value'):
        if kind == 'Button':
            return InputButton(name=name, default=False, comms=self.comms)
        else:
            return Input(name=name, default=default, comms=self.comms)

# The lift needs to adjust a machine pin, but as mentioned above, I don't want to have the lift
# know about micropython pins directly. And I want a place to "hook" for mqtt calls. Hence
# this output needs to be provided with a callback so the main program can "tell" it how
# to get pins set.
class Output:
    '''An Output object is for the lift to have a way to communicate to
    an output pin. I'm trying to make the logic agnostic to where it is running.
    Hence when the logic wants to drive an output, we actually call the callback.
    '''
    def __init__(self, name, callback=lambda x: None, comms=None):
        self.name = name
        self.callback = callback

    def on(self):
        self.callback(1)

    def off(self):
        self.callback(0)


class OutputFactory:
    def __init__(self, comms):
        self.comms = comms
    def __call__(self, name, callback):
        return Output(name=name, callback=callback, comms=self.comms)