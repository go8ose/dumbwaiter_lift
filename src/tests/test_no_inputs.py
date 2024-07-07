from unittest import IsolatedAsyncioTestCase, TestCase
import asyncio
import dumb_waiter
from dumb_waiter.io import OutputFactory, InputFactory

output = False


class TestSetup(IsolatedAsyncioTestCase):

    def output_fired(self):
        output = True

    def setUp(self):
        ofact = OutputFactory(comms=None)
        ifact = InputFactory(comms=None)
        lift = dumb_waiter.lift(
            raise_lift=ofact(name='Raise Lift', callback=self.output_fired),
            lower_lift=ofact(name='Lower Lift', callback=self.output_fired),
            lock_doors=ofact(name='Lock Doors', callback=self.output_fired),
            call_button=ifact(name='Call Button', default=False, kind='Button'),
            limit_top=ifact(name='Limit Top', default=None),
            limit_bottom=ifact(name='Limit Bottom', default=None),
            door_closed_level1=ifact(name='Door Closed Level1', default=None),
            door_closed_ground=ifact(name='Door Closed Ground', default=None),
            estop=ifact(name='EStop', default=None),
        )
        self.lift = lift

class TestNoInput(TestSetup):

    async def test_no_input_no_output(self):
        '''Check that if there is no input, there is no movement. Also check the
        lift logic runs a suitable amount of times'''
        asyncio.create_task(self.lift.main())
        await asyncio.sleep(1)
        self.assertEqual(output,False)
        self.assertGreaterEqual(self.lift.loop_count,9)



if __name__ == '__main__':
    unittest.main()
