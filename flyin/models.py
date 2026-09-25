import heapq

"""
El mapa está formado por diferentes zonas por las que pueden pasar drones
"""


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
            max_drones: int = 1
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

        pending: list[tuple[int, int, Zone]] = []

        counter = 0

        heapq.heappush(pending, (0, counter, start))

        while pending:
            current_cost, _, current = heapq.heappop(pending)

            if current == goal:
                break

            if current_cost > distances[current]:
                continue

            for neighbor in self.get_neighbors(current):
                if neighbor.zone_type == "blocked":
                    continue

                movement_cost = self.get_movement_cost(neighbor)

                new_cost = current_cost + movement_cost

                if new_cost < distances[neighbor]:
                    distances[neighbor] = new_cost
                    previous[neighbor] = current

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
        self.finished = False
        self.drone_map = drone_map

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

        for zone in route[1:]:
            self.move_to(zone)
            print(f"Drone {self.drone_id} moved to {zone.name}")

    def move_one_step(self, destination: Zone) -> None:
        """
        Mueve el dron una sola zona.
        """
        self.move_to(destination)
        self.route_position += 1
        print(f"Drone {self.drone_id} moved to {destination.name}")

    def get_next_zone(self, route: list[Zone]) -> Zone | None:
        """
        Devuelve la siguiente zona de la ruta a la que nos moveremos.
        """
        if self.route_position + 1 >= len(route):
            return None
        return route[self.route_position + 1]

    def move_next(self, route: list[Zone]) -> None:
        """
        Mueve el drona a la siguiente zona de la ruta
        """
        next_zone = self.get_next_zone(route)

        if next_zone is None:
            print(f"Drone {self.drone_id} has reached the end of the route")
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
        drone_id: int = 1

        while drone_id <= number_of_drones:
            drone: Drone = Drone(drone_id, start_zone, drone_map)
            self.drones.append(drone)
            drone_id += 1

    def __repr__(self) -> str:
        return "\n".join(str(drone) for drone in self.drones)

    def run_route(self, route: list[Zone]) -> None:
        """
        Hace que todos los drones de la simulación sigan una ruta.
        """

        if not isinstance(route, list):
            raise TypeError("Route must be a list")

        if not route:
            raise ValueError("Route cannot be empty")

        for drone in self.drones:
            drone.follow_route(route)

    def run_turn(self, route: list[Zone]) -> None:
        """
        Hace avanzar un paso a todos los drones(por turnos).
        """
        for drone in self.drones:
            if drone.finished:
                continue

            next_zone = drone.get_next_zone(route)

            if next_zone is None:
                drone.finish()
                print(
                    f"Drone {drone.drone_id} "
                    "has reached the end of the route"
                )
                continue

            if self.can_enter_zone(next_zone):
                if self.can_use_connection(
                    drone.current_zone,
                    next_zone
                ):
                    drone.move_one_step(next_zone)
                else:
                    print(
                        f"Drone {drone.drone_id} "
                        f"cannot use connection to {next_zone.name}"
                    )
            else:
                print(
                    f"Drone {drone.drone_id} "
                    f"cannot enter {next_zone.name}: zone is full"
                )

    def run_simulation(self, route: list[Zone]) -> None:
        """
        Ejecuta la simulación hasta completar la ruta.
        """
        turn = 0

        while not self.all_drones_finished():
            turn += 1
            print(f"\n--- Turn {turn} ---")
            self.run_turn(route)

    def count_drones_in_zone(self, zone: Zone) -> int:
        """
        Calcula cuantos drones están actualmente en una zona.
        """
        if not isinstance(zone, Zone):
            raise TypeError("Zone must be a Zone")
        count = 0

        for drone in self.drones:
            if drone.current_zone == zone:
                count += 1
        return count

    def can_enter_zone(self, zone: Zone) -> bool:
        """
        Devuleve true si puede entrar otro dron a esa zona.
        """
        if not isinstance(zone, Zone):
            raise ValueError("Zone must be a Zone")

        count_drones = self.count_drones_in_zone(zone)

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
    ) -> bool:
        """
        Comprueba si existe una conexión entre dos zonas y si tiene
        capacidad disponible [max_link_capacity]
        """
        connection = self.map.get_connection(zone_a, zone_b)

        if connection is None:
            return False

        return True


if __name__ == "__main__":
    start: Zone = Zone("start", 0, 0)
    waypoint1: Zone = Zone("waypoint1", 1, 0)
    waypoint2: Zone = Zone("waypoint2", 2, 0)
    goal: Zone = Zone("goal", 3, 0, max_drones=3)
    blocked: Zone = Zone("blocked1", 4, 0, "blocked")
    other: Zone = Zone("other", 5, 0)
    try:
        blocked2: Zone = Zone("blocked2", 4, 0, "blocked2")
    except ValueError as e:
        print(e)
    my_map: Map = Map()
    my_map.add_zone(start)
    my_map.add_zone(waypoint1)
    my_map.add_zone(waypoint2)
    my_map.add_zone(goal)
    my_map.add_zone(blocked)
    print("Zones:")
    for zone in my_map.zones:
        print(zone)

    connection: Connection = Connection(start, waypoint1)
    connection2: Connection = Connection(waypoint1, waypoint2)
    connection3: Connection = Connection(waypoint2, goal)
    my_map.add_connection(connection)
    my_map.add_connection(connection2)
    my_map.add_connection(connection3)

    print("-------------------")
    print("Connections")
    for connections in my_map.connections:
        print(connections)

    print("----------------")
    print(my_map.get_zone("waypoint1"))
    print(my_map.get_zone("unknown"))
    print("-----------------")
    for connections in my_map.get_connections(waypoint2):
        print(connections)

    print("-------------")
    drone1: Drone = Drone(1, start, my_map)
    drone2: Drone = Drone(2, start, my_map)
    print("Drones")
    print(drone1)
    drone1.move_to(waypoint1)
    try:
        drone2.move_to(goal)
    except ValueError as e:
        print(e)
    print(drone1)
    print(drone2)

    print("-----------")
    print("Connection checks")
    print(my_map.are_connected(start, waypoint1))
    print(my_map.are_connected(start, goal))

    print("-------------")
    print("Connection blocked")
    my_map.add_connection(Connection(goal, blocked))
    try:
        drone1.move_to(blocked)
    except ValueError as e:
        print(e)

    print("---------------")
    print("Simulation")
    simulation: Simulation = Simulation(3, start, my_map)
    print(simulation)

    print("----------------")
    print("Validations zone")
    try:
        empty: Zone = Zone(123, 0, 0)
    except TypeError as e:
        print(e)
    try:
        double: Zone = Zone("double", 2.0, 0)
    except TypeError as e:
        print(e)
    try:
        spaces: Zone = Zone("    ", 2, 0)
    except ValueError as e:
        print(e)
    try:
        my_map.add_zone("not a zone")
    except TypeError as e:
        print(e)
    try:
        my_map.add_zone(start)
    except ValueError as e:
        print(e)

    print("------------")
    print("Validations connections")
    try:
        Connection("start", "waypoint1")
    except TypeError as e:
        print(e)
    try:
        Connection(start, start)
    except ValueError as e:
        print(e)
    try:
        duplicate_connection: Connection = Connection(waypoint1, start)
        my_map.add_connection(duplicate_connection)
    except ValueError as e:
        print(e)
    print("Number of connections:", len(my_map.connections))
    try:
        external_zone: Zone = Zone("external", 10, 10)
        invalid_connection: Connection = Connection(goal, external_zone)
        my_map.add_connection(invalid_connection)
    except ValueError as e:
        print(e)

    print("------------")
    print("move_to() validations:")
    try:
        drone1.move_to(waypoint1)
    except ValueError as e:
        print(e)
    try:
        drone1.move_to(blocked)
    except ValueError as e:
        print(e)
    try:
        drone1.move_to(other)
    except ValueError as e:
        print(e)
    try:
        drone1.move_to(goal)
    except ValueError as e:
        print(e)
    try:
        drone1.move_to("waypoint1")
    except TypeError as e:
        print(e)

    print("---------------")
    print("Finish drone")
    drone1.finish()
    print(f"Drone finished: {drone1.finished}")
    try:
        drone1.move_to(waypoint2)
    except ValueError as e:
        print(e)
    try:
        external_zone: Zone = Zone("external", 10, 10)
        Drone(3, external_zone, my_map)
    except ValueError as e:
        print(e)

    print("-------------")
    print("primeras pruebas find_route()")

    route_map = Map()
    start: Zone = Zone("start", 0, 0)
    waypoint1: Zone = Zone("waypoint1", 1, 0)
    waypoint2: Zone = Zone("waypoint2", 2, 0)
    goal: Zone = Zone("goal", 3, 0, max_drones=3)

    route_map.add_zone(start)
    route_map.add_zone(waypoint1)
    route_map.add_zone(waypoint2)
    route_map.add_zone(goal)

    route_map.add_connection(Connection(start, waypoint1))
    route_map.add_connection(Connection(waypoint1, waypoint2))
    route_map.add_connection(Connection(waypoint2, goal))

    try:
        route_map.add_connection(Connection(start, waypoint1))
    except ValueError as e:
        print(e)

    route = route_map.find_route(start, goal)
    print("Ruta encontrada")
    print(" -> ".join(zone.name for zone in route))

    simulation = Simulation(3, start, route_map)
    waypoint1.max_drones = 1
    print("Posiciones iniciales:")
    for drone in simulation.drones:
        print(drone.drone_id, drone.current_zone.name)
    simulation.run_simulation(route)
    count_drones = simulation.count_drones_in_zone(goal)
    print("Posiciones finales:")
    for drone in simulation.drones:
        print(drone.drone_id, drone.current_zone.name)
    for drone in simulation.drones:
        print(
            f"Drone {drone.drone_id} :"
            f"finished = {drone.finished}"
        )
    print(
        "Are drones finished?",
        simulation.all_drones_finished()
    )

    print("\n--- Testing zone metadata ---")

    normal_zone = Zone("normal", 0, 0)

    priority_zone = Zone(
        "corridorA",
        4,
        3,
        "priority",
        "green",
        2,
    )

    blocked_zone = Zone(
        "obstacleX",
        5,
        5,
        "blocked",
        "gray",
        1,
    )

    print(normal_zone)
    print(priority_zone)
    print(blocked_zone)

    print("Priority color:", priority_zone.color)
    print("Priority max drones:", priority_zone.max_drones)

    try:
        Zone("bad", 0, 0, "unknown")
    except ValueError as error:
        print("Error esperado:", error)

    try:
        Zone("bad", 0, 0, "normal", "blue", 0)
    except ValueError as error:
        print("Error esperado:", error)

    try:
        Zone("bad", 0, 0, "normal", "blue", "two")
    except TypeError as error:
        print("Error esperado", error)

    print("----Max link capacity-----")
    high_capacity_connection = Connection(
        priority_zone,
        blocked_zone,
        max_link_capacity=3
    )
    print(high_capacity_connection)
    print(f"Max link capacity: {high_capacity_connection.max_link_capacity}")

    try:
        Connection(start, waypoint1, max_link_capacity=0)
    except ValueError as e:
        print("Error esperado:", e)
    try:
        Connection(start, waypoint1, max_link_capacity="three")
    except TypeError as e:
        print("Error esperado:", e)
    try:
        Connection(start, start)
    except ValueError as e:
        print("Error esperado:", e)
