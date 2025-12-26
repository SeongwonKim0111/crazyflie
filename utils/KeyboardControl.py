from cflib.positioning.motion_commander import MotionCommander


class KeyboardDrone():
    def __init__(self, mc: MotionCommander, default_height):
        self.mc = mc
        self.velocity = 0.3   # 방향 속도 (m/sec)
        self.turnVel = 30 # 회전 속도 (deg/sec)
        self.height = default_height     # 고정 비행 고도
        print("Use keys: w/s = forward/back, a/d = left/right, q/e = (turn) left/right, u/j = up/down, p = quit")

    def on_press(self, key):
        try:
            c = key.char
        except AttributeError:
            return
        if c == 'u':
            self.mc.start_up(self.velocity)
        elif c == 'j':
            self.mc.start_down(self.velocity)
        elif c == 'w':
            self.mc.start_forward(self.velocity)
        elif c == 's':
            self.mc.start_back(self.velocity)
        elif c == 'a':
            self.mc.start_left(self.velocity)
        elif c == 'd':
            self.mc.start_right(self.velocity)
        elif c == 'q':
            self.mc.start_turn_left(self.turnVel)
        elif c =='e':
            self.mc.start_turn_right(self.turnVel)
        elif c == 'p':
            print("Quitting...")
            # stop motion commander and raise to stop listener
            self.mc.stop()
            raise KeyboardInterrupt
        else:
            pass

    def on_release(self, key):
        try:
            c = key.char
        except AttributeError:
            return
        # 키를 뗐을 때 움직임 멈추기
        if c in ('w', 's', 'a', 'd' , 'q', 'e', 'u', 'j'):
            self.mc.stop()