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

    print("\nRoute:")
    try:
        route = map_data.drone_map.find_route(
            map_data.start_zone,
            map_data.end_zone
        )

        print(" -> ".join(zone.name for zone in route))

        movements_cost = map_data.drone_map.get_route_cost(route)
        print(f"Movement cost total: {movements_cost} turn(s)")
    except ValueError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
