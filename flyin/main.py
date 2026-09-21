from parser import MapParser


def main() -> None:
    parser = MapParser("test_map.txt")
    map_data = parser.parse()

    print(f"Drones: {map_data.number_of_drones}")
    print(f"Start: {map_data.start_zone}")
    print(f"End: {map_data.end_zone}")

    print("\nZones:")
    for zone in map_data.drone_map.zones:
        print(f"   {zone}")

    print("\nConnections:")
    for connection in map_data.drone_map.connections:
        print(f"   {connection}")


if __name__ == "__main__":
    main()
