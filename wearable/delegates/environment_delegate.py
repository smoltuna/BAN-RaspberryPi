# from kafka import KafkaProducer
from bluepy.btle import DefaultDelegate
from datetime import datetime
import binascii


class EnvironmentDelegate(DefaultDelegate):
    header = 'timestamp,temperature,humidity,pressure\n'
    actual_temperature, actual_humidity, actual_pressure = 0, 0, 0

    def __init__(self, name, mac_adr):
        super().__init__()
        self.file_name = 'env_data_%s_%s.csv' % (name, str(datetime.now().date()))
        self.mac = mac_adr

        # Write .csv file
        with open(self.file_name, 'a+') as csv_file:
            csv_file.write(self.header)

        # Set handlers
        self.handlers = {
            39: self._unpack_humidity,
            36: self._unpack_pressure,
            33: self._unpack_temperature
        }

    @staticmethod
    def _str_to_int(s):
        """ Transform hex str into int. """
        i = int(s, 16)
        if i >= 2 ** 7:
            i -= 2 ** 8
        return i

    @staticmethod
    def _unpack_pressure(d):
        """ Extract pressure data from data string. """
        tmp = binascii.b2a_hex(d)
        pressure_int = 0
        for i in range(0, 4):
            pressure_int += (int(tmp[i * 2:(i * 2) + 2], 16) << 8 * i)
        pressure_dec = int(tmp[-2:], 16)

        new_pressure = float('{}.{}'.format(pressure_int, pressure_dec))  # hPa
        return new_pressure

    @staticmethod
    def _unpack_gas_data(data):
        """ Extract gas data from data string. """
        tmp = binascii.b2a_hex(data)
        eco2 = int(tmp[:2], 16) + (int(tmp[2:4], 16) << 8)
        tvoc = int(tmp[4:6], 16) + (int(tmp[6:8], 16) << 8)
        return eco2, tvoc

    def _unpack_temperature(self, d):
        tmp = binascii.b2a_hex(d)
        new_temperature = float('{}.{}'.format(self._str_to_int(tmp[:-2]), int(tmp[-2:], 16)))

        return new_temperature

    def _unpack_humidity(self, d):
        """ Extract pressure data from data string. """
        tmp = binascii.b2a_hex(d)
        new_humidity = float('{}'.format(self._str_to_int(tmp)))

        return new_humidity

    def handleNotification(self, handle_code, data):
        print(handle_code)
