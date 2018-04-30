from matrix.components.component import Component
from matrix_io.proto.malos.v1 import driver_pb2
from matrix_io.proto.malos.v1 import sense_pb2

class Humidity(Component):
    def __init__(self, config, push_fn):
        Component.__init__(self, config, push_fn)
        self._configuration_proto = construct_config_proto()
        self._data_callback = humidity_data_callback
        self._needs_keep_alive = True

def construct_config_proto():
    driver_config_proto = driver_pb2.DriverConfig()
    driver_config_proto.delay_between_updates = 2.0
    driver_config_proto.timeout_after_last_ping = 6.0
    driver_config_proto.humidity.current_temperature = 23
    return driver_config_proto

def humidity_data_callback(data):
    """Capture any data and print them to stdout"""
    humidity_info = sense_pb2.Humidity().FromString(data)
    print('data: {0}'.format(humidity_info))
