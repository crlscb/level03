from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from parser import MapParser
from models import Simulation
from display.display import draw_map
from pathlib import Path
import readchar
import time
import sys

GREEN_LIGHT = "#87F160"

console = Console()


def read_key() -> str:
    """Read a keyboard key."""
    return readchar.readkey().lower()


def main() -> None:
    """Run the drone simulation."""
    map_path = "test_map.txt"

    if "--subject" in sys.argv:
        subject_index = sys.argv.index("--subject")
        if subject_index + 1 < len(sys.argv):
            map_path = sys.argv[subject_index + 1]

    parser = MapParser(str(Path(map_path)))
    map_data = parser.parse()

    if map_data.start_zone is None or map_data.end_zone is None:
        raise ValueError(
            "The start or end zone does not exist in the map."
        )

    try:
        routes = map_data.drone_map.find_alternative_routes(
            map_data.start_zone,
            map_data.end_zone
        )

        route = routes[0]
        movements_cost = map_data.drone_map.get_route_cost(route)

        assigned_routes = [
            routes[i % len(routes)]
            for i in range(map_data.number_of_drones)
        ]
        simulation = Simulation(
            map_data.number_of_drones,
            map_data.start_zone,
            map_data.drone_map
        )
        simulation.run_route(assigned_routes)
        if "--subject" in sys.argv:
            simulation.run_simulation()
            return

        turn = 0
        history: list[str] = []
        auto_mode = False
        info_mode = False

        info_lines = [
            f"Drones: {map_data.number_of_drones}",
            f"Start: {map_data.start_zone}",
            f"End: {map_data.end_zone}",
            "",
            "Zones:",
        ]

        for zone in map_data.drone_map.zones:
            info_lines.append(f"  {zone}")

        info_lines.append("")
        info_lines.append("Connections:")

        for connection in map_data.drone_map.connections:
            info_lines.append(f"  {connection}")

        info_lines.extend([
            "",
            "Route:",
            " -> ".join(zone.name for zone in route),
            f"Route starts correctly: "
            f"{route[0] == map_data.start_zone}",
            f"Route ends correctly: "
            f"{route[-1] == map_data.end_zone}",
            "",
            "Movement cost:",
        ])

        for zone in route[1:]:
            cost = map_data.drone_map.get_movement_cost(zone)
            info_lines.append(f"  {zone.name}: {cost} turn(s)")

        info_lines.append(
            f"Movement cost total: {movements_cost} turn(s)"
        )

        info_panel = Panel(
            "\n".join(info_lines),
            title="[bold cyan]SIMULATION INFO[/]",
            border_style="cyan",
            padding=(1, 2)
        )

        prompt_panel = Panel(
            "ENTER: next turn | A: auto | I: information | "
            "R: restart | Q: quit",
            style=GREEN_LIGHT,
            border_style=GREEN_LIGHT,
            padding=(1, 1)
        )

        with Live(
            Group(draw_map(simulation, turn, history), prompt_panel),
            console=console,
            refresh_per_second=4,
            transient=False,
            screen=True
        ) as live:

            while True:
                if simulation.all_drones_finished():
                    live.update(
                        Group(
                            draw_map(
                                simulation,
                                turn,
                                history,
                                status="COMPLETED"
                            ),
                            Panel(
                                "Simulation completed! :) "
                                "Press 'q' to quit, 'i' for information "
                                "or 'r' to restart.",
                                style=GREEN_LIGHT,
                                border_style=GREEN_LIGHT,
                                padding=(1, 1)
                            )
                        ),
                        refresh=True
                    )

                    key = read_key().lower()

                    if key == "q":
                        break

                    elif key == "i":
                        info_mode = True
                        live.update(
                            Group(info_panel, prompt_panel),
                            refresh=True
                        )

                        while info_mode:
                            key = read_key()

                            if key in ("i", "\r", "\n"):
                                info_mode = False
                                live.update(
                                    Group(
                                        draw_map(
                                            simulation,
                                            turn,
                                            history,
                                            status="COMPLETED"
                                        ),
                                        Panel(
                                            "Simulation completed! :) "
                                            "Press 'q' to quit, 'i' "
                                            "for informartion "
                                            "or 'r' to restart.",
                                            style=GREEN_LIGHT,
                                            border_style=GREEN_LIGHT,
                                            padding=(1, 1)
                                        )
                                    )
                                )

                    elif key == "r":
                        simulation = Simulation(
                            map_data.number_of_drones,
                            map_data.start_zone,
                            map_data.drone_map
                        )
                        simulation.run_route(assigned_routes)
                        turn = 0
                        history.clear()
                        auto_mode = False
                        info_mode = False

                        live.update(
                            Group(
                                draw_map(simulation, turn, history),
                                prompt_panel
                            ),
                            refresh=True
                        )
                    continue

                if info_mode:
                    key = read_key()

                    if key in ("i", "\r", "\n"):
                        info_mode = False
                        live.update(
                            Group(
                                draw_map(simulation, turn, history),
                                prompt_panel
                            ),
                            refresh=True
                        )
                    elif key == "q":
                        break

                    continue

                if auto_mode:
                    time.sleep(1)
                    key = "AUTO"
                else:
                    key = read_key()

                if key == "q":
                    break

                elif key == "i":
                    info_mode = True
                    live.update(
                        Group(info_panel, prompt_panel),
                        refresh=True
                    )
                    continue

                elif key == "a":
                    auto_mode = not auto_mode
                    continue

                elif key == "r":
                    simulation = Simulation(
                        map_data.number_of_drones,
                        map_data.start_zone,
                        map_data.drone_map
                    )
                    simulation.run_route(assigned_routes)
                    turn = 0
                    history.clear()
                    auto_mode = False

                    live.update(
                        Group(
                            draw_map(simulation, turn, history),
                            prompt_panel
                        ),
                        refresh=True
                    )
                    continue

                elif key not in ("\r", "\n", "AUTO"):
                    continue

                turn += 1
                movements = simulation.run_turn()

                if movements:
                    history.append(
                        f"Turn {turn}: " + " | ".join(movements)
                    )

                live.update(
                    Group(
                        draw_map(simulation, turn, history),
                        prompt_panel
                    ),
                    refresh=True
                )

        if simulation.all_drones_finished():
            console.print(
                "\n[bold green]¡Simulation complete! :)[/]"
            )

    except ValueError as error:
        console.print(f"[bold red]Error:[/] {error}")


if __name__ == "__main__":
    try:
        main()
    except ValueError as e:
        print(e)
