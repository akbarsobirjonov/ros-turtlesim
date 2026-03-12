#!/usr/bin/env python3
import math
import threading

import rospy
from geometry_msgs.msg import Twist
from turtlesim.srv import Spawn, TeleportAbsolute, SetPen


RATE_HZ = 80
LINEAR_SPEED = 1.2
ANGULAR_SPEED = 2.0
PEN_WIDTH = 4


def normalize_angle(angle):
    while angle > math.pi:
        angle -= 2 * math.pi
    while angle < -math.pi:
        angle += 2 * math.pi
    return angle


class TurtleArtist:
    def __init__(self, name):
        self.name = name
        self.pub = rospy.Publisher(f'/{name}/cmd_vel', Twist, queue_size=10)

        rospy.wait_for_service(f'/{name}/teleport_absolute')
        rospy.wait_for_service(f'/{name}/set_pen')

        self.teleport_srv = rospy.ServiceProxy(
            f'/{name}/teleport_absolute', TeleportAbsolute
        )
        self.pen_srv = rospy.ServiceProxy(
            f'/{name}/set_pen', SetPen
        )

        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0

    def stop(self):
        self.pub.publish(Twist())

    def set_pen(self, enabled, width=PEN_WIDTH, r=0, g=0, b=0):
        self.pen_srv(r, g, b, width, 0 if enabled else 1)

    def goto(self, x, y, theta=0.0):
        self.set_pen(False)
        self.teleport_srv(x, y, theta)
        self.x = x
        self.y = y
        self.theta = theta
        self.stop()
        rospy.sleep(0.03)

    def _publish_for(self, linear_x, angular_z, seconds):
        msg = Twist()
        msg.linear.x = linear_x
        msg.angular.z = angular_z

        rate = rospy.Rate(RATE_HZ)
        end_time = rospy.Time.now() + rospy.Duration.from_sec(seconds)

        while not rospy.is_shutdown() and rospy.Time.now() < end_time:
            self.pub.publish(msg)
            rate.sleep()

        self.stop()
        rospy.sleep(0.01)

    def line(self, distance):
        if abs(distance) < 1e-6:
            return

        speed = LINEAR_SPEED if distance >= 0 else -LINEAR_SPEED
        self._publish_for(speed, 0.0, abs(distance) / LINEAR_SPEED)

        self.x += distance * math.cos(self.theta)
        self.y += distance * math.sin(self.theta)

    def turn(self, angle):
        if abs(angle) < 1e-6:
            return

        speed = ANGULAR_SPEED if angle >= 0 else -ANGULAR_SPEED
        self._publish_for(0.0, speed, abs(angle) / ANGULAR_SPEED)
        self.theta = normalize_angle(self.theta + angle)

    def turn_to(self, target_theta):
        self.turn(normalize_angle(target_theta - self.theta))

    def draw_to(self, x, y):
        dx = x - self.x
        dy = y - self.y
        dist = math.hypot(dx, dy)

        if dist < 1e-6:
            return

        target_theta = math.atan2(dy, dx)
        self.turn_to(target_theta)
        self.line(dist)

    def draw_polyline(self, points):
        if len(points) < 2:
            return

        x0, y0 = points[0]
        x1, y1 = points[1]
        theta0 = math.atan2(y1 - y0, x1 - x0)

        self.goto(x0, y0, theta0)
        self.set_pen(True, width=PEN_WIDTH)

        for px, py in points[1:]:
            self.draw_to(px, py)

        self.stop()
        rospy.sleep(0.03)

    def draw_segments(self, segments):
        for seg in segments:
            self.draw_polyline(seg)


def safe_spawn(name, x, y, theta):
    rospy.wait_for_service('/spawn')
    spawn_srv = rospy.ServiceProxy('/spawn', Spawn)

    try:
        spawn_srv(x, y, theta, name)
    except rospy.ServiceException:
        rospy.logwarn(f'{name} already exists, continue...')


def scale_points(points, x0, y0, w, h):
    return [(x0 + px * w, y0 + py * h) for px, py in points]


# ---------------- DIGITS ----------------

def digit_0(x0, y0, w, h):
    # Более ровный и компактный 0
    pts = scale_points([
        (0.50, 1.00),
        (0.70, 0.95),
        (0.84, 0.82),
        (0.92, 0.60),
        (0.90, 0.35),
        (0.80, 0.14),
        (0.62, 0.02),
        (0.40, 0.02),
        (0.22, 0.14),
        (0.10, 0.35),
        (0.08, 0.60),
        (0.16, 0.82),
        (0.30, 0.95),
        (0.50, 1.00),
    ], x0, y0, w, h)

    return [pts]


def digit_1(x0, y0, w, h):
    main = scale_points([
        (0.25, 0.78),
        (0.50, 1.00),
        (0.50, 0.00),
    ], x0, y0, w, h)

    base = scale_points([
        (0.30, 0.00),
        (0.72, 0.00),
    ], x0, y0, w, h)

    return [main, base]


def digit_2(x0, y0, w, h):
    pts = scale_points([
        (0.12, 0.82),
        (0.20, 0.94),
        (0.38, 1.00),
        (0.58, 0.98),
        (0.76, 0.90),
        (0.88, 0.78),
        (0.86, 0.62),
        (0.74, 0.50),
        (0.56, 0.38),
        (0.36, 0.24),
        (0.20, 0.10),
        (0.12, 0.00),
        (0.90, 0.00),
    ], x0, y0, w, h)

    return [pts]


# ---------------- THREAD WORK ----------------

def worker(artist, start_event, segments):
    start_event.wait()
    artist.draw_segments(segments)
    artist.set_pen(False)
    artist.stop()


def main():
    rospy.init_node('draw_0212_simple_style_fixed')

    # turtle1 уже существует
    safe_spawn('turtle2', 2.0, 2.0, 0.0)
    safe_spawn('turtle3', 2.0, 2.0, 0.0)
    safe_spawn('turtle4', 2.0, 2.0, 0.0)

    t1 = TurtleArtist('turtle1')
    t2 = TurtleArtist('turtle2')
    t3 = TurtleArtist('turtle3')
    t4 = TurtleArtist('turtle4')

    rospy.sleep(0.5)

    # размеры
    w = 1.10
    h = 3.60
    y0 = 3.05

    # фиксированные позиции: 0 и первая 2 сдвинуты правее
    x0 = 1.70
    x1 = 3.50
    x2 = 5.45
    x3 = 7.35

    # 0 2 1 2
    seg0 = digit_0(x0, y0, w, h)
    seg2a = digit_2(x1, y0, w, h)
    seg1 = digit_1(x2, y0, w, h)
    seg2b = digit_2(x3, y0, w, h)

    start_event = threading.Event()

    threads = [
        threading.Thread(target=worker, args=(t1, start_event, seg0)),
        threading.Thread(target=worker, args=(t2, start_event, seg2a)),
        threading.Thread(target=worker, args=(t3, start_event, seg1)),
        threading.Thread(target=worker, args=(t4, start_event, seg2b)),
    ]

    for th in threads:
        th.start()

    rospy.sleep(0.5)
    start_event.set()

    for th in threads:
        th.join()

    rospy.loginfo("0212 drawn correctly.")


if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass
