import bluepy.thingy52
from bluepy.thingy52 import Thingy52
from bluepy.thingy52 import Nordic_UUID
import binascii

# UUID of Thingy configuration services
CONFIGURATION_SERVICE_UUID = 0x0100
DEVICE_NAME_CHARACTERISTIC_UUID = 0x0101
ADV_PARAM_CHARACTERISTIC_UUID = 0x0102
CONN_PARAM_CHARACTERISTIC_UUID = 0x0104


# This class extends bluepy.thingy52.Thingy52 in order to implement the ConfigurationService class
class Thingy52Extended(Thingy52):
    def __init__(self, addr):
        Thingy52.__init__(self, addr)
        self.configuration = ConfigurationService(self)


# This class implements the functions of thingy configuration service
class ConfigurationService:
    """Configuration service module. Instance the class and enable to get access to thingy configuration interface"""
    serviceUUID = Nordic_UUID(CONFIGURATION_SERVICE_UUID)
    adv_param_char_uuid = Nordic_UUID(ADV_PARAM_CHARACTERISTIC_UUID)
    conn_param_char_uuid = Nordic_UUID(CONN_PARAM_CHARACTERISTIC_UUID)
    device_name_char_uuid = Nordic_UUID(DEVICE_NAME_CHARACTERISTIC_UUID)

    def __init__(self, periph):
        self.periph = periph
        self.configuration_service = None
        self.device_name_char = None
        self.adv_param_char = None
        self.conn_param_char = None

    def enable(self):
        """Enable the configuration services"""
        if self.configuration_service is None:
            self.configuration_service = self.periph.getServiceByUUID(self.serviceUUID)
        if self.device_name_char is None:
            self.device_name_char = self.configuration_service.getCharacteristics(self.device_name_char_uuid)[0]
        if self.adv_param_char is None:
            self.adv_param_char = self.configuration_service.getCharacteristics(self.adv_param_char_uuid)[0]
        if self.conn_param_char is None:
            self.conn_param_char = self.configuration_service.getCharacteristics(self.conn_param_char_uuid)[0]

    def configure_device_name(self, device_name=None):
        """Configure device name"""
        if device_name is not None and self.device_name_char is not None:
            self.device_name_char.write(bytearray(device_name, 'utf-8'), True)

    def configure_adv_params(self, adv_interval=None, adv_timeout=None):
        """Configure advertising params"""
        if adv_interval is not None and self.adv_param_char is not None:
            current_config = binascii.b2a_hex(self.adv_param_char.read())
            new_config = bluepy.thingy52.write_uint16(current_config, adv_interval, 0)
            self.adv_param_char.write(binascii.a2b_hex(new_config), True)
        if adv_timeout is not None and self.adv_param_char is not None:
            current_config = binascii.b2a_hex(self.adv_param_char.read())
            new_config = bluepy.thingy52.write_uint8(current_config, adv_timeout, 2)
            self.adv_param_char.write(binascii.a2b_hex(new_config), True)

    def configure_conn_params(self, min_conn_interval=None, max_conn_interval=None, slave_latency=None,
                              conn_sup_timeout=None):
        """Configure Connection params"""
        if min_conn_interval is not None and self.conn_param_char is not None:
            current_config = binascii.b2a_hex(self.conn_param_char.read())
            new_config = bluepy.thingy52.write_uint16(current_config, min_conn_interval, 0)
            self.conn_param_char.write(binascii.a2b_hex(new_config), True)
        if max_conn_interval is not None and self.conn_param_char is not None:
            current_config = binascii.b2a_hex(self.conn_param_char.read())
            new_config = bluepy.thingy52.write_uint16(current_config, max_conn_interval, 1)
            self.conn_param_char.write(binascii.a2b_hex(new_config), True)
        if slave_latency is not None and self.conn_param_char is not None:
            current_config = binascii.b2a_hex(self.conn_param_char.read())
            new_config = bluepy.thingy52.write_uint16(current_config, slave_latency, 2)
            self.conn_param_char.write(binascii.a2b_hex(new_config), True)
        if conn_sup_timeout is not None and self.conn_param_char is not None:
            current_config = binascii.b2a_hex(self.conn_param_char.read())
            new_config = bluepy.thingy52.write_uint16(current_config, conn_sup_timeout, 3)
            self.conn_param_char.write(binascii.a2b_hex(new_config), True)

    def read(self):
        return self.device_name_char.read()
