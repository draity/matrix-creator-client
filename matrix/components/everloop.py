from matrix.components.component import Component
from matrix_io.proto.malos.v1 import driver_pb2
from matrix_io.proto.malos.v1 import io_pb2

import math
import logging

_LOGGER = logging.getLogger(__name__)

class Everloop(Component):
    def __init__(self, config, push_fn):
        Component.__init__(self, config, push_fn)
        self.led_count = 35
        self._configuration_proto = self.construct_config_proto()
        self._needs_keep_alive = False

    def construct_config_proto(self):
        return _create_everloop_color_config(
            _create_everloop_colors(
                self.led_count, [0,0,0,0]
            )
        )

    def set_uniform_intensity(self, intensity):
        self._set_colors([0, 0, 0, intensity])

    def set_uniform_color(self, r, g, b, w):
        self._set_colors([r, g, b, w])

    def set_multiple_colors(self, *color_arrays):
        self._set_colors(color_arrays)

    def _set_colors(self, *color_arrays):
        colors = _create_everloop_colors(self.led_count, *color_arrays)
        config = _create_everloop_color_config(colors)
        self.push(config)

def _create_everloop_colors(led_count, *led_colors_array):
    if len(led_colors_array) > led_count:
        _LOGGER.warn(
            "To many led colors given for everloop. Given: {}. Number of leds: {}".format(
                len(led_colors_array), 
                led_count
            )
        )
    
    # initialize an empty list for the "image" or LEDS
    image = []
    
    for led_idx in range(led_count):
        color_count = len(led_colors_array)
        color_idx = math.floor(((led_idx / color_count) / (led_count / color_count)) * color_count)
        led_color = led_colors_array[color_idx]

        ledValue = io_pb2.LedValue()
        ledValue.red = led_color[0]
        ledValue.green = led_color[1]
        ledValue.blue = led_color[2]
        ledValue.white = led_color[3]
        image.append(ledValue)

    return image

def _create_everloop_color_config(led_array):
    """Set everloop colors"""
    config = driver_pb2.DriverConfig()

    # add the led colors array to the config driver
    config.image.led.extend(led_array)

    return config
