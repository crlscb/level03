from rich.console import Group
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.align import Align
from rich.progress_bar import ProgressBar
from pyfiglet import Figlet
from models import Simulation


def get_zone_color(color: str | None) -> str:
    if color is None:
        return "white"

    return {"orange": "dark_orange"}.get(color, color)


def draw_map(
    simulation: Simulation,
    turn: int,
    history: list[str] | None = None,
    status: str = "RUNNING"
) -> Panel:

    # Header
    figlet = Figlet(font="small_shadow")

    title_panel = Panel(
        Align.center(
            Text(figlet.renderText("FLY-IN").rstrip("\n"), style="bold white")
        ),
        border_style="bright_blue",
        padding=(0, 0)
    )

    finished = sum(1 for d in simulation.drones if d.finished)
    total = len(simulation.drones)

    header = Table.grid(expand=True, padding=(0, 1))
    header.add_column(ratio=1)
    header.add_column(justify="right")
    header.add_row(
        Text.assemble(
            ("Drone Routing Simulation", "bold bright_white"),
            (f"    TURN {turn}", "bold cyan"),
            (f"    DRONES {total}", "bold cyan"),
        ),
        Text("DELIVERED   ", style="bold_ cyan"),
        ProgressBar(
            total=total,
            completed=finished,
            width=18,
            style="grey23",
            complete_style="green",
            finished_style="green"
        ),
        Text.assemble(
            (f"{finished}/{total}   ", "bold white"),
            (
                f"● {status}", "bold green"
                if status == "RUNNING" else "bold yellow"
            )
        ),
    )

    header_panel = Panel(
        header,
        border_style="bright_blue",
        padding=(0, 1)
    )

    # Controls
    controls = Text()

    controls.append("CONTROLS\n", style="bold cyan")
    controls.append("\n")
    controls.append("[Enter]  ", style="cyan")
    controls.append("Next turn\n")
    controls.append("[A]      ", style="cyan")
    controls.append("Auto mode\n")
    controls.append("[I]      ", style="cyan")
    controls.append("Show information\n")
    controls.append("[R]      ", style="cyan")
    controls.append("Reset simulation\n")
    controls.append("[Q]      ", style="cyan")
    controls.append("Quit\n\n")

    controls.append("─ " * 12 + "\n", style="bright_blue")

    controls.append("ZONE TYPES\n", style="bold cyan")
    controls.append("\n")
    controls.append("■ ", style="white")
    controls.append("Normal\n")
    controls.append("■ ", style="red")
    controls.append("Blocked\n")
    controls.append("■ ", style="yellow")
    controls.append("Restricted\n")
    controls.append("■ ", style="green")
    controls.append("Priority\n\n")

    controls.append("─ " * 12 + "\n", style="bright_blue")

    controls.append("SYMBOLS\n", style="bold cyan")
    controls.append("\n")
    controls.append("—[n]—  ", style="white")
    controls.append("Connection (free)\n")
    controls.append("=[x/n]= ", style="yellow")
    controls.append("Connection (in use)")

    controls_panel = Panel(
        controls,
        title="CONTROLS",
        border_style="bright_blue",
        width=32
    )

    # Zones status
    zones_table = Table(
        title="ZONES STATUS",
        title_style="bold cyan",
        show_header=False,
        box=None,
        padding=(0, 1)
    )
    zones_table.add_column("Zone")
    zones_table.add_column("Drones")

    for zone in simulation.map.zones:
        drones_here = [
            f"D{drone.drone_id}"
            for drone in simulation.drones
            if drone.current_zone == zone
        ]

        zone_color = get_zone_color(zone.color)
        zone_name = Text(zone.name, style=zone_color)

        drone_text = Text(
            "["+" ".join(drones_here)+"]" if drones_here else "[ ]",
            style=zone_color if drones_here else "dim"
        )
        zones_table.add_row(zone_name, drone_text)

    zones_panel = Panel(
        zones_table,
        title="ZONES STATUS",
        border_style="bright_blue"
    )

    # Connections map
    connections_table = Table(
        show_header=True,
        header_style="bold cyan",
        box=None,
        padding=(0, 1)
    )
    connections_table.add_column("From")
    connections_table.add_column("Connection")
    connections_table.add_column("To")

    for connection in simulation.map.connections:
        usage = simulation.connections_in_use.get(connection, 0)
        capacity = connection.max_link_capacity

        if usage:
            connection_status = Text(
                f"=[{usage}/{capacity}]=",
                style="bold yellow"
            )
        else:
            connection_status = Text(
                f"—[{capacity}]—",
                style="dim"
            )

        zone_a_color = get_zone_color(connection.zone_a.color)
        zone_b_color = get_zone_color(connection.zone_b.color)

        zone_a_name = Text(
            connection.zone_a.name,
            style=zone_a_color
        )

        zone_b_name = Text(
            connection.zone_b.name,
            style=zone_b_color
        )

        connections_table.add_row(
            zone_a_name,
            connection_status,
            zone_b_name
        )

    map_panel = Panel(
        connections_table,
        title="MAP / CONNECTIONS",
        border_style="bright_blue"
    )

    # Recent movements
    history_text = Text(
        no_wrap=False,
        overflow="fold"
    )

    if history:
        for i, movement in enumerate(history[-5:]):
            if i:
                history_text.append("\n")
            history_text.append(Text.from_ansi(movement))
    else:
        history_text.append("Waiting for first movement...", style="dim")

    history_panel = Panel(
        history_text,
        title="LAST MOVEMENTS",
        border_style="bright_blue",
        padding=(0, 1),
        expand=True
    )

    # Dashboard layout
    middle = Table.grid(expand=True, padding=(0, 0))
    middle.add_column(width=34)
    middle.add_column(ratio=1)
    middle.add_row(
        controls_panel,
        Group(zones_panel, map_panel)
    )

    dashboard = Group(
        title_panel,
        header_panel,
        middle,
        history_panel
    )

    return Panel(
        dashboard,
        title="[bold cyan]FLY-IN CONTROL[/]",
        border_style="cyan",
        padding=(0, 1)
    )
