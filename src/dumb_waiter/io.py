

class Input:
    '''An Input object is an input on the lift. When the lift wants to know the
    status of the input, it calls the callback.'''
    def __init__(self, name, callback, comms):
        self.name = name
        self.callback = callback

    @property
    def value(self):
        return self.callback()

    def __str__(self):
        return f"Input: {self.name}={self.value}"
    def __repr__(self):
        return f'<dumb_waiter.lift_input {self.name}={self.value}'

class InputFalling(Input):
    '''An InputFalling is an input on the lift, that remembers if the input transitioned from high to low.
    It allows the caller to clear that state'''

    # TODO: work out how to use @property for both reading and writing. When reading call the callback. When writing...
    # call the callback with an argumment???
    @property
    def value(self):
        return self.callback()

class InputFactory:
    def __init__(self, comms):
        self.comms = comms
    def __call__(self, name, callback):
        return Input(name=name, callback=callback, comms=self.comms)

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