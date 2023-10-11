import json
from distutils.util import strtobool
import sys
from bluepy.btle import DefaultDelegate
import struct
from datetime import datetime
import binascii
import math
from statistics import mean
import os


class MotionDelegate(DefaultDelegate):

    def __init__(self, name: str, mac_adr: str):
        super().__init__()
        # Load configuration
        self.config = json.load(open(os.path.join(os.getcwd(), 'wearable/settings/config.json')))
        self.session_info = None
        self.sensor_sampling_frequency = self.config['sampling_frequency']
        self.fall_time_window_for_detection = self.config['fall_time_window_for_detection']
        self.shake_time_window_for_detection = self.config['shake_time_window_for_detection']

        # Basic info
        self.sensor_nickname = name
        self.time_start = str(datetime.now().microsecond)
        self.mac = mac_adr
        self.transmission_mode = bool(strtobool(self.config['transmission_mode']))
        self.previously_sent = {'shake': True}
        self.initialized = datetime.now()
        self.data_generation_start = None
        self.delta = None
        self.__path = None

        # Movements data
        self.accelerometer = {}
        self.gyroscope = {}
        self.compass = {}

        # For shaking detection
        self.shake_history_max_length = int(self.sensor_sampling_frequency * self.shake_time_window_for_detection)
        self.possible_shake = False
        self.is_shaking = False
        self.in_use = False
        self.shake_threshold = 1.5
        self.shaking_history = {}
        self.last_magnitude = None
        self.counter = 0

        # Fall detection
        self.fall_history_max_length = int(self.sensor_sampling_frequency * self.fall_time_window_for_detection)
        self.fall_sent_alert = False
        self.fall_detect = False
        self.alarm = False
        self.acc_history = []
        self.gyro_history = []

        # Heading
        self.heading = 'loading...'
        self.heading_is_changed = False
        self.heading_deg = 0

        # Time of event
        self.start_event_time = None
        self.end_event_time = None

        # Set handlers
        self.handlers = {
            77: self._unpack_gravity_vector,
            74: self._unpack_heading,
            71: self._unpack_rotation_matrix,
            68: self._unpack_euler,
            65: self._unpack_raw_data,
            59: self._unpack_quaternion,
            56: self._unpack_orientation
        }

    def __create_dirs(self):
        self.session_info = json.load(open(os.path.join(os.getcwd(), 'wearable/settings/session_info.json')))
        path = os.path.join(os.getcwd(), f'wearable/recordings/{self.session_info["subject_id"]}')
        if not os.path.exists(path):
            os.makedirs(path)
        path += f"/{self.session_info['session_name']}"
        if not os.path.exists(path):
            os.makedirs(path)
        # path += f"/{self.sensor_nickname}"
        # if not os.path.exists(path):
        #     os.makedirs(path)

        return path

    def get_generation_timestamp(self):
        self.data_generation_start = datetime.now()

    def _unpack_rotation_matrix(self, d):
        # 2Q14 fixed point
        now = datetime.now()
        if self.delta is None:
            self.delta = (now - self.data_generation_start) / 2
        if self.__path is None:
            self.__path = self.__create_dirs()

        rotation_matrix = [str((struct.unpack('h', d[i: i + 2])[0] * 1.0) / 2 ** 14) for i in range(0, len(d), 2)]

        # Log to file
        with open(f'{self.__path}/{self.sensor_nickname}_rotation_matrix_{str(self.session_info["task_nr"])}', 'a+') as f:
            f.write(f"{now}, {','.join(str(now - self.delta))}, {','.join(rotation_matrix)}\n")

    def _unpack_gravity_vector(self, d):
        """ Transform byte into float x, y, z gravity vector. """
        # Get Time
        now = datetime.now()
        if self.delta is None:
            self.delta = (now - self.data_generation_start) / 2
        if self.__path is None:
            self.__path = self.__create_dirs()

        gravity_vector = [struct.unpack('f', d[i: i + 4])[0] for i in range(0, len(d), 4)]

        # Log to file
        # receiving time, generation time, x, y, z
        with open(f"{self.__path}/{self.sensor_nickname}_gravity_vector_{str(self.session_info['task_nr'])}.csv", "a+") as f:
            f.write(
                '%s,%s,%s,%s,%s\n' % (now, str(now - self.delta), gravity_vector[0], gravity_vector[1],
                                      gravity_vector[2]))

    def _unpack_quaternion(self, d):
        # 2Q30 fixed point
        now = datetime.now()

        if self.delta is None:
            self.delta = (now - self.data_generation_start) / 2
        if self.__path is None:
            self.__path = self.__create_dirs()

        quaternion = [str((struct.unpack('i', d[i: i + 4])[0] * 1.0) / 2 ** 30) for i in range(0, len(d), 4)]

        # Log to file
        # receiving time, generation time, x, y, z
        with open(f"{self.__path}/{self.sensor_nickname}_quaternion_{str(self.session_info['task_nr'])}.csv", "a+") as f:
            f.write(f"{now},{','.join(str(now - self.delta))},{','.join(quaternion)}\n")

    def _unpack_euler(self, d):
        # 16Q16 fixed point
        now = datetime.now()
        if self.delta is None:
            self.delta = (now - self.data_generation_start) / 2
        if self.__path is None:
            self.__path = self.__create_dirs()

        euler = [str(struct.unpack('i', d[i: i + 4])[0] / 65536) for i in range(0, len(d), 4)]

        # Log to file
        # receiving time, generation time, roll, pitch, yaw
        with open(f"{self.__path}/{self.sensor_nickname}_euler_{str(self.session_info['task_nr'])}.csv", "a+") as f:
            f.write('%s,%s,%s,%s,%s\n' % (now, str(now - self.delta), euler[0], euler[1], euler[2]))

    @staticmethod
    def _unpack_orientation(d):
        tmp = binascii.b2a_hex(d)
        orientation = 'Unknown'

        if tmp == b'00':
            orientation = 'Portrait'
        elif tmp == b'01':
            orientation = 'Landscape'
        elif tmp == b'02':
            orientation = 'Reverse Portrait'
        elif tmp == b'03':
            orientation = 'Reverse Landscape'

        print(orientation)

    @staticmethod
    def _unpack_tap_data(d):
        """ Extract tap data from data string. """
        tmp = binascii.b2a_hex(d)
        direction = tmp[0:2]
        count = tmp[2:4]
        return direction, count

    def _unpack_heading(self, d):
        # Get Time
        now = datetime.now()

        if self.delta is None:
            self.delta = (now - self.data_generation_start) / 2
        if self.__path is None:
            self.__path = self.__create_dirs()

        # Unpack heading degree
        deg = struct.unpack('i', d)[0] / 65536

        # Convert to ordinal
        if 22.5 <= deg < 67.5:
            ordinal_name = 'north-east'

        elif 67.5 <= deg < 112.5:
            ordinal_name = 'east'

        elif 112.5 <= deg < 157.5:
            ordinal_name = 'south-east'

        elif 157.5 <= deg < 202.5:
            ordinal_name = 'south'

        elif 202.5 <= deg < 247.5:
            ordinal_name = 'south-west'

        elif 247.5 <= deg < 292.5:
            ordinal_name = 'west'

        elif 292.5 <= deg < 337.5:
            ordinal_name = 'north-west'

        else:
            ordinal_name = 'north'

        if ordinal_name != self.heading:
            self.heading = ordinal_name
            self.heading_deg = deg
            self.heading_is_changed = True
            # Log to file
            with open(f"{self.__path}/{self.sensor_nickname}_heading_{str(self.session_info['task_nr'])}.csv", "a+") as f:
                f.write('%s,%s,%s,%s\n' % (now, str(now - self.delta), deg, ordinal_name))

        else:
            self.heading_is_changed = False

    def _hand_up_shacking_algorithm(self, new_x, new_y, new_z):
        new_magnitude = math.sqrt(math.pow(new_x, 2) + math.pow(new_y, 2) + math.pow(new_z, 2))

        try:
            if new_x >= .2:
                if self.last_magnitude is None and new_magnitude >= self.shake_threshold:
                    self.counter += 1  # one sample of data says that the sensor is shaking
                    self.last_magnitude = new_magnitude
                    return

                if new_magnitude >= self.shake_threshold and self.last_magnitude >= self.shake_threshold:
                    # The sensor is shaking
                    self.counter += 1
                    self.last_magnitude = new_magnitude

                    if self.counter >= int(32 * 0.1):
                        # It is shaking from to seconds
                        self.is_shaking = True
                        self.in_use = True

                else:
                    # The sensor is not shaking anymore
                    self.last_magnitude = None
                    self.counter = 0
                    self.is_shaking = False

            else:
                # The sensor is not shaking anymore
                self.last_magnitude = None
                self.counter = 0
                self.is_shaking = False

        except Exception as e:
            print(e.args)

    def _chest_shacking_algorithm(self, new_x, new_y, new_z, time):
        new_magnitude = math.sqrt(math.pow(new_x, 2) + math.pow(new_y, 2) + math.pow(new_z, 2))

        try:
            if new_magnitude >= self.shake_threshold:
                self.possible_shake = True

            if self.possible_shake:
                self.shaking_history.update({time: new_magnitude})

                if len(self.shaking_history) >= self.shake_history_max_length:
                    mean_magnitude = mean(self.shaking_history.values())
                    if mean_magnitude >= self.shake_threshold:
                        self.is_shaking = True
                        self.start_event_time = self.datetime_to_timestamp(list(self.shaking_history.keys())[0])
                        self.end_event_time = self.datetime_to_timestamp(list(self.shaking_history.keys())[-1])
                        self.in_use = True

                    else:
                        self.is_shaking = False

                    self.possible_shake = False
                    self.shaking_history = {}

            else:
                self.is_shaking = False
                self.possible_shake = False
                self.start_event_time = None
                self.end_event_time = None
                self.shaking_history = {}

        except Exception as e:
            print(e.args)

    def _fall_detection_algorithm(self, new_x, new_y, new_z, gyro_x, gyro_y, gyro_z, time):
        new_magnitude = math.sqrt(math.pow(new_x, 2) + math.pow(new_y, 2) + math.pow(new_z, 2))
        new_gyro_mag = math.sqrt(math.pow(gyro_x, 2) + math.pow(gyro_y, 2) + math.pow(gyro_z, 2))

        # sys.stdout.write('\r x: {:5.2f}, y: {:5.2f}, z:{:5.2f} -- magnitude: {:5.2f} -- fall: {}'.format(
        #     gyro_x, gyro_y, gyro_z, new_gyro_mag, self.alarm
        # ))
        # sys.stdout.flush()

        # Detect probable falling
        if new_magnitude < .8 and not self.fall_detect:
            self.fall_detect = True

        # Collect falling data
        if self.fall_detect:
            self.acc_history.append(new_magnitude)
            self.gyro_history.append(new_gyro_mag)

        # Analyse fall data
        if len(self.acc_history) >= self.fall_history_max_length and self.fall_detect:

            fall = any(record < .9 for record in self.acc_history)
            impact = any(record >= 1.3 for record in self.acc_history)
            decrease = any(.1 <= record <= .2 for record in self.acc_history)
            static = any(.9 <= record <= 1.2 for record in self.acc_history)
            speed = any(record >= 200 for record in self.gyro_history) and any(
                record <= 15 for record in self.gyro_history)

            if fall and impact and decrease and static and speed and not self.is_shaking:
                self.alarm = True
            else:
                self.alarm = False

            self.fall_detect = False
            self.acc_history = []
            self.gyro_history = []

    def _unpack_raw_data(self, d):
        # Get Time
        now = datetime.now()

        if self.delta is None:
            self.delta = (now - self.data_generation_start) / 2
        if self.__path is None:
            self.__path = self.__create_dirs()

        # Accelerometer
        acc_x = (struct.unpack('h', d[0:2])[0] * 1.0) / 2 ** 10
        acc_y = (struct.unpack('h', d[2:4])[0] * 1.0) / 2 ** 10
        acc_z = (struct.unpack('h', d[4:6])[0] * 1.0) / 2 ** 10

        self.accelerometer = {
            'x': acc_x,
            'y': acc_y,
            'z': acc_z
        }

        # Gyroscope
        gyro_x = (struct.unpack('h', d[6:8])[0] * 1.0) / 2 ** 5
        gyro_y = (struct.unpack('h', d[8:10])[0] * 1.0) / 2 ** 5
        gyro_z = (struct.unpack('h', d[10:12])[0] * 1.0) / 2 ** 5

        self.gyroscope = {
            'x': gyro_x,
            'y': gyro_y,
            'z': gyro_z
        }

        # Compass
        comp_x = (struct.unpack('h', d[12:14])[0] * 1.0) / 2 ** 4
        comp_y = (struct.unpack('h', d[14:16])[0] * 1.0) / 2 ** 4
        comp_z = (struct.unpack('h', d[16:18])[0] * 1.0) / 2 ** 4

        self.compass = {
            'x': comp_x,
            'y': comp_y,
            'z': comp_z
        }

        with open(f"{self.__path}/{self.sensor_nickname}_raw_data_{str(self.session_info['task_nr'])}.csv", 'a+') as f:
            # Log to file
            f.write('%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' %
                    (now, str(now - self.delta), acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z, comp_x, comp_y,
                     comp_z))

        # Check shacking or fall
        self._chest_shacking_algorithm(acc_x, acc_y, acc_z, now)
        self._fall_detection_algorithm(acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z, now)

    def _log_to_console(self):
        sys.stdout.write('\r{} -- {} -- {} -- {}'
                         .format(self.sensor_nickname,
                                 'is shacking' if self.is_shaking else 'not shaking',
                                 'fall' if self.alarm else 'ok',
                                 self.heading
                                 )
                         )
        sys.stdout.flush()

    def reset_path(self):
        self.__path = None

    @staticmethod
    def datetime_to_timestamp(time):
        return int(time.timestamp() * 1000000)

    def handleNotification(self, handle_code, data):
        self.handlers[handle_code](data)
