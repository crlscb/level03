import heapq
import re
from display.utils import color_text


class Zone:
    """
    Representa una zona individual
    """
    VALID_TYPES: set[str] = {"normal", "blocked", "restricted", "priority"}

    def __init__(
            self,
            name: str,
            x: int,
            y: int,
            zone_type: str = "normal",
            color: str | None = None,
            max_drones: int | None = 1
            ) -> None:

        if not isinstance(name, str):
            raise TypeError("Zone name must be a string")

        if not name.strip():
            raise ValueError("Zone name cannot be empty")

        if not isinstance(x, int) or not isinstance(y, int):
            raise TypeError("Zone coordinates must be integers")

        if not isinstance(zone_type, str):
            raise TypeError("Zone type must be a string")

        if zone_type not in self.VALID_TYPES:
            raise ValueError(f"Invalid zone type: {zone_type}")

        if color is not None and not isinstance(color, str):
            raise TypeError("Color must be a string or None")

        if max_drones is not None:
            if not isinstance(max_drones, int):
                raise TypeError("Max drones must be an integer")
            if max_drones <= 0:
                raise ValueError("Max drones must be positive")

        self.name = name
        self.x = x
        self.y = y
        self.zone_type = zone_type
        self.color = color
        self.max_drones = max_drones

    def __repr__(self) -> str:
        return (
            f"{self.name} "
            f"({self.x},{self.y}) "
            f"[{self.zone_type}]"
        )


class Connection:
    """
    Representa una conexión bidireccional entre dos zonas
    """
    def __init__(
            self,
            zone_a: Zone,
            zone_b: Zone,
            max_link_capacity: int = 1
    ) -> None:

        if not isinstance(zone_a, Zone) or not isinstance(zone_b, Zone):
            raise TypeError("Connections must link Zone objects")

        if zone_a == zone_b:
            raise ValueError("A zone cannot connect to itself")

        if not isinstance(max_link_capacity, int):
            raise TypeError("Max link capacity must be an integer")

        if max_link_capacity <= 0:
            raise ValueError("Max link capacity must be positive")

        self.zone_a = zone_a
        self.zone_b = zone_b
        self.max_link_capacity = max_link_capacity

    def __repr__(self) -> str:
        return (
            f"{self.zone_a.name} <-> {self.zone_b.name} "
            f"[capacity={self.max_link_capacity}]"
        )

    def connects(self, zone_a: Zone, zone_b: Zone) -> bool:
        """
        Comprobamos si la conexión une las dos zonas,
        independientemente del orden.
        """
        return (
            (self.zone_a == zone_a and self.zone_b == zone_b) or
            (self.zone_a == zone_b and self.zone_b == zone_a)
        )


class Map:
    """
    Almacena zonas y conexiones, evita duplicados y permite buscarlas
    """
    def __init__(self) -> None:
        self.zones: list[Zone] = []
        self.connections: list[Connection] = []

    def add_zone(self, zone: Zone) -> None:
        """
        Añade una zona al mapa si no existe otra con el mismo nombre.
        """
        if not isinstance(zone, Zone):
            raise TypeError("Only Zone objects can be added to the map")

        if self.get_zone(zone.name) is not None:
            raise ValueError(f"Zone already exists: {zone.name}")

        self.zones.append(zone)

    def add_connection(self, connection: Connection) -> None:
        """
        Añade una conexión válida al mapa.

        Comprueba que el objeto sea una Connection,
        que sus zonas pertenezcan al mapa y que
        no exista ya la misma conexión,
        """
        if not isinstance(connection, Connection):
            raise TypeError("Only Connections objects can be added to the map")

        if connection.zone_a not in self.zones:
            raise ValueError(
                f"Zone not found in map: {connection.zone_a.name}"
            )

        if connection.zone_b not in self.zones:
            raise ValueError(
                f"Zone not found in map: {connection.zone_b.name}"
            )

        for existing_connection in self.connections:
            if existing_connection.connects(
                connection.zone_a, connection.zone_b
            ):
                raise ValueError(
                    f"Connection already exists: "
                    f"{connection.zone_a.name}-{connection.zone_b.name}"
                )

        self.connections.append(connection)

    def get_zone(self, name: str) -> Zone | None:
        """
        Busca una zona por su nombre
        """
        for zone in self.zones:
            if zone.name == name:
                return zone
        return None

    def get_connections(self, zone: Zone) -> list[Connection]:
        """
        Busca las conexiones relacionadas con una zona
        """
        result: list[Connection] = []

        for connection in self.connections:
            if connection.zone_a == zone or connection.zone_b == zone:
                result.append(connection)
        return result

    def are_connected(self, zone_a: Zone, zone_b: Zone) -> bool:
        """
        Comprueba si dos zonas están conectadas directamente
        """
        for connection in self.connections:
            if connection.connects(zone_a, zone_b):
                return True
        return False

    def get_connection(
            self,
            zone_a: Zone,
            zone_b: Zone,
    ) -> Connection | None:
        """
        Devuelve la conexión entre dos zonas, si existe.
        """
        for connection in self.connections:
            if connection.connects(zone_a, zone_b):
                return connection

        return None

    def get_neighbors(self, zone: Zone) -> list[Zone]:
        """
        Devuelve las zonas conectadas directamente a una zona.
        """
        if not isinstance(zone, Zone):
            raise TypeError("Zone must be a Zone")

        neighbors: list[Zone] = []

        for connection in self.get_connections(zone):
            if connection.zone_a == zone:
                neighbors.append(connection.zone_b)
            else:
                neighbors.append(connection.zone_a)

        return neighbors

    def contains_zone(self, zone: Zone) -> bool:
        """
        Comprueba si una zona pertenece exactamente al mapa.
        """
        return zone in self.zones

    def find_route(self, start: Zone, goal: Zone) -> list[Zone]:
        """
        Encuentra una ruta entre una zona inicial y una zona de destino
        Devuelve una lista de zonas que representa el recorrido
        """

        if not isinstance(start, Zone):
            raise TypeError("Start must be a Zone")

        if not isinstance(goal, Zone):
            raise TypeError("Goal must be a Zone")

        if not self.contains_zone(start):
            raise ValueError("Start zone does not belong to the map")

        if not self.contains_zone(goal):
            raise ValueError("Goal zone does not belong to the map")

        if start == goal:
            return [start]

        distances: dict[Zone, float] = {
            zone: float("inf")
            for zone in self.zones
        }

        distances[start] = 0

        previous: dict[Zone, Zone | None] = {
            start: None
        }

        has_priority: dict[Zone, bool] = {
            zone: False
            for zone in self.zones
        }

        pending: list[tuple[int, int, Zone]] = []

        counter = 0

        heapq.heappush(pending, (0, counter, start))

        while pending:
            current_cost, _, current = heapq.heappop(pending)

            if current == goal:
                continue

            if current_cost > distances[current]:
                continue

            for neighbor in self.get_neighbors(current):
                if neighbor.zone_type == "blocked":
                    continue

                movement_cost = self.get_movement_cost(neighbor)

                new_cost = current_cost + movement_cost

                new_has_priority = (
                    has_priority[current]
                    or neighbor.zone_type == "priority"
                )

                if (
                    new_cost < distances[neighbor]
                    or (
                        new_cost == distances[neighbor]
                        and new_has_priority
                        and not has_priority[neighbor]
                    )
                ):
                    distances[neighbor] = new_cost
                    previous[neighbor] = current
                    has_priority[neighbor] = new_has_priority

                    counter += 1

                    heapq.heappush(
                        pending,
                        (new_cost, counter, neighbor)
                    )

        if distances[goal] == float("inf"):
            raise ValueError("No route found between start and goal")

        route: list[Zone] = []
        route_current: Zone | None = goal

        while route_current is not None:
            route.append(route_current)
            route_current = previous[route_current]

        route.reverse()

        return route

    def find_alternative_routes(
        self,
        start: Zone,
        goal: Zone,
        max_routes: int = 5,
    ) -> list[list[Zone]]:
        """Find alternative valid routes ordered by movement cost."""
        if max_routes < 1:
            raise ValueError("max_routes must be at least 1")

        routes: list[list[Zone]] = []
        pending: list[tuple[int, int, list[Zone]]] = []
        counter = 0

        heapq.heappush(pending, (0, counter, [start]))

        while pending and len(routes) < max_routes:
            cost, _, route = heapq.heappop(pending)
            current = route[-1]

            if current == goal:
                routes.append(route)
                continue

            for neighbor in self.get_neighbors(current):
                if neighbor.zone_type == "blocked" or neighbor in route:
                    continue

                new_cost = cost + self.get_movement_cost(neighbor)
                counter += 1

                heapq.heappush(
                    pending,
                    (new_cost, counter, route + [neighbor]),
                )

        if not routes:
            raise ValueError("No route found between start and goal")

        return routes

    def get_movement_cost(self, zone: Zone) -> int:
        """
        Devuelve el coste de movimiento hacia una zona.
        """

        if not isinstance(zone, Zone):
            raise TypeError("Zone must be a Zone")

        if zone.zone_type == "blocked":
            raise ValueError("Cannot enter a blocked zone")

        if zone.zone_type == "restricted":
            return 2

        return 1

    def get_route_cost(self, route: list[Zone]) -> int:
        """
        Calcula el coste total de una ruta.
        """

        if not isinstance(route, list):
            raise TypeError("Route must be a list")

        if not route:
            raise ValueError("Route cannot be empty")

        total_cost: int = 0

        for zone in route[1:]:
            total_cost += self.get_movement_cost(zone)

        return total_cost


class Drone:
    """
    Representa un dron que se desplaza por el mapa
    """
    def __init__(
            self,
            drone_id: int,
            start_zone: Zone,
            drone_map: Map
            ) -> None:
        if not isinstance(drone_id, int):
            raise TypeError("Drone ID must be an integer")

        if drone_id <= 0:
            raise ValueError("Drone ID must be positive")

        if not isinstance(start_zone, Zone):
            raise TypeError("Start zone must be a Zone")

        if not isinstance(drone_map, Map):
            raise TypeError("Drone map must be a Map")

        if not drone_map.contains_zone(start_zone):
            raise ValueError(
                "Start zone does not belong to the drone map"
            )

        self.drone_id = drone_id
        self.current_zone = start_zone
        self.route_position = 0
        self.route: list[Zone] = []
        self.finished = False
        self.drone_map = drone_map
        self.in_transit = False
        self.transit_destination: Zone | None = None
        self.transit_connection: Connection | None = None
        self.transit_turns_remaining = 0

    def __repr__(self) -> str:
        return f"Drone {self.drone_id} at {self.current_zone.name}"

    def move_to(self, destination: Zone) -> None:
        """
        Mueve el dron a una nueva zona si existe una conexión directa
        y la zona no está bloqueada
        """
        if self.finished:
            raise ValueError("Drone has already finished")

        if not isinstance(destination, Zone):
            raise TypeError("Destination must be a zone")

        if not self.drone_map.contains_zone(destination):
            raise ValueError(
                "Destination zone does not belong to the drone map"
            )

        if destination == self.current_zone:
            raise ValueError("Drone is already in this zone")

        if destination.zone_type == "blocked":
            raise ValueError("Cannot move to blocked zone")

        if not self.drone_map.are_connected(self.current_zone, destination):
            raise ValueError(
                f"No connection between "
                f"{self.current_zone.name} and {destination.name}"
            )

        self.current_zone = destination

    def finish(self) -> None:
        """
        Marca el dron como terminado.
        """
        self.finished = True

    def follow_route(self, route: list[Zone]) -> None:
        """
        Hace que el dron recorra una ruta completa.
        """

        if not isinstance(route, list):
            raise TypeError("Route must be a list")

        if not route:
            raise ValueError("Route cannot be empty")

        if route[0] != self.current_zone:
            raise ValueError("Route must start at the drone's current zone")

        self.route = route
        self.route_position = 0

    def start_transit(self, destination: Zone, connection: Connection) -> None:
        """
        Inicia un desplazamiento que tarda más de un turno.
        """
        self.in_transit = True
        self.transit_destination = destination
        self.transit_connection = connection
        self.transit_turns_remaining = 1

    def move_one_step(self, destination: Zone) -> None:
        """
        Mueve el dron una sola zona.
        """
        self.move_to(destination)
        self.route_position += 1

    def get_next_zone(self) -> Zone | None:
        """
        Devuelve la siguiente zona de la ruta a la que nos moveremos.
        """
        if self.route_position + 1 >= len(self.route):
            return None
        return self.route[self.route_position + 1]

    def move_next(self) -> None:
        """
        Mueve el drona a la siguiente zona de la ruta
        """
        next_zone = self.get_next_zone()

        if next_zone is None:
            self.finish()
            return
        self.move_one_step(next_zone)


class Simulation:
    """
    Representa un conjunto de drones
    """
    def __init__(
            self, number_of_drones: int, start_zone: Zone, drone_map: Map
    ) -> None:

        if not isinstance(number_of_drones, int):
            raise TypeError("Number of drones must be an integer")

        if number_of_drones <= 0:
            raise ValueError("Number of drones must be positive")

        if not isinstance(start_zone, Zone):
            raise TypeError("Start zone must be a Zone")

        if not isinstance(drone_map, Map):
            raise TypeError("Drone map must be a Map")

        if not drone_map.contains_zone(start_zone):
            raise ValueError(
                "Start zone does not belong to the drone map"
            )
        self.map = drone_map
        self.drones: list[Drone] = []
        self.connections_in_use: dict[Connection, int] = {}
        self.zone_arrival_reservations: dict[Zone, int] = {}
        drone_id: int = 1

        while drone_id <= number_of_drones:
            drone: Drone = Drone(drone_id, start_zone, drone_map)
            self.drones.append(drone)
            drone_id += 1

    def __repr__(self) -> str:
        return "\n".join(str(drone) for drone in self.drones)

    def run_route(self, routes: list[list[Zone]]) -> None:
        """
        Hace que todos los drones de la simulación sigan una ruta.
        """
        if len(routes) != len(self.drones):
            raise ValueError(
                "Number of routes match number of drones"
            )

        for drone, route in zip(self.drones, routes):
            drone.follow_route(route)

    def run_turn(self) -> list[str]:
        """Planifica y ejecuta los movimientos de un turno."""
        movements: list[str] = []
        arrivals: list[tuple[Drone, Zone, Connection]] = []
        planned_moves: list[tuple[Drone, Zone]] = []

        for drone in self.drones:
            if drone.finished:
                continue

            if drone.in_transit:
                drone.transit_turns_remaining -= 1

                if drone.transit_turns_remaining < 0:
                    raise ValueError("Invalid transit duration")

                if drone.transit_turns_remaining == 0:
                    destination = drone.transit_destination
                    connection = drone.transit_connection

                    if destination is None or connection is None:
                        raise ValueError(
                            "Drone is in transit without destination "
                            "or connection"
                        )

                    arrivals.append((drone, destination, connection))
                continue

            next_zone = drone.get_next_zone()

            if next_zone is None:
                drone.finish()
                continue

            planned_moves.append((drone, next_zone))

        planned_connections = self.connections_in_use.copy()

        for _, _, connection in arrivals:
            planned_connections[connection] -= 1

            if planned_connections[connection] <= 0:
                del planned_connections[connection]

        possible_moves: list[tuple[Drone, Zone]] = []

        for drone, next_zone in planned_moves:
            if self.can_use_connection(
                drone.current_zone,
                next_zone,
                planned_connections,
            ):
                possible_moves.append((drone, next_zone))

                connection = self.map.get_connection(
                    drone.current_zone, next_zone
                )

                if connection is not None:
                    planned_connections[connection] = (
                        planned_connections.get(connection, 0) + 1
                    )

        valid_moves = possible_moves.copy()

        while True:
            planned_exits: dict[Zone, int] = {}

            for drone, _ in valid_moves:
                zone = drone.current_zone
                planned_exits[zone] = planned_exits.get(zone, 0) + 1

            planned_entries: dict[Zone, int] = {}

            for _, destination, _ in arrivals:
                planned_entries[destination] = (
                    planned_entries.get(destination, 0) + 1
                )

            confirmed_moves: list[tuple[Drone, Zone]] = []

            for drone, destination in valid_moves:
                capacity = destination.max_drones

                if capacity is None:
                    confirmed_moves.append((drone, destination))
                    planned_entries[destination] = (
                        planned_entries.get(destination, 0) + 1
                    )
                    continue

                occupied = self.count_drones_in_zone(destination)
                leaving = planned_exits.get(destination, 0)
                entering = planned_entries.get(destination, 0)

                available_space = capacity - occupied + leaving - entering

                if available_space > 0:
                    confirmed_moves.append((drone, destination))
                    planned_entries[destination] = entering + 1

            if confirmed_moves == valid_moves:
                break

            valid_moves = confirmed_moves

        planned_exits = {}

        for drone, _ in valid_moves:
            zone = drone.current_zone
            planned_exits[zone] = planned_exits.get(zone, 0) + 1

        for zone in self.map.zones:
            if zone.max_drones is None:
                continue

            arriving = sum(
                1 for _, destination, _ in arrivals
                if destination == zone
            )

            entering = sum(
                1 for _, destination in valid_moves
                if destination == zone
                and destination.zone_type != "restricted"
            )

            occupied = self.count_drones_in_zone(zone)
            leaving = planned_exits.get(zone, 0)

            if occupied - leaving + arriving + entering > zone.max_drones:
                raise ValueError(
                    f"Mandatory transit arrival exceeds capacity "
                    f"at zone {zone.name}"
                )

        for drone, destination, connection in arrivals:
            reserved = self.zone_arrival_reservations.get(destination, 0)
            if reserved > 0:
                if reserved == 1:
                    del self.zone_arrival_reservations[destination]
                else:
                    self.zone_arrival_reservations[destination] = reserved - 1
            drone.move_to(destination)
            drone.route_position += 1
            drone.in_transit = False
            drone.transit_destination = None
            drone.transit_connection = None
            drone.transit_turns_remaining = 0

            self.connections_in_use[connection] -= 1

            if self.connections_in_use[connection] == 0:
                del self.connections_in_use[connection]

            if drone.route_position == len(drone.route) - 1:
                drone.finish()

            movements.append(
                color_text(
                    f"D{drone.drone_id}-{destination.name}",
                    destination.color,
                )
            )

        for drone, destination in valid_moves:
            connection = self.map.get_connection(
                drone.current_zone, destination
            )

            if connection is None:
                continue

            if destination.zone_type == "restricted":
                drone.start_transit(destination, connection)

                self.connections_in_use[connection] = (
                    self.connections_in_use.get(connection, 0) + 1
                )

                self.zone_arrival_reservations[destination] = (
                    self.zone_arrival_reservations.get(destination, 0) + 1
                )

                movements.append(
                    color_text(
                        f"D{drone.drone_id}-"
                        f"{connection.zone_a.name}-"
                        f"{connection.zone_b.name}",
                        destination.color,
                    )
                )
            else:
                drone.move_one_step(destination)

                if drone.route_position == len(drone.route) - 1:
                    drone.finish()

                movements.append(
                    color_text(
                        f"D{drone.drone_id}-{destination.name}",
                        destination.color,
                    )
                )

        return movements

    def has_drones_in_transit(self) -> bool:
        """Comprueba si hay drones que deben completar un tránsito."""
        return any(drone.in_transit for drone in self.drones)

    def run_simulation(self) -> None:
        """
        Ejecuta la simulación hasta completar la ruta.
        """
        turn = 0
        consecutives_turns = 0

        while not self.all_drones_finished():
            turn += 1
            movements = self.run_turn()
            self.validate_capacities()

            if not movements:
                if self.has_drones_in_transit():
                    consecutives_turns = 0
                    continue

                consecutives_turns += 1
                if consecutives_turns >= 2:
                    raise RuntimeError(
                        "Simulation in stuck: no drones can move."
                    )
                continue
            consecutives_turns = 0
            clean_movements = [
                re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", movement)
                for movement in movements
            ]
            print(" ".join(clean_movements))

    def count_drones_in_zone(self, zone: Zone) -> int:
        """
        Calcula cuantos drones están actualmente en una zona.
        """
        if not isinstance(zone, Zone):
            raise TypeError("Zone must be a Zone")
        count = 0

        for drone in self.drones:
            if drone.current_zone == zone and not drone.in_transit:
                count += 1
        return count

    def validate_capacities(self) -> None:
        """
        Comprueba que las zonas y conexiones respetan sus capacidades.
        """
        for zone in self.map.zones:
            if zone.max_drones is None:
                continue

            count = self.count_drones_in_zone(zone)

            if count > zone.max_drones:
                raise ValueError(
                    f"Zone capacity exceeded: {zone.name} "
                    f"({count}/{zone.max_drones})"
                )

        for connection, count in self.connections_in_use.items():
            if count > connection.max_link_capacity:
                raise ValueError(
                    f"Connection capacity exceeded: "
                    f"{connection.zone_a.name}-{connection.zone_b.name} "
                    f"({count}/{connection.max_link_capacity})"
                )

    def can_enter_zone(self, zone: Zone) -> bool:
        """
        Devuleve true si puede entrar otro dron a esa zona.
        """
        if not isinstance(zone, Zone):
            raise ValueError("Zone must be a Zone")

        count_drones = self.count_drones_in_zone(zone)

        if zone.max_drones is None:
            return True

        if count_drones < zone.max_drones:
            return True

        return False

    def all_drones_finished(self) -> bool:
        """
        Comprueba si todos los drones han terminado (finished = True)
        """
        return all(drone.finished for drone in self.drones)

    def can_use_connection(
            self,
            zone_a: Zone,
            zone_b: Zone,
            connections_in_use: dict[Connection, int]
    ) -> bool:
        """
        Comprueba si existe una conexión entre dos zonas y si tiene
        capacidad disponible [max_link_capacity]
        """
        connection = self.map.get_connection(zone_a, zone_b)

        if connection is None:
            return False

        current_usage = connections_in_use.get(connection, 0)

        return current_usage < connection.max_link_capacity
