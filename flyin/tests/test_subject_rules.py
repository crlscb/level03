"""Pruebas dirigidas a reglas de capacidad y turnos del subject Fly-in.

Ejecutar desde la raíz del proyecto:
    pytest -v tests/test_subject_rules.py

Estas pruebas son complementarias a test_models.py y test_subject.py.
"""
import unittest

from models import Connection, Map, Simulation, Zone
from unittest.mock import patch


class TestLinkCapacity(unittest.TestCase):
    """El número de drones que usan un enlace no supera su capacidad."""

    def test_link_capacity_one_blocks_second_drone_in_same_turn(self) -> None:
        drone_map = Map()
        start = Zone("start", 0, 0, max_drones=None)
        goal = Zone("goal", 1, 0, max_drones=None)
        drone_map.add_zone(start)
        drone_map.add_zone(goal)
        drone_map.add_connection(
            Connection(start, goal, max_link_capacity=1)
        )

        simulation = Simulation(2, start, drone_map)
        for drone in simulation.drones:
            drone.follow_route([start, goal])

        movements = simulation.run_turn()

        self.assertEqual(len(movements), 1)
        self.assertEqual(simulation.count_drones_in_zone(goal), 1)
        self.assertEqual(
            sum(1 for drone in simulation.drones if drone.finished), 1
        )

    def test_link_capacity_two_allows_two_drones_in_same_turn(self) -> None:
        drone_map = Map()
        start = Zone("start", 0, 0, max_drones=None)
        goal = Zone("goal", 1, 0, max_drones=None)
        drone_map.add_zone(start)
        drone_map.add_zone(goal)
        drone_map.add_connection(
            Connection(start, goal, max_link_capacity=2)
        )

        simulation = Simulation(2, start, drone_map)
        for drone in simulation.drones:
            drone.follow_route([start, goal])

        simulation.run_turn()

        self.assertEqual(simulation.count_drones_in_zone(goal), 2)
        self.assertTrue(simulation.all_drones_finished())


class TestSameTurnCapacityRelease(unittest.TestCase):
    """Una salida libera espacio para una entrada en ese mismo turno."""

    def test_zone_capacity_is_released_when_drone_leaves(self) -> None:
        drone_map = Map()
        start = Zone("start", 0, 0, max_drones=None)
        middle = Zone("middle", 1, 0, max_drones=1)
        goal = Zone("goal", 2, 0, max_drones=None)

        for zone in (start, middle, goal):
            drone_map.add_zone(zone)

        drone_map.add_connection(
            Connection(start, middle, max_link_capacity=2)
        )
        drone_map.add_connection(
            Connection(middle, goal, max_link_capacity=2)
        )

        simulation = Simulation(2, start, drone_map)
        for drone in simulation.drones:
            drone.follow_route([start, middle, goal])

        # Turno 1: solo un dron puede entrar en middle.
        simulation.run_turn()
        self.assertEqual(simulation.count_drones_in_zone(middle), 1)
        self.assertEqual(simulation.count_drones_in_zone(start), 1)

        # Turno 2: el primero sale hacia goal y el segundo entra en middle.
        simulation.run_turn()
        self.assertEqual(simulation.count_drones_in_zone(middle), 1)
        self.assertEqual(simulation.count_drones_in_zone(goal), 1)
        self.assertEqual(simulation.count_drones_in_zone(start), 0)

    def test_zone_capacity_is_never_exceeded_by_simultaneous_entries(
        self,
    ) -> None:
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

        simulation = Simulation(3, start, drone_map)

        for drone in simulation.drones:
            drone.follow_route([start, middle, goal])

        # Turno 1: solo un dron puede ocupar middle.
        simulation.run_turn()
        self.assertLessEqual(simulation.count_drones_in_zone(middle), 1)

        # Turnos siguientes: la capacidad nunca debe superar 1.
        for _ in range(5):
            if simulation.all_drones_finished():
                break
            simulation.run_turn()
            simulation.validate_capacities()
            self.assertLessEqual(simulation.count_drones_in_zone(middle), 1)


class TestRestrictedTransitCapacity(unittest.TestCase):
    """Un tránsito restringido reserva enlace y espacio de llegada."""

    def test_only_one_drone_reserves_capacity_one_restricted_zone(
            self
    ) -> None:
        drone_map = Map()
        start = Zone("start", 0, 0, max_drones=None)
        restricted = Zone(
            "restricted", 1, 0, "restricted", max_drones=1
        )
        goal = Zone("goal", 2, 0, max_drones=None)

        for zone in (start, restricted, goal):
            drone_map.add_zone(zone)

        drone_map.add_connection(
            Connection(start, restricted, max_link_capacity=2)
        )
        drone_map.add_connection(Connection(restricted, goal))

        simulation = Simulation(2, start, drone_map)
        for drone in simulation.drones:
            drone.follow_route([start, restricted, goal])

        simulation.run_turn()

        in_transit = [
            drone for drone in simulation.drones if drone.in_transit
        ]
        self.assertEqual(len(in_transit), 1)
        self.assertEqual(
            simulation.zone_arrival_reservations.get(restricted, 0), 1
        )

    def test_arrival_releases_restricted_zone_reservation(self) -> None:
        drone_map = Map()
        start = Zone("start", 0, 0, max_drones=None)
        restricted = Zone("restricted", 1, 0, "restricted")
        goal = Zone("goal", 2, 0, max_drones=None)

        for zone in (start, restricted, goal):
            drone_map.add_zone(zone)

        drone_map.add_connection(Connection(start, restricted))
        drone_map.add_connection(Connection(restricted, goal))

        simulation = Simulation(1, start, drone_map)
        simulation.drones[0].follow_route([start, restricted, goal])

        simulation.run_turn()
        self.assertTrue(simulation.drones[0].in_transit)
        self.assertEqual(
            simulation.zone_arrival_reservations.get(restricted, 0), 1
        )

        simulation.run_turn()
        self.assertFalse(simulation.drones[0].in_transit)
        self.assertEqual(simulation.drones[0].current_zone, restricted)
        self.assertEqual(
            simulation.zone_arrival_reservations.get(restricted, 0), 0
        )

    def test_mandatory_arrival_respects_zone_capacity(self) -> None:
        drone_map = Map()
        start = Zone("start", 0, 0, max_drones=None)
        restricted = Zone("restricted", 1, 0, "restricted", max_drones=1)
        goal = Zone("goal", 2, 0, max_drones=None)

        for zone in (start, restricted, goal):
            drone_map.add_zone(zone)

        drone_map.add_connection(Connection(start, restricted, 2))
        drone_map.add_connection(Connection(restricted, goal, 2))

        simulation = Simulation(2, start, drone_map)

        for drone in simulation.drones:
            drone.follow_route([start, restricted, goal])

        # Turno 1: solo un dron puede reservar la zona restringida.
        simulation.run_turn()
        self.assertEqual(
            len([drone for drone in simulation.drones if drone.in_transit]),
            1,
        )

        # Turno 2: llega el primero; el segundo puede iniciar su tránsito
        # solo si la capacidad y las reservas lo permiten.
        simulation.run_turn()
        simulation.validate_capacities()

        self.assertLessEqual(
            simulation.count_drones_in_zone(restricted)
            + simulation.zone_arrival_reservations.get(restricted, 0),
            1,
        )


class TestSimulationDeadlock(unittest.TestCase):
    """Comprueba que la simulación detecta un bloqueo."""

    def test_stuck_simulation_raises_runtime_error(self) -> None:
        drone_map = Map()
        start = Zone("start", 0, 0, max_drones=None)
        goal = Zone("goal", 1, 0, max_drones=None)

        drone_map.add_zone(start)
        drone_map.add_zone(goal)
        drone_map.add_connection(Connection(start, goal))

        simulation = Simulation(1, start, drone_map)
        simulation.drones[0].follow_route([start, goal])

        with patch.object(simulation, "run_turn", return_value=[]):
            with self.assertRaisesRegex(
                RuntimeError,
                "Simulation in stuck",
            ):
                simulation.run_simulation()


if __name__ == "__main__":
    unittest.main()
