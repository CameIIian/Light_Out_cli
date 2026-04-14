#!/usr/bin/env python3
"""CUI implementation of Lights Out."""

from __future__ import annotations

import argparse
import random
import sys
import time
from dataclasses import dataclass
from typing import Iterable

DIFFICULTY_SIZES = {
    "easy": 4,
    "normal": 5,
    "hard": 7,
    "lunatic": 9,
}


@dataclass
class GameState:
    board: list[list[int]]
    size: int
    move_count: int = 0
    started_at: float = 0.0

    def __post_init__(self) -> None:
        if self.started_at == 0.0:
            self.started_at = time.time()


class LightsOutGame:
    def __init__(self, size: int = 5, seed: int | None = None) -> None:
        if size < 3:
            raise ValueError("Board size must be 3 or larger")
        self.size = size
        self._rng = random.Random(seed)
        self.initial_board = self._generate_solvable_board()
        self.state = GameState(board=self._copy_board(self.initial_board), size=size)

    @staticmethod
    def _copy_board(board: list[list[int]]) -> list[list[int]]:
        return [row[:] for row in board]

    def _empty_board(self) -> list[list[int]]:
        return [[0 for _ in range(self.size)] for _ in range(self.size)]

    def _generate_solvable_board(self) -> list[list[int]]:
        board = self._empty_board()

        # Reverse generation: apply random valid moves from solved state.
        operations = self._rng.randint(self.size, self.size * self.size * 2)
        for _ in range(operations):
            x = self._rng.randrange(self.size)
            y = self._rng.randrange(self.size)
            self._toggle(board, x, y)

        return board

    def _toggle(self, board: list[list[int]], x: int, y: int) -> None:
        for nx, ny in self._neighbors(x, y):
            board[ny][nx] ^= 1

    def _neighbors(self, x: int, y: int) -> Iterable[tuple[int, int]]:
        candidates = [(x, y), (x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
        for nx, ny in candidates:
            if 0 <= nx < self.size and 0 <= ny < self.size:
                yield nx, ny

    def apply_move(self, x: int, y: int) -> None:
        if not (0 <= x < self.size and 0 <= y < self.size):
            raise ValueError(f"Coordinates out of range: x and y must be 0..{self.size - 1}")
        self._toggle(self.state.board, x, y)
        self.state.move_count += 1

    def is_cleared(self) -> bool:
        return all(cell == 0 for row in self.state.board for cell in row)

    def restart(self) -> None:
        self.state = GameState(board=self._copy_board(self.initial_board), size=self.size)

    def new_game(self) -> None:
        self.initial_board = self._generate_solvable_board()
        self.restart()

    def set_size(self, size: int) -> None:
        if size < 3:
            raise ValueError("Board size must be 3 or larger")
        self.size = size
        self.initial_board = self._generate_solvable_board()
        self.state = GameState(board=self._copy_board(self.initial_board), size=self.size)

    def solve_current_board(self) -> list[tuple[int, int]] | None:
        """Return one valid solution move sequence for current board, or None if unsolvable."""
        n = self.size * self.size
        matrix = [0] * n
        rhs = [0] * n

        for y in range(self.size):
            for x in range(self.size):
                row = y * self.size + x
                bits = 0
                for nx, ny in self._neighbors(x, y):
                    bits |= 1 << (ny * self.size + nx)
                matrix[row] = bits
                rhs[row] = self.state.board[y][x]

        pivots: list[int] = []
        pivot_row = 0
        for col in range(n):
            sel = -1
            for row in range(pivot_row, n):
                if (matrix[row] >> col) & 1:
                    sel = row
                    break
            if sel == -1:
                continue

            matrix[pivot_row], matrix[sel] = matrix[sel], matrix[pivot_row]
            rhs[pivot_row], rhs[sel] = rhs[sel], rhs[pivot_row]

            for row in range(n):
                if row != pivot_row and ((matrix[row] >> col) & 1):
                    matrix[row] ^= matrix[pivot_row]
                    rhs[row] ^= rhs[pivot_row]

            pivots.append(col)
            pivot_row += 1
            if pivot_row == n:
                break

        for row in range(pivot_row, n):
            if matrix[row] == 0 and rhs[row]:
                return None

        solution = [0] * n
        for row in range(pivot_row - 1, -1, -1):
            col = pivots[row]
            value = rhs[row]
            tail = matrix[row] >> (col + 1)
            idx = col + 1
            while tail:
                if tail & 1:
                    value ^= solution[idx]
                idx += 1
                tail >>= 1
            solution[col] = value

        moves = []
        for i, pressed in enumerate(solution):
            if pressed:
                x = i % self.size
                y = i // self.size
                moves.append((x, y))
        return moves

    def elapsed(self) -> float:
        return time.time() - self.state.started_at


def board_to_text(board: list[list[int]]) -> str:
    size = len(board)
    header = " y x" + " ".join(f"{i:>2}" for i in range(size))
    lines = [header] # , " y"]
    for y, row in enumerate(board):
        symbols = " ".join(f"{('#' if cell else '.'):>2}" for cell in row)
        lines.append(f"{y:>2}  {symbols}")
    return "\n".join(lines)


def print_help(size: int) -> None:
    print("Commands:")
    print("  x y            : Toggle cell (x=column, y=row) and orthogonal neighbors")
    print("  q     : Quit")
    print("  r     : Restart current board")
    print("  n     : Generate a new solvable board (uses selected difficulty)")
    print("  d LEVEL: Select next difficulty (easy/normal/hard/lunatic)")
    print("  hint  : Show one recommended move")
    print("  ans   : Show one full solution for current board")
    print("  h     : Show this help")
    print("  s     : Show board again")
    print(f"  valid coordinates: 0..{size - 1}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Play Lights Out in your terminal")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--size", type=int, default=None, help="board size N (N >= 3)")
    group.add_argument(
        "--difficulty",
        choices=sorted(DIFFICULTY_SIZES.keys()),
        default=None,
        help="predefined board size",
    )
    parser.add_argument("--seed", type=int, default=None, help="random seed for reproducibility")
    return parser.parse_args(argv)


def resolve_size(args: argparse.Namespace) -> int:
    if args.difficulty:
        return DIFFICULTY_SIZES[args.difficulty]
    if args.size is None:
        return 5
    return args.size


def run_cli(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    size = resolve_size(args)
    try:
        game = LightsOutGame(size=size, seed=args.seed)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 2
    pending_size = game.size

    print("Lights Out (CUI)")
    print("Turn all lights OFF (.)")
    print("Coordinate guide: x = column (horizontal), y = row (vertical)")
    print_help(game.size)
    print(board_to_text(game.state.board))

    while True:
        try:
            raw = input("\nEnter command or x y > ").strip().lower()
        except EOFError:
            print("\nInput closed. Exiting.")
            return 0
        except KeyboardInterrupt:
            print("\nInterrupted. Bye!")
            return 0

        if not raw:
            continue

        if raw in {"q", "quit", "exit"}:
            print("Goodbye!")
            return 0
        if raw == "h":
            print_help(game.size)
            continue
        if raw == "s":
            print(board_to_text(game.state.board))
            continue
        if raw == "r":
            game.restart()
            print("Board restarted.")
            print(board_to_text(game.state.board))
            continue
        if raw == "n":
            if pending_size != game.size:
                game.set_size(pending_size)
                print(f"Applied difficulty change. New board size: {game.size}x{game.size}")
            else:
                game.new_game()
            print("Generated new game.")
            print(board_to_text(game.state.board))
            continue
        if raw.startswith("d "):
            level = raw.split(maxsplit=1)[1].strip()
            if level not in DIFFICULTY_SIZES:
                print("Unknown difficulty. Use: easy / normal / hard / lunatic")
                continue
            pending_size = DIFFICULTY_SIZES[level]
            print(
                f"Difficulty set to '{level}' ({pending_size}x{pending_size}). "
                "It will apply from the next 'n' command."
            )
            continue
        if raw in {"hint", "hi"}:
            moves = game.solve_current_board()
            if moves is None:
                print("No solution found for current board.")
                continue
            if not moves:
                print("Already solved! No moves needed.")
                continue
            x, y = moves[0]
            print(f"Hint: try x={x}, y={y} (column={x}, row={y})")
            continue
        if raw in {"ans", "answer"}:
            moves = game.solve_current_board()
            if moves is None:
                print("No solution found for current board.")
                continue
            if not moves:
                print("Already solved! No moves needed.")
                continue
            formatted = ", ".join(f"({x}, {y})" for x, y in moves)
            print(f"One solution ({len(moves)} moves): {formatted}")
            continue

        parts = raw.split()
        if len(parts) != 2:
            print("Invalid command. Type 'h' for help.")
            continue

        try:
            x, y = int(parts[0]), int(parts[1])
        except ValueError:
            print("Invalid input. Enter coordinates as integers, e.g. '2 3'.")
            continue

        try:
            game.apply_move(x, y)
        except ValueError as exc:
            print(f"Input error: {exc}")
            continue

        print(board_to_text(game.state.board))
        if game.is_cleared():
            print("\n🎉 Cleared! All lights are OFF.")
            print(f"Moves: {game.state.move_count}")
            print(f"Time : {game.elapsed():.1f}s")
            print("Type 'n' for a new board, 'r' to replay this board, or 'q' to quit.")


if __name__ == "__main__":
    raise SystemExit(run_cli())
