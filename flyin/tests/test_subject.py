"""Tests de requisitos del subject Fly-in.

Ejecutar desde la raíz del proyecto:
    pytest -v tests/test_subject.py

Estas pruebas comprueban reglas funcionales descritas en el subject.
No sustituyen la revisión manual de la salida visual, Makefile, README,
tipado, estilo ni benchmarks oficiales.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from models import Connection, Drone, Map, Simulation, Zone
from parser import MapParser, MapData


class TestSubjectZonesAndConnections(unittest.TestCase):
    """Comprueba reglas básicas de zonas y enlaces."""

    def test_zone_types_and_default_capacity(self) -> None:
        zone = Zone("room", 0, 0)
        self.assertEqual(zone.zone_type, "normal")
        self.assertEqual(zone.max_drones, 1)

    def test_blocked_zone_cannot_be_entered(self) -> None:
        drone_map = Map()
        start = Zone("start", 0, 0, max_drones=None)
        blocked = Zone("blocked", 1, 0, "blocked")
        for zone in (start, blocked):
            drone_map.add_zone(zone)
        drone_map.add_connection(Connection(start, blocked))
        drone = Drone(1, start, drone_map)
        with self.assertRaises(ValueError):
            drone.move_to(blocked)

    def test_connections_are_bidirectional(self) -> None:
        drone_map = Map()
        a = Zone("a", 0, 0)
        b = Zone("b", 1, 0)
        drone_map.add_zone(a)
        drone_map.add_zone(b)
        connection = Connection(a, b)
        drone_map.add_connection(connection)
        self.assertTrue(drone_map.are_connected(a, b))
        self.assertTrue(drone_map.are_connected(b, a))


class TestSubjectPathfinding(unittest.TestCase):
    """Comprueba restricciones y costes de las rutas."""

    def test_route_avoids_blocked_zone(self) -> None:
        drone_map = Map()
        start = Zone("start", 0, 0, max_drones=None)
        blocked = Zone("blocked", 1, 0, "blocked")
        detour = Zone("detour", 0, 1)
        goal = Zone("goal", 2, 0, max_drones=None)
        for zone in (start, blocked, detour, goal):
            drone_map.add_zone(zone)
        for a, b in (
            (start, blocked),
            (blocked, goal),
            (start, detour),
            (detour, goal),
        ):
            drone_map.add_connection(Connection(a, b))
        route = drone_map.find_route(start, goal)
        self.assertNotIn(blocked, route)
        self.assertEqual(route[0], start)
        self.assertEqual(route[-1], goal)

    def test_restricted_destination_costs_two_turns(self) -> None:
        drone_map = Map()
        restricted = Zone("restricted", 1, 0, "restricted")
        self.assertEqual(drone_map.get_movement_cost(restricted), 2)

    def test_priority_destination_costs_one_turn(self) -> None:
        drone_map = Map()
        priority = Zone("priority", 1, 0, "priority")
        self.assertEqual(drone_map.get_movement_cost(priority), 1)

    def test_unreachable_goal_raises_error(self) -> None:
        drone_map = Map()
        start = Zone("start", 0, 0, max_drones=None)
        goal = Zone("goal", 1, 0, max_drones=None)
        drone_map.add_zone(start)
        drone_map.add_zone(goal)
        with self.assertRaises((ValueError, RuntimeError)):
            drone_map.find_route(start, goal)


class TestSubjectParser(unittest.TestCase):
    """Comprueba ejemplos válidos y entradas inválidas del formato."""

    def parse_text(self, text: str) -> MapData:
        """Escribe un mapa temporal y lo procesa con MapParser."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "map.txt"
            path.write_text(text, encoding="utf-8")
            return MapParser(str(path)).parse()

    def test_valid_minimal_map(self) -> None:
        parsed = self.parse_text(
            "nb_drones: 2\n"
            "start_hub: start 0 0\n"
            "end_hub: goal 1 0\n"
            "connection: start-goal\n"
        )
        self.assertEqual(parsed.number_of_drones, 2)

    def test_comments_and_metadata_order(self) -> None:
        parsed = self.parse_text(
            "# test map\n"
            "nb_drones: 1\n"
            "start_hub: start 0 0 [color=green max_drones=8]\n"
            "hub: middle 1 0 [color=blue zone=priority max_drones=2]\n"
            "end_hub: goal 2 0 [max_drones=9 color=yellow]\n"
            "connection: start-middle [max_link_capacity=2]\n"
            "connection: middle-goal\n"
        )
        self.assertEqual(parsed.number_of_drones, 1)

    def test_zero_drones_is_rejected(self) -> None:
        with self.assertRaises((ValueError, RuntimeError)):
            self.parse_text(
                "nb_drones: 0\n"
                "start_hub: start 0 0\n"
                "end_hub: goal 1 0\n"
                "connection: start-goal\n"
            )

    def test_missing_start_or_end_is_rejected(self) -> None:
        with self.assertRaises((ValueError, RuntimeError)):
            self.parse_text(
                "nb_drones: 1\n"
                "start_hub: start 0 0\n"
                "hub: middle 1 0\n"
            )

    def test_duplicate_connection_is_rejected(self) -> None:
        with self.assertRaises((ValueError, RuntimeError)):
            self.parse_text(
                "nb_drones: 1\n"
                "start_hub: start 0 0\n"
                "end_hub: goal 1 0\n"
                "connection: start-goal\n"
                "connection: goal-start\n"
            )

    def test_invalid_zone_type_is_rejected(self) -> None:
        with self.assertRaises((ValueError, RuntimeError)):
            self.parse_text(
                "nb_drones: 1\n"
                "start_hub: start 0 0\n"
                "hub: middle 1 0 [zone=unknown]\n"
                "end_hub: goal 2 0\n"
                "connection: start-middle\n"
                "connection: middle-goal\n"
            )

    def test_unknown_zone_in_connection_is_rejected(self) -> None:
        with self.assertRaises((ValueError, RuntimeError)):
            self.parse_text(
                "nb_drones: 1\n"
                "start_hub: start 0 0\n"
                "end_hub: goal 1 0\n"
                "connection: start-missing\n"
            )


class TestSubjectSimulation(unittest.TestCase):
    """Comprueba reglas de ocupación, tránsito y entrega."""

    def build_line(
            self,
            zone_type: str = "normal"
    ) -> tuple[Simulation, Zone, Zone, Zone]:
        """Crea start -> middle -> goal."""
        drone_map = Map()
        start = Zone("start", 0, 0, max_drones=None)
        middle = Zone("middle", 1, 0, zone_type)
        goal = Zone("goal", 2, 0, max_drones=None)
        for zone in (start, middle, goal):
            drone_map.add_zone(zone)
        drone_map.add_connection(Connection(start, middle))
        drone_map.add_connection(Connection(middle, goal))
        simulation = Simulation(1, start, drone_map)
        simulation.drones[0].follow_route([start, middle, goal])
        return simulation, start, middle, goal

    def test_all_drones_start_at_start_zone(self) -> None:
        drone_map = Map()
        start = Zone("start", 0, 0, max_drones=None)
        goal = Zone("goal", 1, 0, max_drones=None)
        drone_map.add_zone(start)
        drone_map.add_zone(goal)
        drone_map.add_connection(Connection(start, goal))
        simulation = Simulation(3, start, drone_map)
        self.assertTrue(all(
            drone.current_zone == start for drone in simulation.drones
        ))

    def test_normal_zone_capacity_is_respected(self) -> None:
        drone_map = Map()
        start = Zone("start", 0, 0, max_drones=None)
        middle = Zone("middle", 1, 0, max_drones=1)
        goal = Zone("goal", 2, 0, max_drones=None)
        for zone in (start, middle, goal):
            drone_map.add_zone(zone)
        drone_map.add_connection(Connection(
            start,
            middle,
            max_link_capacity=2
        ))
        drone_map.add_connection(Connection(middle, goal, max_link_capacity=2))
        simulation = Simulation(2, start, drone_map)
        for drone in simulation.drones:
            drone.follow_route([start, middle, goal])
        simulation.run_turn()
        # No more than one drone can occupy the capacity-1 middle zone.
        self.assertLessEqual(simulation.count_drones_in_zone(middle), 1)

    def test_restricted_transit_is_mandatory_next_turn(self) -> None:
        simulation, start, restricted, goal = self.build_line("restricted")
        first_turn = simulation.run_turn()
        self.assertTrue(simulation.drones[0].in_transit)
        self.assertTrue(first_turn)
        second_turn = simulation.run_turn()
        self.assertFalse(simulation.drones[0].in_transit)
        self.assertEqual(simulation.drones[0].current_zone, restricted)
        self.assertTrue(second_turn)

    def test_simulation_eventually_delivers_drone(self) -> None:
        simulation, _start, _middle, goal = self.build_line()
        for _ in range(5):
            if simulation.all_drones_finished():
                break
            simulation.run_turn()
        self.assertTrue(simulation.all_drones_finished())
        self.assertEqual(simulation.drones[0].current_zone, goal)

    def test_start_and_end_are_unlimited_capacity(self) -> None:
        drone_map = Map()
        start = Zone("start", 0, 0, max_drones=None)
        goal = Zone("goal", 1, 0, max_drones=None)
        drone_map.add_zone(start)
        drone_map.add_zone(goal)
        drone_map.add_connection(Connection(start, goal))
        simulation = Simulation(4, start, drone_map)
        self.assertEqual(simulation.count_drones_in_zone(start), 4)


if __name__ == "__main__":
    unittest.main()
