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

    def elapsed(self) -> float:
        return time.time() - self.state.started_at


def board_to_text(board: list[list[int]]) -> str:
    size = len(board)
    header = "   " + " ".join(str(i) for i in range(size))
    lines = [header]
    for y, row in enumerate(board):
        symbols = " ".join("#" if cell else "." for cell in row)
        lines.append(f"{y}  {symbols}")
    return "\n".join(lines)


def print_help(size: int) -> None:
    print("Commands:")
    print("  x y   : Toggle cell (x, y) and its orthogonal neighbors")
    print("  q     : Quit")
    print("  r     : Restart current board")
    print("  n     : Generate a new solvable board")
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

    print("Lights Out (CUI)")
    print("Turn all lights OFF (.)")
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
            game.new_game()
            print("Generated new game.")
            print(board_to_text(game.state.board))
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
