"""
Unit tests for odometry kinematics math.

Tests the differential drive calculations independently from ROS.
"""

import math
import unittest


# Replicate the kinematics logic from odometry_node for testability
def compute_odometry_step(
    left_delta_ticks: float,
    right_delta_ticks: float,
    ticks_per_rev: int,
    wheel_radius: float,
    wheel_base: float,
    x: float,
    y: float,
    theta: float,
):
    """
    Compute one step of differential drive odometry.

    Returns (new_x, new_y, new_theta, delta_s, delta_theta).
    """
    meters_per_tick = (2.0 * math.pi * wheel_radius) / ticks_per_rev

    delta_left = left_delta_ticks * meters_per_tick
    delta_right = right_delta_ticks * meters_per_tick

    delta_s = (delta_right + delta_left) / 2.0
    delta_theta = (delta_right - delta_left) / wheel_base

    new_theta = theta + delta_theta
    new_x = x + delta_s * math.cos(new_theta)
    new_y = y + delta_s * math.sin(new_theta)

    return new_x, new_y, new_theta, delta_s, delta_theta


class TestOdometryKinematics(unittest.TestCase):

    def setUp(self):
        self.wheel_radius = 0.05
        self.wheel_base = 0.3
        self.ticks_per_rev = 1440

    def test_straight_forward(self):
        """Equal ticks on both wheels -> straight line, no rotation."""
        ticks = 100
        x, y, theta, ds, dtheta = compute_odometry_step(
            ticks, ticks,
            self.ticks_per_rev, self.wheel_radius, self.wheel_base,
            0.0, 0.0, 0.0,
        )

        meters_per_tick = (2.0 * math.pi * self.wheel_radius) / self.ticks_per_rev
        expected_dist = ticks * meters_per_tick

        self.assertAlmostEqual(x, expected_dist, places=6)
        self.assertAlmostEqual(y, 0.0, places=6)
        self.assertAlmostEqual(theta, 0.0, places=6)
        self.assertAlmostEqual(dtheta, 0.0, places=6)

    def test_pure_rotation(self):
        """Equal and opposite ticks -> pure rotation, no translation."""
        ticks = 100
        x, y, theta, ds, dtheta = compute_odometry_step(
            -ticks, ticks,
            self.ticks_per_rev, self.wheel_radius, self.wheel_base,
            0.0, 0.0, 0.0,
        )

        self.assertAlmostEqual(ds, 0.0, places=6)
        self.assertNotAlmostEqual(dtheta, 0.0)
        # x and y should stay near zero (pure rotation)
        self.assertAlmostEqual(x, 0.0, places=4)
        self.assertAlmostEqual(y, 0.0, places=4)

    def test_no_motion(self):
        """Zero ticks -> no change."""
        x, y, theta, ds, dtheta = compute_odometry_step(
            0, 0,
            self.ticks_per_rev, self.wheel_radius, self.wheel_base,
            1.0, 2.0, 0.5,
        )

        self.assertAlmostEqual(x, 1.0, places=6)
        self.assertAlmostEqual(y, 2.0, places=6)
        self.assertAlmostEqual(theta, 0.5, places=6)

    def test_turn_right(self):
        """Left wheel moves more than right -> turns right (negative dtheta)."""
        x, y, theta, ds, dtheta = compute_odometry_step(
            200, 100,
            self.ticks_per_rev, self.wheel_radius, self.wheel_base,
            0.0, 0.0, 0.0,
        )

        # Right wheel moves less -> negative angular change (right turn)
        self.assertLess(dtheta, 0.0)
        # Should have moved forward
        self.assertGreater(ds, 0.0)

    def test_turn_left(self):
        """Right wheel moves more than left -> turns left (positive dtheta)."""
        x, y, theta, ds, dtheta = compute_odometry_step(
            100, 200,
            self.ticks_per_rev, self.wheel_radius, self.wheel_base,
            0.0, 0.0, 0.0,
        )

        self.assertGreater(dtheta, 0.0)
        self.assertGreater(ds, 0.0)

    def test_full_revolution_distance(self):
        """One full wheel revolution should travel 2*pi*r distance."""
        ticks = self.ticks_per_rev  # one full revolution
        x, y, theta, ds, dtheta = compute_odometry_step(
            ticks, ticks,
            self.ticks_per_rev, self.wheel_radius, self.wheel_base,
            0.0, 0.0, 0.0,
        )

        expected_circumference = 2.0 * math.pi * self.wheel_radius
        self.assertAlmostEqual(ds, expected_circumference, places=6)
        self.assertAlmostEqual(x, expected_circumference, places=6)

    def test_initial_heading(self):
        """Starting at theta=pi/2, forward motion should go in +y direction."""
        ticks = 100
        x, y, theta, ds, dtheta = compute_odometry_step(
            ticks, ticks,
            self.ticks_per_rev, self.wheel_radius, self.wheel_base,
            0.0, 0.0, math.pi / 2.0,
        )

        self.assertAlmostEqual(x, 0.0, places=4)
        self.assertGreater(y, 0.0)


if __name__ == '__main__':
    unittest.main()
