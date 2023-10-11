
import json
import os
import threading
from .configuration_service import Thingy52Extended
from bluepy.btle import BTLEGattError


class Sensor(object):

    def __init__(
            self,
            mac,
            thread_sync,
            controller,
            nickname: str = 'NordicThingy',
            sensor_delegates: list = None,
    ):
        self.nickname = nickname
        self.thingy = Thingy52Extended(mac)
        self.mac = mac
        self.synchronizer = thread_sync
        self.controller = controller
        self.sensor_delegates = sensor_delegates
        self.__connected = True
        self.services = []
        self.config: dict = json.load(open(os.path.join(os.getcwd(), 'wearable/settings/config.json')))
        self.thingy.battery.enable()
        self.battery = self.thingy.battery.read()
        # Set delegates
        for delegate in sensor_delegates:
            self.thingy.setDelegate(delegate(self.nickname, self.thingy.addr))

        self.thingy.ui.enable()
        self.thingy.ui.set_led_mode_constant(0, 255, 0)

    def enabling_selected_sensors(self):

        # Enabling selected sensors
        self.services = json.load(open(os.path.join(os.getcwd(), 'wearable/settings/session_info.json')))['services']

        # Configuration Service
        try:
            self.thingy.configuration.enable()
            self.thingy.configuration.configure_adv_params(adv_interval=self.config['adv_interval'],
                                                           adv_timeout=self.config['adv_timeout'])
            self.thingy.configuration.configure_conn_params(min_conn_interval=self.config['min_conn_interval'],
                                                            max_conn_interval=self.config['max_conn_interval'],
                                                            slave_latency=self.config['slave_latency'],
                                                            conn_sup_timeout=self.config['conn_sup_timeout'])

        except BTLEGattError:
            print('Invalid values for advertising. Default values have been set.')
            self.thingy.configuration.configure_adv_params(adv_interval=32, adv_timeout=0)
            print('Invalid values for connection. Default values have been set.')
            self.thingy.configuration.configure_conn_params(min_conn_interval=6,
                                                            max_conn_interval=6,
                                                            slave_latency=0,
                                                            conn_sup_timeout=10)

        # Environment Service
        if 'temperature' in self.services:
            try:
                self.thingy.environment.enable()
                self.thingy.environment.configure(temp_int=self.config['temp_int'])

            except BTLEGattError:
                print('Invalid value for temperature. Default value have been set.')
                self.thingy.environment.configure(temp_int=1000)

            self.thingy.environment.set_temperature_notification(True)

        if 'pressure' in self.services:
            try:
                self.thingy.environment.enable()
                self.thingy.environment.configure(press_int=self.config['press_int'])

            except BTLEGattError:
                print('Invalid value for pressure. Default value have been set.')
                self.thingy.environment.configure(press_int=1000)

            self.thingy.environment.set_pressure_notification(True)

        if 'humidity' in self.services:
            try:
                self.thingy.environment.enable()
                self.thingy.environment.configure(humid_int=self.config['humid_int'])

            except BTLEGattError:
                print('Invalid value for humidity. Default value have been set.')
                self.thingy.environment.configure(humid_int=1000)

            self.thingy.environment.set_humidity_notification(True)

        if 'gas' in self.services:
            try:
                self.thingy.environment.enable()
                self.thingy.environment.configure(gas_mode_int=self.config['gas_mode_int'])

            except BTLEGattError:
                print('Invalid value for gas mode. Default value have been set.')
                self.thingy.environment.configure(gas_mode_int=1)

            self.thingy.environment.set_gas_notification(True)

        if 'color' in self.services:
            try:
                self.thingy.environment.enable()
                self.thingy.environment.configure(color_int=self.config['color_int'], color_sens_calib=[0, 0, 0])

            except BTLEGattError:
                print('Invalid values for color. Default values have been set.')
                self.thingy.environment.configure(color_int=1000, color_sens_calib=[0, 0, 0])

            self.thingy.environment.set_color_notification(True)

        # User Interface Service
        if 'keypress' in self.services:
            self.thingy.ui.enable()
            self.thingy.ui.set_btn_notification(True)

        # Motion Service
        if 'tap' in self.services:
            self.thingy.motion.enable()
            self.thingy.motion.set_tap_notification(True)
        if 'orientation' in self.services:
            self.thingy.motion.enable()
            self.thingy.motion.set_orient_notification(True)
        if 'quaternion' in self.services:
            self.thingy.motion.enable()
            self.thingy.motion.set_quaternion_notification(True)
        if 'step_count' in self.services:
            try:
                self.thingy.motion.enable()
                self.thingy.motion.configure(step_int=self.config['step_int'])

            except BTLEGattError:
                print('Invalid value for stepcnt. Default value have been set')
                self.thingy.motion.configure(step_int=100)

            self.thingy.motion.set_stepcnt_notification(True)

        if 'raw_data' in self.services:
            try:
                self.thingy.motion.enable()
                self.thingy.motion.configure(motion_freq=self.config['sampling_frequency'],
                                             magnet_comp_int=self.config['magnet_comp_int'])

            except BTLEGattError:
                print('Invalid values for rawdata. Default values have been set')
                self.thingy.motion.configure(motion_freq=128, magnet_comp_int=100)

            self.thingy.motion.set_rawdata_notification(True)

        if 'euler' in self.services:
            self.thingy.motion.enable()
            self.thingy.motion.set_euler_notification(True)
        if 'rotation' in self.services:
            self.thingy.motion.enable()
            self.thingy.motion.set_rotation_notification(True)
        if 'heading' in self.services:
            self.thingy.motion.enable()
            self.thingy.motion.set_heading_notification(True)
        if 'gravity' in self.services:
            self.thingy.motion.enable()
            self.thingy.motion.set_gravity_notification(True)

        # Sound Service
        if 'speaker' in self.services:
            self.thingy.sound.enable()
            self.thingy.sound.configure(speaker_mode=0x03)
            self.thingy.sound.set_speaker_status_notification(True)
            # Test speaker
            self.thingy.sound.play_speaker_sample(1)
        if 'microphone' in self.services:
            self.thingy.sound.enable()
            self.thingy.sound.configure(microphone_mode=0x01)
            self.thingy.sound.set_microphone_notification(True)

        # Get data generation start timestamp
        self.thingy.delegate.get_generation_timestamp()

    def configure_device_name(self, dev_name):
        try:
            self.thingy.configuration.enable()
            self.thingy.configuration.configure_device_name(device_name=dev_name)

        except BTLEGattError:
            print('Invalid device_name')

    def start(self):
        """ Start sensor thread """
        thread = threading.Thread(target=self.recording)
        thread.daemon = True
        thread.start()

    def recording(self):
        """ Start the recording of a sensor """
        while self.__connected:
            self.synchronizer.wait()
            self.thingy.delegate.reset_path()
            try:
                # Enable sensors
                self.enabling_selected_sensors()

                # Set LED in recording mode
                self.thingy.ui.set_led_mode_breathe(0x01, 50, 100)

                while self.synchronizer.is_set():
                    self.thingy.waitForNotifications(1.)  # 1 seconds

                self.thingy.delegate.reset_path()
                self.thingy.ui.set_led_mode_constant(0, 255, 0)

            except Exception as e:
                print(e.args)
                self.__connected = False

    def disconnect(self):
        self.__connected = False
        self.thingy.disconnect()


