*This project has been created as part of the 42 curriculum by cesccobio.*

# Fly-in

## Description

Fly-in is a Python project developed as part of the 42 curriculum. It simulates a fleet of drones navigating a network of connected zones, with the objective of transporting every drone from a starting zone to a destination while respecting movement rules and capacity constraints.

The map is represented as a graph consisting of zones (nodes) and connections (edges). Each zone has coordinates, a type, an optional color and an occupancy capacity. Connections are bidirectional and can define a maximum number of drones allowed to traverse them simultaneously.

The project focuses on object-oriented programming, graph traversal, pathfinding, discrete-time simulation, input validation and terminal visualization.

### Main features

- Object-oriented implementation using Python.
- Map parsing with validation and informative error messages.
- Weighted pathfinding using Dijkstra's algorithm.
- Support for normal, restricted, priority and blocked zones.
- Zone occupancy and connection capacity management.
- Turn-based drone movement and restricted-zone transit.
- Interactive terminal visualization using Rich.
- Automated tests and static code analysis.

## Instructions

### Requirements

- Python 3.10 or later.
- pip.
- A terminal capable of displaying Rich output.

### Installation

Clone the repository and enter the project directory:

```bash
git clone <repository-url>
cd flyin
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
make install
```

### Running the project

Launch the interactive simulation:

```bash
make run
```

The default map is `maps/medium/02_circular_loop.txt`.

To run a specific map in subject-compatible output mode:

```bash
python3 main.py --subject maps/easy/01_linear_path.txt
```

Replace the map path with the input file you want to simulate.

### Interactive controls

During the interactive simulation, the available controls are:

- **ENTER:** Advance one simulation turn.
- **A:** Toggle automatic simulation.
- **I:** Display simulation information.
- **R:** Restart the simulation.
- **Q:** Quit or exit the information panel.

### Development commands

The Makefile provides the following commands:

| Command | Description |
|---|---|
| `make install` | Install project dependencies. |
| `make run` | Start the interactive simulation. |
| `make debug` | Run the program using Python's debugger (`pdb`). |
| `make lint` | Run the Flake8 style checker. |
| `make typecheck` | Run MyPy with strict type checking. |
| `make test` | Execute the test suite with pytest. |
| `make clean` | Remove Python bytecode and test/type-checking caches. |

## Map Format

The parser reads a text file describing the number of drones, the zones and the connections.

Example:

```text
nb_drones: 1

start_hub: start 0 0 [color=green]
end_hub: goal 2 0 [color=yellow]
hub: mid 1 0 [zone=normal color=blue]

connection: start-mid
connection: mid-goal
```

### Zone types

| Type | Description |
|---|---|
| `normal` | Standard zone with a movement cost of one turn. |
| `restricted` | Zone requiring two turns to reach. |
| `priority` | Zone with a movement cost of one turn, preferred by the pathfinding algorithm when route costs are equal. |
| `blocked` | Inaccessible zone that drones cannot enter. |

### Metadata

Zone metadata is optional and can include:

- `zone`: The zone type.
- `color`: The color used by the visualization.
- `max_drones`: The maximum number of drones allowed in a zone.

Connection metadata can include:

- `max_link_capacity`: The maximum number of drones allowed to traverse a connection simultaneously.

The start and end zones have unlimited occupancy capacity, as specified by the project subject.

Lines beginning with `#` are treated as comments.

## Algorithm and Implementation Strategy

### Object-oriented architecture

The project separates its responsibilities into dedicated classes and modules.

- **`Zone`** represents a zone, including its coordinates, type, color and capacity.
- **`Connection`** represents a bidirectional link between two zones.
- **`Map`** stores the graph and provides operations to retrieve neighbors, inspect connections, calculate movement costs and find routes.
- **`Drone`** represents an individual drone and manages its route, movement and transit state.
- **`Simulation`** coordinates the drones, processes simulation turns and checks zone and connection capacity constraints.
- **`MapParser`** reads the input file, validates its contents and builds the map data.
- **`display.py`** renders the map and simulation state in the terminal.
- **`main.py`** connects the parser, pathfinding, simulation and visualization.

### Pathfinding

The `Map.find_route()` method uses Dijkstra's algorithm to find a route between the starting zone and the destination.

The algorithm considers the movement cost of each destination zone:

- Normal zones cost one turn.
- Priority zones cost one turn and are preferred when route costs are equal.
- Restricted zones cost two turns.
- Blocked zones cannot be used.

The route cost is calculated using `get_route_cost()`. This weighted approach allows the algorithm to account for movement costs rather than simply counting the number of connections.

### Simulation and movement constraints

The simulation advances in discrete turns. During each turn, drones can move, enter transit or remain in place when movement is not possible.

The simulation accounts for:

- Zone occupancy limits.
- Connection traversal capacity.
- Drones leaving a zone and freeing capacity during the same turn.
- Restricted-zone movements that require two turns.
- Delivery of drones to the destination.
- Detection of a simulation that cannot make progress.

Restricted-zone transit requires special handling: once a drone begins a two-turn movement, it must reach its destination on the next turn and cannot wait on the connection.

### Testing and validation

The project includes automated tests for the models, parser, simulation rules and reference maps.

The development workflow uses:

- **pytest** for automated testing.
- **Flake8** for code style.
- **MyPy** for static type checking.
- Python type annotations and docstrings to improve code clarity and maintainability.

## Visual Representation

The interactive terminal interface is implemented using Rich.

It displays the map, zones, connections, drone positions, simulation status and movement history. Zone colors provide visual distinctions, while the information panel presents details about the map and the selected route.

The interface supports step-by-step execution and automatic simulation, allowing users to observe how drones move through the network and how the simulation progresses.

The `--subject` mode provides a text output compatible with the movement format required by the subject.

## Example Input and Output

Using the example map defined in the Map Format section, the expected subject-compatible output is:

```text
D1-mid
D1-goal
```

Each output line represents one simulation turn. Movements are represented using the format `D<ID>-<destination>`. Drones that do not move during a turn are omitted.

For restricted-zone movements, the output must also represent the drone's transit through the relevant connection according to the subject's output format.

## Resources

- [Python documentation](https://docs.python.org/3/)
- [Rich documentation](https://rich.readthedocs.io/en/stable/)
- [pytest documentation](https://docs.pytest.org/)
- [Flake8 documentation](https://flake8.pycqa.org/)
- [MyPy documentation](https://mypy.readthedocs.io/)
- [Dijkstra's algorithm](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)

### AI usage

AI tools were used to assist in the creation and development of the project's test suite. They helped identify relevant test cases, suggest edge cases, and design tests to validate the behavior of the parser, models, and simulation.

The generated suggestions were reviewed and tested to ensure they were consistent with the project requirements. The final responsibility for understanding, validating, and maintaining the tests remains with the project author.

