import asyncio
import paho.mqtt.client as paho
from async_paho_mqtt_client import AsyncClient as amqtt


class CommsError(Exception):
    pass

class Comms:
    def __init__(self, connection_str: str):
        self.MQTTS_BROKER = connection_str
        # For some reason, that I don't understand, when I don't pass a client
        # into amqtt, the paho.Client() __init__ method has a callback_api_version parameter
        # that is None. That causes an exception to be thrown.
        # But note that I know that version1 is deprecated.
        paho_client = paho.Client(paho.CallbackAPIVersion.VERSION1)
        client = amqtt(
            client = paho_client,
            host=self.MQTTS_BROKER,
            #port=self.MQTTS_PORT,
            #username=self.MQTTS_USERNAME,
            #password=self.MQTTS_PASSWORD,
            #client_id=self.MQTTS_ID,
            #tls=self.tls,
            #tls_insecure=self.tls_insecure,
            #keepalive=self.keepalive,
            #notify_birth=self.notify_birth,
        )
        self.client = client

    @property
    def connected(self):
        return self.client.connected

    async def connect(self):
        await self.client.start()
        await self.client.wait_started()


    async def send(self, topic: str, payload):
        if not self.connected:
            return

        result = await self.client.publish(topic, payload)
        
        pass

    def stop(self):
        self.client.stop()