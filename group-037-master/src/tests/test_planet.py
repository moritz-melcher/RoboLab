#!/usr/bin/env python3

import unittest
from planet import Direction, Planet
from typing import List, Tuple, Dict, Union, get_type_hints


class ExampleTestPlanet(unittest.TestCase):
    def setUp(self):
        print("DEBUG")
        """
        Instantiates the planet data structure and fills it with paths

        +--+
        |  |
        +-0,3------+
           |       |
          0,2-----2,2 (target)
           |      /
        +-0,1    /
        |  |    /
        +-0,0-1,0
           |
        (start)

        """
        # Initialize your data structure here
        self.planet = Planet()
        self.planet.add_path(((0, 0), Direction.NORTH), ((0, 1), Direction.SOUTH), 1)
        self.planet.add_path(((0, 1), Direction.WEST), ((0, 0), Direction.WEST), 1)
        print(self.paths)

    @unittest.skip('Example test, should not count in final test results')
    def test_target_not_reachable_with_loop(self):
        """
        This test should check that the shortest-path algorithm does not get stuck in a loop between two points while
        searching for a target not reachable nearby

        Result: Target is not reachable
        """
        self.assertIsNone(self.planet.shortest_path((0, 0), (1, 2)))


class TestRoboLabPlanet(unittest.TestCase):
    def setUp(self):
        """
        Instantiates the planet data structure and fills it with paths

        MODEL YOUR TEST PLANET HERE (if you'd like):

        """
        # Initialize your data structure here
        self.planet = Planet()
        self.planet.add_path(((0,0), Direction.NORTH), ((0,1), Direction.NORTH), 3)
        self.planet.add_path(((0,0), Direction.SOUTH), ((1,0), Direction.NORTH), 5)
        self.planet.add_path(((0,1), Direction.SOUTH), ((1,1), Direction.NORTH), 4)
        self.planet.add_path(((1,0), Direction.EAST), ((1,1), Direction.WEST), 1)
        self.planet.add_path(((1,0), Direction.SOUTH), ((2,1), Direction.NORTH), 2)
        self.planet.add_path(((2,0), Direction.EAST), ((2,1), Direction.WEST), 7)
        self.planet.add_path(((2,1), Direction.EAST), ((2,2), Direction.WEST), 1)
        self.planet.add_path(((1,1), Direction.EAST), ((1,2), Direction.WEST), 2)
        self.planet.add_path(((1,2), Direction.EAST), ((1,2), Direction.SOUTH), 4)
        self.planet.add_path(((0,2), Direction.SOUTH), ((1,2), Direction.NORTH), 1)
        self.planet.add_path(((0,1), Direction.WEST), ((1,0), Direction.WEST), 1)
        
    def test_integrity(self):
        print("\ntest_integrity")
        paths = self.planet.get_paths()
        self.assertEqual(type(paths), dict)
        for key in paths:
            self.assertEqual(type(key), tuple)
            for i in key:
                self.assertEqual(type(i), int)
            val = paths[key]
            self.assertEqual(type(val), dict)
            for keys in val:
                vals = val[keys]
                self.assertEqual(type(keys), Direction)
                self.assertEqual(type(vals), tuple)
                self.assertEqual(type(vals[0]), tuple)
                self.assertEqual(type(vals[0][0]), int)
                self.assertEqual(type(vals[0][1]), int)
                self.assertEqual(type(vals[1]), Direction)
                self.assertEqual(type(vals[2]), int)
        #self.assertEqual(get_type_hints(self.planet.get_paths), Dict[Tuple[int, int], Dict[Direction, Tuple[Tuple[int, int], Direction, int]]])
        """
        This test should check that the dictionary returned by "planet.get_paths()" matches the expected structure
        """
        
        #self.fail('implement me!')

    def test_empty_planet(self):
        print("\ntest_empty_planet")
        empty_planet = Planet()
        self.assertEqual(empty_planet.paths, {})
        self.assertEqual(empty_planet.points, [])
        self.assertEqual(empty_planet.checked_points, [])
        """
        This test should check that an empty planet really is empty
        """

    def test_target(self):
        print("\ntest_target")
        spath = self.planet.shortest_path((0,0),(1,1))
        spath_should = [((0, 0), Direction.NORTH), ((0, 1), Direction.WEST), ((1, 0), Direction.EAST)]
        self.assertCountEqual(spath, spath_should)
        
        spath = self.planet.shortest_path((2,0),(0,2))
        spath_should = [((2,0), Direction.EAST),((2,1), Direction.NORTH),((1,0), Direction.EAST), ((1,1), Direction.EAST), ((1,2), Direction.NORTH)]
        self.assertEqual(spath, spath_should)

        self.assertEqual(type(spath), list)
        """
        This test should check that the shortest-path algorithm implemented works.

        Requirement: Minimum distance is three nodes (two paths in list returned)
    """

    def test_target_not_reachable(self):
        print("\ntest_target_not_reachable")
        self.assertIsNone(self.planet.shortest_path((0,0),(0,3)))

        self.planet.add_path(((2,0), Direction.EAST), ((2,1), Direction.WEST), -1)

        self.assertIsNone(self.planet.shortest_path((0,0),(2,0)))
        self.assertIsNone(self.planet.shortest_path((2,0),(1,1)))

        self.assertIsNone(self.planet.shortest_path((0,0),(0,0)))
        """
        This test should check that a target outside the map or at an unexplored node is not reachable
        """

    def test_same_length(self):
        print("\ntest_same_length")
        self.planet.add_path(((1,1), Direction.SOUTH), ((2,1), Direction.NORTH), 1)
        self.planet.add_path(((1,0), Direction.SOUTH), ((2,1), Direction.SOUTH), 3)
        self.assertIsNotNone(self.planet.shortest_path((0,0),(2,1)))


        """
        This test should check that the shortest-path algorithm implemented returns a shortest path even if there
        are multiple shortest paths with the same length.

        Requirement: Minimum of two paths with same cost exists, only one is returned by the logic implemented
        """

    def test_target_with_loop(self):
        print("\ntest_target_with_loop")
        self.assertIsNotNone(self.planet.shortest_path((1,1),(0,2)))
        """
        This test should check that the shortest-path algorithm does not get stuck in a loop between two points while
        searching for a target nearby

        Result: Target is reachable
        """

    def test_target_not_reachable_with_loop(self):
        print("\ntest_target_not_reachable_with_loop")
        self.planet.add_path(((1,1), Direction.EAST), ((1,2), Direction.EAST), -1)

        self.assertIsNone(self.planet.shortest_path((0,0), (1,2)))
        """
        This test should check that the shortest-path algorithm does not get stuck in a loop between two points while
        searching for a target not reachable nearby

        Result: Target is not reachable
        """


if __name__ == "__main__":
    unittest.main()
