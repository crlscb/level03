"""
El mapa está formado por diferentes zonas por las que pueden pasar drones
"""


class Zone:
    """
    Representa una zona individual
    """
    VALID_TYPES = {"normal", "blocked", "restricted", "priority"}

    def __init__(
            self, name: str, x: int, y: int, zone_type: str = "normal"
                ) -> None:
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
        if self.get_zone(zone.name) is not None:
            return
        self.zones.append(zone)

    def add_connection(self, connection: Connection) -> None:
        for existing_connection in self.connections:
            if existing_connection.connects(
                connection.zone_a, connection.zone_b
            ):
                return
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


class Drone:
    """
    Representa un dron que se desplaza por el mapa
    """
    def __init__(
            self, drone_id: int, start_zone: Zone, drone_map: Map
                ) -> None:
        self.drone_id = drone_id
        self.current_zone = start_zone
        self.finished = False
        self.drone_map = drone_map

    def __repr__(self) -> str:
        return f"Drone {self.drone_id} at {self.current_zone.name}"

    def move_to(self, zone: Zone) -> None:
        """
        Mueve el dron a una nueva zona si existe una conexión directa
        y la zona no está bloqueada
        """

        if zone.zone_type == "blocked":
            raise ValueError(
                f"Cannot move to blocked zone: {zone.name}"
            )

        if self.drone_map.are_connected(self.current_zone, zone):
            self.current_zone = zone
        else:
            raise ValueError(
                f"No connection between "
                f"{self.current_zone.name} and {zone.name}"
            )


class Simulation:
    """
    Representa un conjunto de drones
    """
    def __init__(
            self, number_of_drones: int, start_zone: Zone, drone_map: Map
    ) -> None:
        self.drones: list[Drone] = []
        drone_id = 1

        while drone_id <= number_of_drones:
            drone = Drone(drone_id, start_zone, drone_map)
            self.drones.append(drone)
            drone_id += 1

    def __repr__(self) -> str:
        return "\n".join(str(drone) for drone in self.drones)


if __name__ == "__main__":
    start = Zone("start", 0, 0)
    waypoint1 = Zone("waypoint1", 1, 0)
    waypoint2 = Zone("waypoint2", 2, 0)
    goal = Zone("goal", 3, 0)
    blocked = Zone("blocked1", 4, 0, "blocked")
    try:
        blocked2 = Zone("blocked2", 4, 0, "blocked2")
    except ValueError as e:
        print(e)
    my_map = Map()
    my_map.add_zone(start)
    my_map.add_zone(waypoint1)
    my_map.add_zone(waypoint2)
    my_map.add_zone(goal)
    my_map.add_zone(blocked)
    print("Zones:")
    for zone in my_map.zones:
        print(zone)

    connection = Connection(start, waypoint1)
    connection2 = Connection(waypoint1, waypoint2)
    connection3 = Connection(waypoint2, goal)
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

    print("----------------")
    duplicate_connection = Connection(waypoint1, start)
    my_map.add_connection(duplicate_connection)
    print("Number of connection", len(my_map.connections))

    print("-------------")
    drone1 = Drone(1, start, my_map)
    drone2 = Drone(2, start, my_map)
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
    simulation = Simulation(3, start, my_map)
    print(simulation)
