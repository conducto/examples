import conducto as co
import json

def myfunc(mem, cpu: int = 1200):
    print("node has 0.75 cpu cores")
    print("node has 1.5 GB of ram")
    print(f"Ryzen {cpu}'s support {mem}")

def otherfunc(payload):

    # 'payload' will come in as a string
    print(payload)

    # so this will fail
    for k, v in payload.items():
        print(k, ":", v)

def fixedfunc(payload : dict):
    # instead, serialize on either side
    otherfunc(json.loads(payload))

def disambiguate() -> co.Parallel:
    with co.Parallel(image=co.Image(copy_dir=".")) as node:

        # no ambiguity here, all kwargs refer to conducto.Node.__init__
        co.Exec('''echo "node has 1.5 cpu's"''', name="A", cpu=1.5)

        # native method parameters come first
        # modify the node object in a second step, then connect it to its parent
        node_obj = co.Exec(myfunc, "DDR4-2933 (quad channel)", cpu=2950)
        node_obj.set(cpu=0.75, mem=1.5)
        node["B"] = node_obj

        # or connect it to its parent, then modify it in place
        node["C"] = co.Exec(myfunc, "DDR4-2667 (dual channel)")
        node["C"].set(cpu=0.75, mem=1.5)


        # there are more than one way to display this as a string
        payload = { "foo" : 2,
                    "bar" : 3 }

        # this will call payload.__str__, which is probably not what you want
        node["D"] = co.Exec(otherfunc, payload)

        # so you may have to hand the serialization yourself
        node["E"] = co.Exec(fixedfunc, json.dumps(payload))

    return node


if __name__ == "__main__":
    co.main(default=disambiguate)
