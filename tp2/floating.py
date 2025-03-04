"""
Variation of the invgeom3d.py example, using a floating robot.
This test exhibits that the quaternion should be kept of norm=1
when computing the robot configuration. Otherwise, a nonunit quaternion
does not correspond to any meaningful rotation. Here the viewer tends
to interpret this nonunit quaternion as the composition of a rotation
and a nonhomogeneous scaling, leading to absurd 3d display.
When the quaternion is explicitly kept of norm 1, everything works
fine and similarly to the unconstrained case.
"""

import time
import unittest

import example_robot_data as robex
import numpy as np
import pinocchio as pin
from numpy.linalg import norm
from scipy.optimize import fmin_bfgs

from supaero2024.meshcat_viewer_wrapper import MeshcatVisualizer

# --- Load robot model
# Solo12 is a quadruped robot. Its configuration is composed of:
# - 3 first coefficients are the translation of the basis
# - 4 next coefficients are the quaternion representing the rotation of the basis
# - then each leg has a configuration of dimension 3 (hip roll and pitch, knee pitch).
robot = robex.load("solo12")
NQ = robot.model.nq
NV = robot.model.nv

# Open the viewer
viz = MeshcatVisualizer(robot)
viz.display(robot.q0)

# %jupyter_snippet 1
robot.feetIndexes = [
    robot.model.getFrameId(frameName)
    for frameName in ["HR_FOOT", "HL_FOOT", "FR_FOOT", "FL_FOOT"]
]

# --- Add box to represent target
# We define 4 targets, one for each leg.
colors = ["red", "blue", "green", "magenta"]
for color in colors:
    viz.addSphere("world/%s" % color, 0.05, color)
    viz.addSphere("world/%s_des" % color, 0.05, color)

#
# OPTIM 6D #########################################################
#

targets = [
    np.array([-0.7, -0.2, 1.2]),
    np.array([-0.3, 0.5, 0.8]),
    np.array([0.3, 0.1, -0.1]),
    np.array([0.9, 0.9, 0.5]),
]
for i in range(4):
    targets[i][2] += 1


def cost(q):
    """
    Compute score from a configuration: sum of the 4 reaching
    tasks, one for each leg.
    """
    cost = 0.0
    for i in range(4):
        p_i = robot.framePlacement(q, robot.feetIndexes[i]).translation
        cost += norm(p_i - targets[i]) ** 2
    return cost


def callback(q):
    """
    Diplay the robot, postion a ball of different color for
    each foot, and the same ball of same color for the location
    of the corresponding target.
    """
    for i in range(4):
        p_i = robot.framePlacement(q, robot.feetIndexes[i])
        viz.applyConfiguration("world/%s" % colors[i], p_i)
        viz.applyConfiguration(
            "world/%s_des" % colors[i], list(targets[i]) + [1, 0, 0, 0]
        )

    viz.display(q)
    time.sleep(1e-2)

qopt = fmin_bfgs(cost, robot.q0, callback=callback)
# %end_jupyter_snippet


### TEST ZONE ############################################################
### This last part is to automatically validate the versions of this example.
class FloatingTest(unittest.TestCase):
    def test_cost(self):
        self.assertLess(cost(qopt), 1e-10)


FloatingTest().test_cost()
