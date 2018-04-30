from matrix.components.component import Component
from matrix_io.proto.malos.v1 import driver_pb2
from matrix_io.proto.malos.v1 import comm_pb2

import math
import logging
from enum import Enum
import asyncio
from functools import partial

logging.basicConfig()
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)

class Status(Enum):
    NONE = 1
    RESET_GATEWAY = 2
    CHECK_GATEWAY_ACTIVE = 3
    WAITING_FOR_DEVICES = 4
    WAITING_FOR_NETWORK_STATUS = 5
    NODES_DISCOVERED = 6

class Zigbee(Component):
    status = Status.NONE

    def __init__(self, config, push_fn):
        Component.__init__(self, config, push_fn)
        self._configuration_proto = self.construct_config_proto()
        self._data_callback = self.zigbee_message_callback
        self._needs_keep_alive = True
        self.services = ZigbeeServices(push_fn)
        self.devices = []

    def construct_config_proto(self):
        # Create a new driver config
        driver_config_proto = driver_pb2.DriverConfig()

        driver_config_proto.delay_between_updates = 1.0
        driver_config_proto.timeout_after_last_ping = 1.0

        return driver_config_proto

    def zigbee_message_callback(self, data):
        zig_msg = comm_pb2.ZigBeeMsg.FromString(data)

        _LOGGER.info("Message: %s", zig_msg)
        _LOGGER.info("network mgmt: %s", zig_msg.type == comm_pb2.ZigBeeMsg.ZigBeeCmdType.Value("NETWORK_MGMT"))

        if zig_msg.type == comm_pb2.ZigBeeMsg.ZigBeeCmdType.Value("NETWORK_MGMT"):
            self.handleNetworkManagementMsg(zig_msg)
            
    def handleNetworkManagementMsg(self, zig_msg):
        network_mgmt_cmd_type = zig_msg.network_mgmt_cmd.type
        all_network_mgmt_msg_types = comm_pb2.ZigBeeMsg.NetworkMgmtCmd.NetworkMgmtCmdTypes

        if network_mgmt_cmd_type == all_network_mgmt_msg_types.Value("DISCOVERY_INFO"):
            number_of_added_devices = self.add_zigbee_devices(zig_msg)
            if number_of_added_devices > 0:
                _LOGGER.info('%s nodes discovered and added', number_of_added_devices)
                return Status.NODES_DISCOVERED
            else:
                _LOGGER.warning('No devices found!')
                return Status.NONE
        elif network_mgmt_cmd_type == all_network_mgmt_msg_types.Value("IS_PROXY_ACTIVE"):
            self.handle_proxy_active_msg(zig_msg)
        elif network_mgmt_cmd_type == all_network_mgmt_msg_types.Value("NETWORK_STATUS"):
            self.handle_network_status(zig_msg)

    def handle_proxy_active_msg(self, zig_msg):
        if zig_msg.network_mgmt_cmd.is_proxy_active:
            _LOGGER.info('Gateway connected')
            # self.services.RequestNetworkStatus()
            return Status.WAITING_FOR_NETWORK_STATUS
        elif not status == Status.RESETTING:
            self.services.ResetGateway()
            _LOGGER.info('Waiting 3 sec ....')
            loop = asyncio.get_event_loop()
            loop.create_task(self.services.checkGatewayActive())
            return Status.RESETTING
        else:
            _LOGGER.warning('Gateway reset failed')
            return Status.NONE

    def handle_network_status(self, zig_msg):
        network_status_type = zig_msg.network_mgmt_cmd.network_status.type
        network_status_types = comm_pb2.ZigBeeMsg.NetworkMgmtCmd.NetworkStatus.Status

        _LOGGER.info('Network status type: %s', network_status_type)

        if network_status_type == network_status_types.Value("NO_NETWORK"):
            self.services.CreateNetwork()
            return Status.WAITING_FOR_NETWORK_STATUS

        elif network_status_type == network_status_types.Value("JOINED_NETWORK"):
            # add already connected devices
            self.add_zigbee_devices(zig_msg)
            return Status.WAITING_FOR_DEVICES
        else:
            message = 'JOINING_NETWORK message received' if network_status_type == network_status_types.Value("JOINING_NETWORK") else 'JOINED_NETWORK_NO_PARENT' if network_status_type == network_status_types.Value("JOINED_NETWORK_NO_PARENT") else 'LEAVING_NETWORK message received' if network_status_type ==  network_status_types.Value("LEAVING_NETWORK") else None
            _LOGGER.info(message)

    def add_devices(self, devices):
        for d in devices:
            print("{}, %s", d.name, d.endpoint_index)
            d.toggle()

    def add_zigbee_devices(self, zig_msg):
        nodes_id = []
        for node in zig_msg.network_mgmt_cmd.connected_nodes:
            for endpoint in node.endpoints:
                for cluster in endpoint.clusters:
                    if cluster.cluster_id == 6:
                        nodes_id.append((node.node_id, endpoint.endpoint_index))

        self.devices.extend([ ZigbeeBulb(self.push, x,y) for x, y in nodes_id])
        return len(nodes_id)

class ZigbeeServices(object):

    def __init__(self, push_fn):
        self.push = push_fn

    def ResetGateway(self):
        _LOGGER.info('Reseting the Gateway App')
        _LOGGER.info(_comm_pb2.ZigBeeMsg.ZigBeeCmdType.keys())
        driver_config_proto = driver_pb2.DriverConfig()
        driver_config_proto.zigbee_message.type = comm_pb2.ZigBeeMsg.ZigBeeCmdType.Value("NETWORK_MGMT")
        driver_config_proto.zigbee_message.network_mgmt_cmd.type = comm_pb2.ZigBeeMsg.NetworkMgmtCmd.NetworkMgmtCmdTypes.Value("RESET_PROXY")
        self.push(driver_config_proto)
        return Status.RESET_GATEWAY
        
    def IsGatewayActive(self):
        _LOGGER.info('Checking connection with the Gateway')
        driver_config_proto = driver_pb2.DriverConfig()
        driver_config_proto.zigbee_message.type = comm_pb2.ZigBeeMsg.ZigBeeCmdType.Value("NETWORK_MGMT")
        driver_config_proto.zigbee_message.network_mgmt_cmd.type = comm_pb2.ZigBeeMsg.NetworkMgmtCmd.NetworkMgmtCmdTypes.Value("IS_PROXY_ACTIVE")
        self.push(driver_config_proto)
        return Status.CHECK_GATEWAY_ACTIVE

    def RequestNetworkStatus(self):
        _LOGGER.info('Requesting network status')
        driver_config_proto = driver_pb2.DriverConfig()
        driver_config_proto.zigbee_message.type = comm_pb2.ZigBeeMsg.ZigBeeCmdType.Value("NETWORK_MGMT")
        driver_config_proto.zigbee_message.network_mgmt_cmd.type = comm_pb2.ZigBeeMsg.NetworkMgmtCmd.NetworkMgmtCmdTypes.Value("NETWORK_STATUS")
        driver_config_proto.zigbee_message.network_mgmt_cmd.permit_join_params.time = 60
        self.push(driver_config_proto)
        return Status.WAITING_FOR_NETWORK_STATUS

    def CreateNetwork(self):
        _LOGGER.info('NO NETWORK')
        _LOGGER.info('CREATING A ZigBee Network')

        driver_config_proto = driver_pb2.DriverConfig()
        driver_config_proto.zigbee_message.type = comm_pb2.ZigBeeMsg.ZigBeeCmdType.Value("NETWORK_MGMT")
        driver_config_proto.zigbee_message.network_mgmt_cmd.type = comm_pb2.ZigBeeMsg.NetworkMgmtCmd.NetworkMgmtCmdTypes.Value("CREATE_NWK")
        driver_config_proto.zigbee_message.network_mgmt_cmd.permit_join_params.time = 60
        self.push(driver_config_proto)
        return Status.WAITING_FOR_NETWORK_STATUS

    def PermitJoin(self):
        _LOGGER.info('Permitting join')
        driver_config_proto = driver_pb2.DriverConfig()
        driver_config_proto.zigbee_message.type = comm_pb2.ZigBeeMsg.ZigBeeCmdType.Value("NETWORK_MGMT")
        driver_config_proto.zigbee_message.network_mgmt_cmd.type = comm_pb2.ZigBeeMsg.NetworkMgmtCmd.NetworkMgmtCmdTypes.Value("PERMIT_JOIN")
        driver_config_proto.zigbee_message.network_mgmt_cmd.permit_join_params.time = 60
        self.push(driver_config_proto)
        
        _LOGGER.info('Please reset your zigbee devices')
        _LOGGER.info('.. Waiting 60s for new devices')            
        return Status.WAITING_FOR_DEVICES

    async def checkGatewayActive(self):
        await asyncio.sleep(3)
        self.IsGatewayActive()

class ZigbeeBulb():

    def __init__(self, push_fn, nodeId, endointIndex):
        """Initialize an ZigbeeDevice."""
        self.push = push_fn
        self._nodeId = nodeId
        self._endpointIndex = endointIndex
        self._name = str(nodeId)
        self._state = None
        self._brightness = 50
        self._colorTemp = 340

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def endpoint_index(self):
        return self._endpointIndex

    #@property
    #def should_poll(self) -> bool:
    #    """No polling needed for a demo light."""
    #    return False

    @property
    def brightness(self):
        """Return the brightness of the light.
        This method is optional. Removing it indicates to Home Assistant
        that brightness is not supported for this light.
        """
        return self._brightness

    @property
    def white_value(self):
        """Return the white value of this light between 0..255."""
        return self._colorTemp

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._state

    def turn_on(self):
        self._state = True
        config = driver_pb2.DriverConfig()

        config.zigbee_message.type = comm_pb2.ZigBeeMsg.ZigBeeCmdType.Value("ZCL")
        config.zigbee_message.zcl_cmd.type = comm_pb2.ZigBeeMsg.ZCLCmd.ZCLCmdType.Value("ON_OFF")
        config.zigbee_message.zcl_cmd.onoff_cmd.type = comm_pb2.ZigBeeMsg.ZCLCmd.OnOffCmd.ZCLOnOffCmdType.Value("ON")
        config.zigbee_message.zcl_cmd.node_id = self._nodeId
        config.zigbee_message.zcl_cmd.endpoint_index = self._endpointIndex

        self.push(config)

    def turn_off(self):
        self._state = False
        
        config = driver_pb2.DriverConfig()

        config.zigbee_message.type = comm_pb2.ZigBeeMsg.ZigBeeCmdType.Value("ZCL")
        config.zigbee_message.zcl_cmd.type = comm_pb2.ZigBeeMsg.ZCLCmd.ZCLCmdType.Value("ON_OFF")
        config.zigbee_message.zcl_cmd.onoff_cmd.type = comm_pb2.ZigBeeMsg.ZCLCmd.OnOffCmd.ZCLOnOffCmdType.Value("OFF")
        config.zigbee_message.zcl_cmd.node_id = self._nodeId
        config.zigbee_message.zcl_cmd.endpoint_index = self._endpointIndex

        self.push(config)

    def toggle(self):
        config = driver_pb2.DriverConfig()

        config.zigbee_message.type = comm_pb2.ZigBeeMsg.ZigBeeCmdType.Value("ZCL")
        config.zigbee_message.zcl_cmd.type = comm_pb2.ZigBeeMsg.ZCLCmd.ZCLCmdType.Value("ON_OFF")
        config.zigbee_message.zcl_cmd.onoff_cmd.type = comm_pb2.ZigBeeMsg.ZCLCmd.OnOffCmd.ZCLOnOffCmdType.Value("TOGGLE")
        config.zigbee_message.zcl_cmd.node_id = self._nodeId
        config.zigbee_message.zcl_cmd.endpoint_index = self._endpointIndex

        self.push(config)


    def set_brightness(self, brightness):
        self._brightness = brightness
        config = driver_pb2.DriverConfig()

        config.zigbee_message.type = comm_pb2.ZigBeeMsg.ZigBeeCmdType.Value("ZCL")
        config.zigbee_message.zcl_cmd.type = comm_pb2.ZigBeeMsg.ZCLCmd.ZCLCmdType.Value("LEVEL")
        config.zigbee_message.zcl_cmd.level_cmd.type = comm_pb2.ZigBeeMsg.ZCLCmd.LevelCmd.ZCLLevelCmdType.Value("MOVE_TO_LEVEL")
        config.zigbee_message.zcl_cmd.level_cmd.move_to_level_params.level = brightness
        config.zigbee_message.zcl_cmd.level_cmd.move_to_level_params.transition_time = 10
        config.zigbee_message.zcl_cmd.node_id = self._nodeId
        config.zigbee_message.zcl_cmd.endpoint_index = self._endpointIndex

        self.push(config)

    def set_color_temp(self, color_temp):
        self._colorTemp = color_temp
        config = driver_pb2.DriverConfig()

        config.zigbee_message.type = comm_pb2.ZigBeeMsg.ZigBeeCmdType.Value("ZCL")
        config.zigbee_message.zcl_cmd.type = comm_pb2.ZigBeeMsg.ZCLCmd.ZCLCmdType.Value("COLOR_CONTROL")
        config.zigbee_message.zcl_cmd.colorcontrol_cmd.type = comm_pb2.ZigBeeMsg.ZCLCmd.ColorControlCmd.ZCLColorControlCmdType.Value("MOVETOCOLORTEMP")
        config.zigbee_message.zcl_cmd.colorcontrol_cmd.movetocolortemp_params.color_temperature = color_temp
        config.zigbee_message.zcl_cmd.colorcontrol_cmd.movetocolortemp_params.transition_time = 10
        config.zigbee_message.zcl_cmd.node_id = self._nodeId
        config.zigbee_message.zcl_cmd.endpoint_index = self._endpointIndex

        self.push(config)

    def update(self):
        """Fetch new state data for this light.
        This is the only method that should fetch new data for Home Assistant.
        """
        # TODO:
        #self._light.update()
        #self._state = self._light.is_on()
        #self._brightness = self._light.brightness