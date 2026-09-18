from models import Map, Zone


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

        data: str
        zone: Zone

        for line in clean_lines[1:]:
            if line.startswith("start_hub:"):
                data = line[len("start_hub:"):].strip()
                zone = self.parse_zone_data(data)
                map_data.start_zone = zone
                map_data.drone_map.add_zone(zone)
            elif line.startswith("end_hub:"):
                data = line[len("end_hub:"):].strip()
                zone = self.parse_zone_data(data)
                map_data.end_zone = zone
                map_data.drone_map.add_zone(zone)
            elif line.startswith("hub:"):
                data = line[len("hub:"):].strip()
                zone = self.parse_zone_data(data)
                map_data.drone_map.add_zone(zone)
            elif line.startswith("connection:"):
                # conexión
                pass
            else:
                raise ValueError(f"Unknown line: {line}")

        first_line: str = clean_lines[0]
        self.parse_number_of_drones(first_line, map_data)

        print(clean_lines)

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

    def parse_zone_data(self, line: str) -> Zone:
        """
        Extrae el nombre y las coordenadas de la zona.
        """
        parts: list[str] = line.split()

        if len(parts) < 3:
            raise ValueError("Invalid zone format")

        name: str = parts[0]
        x: int = int(parts[1])
        y: int = int(parts[2])

        return Zone(name, x, y)


if __name__ == "__main__":
    parser: MapParser = MapParser("test_map.txt")
    map_data: MapData = parser.parse()

    print("Number of drones:", map_data.number_of_drones)
    print("Start zone:", map_data.start_zone)
    print("End zone:", map_data.end_zone)
    print("Zones:", map_data.drone_map.zones)
