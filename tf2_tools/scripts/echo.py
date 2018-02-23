#!/usr/bin/env python

import argparse
import rospy
# import sys
import tf2_py as tf2
import tf2_ros

from geometry_msgs.msg import TransformStamped
# https://github.com/ros/geometry2/issues/222
# from tf import transformations


class Echo():
    def __init__(self, args):
        self.tf_buffer = tf2_ros.Buffer(cache_time=args.cache_time)
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)
        self.args = args

        self.count = 0
        self.timer = rospy.Timer(rospy.Duration(1.0 / self.args.rate), self.lookup)

    def lookup(self, event):
        self.count += 1
        if self.args.limit:
            if self.count > self.args.limit:
                # TODO(lucasw) is there a better method to stop the spin()?
                rospy.signal_shutdown("tf echo finished")
                return

        cur_time = rospy.Time.now()
        # If the transform is from tf_static the ts.header.stamp will be 0.0
        # when offset == 0 or lookup_time is rospy.Time()
        if self.args.time:
            lookup_time = rospy.Time(self.args.time)
        elif self.args.offset:
            # If the transform is static this will always work
            lookup_time = cur_time + rospy.Duration(self.args.offset)
        else:
            # Get the most recent transform
            lookup_time = rospy.Time()

        try:
            ts = self.tf_buffer.lookup_transform(self.args.source_frame,
                                                 self.args.target_frame,
                                                 lookup_time)
	except tf2.LookupException as ex:
            msg = "At time {}, (current time {}) ".format(lookup_time.to_sec(), cur_time.to_sec())
	    rospy.logerr(msg + str(ex))
            return
	except tf2.ExtrapolationException as ex:
            msg = "(current time {}) ".format(cur_time.to_sec())
	    rospy.logerr(msg + str(ex))
            return

        # The old tf1 static_transform_publisher (which published into /tf, not /tf_static
        # publishes transforms 0.5 seconds into future so the cur_time and header stamp
        # will be identical.
        msg = "At time {}, (current time {})".format(ts.header.stamp.to_sec(), cur_time.to_sec())
        xyz = ts.transform.translation
        msg += "\n- Translation: [{:.3f}, {:.3f}, {:.3f}]\n".format(xyz.x, xyz.y, xyz.z)
        quat = ts.transform.rotation
        msg += "- Rotation: in Quaternion [{:.3f}, {:.3f}, {:.3f}, {:.3f}]\n".format(quat.x, quat.y, quat.z, quat.w)
        # TODO(lucasw) need to get quaternion to euler from somewhere, but not tf1
        # or a dependency that isn't in Ubuntu or ros repos
        print msg

def positive_float(x):
    x = float(x)
    if x <= 0.0:
        raise argparse.ArgumentTypeError("{} must be > 0.0".format(x))
    return x

def positive_int(x):
    x = int(x)
    if x <= 0:
        raise argparse.ArgumentTypeError("{} must be > 0".format(x))
    return x

if __name__ == '__main__':
    rospy.init_node("echo")
    parser = argparse.ArgumentParser()
    parser.add_argument("source_frame")  # parent
    parser.add_argument("target_frame")  # child
    parser.add_argument("-r", "--rate",
                        help="update rate, must be > 0.0",
                        default=1.0,
                        type=positive_float)
    parser.add_argument("-c", "--cache_time",
                        help="length of tf buffer cache in seconds",
                        type=positive_float)
    parser.add_argument("-o", "--offset",
                        help="offset the lookup from current time, ignored if using -t",
                        type=float)
    parser.add_argument("-t", "--time",
                        help="fixed time to do the lookup",
                        type=float)
    parser.add_argument("-l", "--limit",
                        help="lookup fixed number of times",
                        type=positive_int)
    args = parser.parse_args()

    echo = Echo(args)
    rospy.spin()
