import unittest

from lights_out import LightsOutGame, board_to_text, resolve_size


class TestLightsOut(unittest.TestCase):
    def test_toggle_center(self):
        game = LightsOutGame(size=5, seed=1)
        board = [[0] * 5 for _ in range(5)]
        game._toggle(board, 2, 2)

        expected_on = {(2, 2), (1, 2), (3, 2), (2, 1), (2, 3)}
        for y in range(5):
            for x in range(5):
                self.assertEqual(board[y][x], int((x, y) in expected_on))

    def test_toggle_corner_boundary(self):
        game = LightsOutGame(size=4, seed=2)
        board = [[0] * 4 for _ in range(4)]
        game._toggle(board, 0, 0)

        expected_on = {(0, 0), (1, 0), (0, 1)}
        for y in range(4):
            for x in range(4):
                self.assertEqual(board[y][x], int((x, y) in expected_on))

    def test_clear_judgement(self):
        game = LightsOutGame(size=5, seed=3)
        game.state.board = [[0] * 5 for _ in range(5)]
        self.assertTrue(game.is_cleared())
        game.state.board[1][1] = 1
        self.assertFalse(game.is_cleared())

    def test_restart_and_new_game(self):
        game = LightsOutGame(size=5, seed=10)
        original = [row[:] for row in game.initial_board]
        game.apply_move(0, 0)
        game.restart()
        self.assertEqual(game.state.board, original)
        self.assertEqual(game.state.move_count, 0)

        game.new_game()
        self.assertEqual(game.state.move_count, 0)
        self.assertEqual(game.state.board, game.initial_board)

    def test_invalid_size(self):
        with self.assertRaises(ValueError):
            LightsOutGame(size=2)

    def test_board_render(self):
        board = [[0, 1], [1, 0]]
        rendered = board_to_text(board)
        self.assertIn("0 1", rendered)
        self.assertIn("0  . #", rendered)
        self.assertIn("1  # .", rendered)

    def test_solvable_by_reverse_generation(self):
        game = LightsOutGame(size=5, seed=42)
        work = [row[:] for row in game.initial_board]

        # Recreate the random operation sequence and apply it again to solve.
        # (same move twice cancels in Lights Out over GF(2))
        replay = LightsOutGame(size=5, seed=42)
        for y in range(5):
            for x in range(5):
                # neutralize randomness by ensuring deterministic object already built
                _ = replay.state.board[y][x]

        # recover sequence by regenerating from same RNG stream
        import random

        rng = random.Random(42)
        operations = rng.randint(5, 5 * 5 * 2)
        seq = [(rng.randrange(5), rng.randrange(5)) for _ in range(operations)]

        for x, y in seq:
            game._toggle(work, x, y)

        self.assertTrue(all(cell == 0 for row in work for cell in row))

    def test_resolve_size(self):
        class Args:
            difficulty = "hard"
            size = None

        self.assertEqual(resolve_size(Args), 7)


if __name__ == "__main__":
    unittest.main()
