import logging
import asyncio
import zmq
import zmq.asyncio
from matrix_io.proto.malos.v1 import driver_pb2
from matrix_io.proto.malos.v1 import comm_pb2
from matrix_io.proto.malos.v1 import sense_pb2
from matrix_io.proto.malos.v1 import io_pb2

_LOGGER = logging.getLogger(__name__)
ctx = zmq.asyncio.Context.instance()

class Matrix():
    @classmethod
    async def create(cls, config):
        self = cls()
        self.config = config
        loop = asyncio.get_event_loop()

        _LOGGER.warning("Host: %s", 'tcp://{0}'.format(config.host))
 
        sendConfig = await receive_push_fn(config.host, config.components[0].port)
        
        # Create a new driver config
        driver_config_proto = driver_pb2.DriverConfig()
        driver_config_proto.delay_between_updates = 2.0
        driver_config_proto.timeout_after_last_ping = 6.0
        driver_config_proto.humidity.current_temperature = 23
        sendConfig(driver_config_proto)

        loop.create_task(ping_component(config.host, config.components[0].port + 1))

        loop.create_task(register_callback(config.host, config.components[0].port + 2, humidity_error_callback))
        loop.create_task(register_callback(config.host, config.components[0].port + 3, humidity_data_callback))

        return self

def humidity_data_callback(data):
    """Capture any data and print them to stdout"""
    humidity_info = sense_pb2.Humidity().FromString(data)
    print('data: {0}'.format(humidity_info))


def humidity_error_callback(error):
    """Capture any errors and send them to stdout"""
    print('error: {0}'.format(error.decode('utf-8')))

async def ping_component(host, port, ping = 5):
    s = ctx.socket(zmq.PUSH)
    s.connect('tcp://{0}:{1}'.format(host, port))
    # Start a forever loop
    while True:
        # Ping with empty string to let the drive know we're still listening
        s.send_string('')
        # Delay between next ping
        await asyncio.sleep(ping)

async def receive_push_fn(host, port):
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
    
