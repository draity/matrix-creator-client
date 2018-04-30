import importlib

class Component():
    def __init__(self, config, push_fn):
        self.name = config.name
        self.port = config.port
        self.push = push_fn
        self._configuration_proto = {}
        self._error_callback = lambda error: print('error: {0}'.format(error.decode('utf-8')))
        self._data_callback = None #lambda data: print('data: {0}'.format(data))
        self._needs_keep_alive = False
        
    def get_configuration_proto(self):
        return self._configuration_proto
        
    def get_error_callback(self):
        return self._error_callback
    
    def get_data_callback(self):
        return self._data_callback

    def get_needs_keep_alives(self):
        return self._needs_keep_alive

    configuration_proto = property(get_configuration_proto)
    error_callback = property(get_error_callback)
    data_callback = property(get_data_callback)
    needs_keep_alive = property(get_needs_keep_alives)

    @classmethod
    def create(cls, config, push_fn):
        return get_component(config, push_fn)
    
def get_component(config, push_fn):
    module = importlib.import_module('matrix.components.{}'.format(config.name))
    my_class = getattr(module, config.name.title())
    my_instance = my_class(config, push_fn)
    return my_instance



