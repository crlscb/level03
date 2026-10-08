from models import Simulation
from utils import color_text

def draw_map(simulation: Simulation, turn: int) -> None:
    print()
    print("╔══════════════════════════════╗")
    print(f"║        TURN {turn:<12}     ║")
    print("╚══════════════════════════════╝")

    for zone in simulation.map.zones:
        drones = [
            f"D{drone.drone_id}"
            for drone in simulation.drones
            if drone.current_zone == zone
        ]

        drone_text = " ".join(drones)

        if drone_text:
            drone_text = color_text(
                f"[{drone_text}]",
                zone.color
            )
        else:
            drone_text = "[ ]"

        print(f"{zone.name:<12} {drone_text}")

    print()
    draw_network(simulation)

def draw_connections(simulation: Simulation) -> None:
    print("Connections:")

    for connection in simulation.map.connections:
        print(
            f"  {connection.zone_a.name}"
            f" ───── "
            f"{connection.zone_b.name}"
        )
    print()

def draw_network(simulation: Simulation) -> None:
    zones = {
        zone.name: zone
        for zone in simulation.map.zones
    }

    def zone_text(name: str) -> str:
        zone = zones[name]

        drones = [
            f"D{drone.drone_id}"
            for drone in simulation.drones
            if drone.current_zone == zone
        ]

        if drones:
            text = f"[{name}: {' '.join(drones)}]"
        else:
            text = f"[{name}]"

        return color_text(text, zone.color)

    def connection_text(zone_a: str, zone_b: str) -> str:
        connection = simulation.map.get_connection(
            zones[zone_a],
            zones[zone_b]
        )

        if connection is None:
            return "────"

        current_usage = simulation.connections_in_use.get(
            connection,
            0
        )

        if current_usage > 0:
            return color_text(
                f"=[{current_usage}/{connection.max_link_capacity}]=",
                "yellow"
            )

        return f"─[{connection.max_link_capacity}]─"

    print("Map:")
    print()

    print(
        zone_text("start")
        + connection_text("start", "waypoint1")
        + zone_text("waypoint1")
        + connection_text("waypoint1", "waypoint2")
        + zone_text("waypoint2")
        + connection_text("waypoint2", "waypoint3")
        + zone_text("waypoint3")
        + connection_text("waypoint3", "goal")
        + zone_text("goal")
    )

    print(" " * 31 + "│")
    print(" " * 31 + "│")

    print(
        " " * 20
        + zone_text("waypoint4")
        + connection_text("waypoint4", "goal")
        + zone_text("goal")
    )

    print()