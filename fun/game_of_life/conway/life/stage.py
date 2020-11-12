import sys
import json
import math
import pytest
from collections import namedtuple

# setuptools entrypoint. Takes a string, prints a grid
# detects input as either a json neighbor list or a raw string with 0's and 1's
def to_grid():

    if len(sys.argv) > 1:
        in_str = sys.argv[1]
    else:
        in_str = sys.stdin.read()

    out_str = input_to_grid(in_str)
    print(json.dumps(out_str, indent=2))

# input as defined by user
def test_to_grid_str():
    in_str = '''101
                001
                111'''

    out = ['101',
           '001',
           '111']
    assert input_to_grid(in_str) == out

# input as filtered by rules
def test_to_grid_neighbors():

    in_str = json.dumps([{ 'x'     : 0,
                           'y'     : 0,
                           'alive' : False },

                         { 'x'     : 1,
                           'y'     : 0,
                           'alive' : False },

                         { 'x'     : 0,
                           'y'     : 1,
                           'alive' : True },

                         { 'x'     : 1,
                           'y'     : 1,
                           'alive' : True }])

    out = ['00',
           '11']

    assert input_to_grid(in_str) == out

# normalize input to a grid
# tolerate multiple input types
def input_to_grid(in_str):

    output = []

    if '[' in in_str and '{' in in_str:
        # assume input is a list of neighborhoods
        neighborhoods = json.loads(in_str)
        if type(neighborhoods) !=  list:
            raise json.JSONDecodeError("expected a list of neighborhoods",
                                       in_str,
                                       0)

        # for each unique y value
        for y in sorted(set([ n['y'] for n in neighborhoods ])):

            # sort cells by x value
            row= sorted(filter(lambda n : n['y'] == y,
                               neighborhoods),
                        key=lambda n : n['x'])

            # add row to list as single string
            output.append(''.join([ str(int(n['alive'])) for n in row ]))

    else:
        # assume input is a string, filter anything but 0, or 1
        cells = list(filter(lambda c: c in ['0', '1'], in_str))

        # make a grid out of it
        sidelen = int(math.sqrt(len(cells)))
        for row_idx in range(0, len(cells), sidelen):
            output.append(''.join(cells[row_idx : row_idx + sidelen]))

    return output


# setuptools entrypoint. Takes a grid, prints a list of neighborhoods
def as_neighborhoods():

    # support input via pipe or arg
    if not sys.stdin.isatty():
        in_str = sys.stdin.read()
    else:
        in_str = sys.argv[1]

    in_grid = json.loads(in_str)
    out_list = grid_as_neighborhoods(in_grid)
    print(json.dumps(out_list, indent=2))

def test_to_neighborhoods():

    in_grid = ['010',
               '001',
               '111']

    out_neighborhoods = [ # row 0
                          { 'x'         : 0,
                            'y'         : 0,
                            'alive'     : False,
                            'neighbors' : 1 },

                          { 'x'         : 1,
                            'y'         : 0,
                            'alive'     : True,
                            'neighbors' : 1 },

                          { 'x'         : 2,
                            'y'         : 0,
                            'alive'     : False,
                            'neighbors' : 2 },

                          # row  1
                          { 'x'         : 0,
                            'y'         : 1,
                            'alive'     : False,
                            'neighbors' : 3 },

                          { 'x'         : 1,
                            'y'         : 1,
                            'alive'     : False,
                            'neighbors' : 5 },

                          { 'x'         : 2,
                            'y'         : 1,
                            'alive'     : True,
                            'neighbors' : 3 },

                          # row 2
                          { 'x'         : 0,
                            'y'         : 2,
                            'alive'     : True,
                            'neighbors' : 1 },

                          { 'x'         : 1,
                            'y'         : 2,
                            'alive'     : True,
                            'neighbors' : 3 },

                          { 'x'         : 2,
                            'y'         : 2,
                            'alive'     : True,
                            'neighbors' : 2 }
                        ]

    assert grid_as_neighborhoods(in_grid) == out_neighborhoods

# count living neighbors for each cell
def grid_as_neighborhoods(_grid):

    grid = _grid
    Coordinates = namedtuple('Coordinates', 'x y')

    cells = []
    for y in range(0, len(grid)):
       for x in range(0, len(grid[y])):
           cells.append(Coordinates(x, y))

    def is_alive(the_cell, unit_vector):
        x = the_cell.x + unit_vector.x
        y = the_cell.y + unit_vector.y
        if x < 0 or y < 0:
            return False
        else:
            try:
                return grid[y][x] == '1'
            except IndexError:
                return False

    neighborhoods = []

    for cell in cells:
        # offset in all directions, count living neighbors
        neighbors = 0
        for vx in [ -1, 0, +1 ]:
            for vy in [ -1, 0, +1 ]:

                # don't count a cell as its own neighbor
                if not (vx == vy == 0):
                    unit_vector = Coordinates(vx, vy)
                    if is_alive(cell, unit_vector):
                        neighbors += 1

        alive = grid[cell.y][cell.x] == '1'

        neighborhoods.append({ 'x'         : cell.x,
                               'y'         : cell.y,
                               'alive'     : alive,
                               'neighbors' : neighbors })

    return neighborhoods


