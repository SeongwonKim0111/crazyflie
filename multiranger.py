import logging
import time

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie

from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncLogger import SyncLogger

# URI to the Crazyflie to connect to
uri = 'radio://0/80/2M/E7E7E7E7E7'

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)

def convert_log_to_distance(data):
    for ranges in data:
        if data[ranges] >= 8000:
            data[ranges] = None
        else:
            data[ranges] = data[ranges]/1000.0

    return data

def lg_range_callback(timestamp, data, logconf):
    data_in_meter = convert_log_to_distance(data)
    print('[%d][%s]: %s' % (timestamp, logconf.name, data_in_meter))

if __name__ == '__main__':
    cflib.crtp.init_drivers()

    lg_range = LogConfig(name='multiranger', period_in_ms=50)
    lg_range.add_variable('range.front', 'float') ##Unit is mm
    lg_range.add_variable('range.back', 'float')
    lg_range.add_variable('range.left', 'float')
    lg_range.add_variable('range.right', 'float')
    lg_range.add_variable('range.up', 'float')
    lg_range.add_variable('range.zrange', 'float')

    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:

        cf = scf.cf
        cf.log.add_config(lg_range)
        lg_range.data_received_cb.add_callback(lg_range_callback)
        lg_range.start()
        time.sleep(5)
        lg_range.stop()
