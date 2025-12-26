import os, csv, time, logging
from pynput import keyboard

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander

from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncLogger import SyncLogger  

from utils.KeyboardControl import KeyboardDrone

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

position_estimate = [0,0]

# URI to the Crazyflie to connect to
uri = 'radio://0/80/2M/E7E7E7E7E7'

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)

# Set default height of Crazyflie
DEFAULT_HEIGHT = 0.5

# Convert mm to m
def convert_log_to_distance(data):
    for ranges in data:
        if data[ranges] >= 8000:
            data[ranges] = None
        else:
            data[ranges] = data[ranges]/1000.0

    return data


if __name__ == '__main__':

    outdir = './logs'
    period_ms = 50
    cflib.crtp.init_drivers()

    # === log block 1: 6-DoF pose ===
    lg_stab = LogConfig(name='Stabilizer', period_in_ms=period_ms)
    for v in ("stateEstimate.x","stateEstimate.y","stateEstimate.z", "stateEstimate.roll","stateEstimate.pitch","stateEstimate.yaw"):
        lg_stab.add_variable(v, "float")


    # === log block 2: multiranger measurement ===
    lg_range = LogConfig(name='multiranger', period_in_ms=period_ms)
    for v in ("range.front","range.back","range.left","range.right","range.up","range.zrange"):
        lg_range.add_variable(v, "uint16_t")

    
    ensure_dir(outdir)
    # CSV 핸들러 준비 (두 파일로 분리: 블록도 분리했으니 가장 단순)
    state_csv = open(os.path.join(outdir, "state.csv"), "w", newline="")
    range_csv = open(os.path.join(outdir, "range.csv"), "w", newline="")
    w_state = csv.writer(state_csv)
    w_range = csv.writer(range_csv)
    # 헤더
    w_state.writerow(["timestamp","x","y","z","roll_deg","pitch_deg","yaw_deg"])
    w_range.writerow(["timestamp","front_m","back_m","left_m","right_m","up_m","zrange_m"])

    try:
        with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:

            cf = scf.cf

            # Callback function for stablizer log
            def lg_stab_callback(timestamp, data, logconf):
                global position_estimate
                position_estimate[0] = data['stateEstimate.x']
                position_estimate[1] = data['stateEstimate.y']

                w_state.writerow([
                    timestamp,
                    data.get("stateEstimate.x", float("nan")),
                    data.get("stateEstimate.y", float("nan")),
                    data.get("stateEstimate.z", float("nan")),
                    data.get("stateEstimate.roll", float("nan")),
                    data.get("stateEstimate.pitch", float("nan")),
                    data.get("stateEstimate.yaw", float("nan")),
                ])


            def lg_range_callback(timestamp, data, logconf):
                data_in_meter = convert_log_to_distance(data)

                w_range.writerow([
                    timestamp,
                    data_in_meter.get("range.front", None),
                    data_in_meter.get("range.back", None),
                    data_in_meter.get("range.left", None),
                    data_in_meter.get("range.right", None),
                    data_in_meter.get("range.up", None),
                    data_in_meter.get("range.zrange", None),
                ])

            
            cf.log.add_config(lg_stab)
            cf.log.add_config(lg_range)
            lg_stab.data_received_cb.add_callback(lg_stab_callback)
            lg_range.data_received_cb.add_callback(lg_range_callback)
        

            print(f"[CF] logging @ {1000/period_ms:.1f} Hz  →  {outdir}/state.csv, range.csv")

            # Arm the Crazyflie
            print("[CF] Send arming request...")
            scf.cf.platform.send_arming_request(True)
            time.sleep(1.0)

            print("[CF] Crazyflie is armed!")

            
            with MotionCommander(scf) as mc:
                lg_stab.start()
                lg_range.start()
                kd = KeyboardDrone(mc, default_height=DEFAULT_HEIGHT)

                # Control by keyboard
                with keyboard.Listener(on_press=kd.on_press, on_release=kd.on_release, suppress=True) as listner:
                    listner.join()
                # raise KeyboardInterrupt

    except KeyboardInterrupt:
        print("\n[CF] Stop Crazyflie")
    finally:
        try:
            state_csv.close()
            range_csv.close()
        except:
            pass

