from unittest import IsolatedAsyncioTestCase
import asyncio
from dataclasses import dataclass

import dumb_waiter
from dumb_waiter.io import OutputFactory, InputFactory

output = False

@dataclass
class FakePin:
    value: int

class TestDoorsOpen(IsolatedAsyncioTestCase):
    '''i.e. the estop is showing it's off, but the doors are not shut'''

    def output_fired(self):
        output = True

    def setUp(self):
        ofact = OutputFactory(comms=None)
        ifact = InputFactory(comms=None)
        lift = dumb_waiter.lift(
            raise_lift=ofact(name='Raise Lift', callback=self.output_fired),
            lower_lift=ofact(name='Lower Lift', callback=self.output_fired),
            lock_doors=ofact(name='Lock Doors', callback=self.output_fired),
            call_button=ifact(name='Call Button', default=FakePin(False), kind='Button'),
            limit_top=ifact(name='Limit Top', default=None),
            limit_bottom=ifact(name='Limit Bottom', default=None),
            door_closed_level1=ifact(name='Door Closed Level1', default=None),
            door_closed_ground=ifact(name='Door Closed Ground', default=None),
            estop=ifact(name='EStop', default=None),
        )
        self.lift = lift



    async def test_no_move_while_doors_open(self):
        pb=FakePin(value=True)
        estop=FakePin(value=True)
        asyncio.create_task(self.lift.main())
        self.lift.estop(estop)
        await asyncio.sleep(1)
        self.lift.call_button(pb)
        await asyncio.sleep(1)
        self.assertEqual(output,False)


if __name__ == '__main__':
    unittest.main()
