from models import Map, Zone, Connection


class MapData:
    """
    Almacena toda la información extraída del archivo del mapa.
    """

    def __init__(self) -> None:
        self.number_of_drones: int = 0
        self.start_zone: Zone | None = None
        self.end_zone: Zone | None = None
        self.drone_map: Map = Map()


class MapParser:
    """
    Lee y convierte un archivo de mapa en un objeto MapData.
    """

    def __init__(self, filename: str) -> None:
        self.filename: str = filename

    def parse(self) -> MapData:
        """
        Lee el archivo y devuelve los datos del mapa.
        """
        map_data: MapData = MapData()

        with open(self.filename, "r", encoding="utf-8") as file:
            lines: list[str] = file.readlines()

        clean_lines: list[str] = [
            line.strip()
            for line in lines
            if line.strip() and not line.strip().startswith("#")
        ]

        if not clean_lines:
            raise ValueError("Map file is empty")

        first_line: str = clean_lines[0]
        self.parse_number_of_drones(first_line, map_data)

        for line in clean_lines[1:]:
            if line.startswith("start_hub:"):
                if map_data.start_zone is not None:
                    raise ValueError("Multiple start_hub definitions")

                start_data: str = line[len("start_hub:"):].strip()
                start_zone: Zone = self.parse_zone_data(
                    start_data,
                    ignore_max_drones=True
                )
                map_data.start_zone = start_zone
                map_data.drone_map.add_zone(start_zone)
            elif line.startswith("end_hub:"):
                if map_data.end_zone is not None:
                    raise ValueError("Multiple end_hub definitions")

                end_data: str = line[len("end_hub:"):].strip()
                end_zone: Zone = self.parse_zone_data(
                    end_data,
                    ignore_max_drones=True
                )
                map_data.end_zone = end_zone
                map_data.drone_map.add_zone(end_zone)
            elif line.startswith("hub:"):
                hub_data: str = line[len("hub:"):].strip()
                hub_zone: Zone = self.parse_zone_data(hub_data)
                map_data.drone_map.add_zone(hub_zone)
            elif line.startswith("connection:"):
                connection_data: str = line[len("connection:"):].strip()
                self.parse_connection_data(connection_data, map_data)
            else:
                raise ValueError(f"Unknown line: {line}")

        if map_data.start_zone is None:
            raise ValueError("Missing start_hub")

        if map_data.end_zone is None:
            raise ValueError("Missing end_hub")

        return map_data

    def parse_number_of_drones(self, line: str, map_data: MapData) -> None:
        """
        Extrae el número de drones de una línea.
        """
        prefix: str = "nb_drones:"

        if not line.startswith(prefix):
            raise ValueError("Invalid number of drones line")

        value: str = line[len(prefix):].strip()

        try:
            number_of_drones: int = int(value)
        except ValueError:
            raise ValueError("Number of drones must be a positive integer")

        if number_of_drones <= 0:
            raise ValueError("Number of drones must be a positive integer")

        map_data.number_of_drones = number_of_drones

    def parse_zone_data(
            self,
            line: str,
            ignore_max_drones: bool = False
            ) -> Zone:
        """
        Extrae el nombre y las coordenadas de la zona.
        """
        parts: list[str] = line.split()

        if len(parts) < 3:
            raise ValueError("Invalid zone format")

        name: str = parts[0]

        if "-" in name:
            raise ValueError('Zone name cannot contain hyphens ("-")')

        try:
            x: int = int(parts[1])
            y: int = int(parts[2])
        except ValueError:
            raise ValueError("Zone coordinates must be integers")

        zone_type: str = "normal"
        color: str | None = None
        max_drones: int = 1
        metadata: str = " ".join(parts[3:])

        if len(parts) > 3:

            if not metadata.startswith("[") or not metadata.endswith("]"):
                raise ValueError("Invalid zone metadata")

            metadata = metadata[1:-1]

            for item in metadata.split():
                if item.startswith("color="):
                    color = item[6:]

                    if not color:
                        raise ValueError("Color cannot be empty")

                elif item.startswith("zone="):
                    zone_type = item[5:]

                    if not zone_type:
                        raise ValueError("Zone type cannot be empty")

                elif item.startswith("max_drones="):
                    if ignore_max_drones:
                        continue

                    value: str = item[11:]

                    if not value:
                        raise ValueError("Max drones cannot be empty")

                    try:
                        max_drones = int(value)
                    except ValueError:
                        raise ValueError(
                            "max_drones must be a positive integer"
                        )

                    if max_drones <= 0:
                        raise ValueError(
                            "max_drones must be a positive integer"
                        )
                else:
                    raise ValueError(f"Unknown zone metadata: {item}")

        return Zone(
            name,
            x,
            y,
            zone_type=zone_type,
            color=color,
            max_drones=max_drones
        )

    def parse_connection_data(self, data: str, map_data: MapData) -> None:
        """
        Extrae los nombres de las zonas y crea una conexión.
        """
        parts: list[str] = data.split()

        if len(parts) < 1:
            raise ValueError("Invalid connection format")

        connection_data: str = parts[0]
        metadata: str = " ".join(parts[1:])
        max_link_capacity: int = 1

        zone_parts: list[str] = connection_data.split("-")

        if len(zone_parts) != 2:
            raise ValueError("Invalid connection format")

        zone_a_name: str = zone_parts[0]
        zone_b_name: str = zone_parts[1]

        if not zone_a_name or not zone_b_name:
            raise ValueError(
                "Connection zone names cannot be empty"
            )

        if metadata:
            if not metadata.startswith("[") or not metadata.endswith("]"):
                raise ValueError("Invalid connection metadata")

            metadata = metadata[1:-1]

            for item in metadata.split():
                if item.startswith("max_link_capacity="):
                    value: str = item[18:]

                    try:
                        max_link_capacity = int(value)
                    except ValueError:
                        raise ValueError(
                            "max_link_capacity must be a positive integer"
                        )

                    if max_link_capacity <= 0:
                        raise ValueError(
                            "max_link_capacity must be a positive integer"
                        )

                else:
                    raise ValueError(
                        f"Unknown connection metadata: {item}"
                    )

        zone_a: Zone | None = map_data.drone_map.get_zone(zone_a_name)
        zone_b: Zone | None = map_data.drone_map.get_zone(zone_b_name)

        if zone_a is None:
            raise ValueError(
                f"Connection '{zone_a_name}-{zone_b_name}' "
                f"references as unknown zone: {zone_a_name}"
            )

        if zone_b is None:
            raise ValueError(
                f"Connection '{zone_a_name}-{zone_b_name}' "
                f"references unknown zone: {zone_b_name}"
            )

        connection: Connection = Connection(
            zone_a,
            zone_b,
            max_link_capacity=max_link_capacity
        )
        map_data.drone_map.add_connection(connection)


if __name__ == "__main__":
    try:
        parser: MapParser = MapParser("test_map.txt")
        map_data: MapData = parser.parse()

        print("Number of drones:", map_data.number_of_drones)
        print("Start zone:", map_data.start_zone)
        print("End zone:", map_data.end_zone)

        print("\n---- ZONES ----")

        for zone in map_data.drone_map.zones:
            print("Name:", zone.name)
            print("X:", zone.x)
            print("Y:", zone.y)
            print("Type:", zone.zone_type)
            print("Color:", zone.color)
            print("Max drones:", zone.max_drones)
            print()

        print("---- CONNECTIONS ----")

        for connection in map_data.drone_map.connections:
            print(connection)

    except ValueError as error:
        print(f"Error: {error}")
