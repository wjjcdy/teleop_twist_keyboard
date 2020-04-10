#!/usr/bin/env python

from __future__ import print_function

import roslib; roslib.load_manifest('teleop_twist_keyboard')
import rospy

from geometry_msgs.msg import Twist
from std_msgs.msg import Float64
from sensor_msgs.msg import JointState

import sys, select, termios, tty


global Zero_right_en
global Zero_left_en

pub1 = rospy.Publisher('joint_left_position_controller/command', Float64, queue_size = 1)
pub2 = rospy.Publisher('joint_right_position_controller/command', Float64, queue_size = 1)

msg = """
Reading from the keyboard  and Publishing to Twist!
---------------------------
Moving around:
   u    i    o
   j    k    l
   m    ,    .

For Holonomic mode (strafing), hold down the shift key:
---------------------------
   U    I    O
   J    K    L
   M    <    >

t : up (+z)
b : down (-z)

anything else : stop

q/z : increase/decrease max speeds by 10%
w/x : increase/decrease only linear speed by 10%
e/c : increase/decrease only angular speed by 10%

CTRL-C to quit
"""

moveBindings = {
        'i':(1,0,0,0),
        'o':(1,0,0,-1),
        'j':(0,0,0,1),
        'l':(0,0,0,-1),
        'u':(1,0,0,1),
        ',':(-1,0,0,0),
        '.':(-1,0,0,1),
        'm':(-1,0,0,-1),
        'O':(1,-1,0,0),
        'I':(1,0,0,0),
        'J':(0,1,0,0),
        'L':(0,-1,0,0),
        'U':(1,1,0,0),
        '<':(-1,0,0,0),
        '>':(-1,-1,0,0),
        'M':(-1,1,0,0),
        't':(0,0,1,0),
        'b':(0,0,-1,0),
    }

speedBindings={
        'q':(1.1,1.1),
        'z':(.9,.9),
        'w':(1.1,1),
        'x':(.9,1),
        'e':(1,1.1),
        'c':(1,.9),
    }

def getKey():
    tty.setraw(sys.stdin.fileno())
    select.select([sys.stdin], [], [], 0)
    key = sys.stdin.read(1)
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


def vels(speed,turn):
    return "currently:\tspeed %s\tturn %s " % (speed,turn)

def jointStateCallback(state):
    global Zero_right_en
    global Zero_left_en
    if len(state.velocity):
        left_position = state.position[1]
        right_position = state.position[5]
        
        left_vel = state.velocity[1]
        right_vel = state.velocity[5]

        effort_test = Float64()
        effort_test.data = 0

        if abs(left_vel) > 0.001 and abs(left_position) > 3.1415926/4:
            pub1.publish(effort_test)

        if abs(right_vel) > 0.001 and abs(right_position) > 3.1415926/4:
            pub2.publish(effort_test)

        

        if Zero_left_en == 1:
            # if left_position > 0:
            #     effort_test.data = -0.1
            # else:
            #     effort_test.data = 0.1
            effort_test.data = -left_position
            if abs(left_vel) > 0.001 and abs(left_position) < 0.01:
                effort_test.data = 0
                Zero_left_en = 0 
                print("left finished reset")
            pub1.publish(effort_test)
            
        if Zero_right_en == 1:
            # if right_position > 0:
            #     effort_test.data = -0.1
            # else:
            #     effort_test.data = 0.1
            effort_test.data = -right_position
            if abs(right_vel) > 0.001 and abs(right_position) < 0.01:
                effort_test.data = 0
                Zero_right_en = 0 
                print("right finished reset")
            pub2.publish(effort_test)

if __name__=="__main__":
    settings = termios.tcgetattr(sys.stdin)
    
    pub = rospy.Publisher('mobile_base_controller/cmd_vel', Twist, queue_size = 1)
    # pub1 = rospy.Publisher('joint_left_position_controller/command', Float64, queue_size = 1)
    # pub2 = rospy.Publisher('joint_right_position_controller/command', Float64, queue_size = 1)

    global Zero_right_en
    global Zero_left_en
    Zero_right_en = 0
    Zero_left_en = 0 
    odom_sub = rospy.Subscriber('/joint_states',JointState, jointStateCallback)
    rospy.init_node('teleop_twist_keyboard')

    speed = rospy.get_param("~speed", 0.5)
    turn = rospy.get_param("~turn", 1.0)
    x = 0
    y = 0
    z = 0
    th = 0
    status = 0

    effort_data = 0

    try:
        print(msg)
        print(vels(speed,turn))
        while(1):
            key = getKey()
            if key == 'g':
                effort_data = 0.1
                x = 0
                y = 0
                z = 0
                th = 0
            elif key == 'h':
                effort_data = -0.1
                x = 0
                y = 0
                z = 0
                th = 0
            elif key == 'k':
                effort_data = 0
                x = 0
                y = 0
                z = 0
                th = 0
            elif key == 'r':
                effort_data = 0
                x = 0
                y = 0
                z = 0
                th = 0
                Zero_left_en = 1
                Zero_right_en = 1
            elif key in moveBindings.keys():
                x = moveBindings[key][0]
                y = moveBindings[key][1]
                z = moveBindings[key][2]
                th = moveBindings[key][3]
                effort_data = 0
            elif key in speedBindings.keys():
                speed = speed * speedBindings[key][0]
                turn = turn * speedBindings[key][1]

                print(vels(speed,turn))
                if (status == 14):
                    print(msg)
                status = (status + 1) % 15
                effort_data = 0
            else:
                x = 0
                y = 0
                z = 0
                th = 0
                effort_data = 0
                if (key == '\x03'):
                    break

                    

            twist = Twist()
            twist.linear.x = x*speed; twist.linear.y = y*speed; twist.linear.z = z*speed;
            twist.angular.x = 0; twist.angular.y = 0; twist.angular.z = th*turn
            pub.publish(twist)

            effort_test = Float64()
            effort_test.data = effort_data
            pub1.publish(effort_test)
            pub2.publish(effort_test)

    except Exception as e:
        print(e)

    finally:
        twist = Twist()
        twist.linear.x = 0; twist.linear.y = 0; twist.linear.z = 0
        twist.angular.x = 0; twist.angular.y = 0; twist.angular.z = 0
        effort_test = Float64()
        effort_test.data = 0
        pub.publish(twist)
        pub1.publish(effort_test)
        pub2.publish(effort_test)

        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
