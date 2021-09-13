import sys
import logging
import time

from NatNetClient import NatNetClient
import DataDescriptions
import MoCapData

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander

# This is a callback function that gets connected to the NatNet client
# and called once per mocap frame.
def receive_new_frame(data_dict):
    order_list=[ "frameNumber", "markerSetCount", "unlabeledMarkersCount", "rigidBodyCount", "skeletonCount",
                "labeledMarkerCount", "timecode", "timecodeSub", "timestamp", "isRecording", "trackedModelsChanged" ]
    dump_args = False
    if dump_args == True:
        out_string = "    "
        for key in data_dict:
            out_string += key + "="
            if key in data_dict :
                out_string += data_dict[key] + " "
            out_string+="/"
        print(out_string)

# This is a callback function that gets connected to the NatNet client. It is called once per rigid body per frame
def receive_rigid_body_frame( new_id, position, rotation ):
    print(position)
    print(rotation)
    position_motion_capture = [position[0], position[2], position[1]]
    rotation_motion_capure = [rotation[3], rotation[0], rotation[2], -rotation[1]]
    # pass

    #print( "Received frame for rigid body", new_id )
    #print( "Received frame for rigid body", new_id," ",position," ",rotation )

def add_lists(totals, totals_tmp):
    totals[0]+=totals_tmp[0]
    totals[1]+=totals_tmp[1]
    totals[2]+=totals_tmp[2]
    return totals

# def print_configuration(natnet_client):
    print("Connection Configuration:")
    print("  Client:          %s"% natnet_client.local_ip_address)
    print("  Server:          %s"% natnet_client.server_ip_address)
    print("  Command Port:    %d"% natnet_client.command_port)
    print("  Data Port:       %d"% natnet_client.data_port)

    if natnet_client.use_multicast:
        print("  Using Multicast")
        print("  Multicast Group: %s"% natnet_client.multicast_address)
    else:
        print("  Using Unicast")

    #NatNet Server Info
    application_name = natnet_client.get_application_name()
    nat_net_requested_version = natnet_client.get_nat_net_requested_version()
    nat_net_version_server = natnet_client.get_nat_net_version_server()
    server_version = natnet_client.get_server_version()

    print("  NatNet Server Info")
    print("    Application Name %s" %(application_name))
    print("    NatNetVersion  %d %d %d %d"% (nat_net_version_server[0], nat_net_version_server[1], nat_net_version_server[2], nat_net_version_server[3]))
    print("    ServerVersion  %d %d %d %d"% (server_version[0], server_version[1], server_version[2], server_version[3]))
    print("  NatNet Bitstream Requested")
    print("    NatNetVersion  %d %d %d %d"% (nat_net_requested_version[0], nat_net_requested_version[1],\
       nat_net_requested_version[2], nat_net_requested_version[3]))
    #print("command_socket = %s"%(str(natnet_client.command_socket)))
    #print("data_socket    = %s"%(str(natnet_client.data_socket)))


def request_data_descriptions(s_client):
    # Request the model definitions
    s_client.send_request(s_client.command_socket, s_client.NAT_REQUEST_MODELDEF,    "",  (s_client.server_ip_address, s_client.command_port) )

def test_classes():
    totals = [0,0,0]
    print("Test Data Description Classes")
    totals_tmp = DataDescriptions.test_all()
    totals=add_lists(totals, totals_tmp)
    print("")
    print("Test MoCap Frame Classes")
    totals_tmp = MoCapData.test_all()
    totals=add_lists(totals, totals_tmp)
    print("")
    print("All Tests totals")
    print("--------------------")
    print("[PASS] Count = %3.1d"%totals[0])
    print("[FAIL] Count = %3.1d"%totals[1])
    print("[SKIP] Count = %3.1d"%totals[2])

def my_parse_args(arg_list, args_dict):
    # set up base values
    arg_list_len=len(arg_list)
    if arg_list_len>1:
        args_dict["serverAddress"] = arg_list[1]
        if arg_list_len>2:
            args_dict["clientAddress"] = arg_list[2]
        if arg_list_len>3:
            if len(arg_list[3]):
                args_dict["use_multicast"] = True
                if arg_list[3][0].upper() == "U":
                    args_dict["use_multicast"] = False

    return args_dict

#Crazyflie stuff starts here

URI = 'radio://0/80/2M/E7E7E7E7E7'
DEFAULT_HEIGHT = 0.3
BOX_LIMIT = 0.3

is_deck_attached = False

logging.basicConfig(level=logging.ERROR)

position_estimate = [0, 0]
range_sensor = [0, 0, 0, 0, 0, 0]
gyro_sensor = [0, 0, 0]


def move_box_limit(scf, position_motion_capture):
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

            if position_motion_capture[0] > BOX_LIMIT:
                body_x_cmd = -max_vel
            elif position_motion_capture[0] < -BOX_LIMIT:
                body_x_cmd = max_vel
            if position_motion_capture[0] < BOX_LIMIT:
                body_x_cmd = 0
            elif position_motion_capture[0] > -BOX_LIMIT:
                body_x_cmd = 0
            if position_motion_capture[1] > BOX_LIMIT:
                body_y_cmd = -max_vel
            elif position_motion_capture[1] < -BOX_LIMIT:
                body_y_cmd = max_vel
            if position_motion_capture[1] < BOX_LIMIT:
                body_y_cmd = 0
            elif position_motion_capture[1] > -BOX_LIMIT:
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

if __name__ == "__main__":
    cflib.crtp.init_drivers()

    optionsDict = {}
    optionsDict["clientAddress"] = "127.0.0.1"
    optionsDict["serverAddress"] = "127.0.0.1"
    optionsDict["use_multicast"] = True

    # This will create a new NatNet client
    #optionsDict = my_parse_args(sys.argv, optionsDict)

    streaming_client = NatNetClient()
    streaming_client.set_client_address(optionsDict["clientAddress"])
    streaming_client.set_server_address(optionsDict["serverAddress"])
    streaming_client.set_use_multicast(optionsDict["use_multicast"])

    # Configure the streaming client to call our rigid body handler on the emulator to send data out.
    streaming_client.new_frame_listener = receive_new_frame
    streaming_client.rigid_body_listener = receive_rigid_body_frame

    # Start up the streaming client now that the callbacks are set up.
    # This will run perpetually, and operate on a separate thread.
    is_running = streaming_client.run()
    if not is_running:
        print("ERROR: Could not start streaming client.")
        try:
            sys.exit(1)
        except SystemExit:
            print("...")
        finally:
            print("exiting")

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
            move_box_limit(scf, position_motion_capture)
            logconf.stop()
            logconf2.stop()
            logconf3.stop()