from sh import tree
import sys

def main():
    print("Pine, Oak, Parse, Palm... There are so many lovely kinds of trees. Here's one:")
    sys.stdout.flush()
    tree(["-L", "2", ".."], _out=sys.stdout)
