class Config():
    def __init__(self, host, components):
        self.host = host
        self.components = components

class ComponentConfig():
    def __init__(self, name, port): 
        self.name = name
        self.port = port