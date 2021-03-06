#
# Copyright (c) 2020 FRC Team 3260
#

import unittest
from unittest.mock import Mock
from planning import Planning
from geometry import Polygon
from tests.test_utils import *


class TestWorldStatePreprocessor(unittest.TestCase):
    def setUp(self):
        config = Mock()
        config.field_columns = []
        config.field_trenches = []
        config.alliance = "Blue"
        config.blue_goal_region = Polygon(make_square_vertices(side_length=0.5, center=(-2.5, -3.5)))
        config.blue_chute_pos = np.array([10, 10])
        config.occupancy_grid_num_cols = 6
        config.occupancy_grid_num_rows = 6
        config.occupancy_grid_cell_resolution = 1
        config.occupancy_grid_origin = (0, 0)
        config.occupancy_grid_dilation_kernel_size = 3
        config.ball_probability_decay_factor = 1
        config.ball_probability_growth_factor = 1
        config.ball_probability_threshold = 1
        config.obstacle_probability_decay_factor = 1
        config.obstacle_probability_growth_factor = 1
        config.obstacle_probability_threshold = 1
        config.lidar_deadzone_radius = 1.0

        self.planning = Planning(config)

    def test_robot_remembers_balls_within_lidar_deadzone(self):
        world_state = {
            'pose': ((0, 0), 0),
            'balls': [(0.5, 0.5)],
            'obstacles': []
        }

        self.planning.preprocess_world_state(world_state)

        world_state = {
            'pose': ((0, 0), 0),
            'numIngestedBalls': 0,
            'balls': [],
            'obstacles': [],
        }

        self.planning.preprocess_world_state(world_state)

        expected = {
            'pose': ((0, 0), 0),
            'numIngestedBalls': 0,
            'balls': [(0.5, 0.5)],
            'obstacles': [],
        }
        actual = world_state
        self.assertEqual(expected, actual)

    def test_robot_forgets_balls_outside_lidar_deadzone(self):
        world_state = {
            'pose': ((0, 0), 0),
            'balls': [(2.5, 2.5)],
            'obstacles': []
        }

        self.planning.preprocess_world_state(world_state)

        world_state = {
            'pose': ((0, 0), 0),
            'numIngestedBalls': 0,
            'balls': [],
            'obstacles': [],
        }

        self.planning.preprocess_world_state(world_state)

        expected = {
            'pose': ((0, 0), 0),
            'numIngestedBalls': 0,
            'balls': [],
            'obstacles': [],
        }
        actual = world_state
        self.assertEqual(expected, actual)

    def test_robot_forgets_obstacles_that_appear_sporadically(self):
        world_state = {
            'pose': ((0, 0), 0),
            'balls': [],
            'obstacles': [((-1, -1), (1, 1))]
        }

        self.planning.preprocess_world_state(world_state)

        world_state = {
            'pose': ((0, 0), 0),
            'numIngestedBalls': 0,
            'balls': [],
            'obstacles': [],
        }

        self.planning.preprocess_world_state(world_state)

        expected = {
            'pose': ((0, 0), 0),
            'numIngestedBalls': 0,
            'balls': [],
            'obstacles': [],
        }
        actual = world_state
        self.assertEqual(expected, actual)


class TestBehaviorPlanning(unittest.TestCase):
    def setUp(self):
        self.config = Mock()
        self.config.alliance = "Blue"
        self.config.blue_goal_region = Polygon(make_square_vertices(side_length=0.5, center=(-2.5, -3.5)))
        self.config.blue_chute_pos = np.array([10, 10])
        self.config.occupancy_grid_num_cols = 6
        self.config.occupancy_grid_num_rows = 6
        self.config.occupancy_grid_cell_resolution = 1
        self.config.occupancy_grid_origin = (0, 0)
        self.config.occupancy_grid_dilation_kernel_size = 3
        self.config.ball_probability_decay_factor = 0
        self.config.ball_probability_growth_factor = 1
        self.config.ball_probability_threshold = 1
        self.config.obstacle_probability_decay_factor = 0
        self.config.obstacle_probability_growth_factor = 1
        self.config.obstacle_probability_threshold = 1
        self.config.lidar_deadzone_radius = 0.85

        self.planning = Planning(self.config)

    def test_robot_runs_intake_and_goes_to_nearest_ball_while_far_from_goal_and_has_fewer_than_five_balls(self):
        world_state = {
            'pose': ((0, 0), 0),
            'numIngestedBalls': 0,
            'balls': [(2.5, 2.5)],
            'obstacles': []
        }

        self.planning.behavior_planning(world_state)

        expected = {
            'goal': (2.5, 2.5),
            'direction': 1,
            'tube_mode': 'INTAKE'
        }
        actual = {k: world_state[k] for k in ('goal', 'direction', 'tube_mode')}
        self.assertEqual(expected, actual)

    def test_robot_drives_to_goal_backwards_when_it_has_five_balls_and_is_far_from_goal(self):
        world_state = {
            'pose': ((0, 0), 0),
            'numIngestedBalls': 5,
            'balls': [(2.5, 2.5)],
            'obstacles': []
        }

        self.planning.behavior_planning(world_state)

        expected = {
            'goal': self.planning.scoring_zone,
            'direction': -1,
            'tube_mode': 'INTAKE',
            'flail': False,
        }
        actual = {k: world_state[k] for k in ('goal', 'direction', 'tube_mode', 'flail')}
        self.assertEqual(expected, actual)

    def test_robot_scores_when_it_has_five_balls_and_is_at_goal(self):
        world_state = {
            'pose': ((-2.5, -2.5), 0),
            'numIngestedBalls': 5,
            'balls': [(2.5, 2.5)],
            'obstacles': []
        }

        self.planning.behavior_planning(world_state)

        expected = {
            'goal': self.planning.scoring_zone,
            'direction': 0,
            'tube_mode': 'OUTTAKE',
            'flail': False,
        }
        actual = {k: world_state[k] for k in ('goal', 'direction', 'tube_mode', 'flail')}
        self.assertEqual(expected, actual)

    def test_robot_stays_at_goal_while_scoring(self):
        world_state = {
            'pose': ((-2.5, -2.5), 0),
            'numIngestedBalls': 4,
            'balls': [(2.5, 2.5)],
            'obstacles': []
        }

        self.planning.behavior_planning(world_state)

        expected = {
            'goal': self.planning.scoring_zone,
            'direction': 0,
            'tube_mode': 'OUTTAKE',
            'flail': False,
        }
        actual = {k: world_state[k] for k in ('goal', 'direction', 'tube_mode', 'flail')}
        self.assertEqual(expected, actual)

    def test_robot_flails_when_inside_obstacle(self):
        world_state = {
            'pose': ((0, 0), 0),
            'numIngestedBalls': 0,
            'balls': [],
            'obstacles': []
        }

        self.planning.obstacle_grid.occupancy[:,:] = 1
        self.planning.behavior_planning(world_state)

        self.assertTrue(world_state['flail'])


class TestMotionPlanning(unittest.TestCase):
    def setUp(self):
        self.config = Mock()
        self.config.field_columns = []
        self.config.field_trenches = []
        self.config.occupancy_grid_num_cols = 6
        self.config.occupancy_grid_num_rows = 6
        self.config.occupancy_grid_cell_resolution = 1
        self.config.occupancy_grid_origin = (0, 0)
        self.config.occupancy_grid_dilation_kernel_size = 3
        self.config.ball_probability_decay_factor = 0
        self.config.ball_probability_growth_factor = 1
        self.config.ball_probability_threshold = 1
        self.config.obstacle_probability_decay_factor = 0
        self.config.obstacle_probability_growth_factor = 1
        self.config.obstacle_probability_threshold = 1
        self.config.alliance = "Blue"
        self.config.blue_goal_region = Polygon(make_square_vertices(side_length=0.5, center=(-2.5, -2.5)))
        self.config.blue_chute_pos = np.array([10, 10])

        self.pose = ((-2.5, -2.5), 0)
        self.goal = (2.5, 2.5)

        self.planning = Planning(self.config)

    def test_motion_planning_with_empty_world(self):
        world_state = {
            'obstacles': [],
            'pose': self.pose,
            'goal': self.goal,
            'flail': False,
        }

        self.planning.motion_planning(world_state)

        expected_trajectory_length = 2
        actual_trajectory_length = len(world_state['trajectory'])
        expected_occupancy_grid = np.zeros(shape=(6,6))
        actual_occupancy_grid = world_state['grid'].occupancy

        self.assertEqual(expected_trajectory_length, actual_trajectory_length)
        np.testing.assert_array_equal(expected_occupancy_grid, actual_occupancy_grid)

    def test_motion_planning_avoids_obstacles(self):
        self.planning.obstacle_grid.occupancy[1:5,1:5] = 1

        world_state = {
            'obstacles': [],
            'pose': self.pose,
            'goal': self.goal,
            'flail': False,
        }

        self.planning.motion_planning(world_state)

        expected_occupancy_grid = np.zeros(shape=(6,6), dtype=np.uint8)
        expected_occupancy_grid[1:5,1:5] = np.ones(shape=(4,4))
        actual_occupancy_grid = world_state['grid'].occupancy
        expected_trajectory_length = 4

        actual_trajectory_length = len(world_state['trajectory'])
        np.testing.assert_array_equal(expected_occupancy_grid, actual_occupancy_grid)
        self.assertEqual(expected_trajectory_length, actual_trajectory_length)

    def test_motion_planning_returns_none_when_no_feasible_trajectory(self):
        world_state = {
            'obstacles': [((1, 1), (2, 2))],
            'pose': self.pose,
            'goal': self.goal,
            'flail': False,
        }

        goal_cell = self.planning.obstacle_grid.get_cell(self.goal)
        self.planning.obstacle_grid.occupancy[goal_cell.indices] = 1
        self.planning.motion_planning(world_state)

        self.assertIsNone(world_state['trajectory'])

    def test_motion_planning_returns_trivial_plan_when_goal_reached(self):
        world_state = {
            'obstacles': [],
            'pose': self.pose,
            'goal': self.pose[0],
            'flail': False,
        }

        self.planning.motion_planning(world_state)

        expected = 2
        actual = len(world_state['trajectory'])
        self.assertEqual(expected, actual)

    def test_flail_returns_no_trajectory(self):
        world_state = {
            'obstacles': [],
            'pose': self.pose,
            'goal': self.pose[0],
            'flail': True,
        }

        self.planning.motion_planning(world_state)

        self.assertIsNone(world_state['trajectory'])


class TestRun(unittest.TestCase):
    def setUp(self):
        self.config = Mock()
        self.config.field_columns = []
        self.config.field_trenches = []
        self.config.alliance = "Blue"
        self.config.blue_goal_region = Polygon(make_square_vertices(side_length=0.5, center=(-2.5, -3.5)))
        self.config.blue_chute_pos = np.array([10, 10])
        self.config.occupancy_grid_num_cols = 6
        self.config.occupancy_grid_num_rows = 6
        self.config.occupancy_grid_cell_resolution = 1
        self.config.occupancy_grid_origin = (0, 0)
        self.config.occupancy_grid_dilation_kernel_size = 3
        self.config.ball_probability_decay_factor = 0
        self.config.ball_probability_growth_factor = 1
        self.config.ball_probability_threshold = 1
        self.config.obstacle_probability_decay_factor = 0
        self.config.obstacle_probability_growth_factor = 1
        self.config.obstacle_probability_threshold = 1

        self.planning = Planning(self.config)

    def test_run(self):
        world_state = {
            'pose': ((-2.5, -2.5), 0),
            'balls': [(2.5, 2.5)],
            'obstacles': [],
            'numIngestedBalls': 0,
        }

        self.planning.run(world_state)

        expected = 2
        actual = len(world_state['trajectory'])

        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
