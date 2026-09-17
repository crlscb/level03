"""
El mapa está formado por diferentes zonas por las que pueden pasar drones
"""


class Zone:
    """
    Representa una zona individual
    """
    VALID_TYPES: set[str] = {"normal", "blocked", "restricted", "priority"}

    def __init__(
            self, name: str, x: int, y: int, zone_type: str = "normal"
                ) -> None:

        if not isinstance(name, str):
            raise TypeError("Zone name must be a string")

        if not name.strip():
            raise ValueError("Zone name cannot be empty")

        if not isinstance(x, int) or not isinstance(y, int):
            raise TypeError("Zone coordinates must be integers")

        if zone_type not in self.VALID_TYPES:
            raise ValueError(f"Invalid zone type: {zone_type}")

        self.name = name
        self.x = x
        self.y = y
        self.zone_type = zone_type

    def __repr__(self) -> str:
        return f"{self.name} ({self.x}, {self.y}) [{self.zone_type}]"


class Connection:
    """
    Representa una conexión entre dos zonas
    """
    def __init__(self, zone_a: Zone, zone_b: Zone) -> None:
        if not isinstance(zone_a, Zone) or not isinstance(zone_b, Zone):
            raise TypeError("Connections must link Zone objects")

        if zone_a == zone_b:
            raise ValueError("A zone cannot connect to itself")

        self.zone_a = zone_a
        self.zone_b = zone_b

    def __repr__(self) -> str:
        return f"{self.zone_a.name} <-> {self.zone_b.name}"

    def connects(self, zone_a: Zone, zone_b: Zone) -> bool:
        """
        Comprobamos si conecta las mismas zonas que otra conexión
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
            return start

        pending = [start] # zonas pendientes de explorar
        visited = {start} # zonas que ya hemos visitado
        previous: dict[Zone, Zone | None] = {start: None} # recuerda desde que zona llegamos a cada zona

        while pending:
            current = pending.pop(0)

            for neighbor in self.get_connections(current):
                if neighbor in visited:
                    continue

                visited.add(neighbor)
                previous[neighbor] = current

                if neighbor == goal:
                    pending.clear()
                    break

                pending.append(neighbor)

        if goal not in previous:
            raise ValueError("No route found between start and goal")

        route: list[Zone] = []
        current: Zone | None = goal

        while current is not None:
            route.append(current)
            current = previous[current]

        route.reverse()
        return route



class Drone:
    """
    Representa un dron que se desplaza por el mapa
    """
    def __init__(
            self, drone_id: int, start_zone: Zone, drone_map: Map
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
        self.drones: list[Drone] = []
        drone_id: int = 1

        while drone_id <= number_of_drones:
            drone: Drone = Drone(drone_id, start_zone, drone_map)
            self.drones.append(drone)
            drone_id += 1

    def __repr__(self) -> str:
        return "\n".join(str(drone) for drone in self.drones)


if __name__ == "__main__":
    start: Zone = Zone("start", 0, 0)
    waypoint1: Zone = Zone("waypoint1", 1, 0)
    waypoint2: Zone = Zone("waypoint2", 2, 0)
    goal: Zone = Zone("goal", 3, 0)
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