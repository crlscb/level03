"""Comprueba los objetivos de rendimiento de los mapas del subject.

Ejecutar desde la raíz del proyecto:
    pytest -v test/test_benchmarks.py

Los turnos se cuentan a partir de las líneas que imprime el programa.
La ejecución se adapta al CLI actual del proyecto: main.py --subject <mapa>.
Si el CLI difiere, cambia únicamente run_map().
"""
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent

BENCHMARKS = (
    ("maps/easy/01_linear_path.txt", 2, 6),
    ("maps/easy/02_simple_fork.txt", 4, 8),
    ("maps/easy/03_basic_capacity.txt", 4, 6),
    ("maps/medium/01_dead_end_trap.txt", 5, 12),
    ("maps/medium/02_circular_loop.txt", 6, 15),
    ("maps/medium/03_priority_puzzle.txt", 5, 12),
    ("maps/hard/01_maze_nightmare.txt", 8, 30),
    ("maps/hard/02_capacity_hell.txt", 12, 35),
    ("maps/hard/03_ultimate_challenge.txt", 15, 45),
)


def run_map(map_path: Path) -> subprocess.CompletedProcess[str]:
    """Ejecuta main.py usando el modo subject y un mapa concreto."""
    return subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "--subject", str(map_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )


def movement_lines(output: str) -> list[str]:
    """Extrae líneas de movimientos que contienen tokens D<ID>-destino."""
    return [
        line.strip()
        for line in output.splitlines()
        if re.search(r"\bD\d+-[A-Za-z0-9_]+", line)
    ]


class TestReferenceBenchmarks(unittest.TestCase):
    """Ejecuta los nueve mapas de referencia y compara los turnos."""

    def test_reference_map_turn_targets(self) -> None:
        failures: list[str] = []

        for relative_path, expected_drones, target_turns in BENCHMARKS:
            map_path = ROOT / relative_path
            with self.subTest(map=relative_path):
                self.assertTrue(
                    map_path.is_file(),
                    f"No se encuentra el mapa: {relative_path}",
                )

                result = run_map(map_path)
                if result.returncode != 0:
                    failures.append(
                        f"{relative_path}: el programa terminó con "
                        f"código {result.returncode}.\n"
                        f"STDERR:\n{result.stderr[-1500:]}\n"
                        f"STDOUT:\n{result.stdout[-1500:]}"
                    )
                    continue

                lines = movement_lines(result.stdout)
                if not lines:
                    failures.append(
                        f"{relative_path}: no se detectaron líneas de "
                        "movimientos en la salida. Puede que --subject "
                        "muestre una interfaz visual distinta; revisa "
                        "la salida y adapta movement_lines()."
                    )
                    continue

                turns = len(lines)
                drone_ids = {
                    int(drone_id)
                    for drone_id in re.findall(r"\bD(\d+)-", result.stdout)
                }
                expected_ids = set(range(1, expected_drones + 1))

                if drone_ids != expected_ids:
                    failures.append(
                        f"{relative_path}: se esperaban los drones "
                        f"{sorted(expected_ids)}, pero aparecen "
                        f"{sorted(drone_ids)}."
                    )
                    continue

                goal_arrivals = re.findall(
                    r"\bD(\d+)-goal\b",
                    result.stdout,
                )
                arrived_ids = {int(drone_id) for drone_id in goal_arrivals}

                if arrived_ids != expected_ids:
                    failures.append(
                        f"{relative_path}: no se ha confirmado la llegada "
                        f"de todos los drones a goal. "
                        f"Llegadas detectadas: {sorted(arrived_ids)}."
                    )
                    continue
                if turns > target_turns:
                    failures.append(
                        f"{relative_path} ({expected_drones} drones): "
                        f"{turns} turnos; objetivo <= {target_turns}."
                    )

        self.assertFalse(
            failures,
            "Problemas detectados en los benchmarks:\n\n"
            + "\n\n".join(failures),
        )


if __name__ == "__main__":
    unittest.main()
