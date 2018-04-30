import logging
import asyncio
import zmq
import zmq.asyncio
from matrix_io.proto.malos.v1 import driver_pb2
from matrix_io.proto.malos.v1 import comm_pb2
from matrix_io.proto.malos.v1 import sense_pb2
from matrix_io.proto.malos.v1 import io_pb2

from matrix.components.component import Component

_LOGGER = logging.getLogger(__name__)
ctx = zmq.asyncio.Context.instance()

class Matrix():
    @classmethod
    async def create(cls, config):
        self = cls()
        self.config = config
        self.components = []
        loop = asyncio.get_event_loop()

        _LOGGER.warning("Host: %s", 'tcp://{0}'.format(config.host))

        self.components = [Component.create(c, await get_push_fn(config.host, c.port)) for c in config.components]
 
        for c in self.components:
            c.push(c.configuration_proto)

            if c.needs_keep_alive:
                loop.create_task(ping_component(config.host, c.port + 1))

            loop.create_task(register_callback(config.host, c.port + 2, c.error_callback))

            if c.data_callback is not None:
                loop.create_task(register_callback(config.host, c.port + 3, c.data_callback))

        return self

async def ping_component(host, port, ping = 5):
    s = ctx.socket(zmq.PUSH)
    s.connect('tcp://{0}:{1}'.format(host, port))
    # Start a forever loop
    while True:
        # Ping with empty string to let the drive know we're still listening
        s.send_string('')
        # Delay between next ping
        await asyncio.sleep(ping)

async def get_push_fn(host, port):
    s = ctx.socket(zmq.PUSH)
    s.connect('tcp://{0}:{1}'.format(host, port))
    def sendConfig(proto):
        s.send(proto.SerializeToString())
    return sendConfig

async def register_callback(host, port, callback):
    s = ctx.socket(zmq.SUB)
    s.connect('tcp://{0}:{1}'.format(host, port))
    s.subscribe(b'')
    while True:
        msg = await s.recv()
        callback(msg)
    s.close()
    
