import conducto as co
from inspect import cleandoc
import sys

# Docker Images
###############

# for playing the game tick-at-a-time
game_of_life= co.Image(dockerfile='conway/Dockerfile',
                       context='conway')

# Command Templates
###################

# for all commands, use strict mode so that errors draw attention
header = "set -euo pipefail"


# create the start state and stash it
initialize_grid = cleandoc('''
    {header}
    to_grid '0010000000
             0010000011
             0010100011
             0100010000
             0101110001
             0100000001
             0001000111
             0010100000
             0101010010
             0010011000' > grid.json

    # store it as the only item in a list (subsequent grids coming soon)
    cat grid.json | jq '[.]' | tee grids.json
    cat grids.json > /conducto/data/pipeline/grids
''').format(header=header)

# normalize grid representation
show_grid_template = cleandoc('''
     {header}
     # get most recent grid
     cat /conducto/data/pipeline/grids | jq '.[-1]' > grid.json

     # make an image
     cat grid.json | to_png /conducto/data/pipeline/image_{tick}.png {tick}
     IMAGE_URL=$(conducto-data-pipeline url --name "image_{tick}.png" | sed 's/"//g')

     # display it
     echo -n "<ConductoMarkdown>
     ![grid{tick}]($IMAGE_URL)
     </ConductoMarkdown>"
''')

def show_grid(tick):
    return show_grid_template.format(header=header, tick=tick)

# create metadata for each cell
find_neighborhoods_template = cleandoc('''
     {header}
     # get most recent grid
     cat /conducto/data/pipeline/grids | jq '.[-1]' > grid.json

     # consider population density
     cat grid.json | as_neighborhoods > neighborhoods.json
     echo "Neighborhood Samples:"
     cat neighborhoods.json | jq '[first, last]'

     # store neighborhoods for rule consumption
     cat neighborhoods.json > /conducto/data/pipeline/neighborhoods_{tick}
''')

def find_neighborhoods(tick):
    return find_neighborhoods_template.format(header=header, tick=tick)

rule_header_template = header + '\n' + cleandoc('''
     # get neighborhoods
     cat /conducto/data/pipeline/neighborhoods_{tick} > neighborhoods.json
''')

# which cells die because of too-few neighbors?
isolate_template = cleandoc('''
     {rule_header}
     cat neighborhoods.json \\
         | jq 'map(select(.alive == true and .neighbors < 2)
                   | .alive = false)' \\
         | tee isolations.json \\
         > /conducto/data/pipeline/isolations_{tick}

     cat isolations.json
''')

def isolate(tick):
    rule_header = rule_header_template.format(tick=tick)
    return isolate_template.format(rule_header=rule_header, tick=tick)

# which cells survive because of ideal neighbor density?
survive_template = cleandoc('''
     {rule_header}
     cat neighborhoods.json \\
         | jq 'map(select(.alive == true
                          and (.neighbors == 2 or .neighbors == 3))) '\\
         | tee survivals.json \\
         > /conducto/data/pipeline/survivals_{tick}

     cat survivals.json
''')

def survive(tick):
    rule_header = rule_header_template.format(tick=tick)
    return survive_template.format(rule_header=rule_header, tick=tick)

# which cells die because of crowding?
crowd_template = cleandoc('''
     {rule_header}
     cat neighborhoods.json \\
         | jq 'map(select(.alive == true and .neighbors > 3)
                   | .alive = false)' \\
         | tee crowdings.json \\
         > /conducto/data/pipeline/crowdings_{tick}

     cat crowdings.json
''')

def crowd(tick):
    rule_header = rule_header_template.format(tick=tick)
    return crowd_template.format(rule_header=rule_header, tick=tick)

# which cells come alive because of reproduction?
reproduce_template = cleandoc('''
     {rule_header}
     cat neighborhoods.json \\
         | jq 'map(select(.alive == false and .neighbors == 3)
                   | .alive = true)' \\
         | tee reproductions.json \\
         > /conducto/data/pipeline/reproductions_{tick}

     cat reproductions.json
''')

def reproduce(tick):
    rule_header = rule_header_template.format(tick=tick)
    return reproduce_template.format(rule_header=rule_header, tick=tick)

# which cells were dead and stay dead
ignore_template = cleandoc('''
     {rule_header}
     cat neighborhoods.json \\
         | jq 'map(select(.alive == false and .neighbors != 3)
                   | .alive = false)' \\
         | tee ignores.json \\
         > /conducto/data/pipeline/ignores_{tick}

     cat ignores.json
''')

def ignore(tick):
    rule_header = rule_header_template.format(tick=tick)
    return ignore_template.format(rule_header=rule_header, tick=tick)

# pull updated cells into grid for next tick
next_grid_template = cleandoc('''
     {header}
     # get grids so far
     cat /conducto/data/pipeline/grids > grids.json

     # get rule outputs
     cat /conducto/data/pipeline/isolations_{tick}    | jq '.[]' > isolations.json
     cat /conducto/data/pipeline/survivals_{tick}     | jq '.[]' > survivals.json
     cat /conducto/data/pipeline/crowdings_{tick}     | jq '.[]' > crowdings.json
     cat /conducto/data/pipeline/reproductions_{tick} | jq '.[]' > reproductions.json
     cat /conducto/data/pipeline/ignores_{tick}       | jq '.[]' > ignores.json

     # make grid from them
     cat isolations.json survivals.json crowdings.json reproductions.json ignores.json \\
         | jq -s . \\
         | to_grid \\
         | tee new_grid.json


     # append it to the grid list
     cat grids.json | jq ". + [$(cat new_grid.json)]" \\
         | tee updated_grids.json \\
         > /conducto/data/pipeline/"grids"

     cat updated_grids.json
''')

def next_grid(tick):
    return next_grid_template.format(header=header, tick=tick)

animate_template = cleandoc('''
    {header}
    # make a gif
    convert -delay 50 /conducto/data/pipeline/image_*.png -loop 0 /conducto/data/pipeline/life.gif
    IMAGE_URL=$(conducto-data-pipeline url --name "life.gif" | sed 's/"//g')

    # display it
    echo -n "<ConductoMarkdown>
    ![grids]($IMAGE_URL)
    </ConductoMarkdown>"
''')

def animate(image_list):
    return animate_template.format(header=header,
                                   image_list=image_list)

# Pipeline Definition
#####################

num_ticks = 15
ticks = [ str(i).zfill(len(str(num_ticks))) for i in range(num_ticks) ]

# root node
def life() -> co.Serial:


    with co.Serial(image=game_of_life) as pipeline:

        pipeline["initialize grid"] = co.Exec(initialize_grid)

        image_names = []
        # TODO: instead of modeling a fixed number of clock ticks
        # use a lazy node to extend this until a grid state is repeated
        for tick in ticks:
            with co.Serial(name=f"tick {tick}",
                           image=game_of_life) as iteration:

                iteration["show grid"]      = co.Exec(show_grid(tick))
                iteration["find neighbors"] = co.Exec(find_neighborhoods(tick))

                with co.Parallel(name=f"apply_rules",
                               image=game_of_life) as rules:

                    rules["isolate"]   = co.Exec(isolate(tick))
                    rules["survive"]   = co.Exec(survive(tick))
                    rules["crowd"]     = co.Exec(crowd(tick))
                    rules["reproduce"] = co.Exec(reproduce(tick))
                    rules["ignore"]    = co.Exec(ignore(tick))

                iteration["next grid"] = co.Exec(next_grid(tick))

            image_names.append(f"image_{tick}.png")

        image_list = " ".join(image_names)
        pipeline["animate"] = co.Exec(animate(image_list))

    return pipeline

if __name__ == "__main__":
    co.main(default=life)
