#from typing import Protocol, Callable, Optional
from typing import Callable, Optional
from abc import ABC, abstractmethod

class Input(ABC):
    '''Each input needs to be able to fire on edges (though for some, like door closed, we don’t 
    trigger a state transition), and the state machine needs to be able to check each inputs current 
    value.'''

    falling_edge_callback: Optional[Callable] = None
    rising_edge_callback: Optional[Callable] = None

    @abstractmethod
    def __call__(self) -> bool:
        '''Return the current value of the input'''
        ...

class Output(ABC):
    '''An Output object is for the lift to have a way to communicate to
    an output pin. I'm trying to make the logic agnostic to where it is running.
    Hence when the logic wants to drive an output, we actually call the callback.
    '''

    @property
    @abstractmethod
    def value(self) -> bool:
        '''Get the current value of the output'''
        ...

    @abstractmethod
    def on(self) -> None:
        '''Turn the output on'''
        ...

    @abstractmethod
    def off(self) -> None:
        '''Turn the output off'''
        ...