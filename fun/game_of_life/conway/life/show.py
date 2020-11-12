import sys
import pytest
import json
from PIL import Image, ImageDraw, ImageFont

# some parameters for image creation
color = {
    "0" : (223, 223, 224),  # dead
    "1" : (41,  43,  47)  # alive
}
bg = (69, 63, 86)
text = (149, 255, 66)
cell_size = 15
border_size = 15

# make an image of the given grid
# put a number in the upper left corner to indicate which iteration
def image_from_grid(grid, number=None):

    side = len(grid)
    side_px = cell_size * side + 2*border_size
    image = Image.new('RGB', (side_px, side_px), color=bg)
    canvas = image.load()

    # for each cell
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):

            # for each pixel in that cell
            for i in range(cell_size):
                for j in range(cell_size):

                    # color based on aliveness
                    canvas[border_size + x * cell_size + i,
                           border_size + y * cell_size + j] = color[cell]

    # number this image
    if number or number == 0:
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype("/usr/share/fonts/ttf-liberation/LiberationMono-Bold.ttf", cell_size)
        location = (0,0)
        draw.text(location, str(number), text, font=font)

    return image

def test_image_from_grid():
    image = image_from_grid(['101','010','101'])
    image.save('show.py.testimage.png')

def test_image_from_grid_with_number():
    image = image_from_grid(['1011','0101','1011','1100'], number=17)
    image.save('show.py.testimage.number.png')


# setuptools entrypoint, makes a still frame of a grid
# use like:
#   echo '["10","01"] | picture outfile.png 2
def to_png():

    # the file to write
    filename = sys.argv[1]

    # annotate the image with this number
    number = int(sys.argv[2])

    # read grid from stdin
    grid = json.loads(sys.stdin.read())

    image = image_from_grid(grid, number=number)
    image.save(filename)
