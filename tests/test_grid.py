"""Grid 的测试。"""
import pytest
from src.cell import Cell
from src.grid import Grid


class TestGrid:
    @pytest.fixture
    def grid(self):
        return Grid(width=10, height=10, boundary="toroidal")

    @pytest.fixture
    def walled_grid(self):
        return Grid(width=10, height=10, boundary="walled")

    def test_initial_grid_is_empty(self, grid):
        assert grid.alive_count == 0
        assert grid.total_energy == 0.0

    def test_place_and_get_cell(self, grid):
        c = Cell(x=3, y=5, type=1, energy=5.0)
        grid.place(c)
        assert grid.get(3, 5) is c
        assert grid.alive_count == 1
        assert grid.total_energy == 5.0

    def test_place_overwrites_existing(self, grid):
        c1 = Cell(x=0, y=0, id="old")
        c2 = Cell(x=0, y=0, id="new")
        grid.place(c1)
        grid.place(c2)
        assert grid.get(0, 0).id == "new"
        assert grid.alive_count == 1

    def test_remove_cell(self, grid):
        grid.place(Cell(x=2, y=2, energy=3.0))
        removed = grid.remove(2, 2)
        assert removed is not None
        assert grid.get(2, 2) is None
        assert grid.alive_count == 0

    def test_remove_empty_cell_returns_none(self, grid):
        assert grid.remove(5, 5) is None

    def test_is_empty(self, grid):
        assert grid.is_empty(3, 3)
        grid.place(Cell(x=3, y=3))
        assert not grid.is_empty(3, 3)

    def test_neighbors_toroidal_center_returns_8(self, grid):
        grid.place(Cell(x=5, y=5))
        neighbors = grid.get_neighbors(5, 5)
        assert len(neighbors) == 8
        assert all(n is None for n in neighbors)

    def test_neighbors_toroidal_corner_wraps(self, grid):
        grid.place(Cell(x=0, y=0))
        neighbors = grid.get_neighbors(0, 0)
        assert len(neighbors) == 8

    def test_neighbors_walled_corner_boundary_markers(self, walled_grid):
        neighbors = walled_grid.get_neighbors(0, 0)
        valid = [n for n in neighbors if n is not None]
        assert len(valid) <= 3

    def test_neighbors_include_occupied_cells(self, grid):
        center = Cell(x=5, y=5, id="center")
        north = Cell(x=5, y=4, id="north", type=1)
        grid.place(center)
        grid.place(north)
        neighbors = grid.get_neighbors(5, 5)
        assert north in neighbors

    def test_all_cells_iterates_all(self, grid):
        grid.place(Cell(x=0, y=0))
        grid.place(Cell(x=1, y=1))
        assert len(list(grid.all_cells)) == 2

    def test_random_empty_position_none_when_full(self, grid):
        for x in range(10):
            for y in range(10):
                grid.place(Cell(x=x, y=y))
        assert grid.random_empty_position() is None

    def test_random_empty_position_finds_spot(self, grid):
        pos = grid.random_empty_position()
        assert pos is not None
        x, y = pos
        assert grid.is_empty(x, y)

    def test_positions_around_returns_8(self, grid):
        positions = grid.positions_around(5, 5)
        assert len(positions) == 8
        assert (5, 4) in positions
        assert (5, 6) in positions

    def test_empty_positions_around_excludes_occupied(self, grid):
        grid.place(Cell(x=5, y=4))
        empty = grid.empty_positions_around(5, 5)
        assert (5, 4) not in empty
        assert len(empty) == 7
