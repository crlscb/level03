"""Unit tests for the Fly-in domain model.

Run with:
    pytest -v tests/test_models.py
or:
    python -m unittest discover -v
"""

import unittest

from models import Connection, Drone, Map, Simulation, Zone


class TestZone(unittest.TestCase):
    """Tests for zone validation and defaults."""

    def test_default_values(self) -> None:
        zone = Zone("hub", 0, 0)
        self.assertEqual(zone.zone_type, "normal")
        self.assertIsNone(zone.color)
        self.assertEqual(zone.max_drones, 1)

    def test_invalid_zone_type_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Zone("bad", 0, 0, "unknown")

    def test_non_positive_capacity_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Zone("bad", 0, 0, max_drones=0)


class TestConnection(unittest.TestCase):
    """Tests for connection validation and direction-independent links."""

    def setUp(self) -> None:
        self.a = Zone("a", 0, 0, max_drones=None)
        self.b = Zone("b", 1, 0)

    def test_connection_is_bidirectional(self) -> None:
        connection = Connection(self.a, self.b)
        self.assertTrue(connection.connects(self.a, self.b))
        self.assertTrue(connection.connects(self.b, self.a))

    def test_non_positive_link_capacity_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Connection(self.a, self.b, max_link_capacity=0)

    def test_self_connection_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Connection(self.a, self.a)


class TestMap(unittest.TestCase):
    """Tests for map membership, links, and pathfinding."""

    def setUp(self) -> None:
        self.drone_map = Map()
        self.start = Zone("start", 0, 0, max_drones=None)
        self.middle = Zone("middle", 1, 0)
        self.goal = Zone("goal", 2, 0, max_drones=None)
        for zone in (self.start, self.middle, self.goal):
            self.drone_map.add_zone(zone)
        self.drone_map.add_connection(Connection(self.start, self.middle))
        self.drone_map.add_connection(Connection(self.middle, self.goal))

    def test_find_zone_and_neighbors(self) -> None:
        self.assertIs(self.drone_map.get_zone("middle"), self.middle)
        self.assertIsNone(self.drone_map.get_zone("missing"))
        self.assertEqual(
            set(self.drone_map.get_neighbors(self.middle)),
            {self.start, self.goal},
        )

    def test_duplicate_zone_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.drone_map.add_zone(Zone("start", 9, 9))

    def test_duplicate_connection_is_rejected_even_reversed(self) -> None:
        with self.assertRaises(ValueError):
            self.drone_map.add_connection(Connection(self.middle, self.start))

    def test_find_route_and_route_cost(self) -> None:
        route = self.drone_map.find_route(self.start, self.goal)
        self.assertEqual(route, [self.start, self.middle, self.goal])
        self.assertEqual(self.drone_map.get_route_cost(route), 2)

    def test_restricted_zone_costs_two_turns(self) -> None:
        restricted = Zone("restricted", 1, 1, "restricted")
        self.assertEqual(self.drone_map.get_movement_cost(restricted), 2)

    def test_blocked_zone_is_not_used_by_pathfinder(self) -> None:
        blocked_map = Map()
        start = Zone("start", 0, 0, max_drones=None)
        blocked = Zone("blocked", 1, 0, "blocked")
        goal = Zone("goal", 2, 0, max_drones=None)
        for zone in (start, blocked, goal):
            blocked_map.add_zone(zone)
        blocked_map.add_connection(Connection(start, blocked))
        blocked_map.add_connection(Connection(blocked, goal))
        with self.assertRaises(ValueError):
            blocked_map.find_route(start, goal)


class TestDrone(unittest.TestCase):
    """Tests for individual drone movement and route setup."""

    def setUp(self) -> None:
        self.drone_map = Map()
        self.start = Zone("start", 0, 0, max_drones=None)
        self.next_zone = Zone("next", 1, 0)
        self.blocked = Zone("blocked", 0, 1, "blocked")
        for zone in (self.start, self.next_zone, self.blocked):
            self.drone_map.add_zone(zone)
        self.drone_map.add_connection(Connection(self.start, self.next_zone))
        self.drone_map.add_connection(Connection(self.start, self.blocked))
        self.drone = Drone(1, self.start, self.drone_map)

    def test_move_to_connected_zone(self) -> None:
        self.drone.move_one_step(self.next_zone)
        self.assertIs(self.drone.current_zone, self.next_zone)
        self.assertEqual(self.drone.route_position, 1)

    def test_cannot_move_to_blocked_zone(self) -> None:
        with self.assertRaises(ValueError):
            self.drone.move_to(self.blocked)

    def test_route_must_start_at_current_zone(self) -> None:
        with self.assertRaises(ValueError):
            self.drone.follow_route([self.next_zone])


class TestSimulation(unittest.TestCase):
    """Tests for turn scheduling, capacities, and restricted transit."""

    def setUp(self) -> None:
        self.drone_map = Map()
        self.start = Zone("start", 0, 0, max_drones=None)
        self.restricted = Zone(
            "restricted", 1, 0, "restricted", max_drones=1
        )
        self.goal = Zone("goal", 2, 0, max_drones=None)
        for zone in (self.start, self.restricted, self.goal):
            self.drone_map.add_zone(zone)
        self.start_restricted = Connection(
            self.start, self.restricted, max_link_capacity=2
        )
        self.restricted_goal = Connection(self.restricted, self.goal)
        self.drone_map.add_connection(self.start_restricted)
        self.drone_map.add_connection(self.restricted_goal)

    def test_all_drones_start_in_start_zone(self) -> None:
        simulation = Simulation(3, self.start, self.drone_map)
        self.assertEqual(len(simulation.drones), 3)
        self.assertEqual(simulation.count_drones_in_zone(self.start), 3)

    def test_two_drones_do_not_reserve_one_restricted_slot(self) -> None:
        simulation = Simulation(2, self.start, self.drone_map)
        for drone in simulation.drones:
            drone.follow_route([self.start, self.restricted, self.goal])

        simulation.run_turn()

        drones_in_transit = [
            drone for drone in simulation.drones if drone.in_transit
        ]
        self.assertEqual(len(drones_in_transit), 1)
        self.assertEqual(
            simulation.zone_arrival_reservations.get(self.restricted, 0), 1
        )
        self.assertLessEqual(
            simulation.zone_arrival_reservations.get(self.restricted, 0), 1
        )

    def test_restricted_transit_arrives_and_releases_reservation(self) -> None:
        simulation = Simulation(1, self.start, self.drone_map)
        drone = simulation.drones[0]
        drone.follow_route([self.start, self.restricted, self.goal])

        simulation.run_turn()
        self.assertTrue(drone.in_transit)
        self.assertEqual(
            simulation.zone_arrival_reservations.get(self.restricted, 0), 1
        )

        simulation.run_turn()
        self.assertFalse(drone.in_transit)
        self.assertIs(drone.current_zone, self.restricted)
        self.assertEqual(
            simulation.zone_arrival_reservations.get(self.restricted, 0), 0
        )
        self.assertEqual(simulation.count_drones_in_zone(self.restricted), 1)

    def test_normal_zone_capacity_allows_only_one_entry(self) -> None:
        normal_map = Map()
        start = Zone("start", 0, 0, max_drones=None)
        middle = Zone("middle", 1, 0, max_drones=1)
        goal = Zone("goal", 2, 0, max_drones=None)
        for zone in (start, middle, goal):
            normal_map.add_zone(zone)
        normal_map.add_connection(Connection(start, middle, 2))
        normal_map.add_connection(Connection(middle, goal))

        simulation = Simulation(2, start, normal_map)
        for drone in simulation.drones:
            drone.follow_route([start, middle, goal])

        simulation.run_turn()
        self.assertEqual(simulation.count_drones_in_zone(middle), 1)
        self.assertLessEqual(simulation.count_drones_in_zone(middle), 1)

    def test_simulation_constructor_rejects_zero_drones(self) -> None:
        with self.assertRaises(ValueError):
            Simulation(0, self.start, self.drone_map)


if __name__ == "__main__":
    unittest.main()
