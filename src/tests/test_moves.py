from unittest import IsolatedAsyncioTestCase
from dataclasses import dataclass
import asyncio

import dumb_waiter
from dumb_waiter.io import OutputFactory, InputFactory

@dataclass
class FakePin:
    value: int

class SetupLiftReadyToMove(IsolatedAsyncioTestCase):
    def lift_up(self, value):
        self.move_lift = 'up' if value else 'stopped'

    def lift_down(self, value):
        self.move_lift = 'down' if value else 'stopped'

    def lock_doors(self, value):
        self.doors = 'locked' if value else 'unlocked'

    def setUp(self):
        self.move_lift = None
        self.doors = None
        ofact = OutputFactory(comms=None)
        ifact = InputFactory(comms=None)
        lift = dumb_waiter.lift(
            raise_lift=ofact(name='Raise Lift', callback=self.lift_up),
            lower_lift=ofact(name='Lower Lift', callback=self.lift_down),
            lock_doors=ofact(name='Lock Doors', callback=self.lock_doors),
            call_button=ifact(name='Call Button', default=FakePin(False), kind='Button'),
            limit_top=ifact(name='Limit Top', default=None),
            limit_bottom=ifact(name='Limit Bottom', default=None),
            door_closed_level1=ifact(name='Door Closed Level1', default=None),
            door_closed_ground=ifact(name='Door Closed Ground', default=None),
            estop=ifact(name='EStop', default=None),
        )
        self.lift = lift
        self.lift.estop(FakePin(False))
        self.lift.door_closed_ground(FakePin(True))
        self.lift.door_closed_level1(FakePin(True))

class TestUnknownPosMoveDown(SetupLiftReadyToMove):

    async def test_unknown_position_move_down(self):
        asyncio.create_task(self.lift.main())
        await asyncio.sleep(1)
        self.lift.call_button(None)
        await asyncio.sleep(1)
        self.assertEqual(self.move_lift,'down')




class TestMoveUp(SetupLiftReadyToMove):

    async def test_on_bottom_limit_move_up(self):
        self.lift.limit_bottom(FakePin(True))
        asyncio.create_task(self.lift.main())
        await asyncio.sleep(1)
        self.lift.call_button(None)
        await asyncio.sleep(1)
        self.assertEqual(self.move_lift,'up')

class TestMoveDown(SetupLiftReadyToMove):

    async def test_on_top_limit_move_up(self):
        self.lift.limit_top(FakePin(True))
        asyncio.create_task(self.lift.main())
        await asyncio.sleep(1)
        self.lift.call_button(None)
        await asyncio.sleep(1)
        self.assertEqual(self.move_lift,'down')

class TestMoveTimeOut(SetupLiftReadyToMove):

    async def test_timeout(self):
        test_timeout = 3
        dumb_waiter.logic.SAFETY_TIME = test_timeout
        self.lift.limit_top(FakePin(True))
        asyncio.create_task(self.lift.main())
        await asyncio.sleep(1)
        self.lift.call_button(None)
        await asyncio.sleep(test_timeout*1.1)
        self.assertEqual(self.move_lift,'stopped')

if __name__ == '__main__':
    unittest.main()
