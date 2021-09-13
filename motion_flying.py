import logging
import time

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils.multiranger import Multiranger


URI = 'radio://0/80/2M/E7E7E7E7E7'
DEFAULT_HEIGHT = 0.4
BOX_LIMIT = 0.3

is_deck_attached = False

logging.basicConfig(level=logging.ERROR)

position_estimate = [0, 0]
range_sensor = [0, 0, 0, 0, 0, 0]
gyro_sensor = [0, 0, 0]


def move_box_limit(scf):
    with MotionCommander(scf, default_height=DEFAULT_HEIGHT) as mc:
        body_x_cmd = 0.2
        body_y_cmd = 0.2
        max_vel = 0.1
        min_distance = 200

        while 1:
            # if position_estimate[0] > BOX_LIMIT:
            #    mc.start_back()
            # elif position_estimate[0] < -BOX_LIMIT:
            #    mc.start_forward()

            if position_estimate[0] > BOX_LIMIT:
                body_x_cmd = -max_vel
            elif position_estimate[0] < -BOX_LIMIT:
                body_x_cmd = max_vel
            if position_estimate[0] < BOX_LIMIT:
                body_x_cmd = 0
            elif position_estimate[0] > -BOX_LIMIT:
                body_x_cmd = 0
            if position_estimate[1] > BOX_LIMIT:
                body_y_cmd = -max_vel
            elif position_estimate[1] < -BOX_LIMIT:
                body_y_cmd = max_vel
            if position_estimate[1] < BOX_LIMIT:
                body_y_cmd = 0
            elif position_estimate[1] > -BOX_LIMIT:
                body_y_cmd = 0

            if range_sensor[3] < min_distance:
                mc.land()
            if range_sensor[2] < min_distance:
                mc.land()
            if range_sensor[1] < min_distance:
                mc.land()
            if range_sensor[0] < min_distance:
                mc.land()
            if range_sensor[4] < min_distance:
                mc.land()
            if abs(gyro_sensor[0]) > 10:
                mc.stop()
            if abs(gyro_sensor[1]) > 10:
                mc.stop()

            mc.start_linear_motion(body_x_cmd, body_y_cmd, 0)

            time.sleep(0.1)


def move_linear_simple(scf):
    with MotionCommander(scf, default_height=DEFAULT_HEIGHT) as mc:
        time.sleep(2)
        mc.forward(0.5)
        time.sleep(1)
        mc.turn_left(180, rate=20)
        time.sleep(1)
        mc.forward(0.5)
        time.sleep(1)
        mc.circle_left(0.3, velocity=0.3, angle_degrees=360.0)
        time.sleep(2)

        if abs(gyro_sensor[0]) > 10:
            mc.stop()
        if abs(gyro_sensor[1]) > 10:
            mc.stop()


def take_off_simple(scf):
    with MotionCommander(scf, default_height=DEFAULT_HEIGHT) as mc:
        time.sleep(3)


def log_pos_callback(timestamp, data, logconf):
    print("time in ms:", timestamp)
    print(data)
    global position_estimate
    position_estimate[0] = data['stateEstimate.x']
    position_estimate[1] = data['stateEstimate.y']


def log_ran_callback(timestamp, data, logconf2):
    print(data)
    global range_sensor
    range_sensor[0] = data['range.front']
    range_sensor[1] = data['range.back']
    range_sensor[2] = data['range.left']
    range_sensor[3] = data['range.right']
    range_sensor[4] = data['range.up']
    range_sensor[5] = data['range.zrange']


def log_gyr_callback(timestamp, data, logconf3):
    print(data)
    global gyro_sensor
    gyro_sensor[0] = data['stabilizer.roll']
    gyro_sensor[1] = data['stabilizer.pitch']
    gyro_sensor[2] = data['stabilizer.yaw']


def param_deck_flow(name, value_str):
    value = int(value_str)
    print(value)
    global is_deck_attached
    if value:
        is_deck_attached = True
        print('Deck is attached!')
    else:
        is_deck_attached = False
        print('Deck is NOT attached!')


if __name__ == '__main__':
    cflib.crtp.init_drivers()

    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:

        scf.cf.param.add_update_callback(group="deck", name="bcFlow2", cb=param_deck_flow)
        time.sleep(1.5)

        logconf = LogConfig(name='Position', period_in_ms=1000)
        # logconf.add_variable('time', 'float')
        logconf.add_variable('stateEstimate.x', 'float')
        logconf.add_variable('stateEstimate.y', 'float')

        scf.cf.log.add_config(logconf)
        logconf.data_received_cb.add_callback(log_pos_callback)

        logconf2 = LogConfig(name='Range', period_in_ms=1000)
        logconf2.add_variable('range.front', 'float')
        logconf2.add_variable('range.back', 'float')
        logconf2.add_variable('range.left', 'float')
        logconf2.add_variable('range.right', 'float')
        logconf2.add_variable('range.up', 'float')
        logconf2.add_variable('range.zrange', 'float')

        # scf.cf.log.add_config(logconf)
        scf.cf.log.add_config(logconf2)
        # logconf.data_received_cb.add_callback(log_pos_callback)
        logconf2.data_received_cb.add_callback(log_ran_callback)

        logconf3 = LogConfig(name='Gyro', period_in_ms=1000)
        logconf3.add_variable('stabilizer.roll', 'float')
        logconf3.add_variable('stabilizer.pitch', 'float')
        logconf3.add_variable('stabilizer.yaw', 'float')

        scf.cf.log.add_config(logconf3)
        logconf3.data_received_cb.add_callback(log_gyr_callback)

        if is_deck_attached:
            logconf.start()
            logconf2.start()
            logconf3.start()
            # move_linear_simple(scf)
            move_box_limit(scf)
            logconf.stop()
            logconf2.stop()
            logconf3.stop()
