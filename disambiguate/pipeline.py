import conducto as co
import json

def myfunc(mem, cpu: int = 1200):
    print("node has 0.75 cpu cores")
    print("node has 1.5 GB of ram")
    print(f"Ryzen {cpu}'s support {mem}")

def func(payload: dict):
    for k, v in payload.items():
        print(k, ":", v)

def wrappedfunc(payload: str):
    func(json.loads(payload))

# for custom types, provide to_str and from_str
class Emoticon:
    def __init__(self, happy=False):
        self.happy = happy

    def to_str(self):
        if self.happy:
            return ":)"
        else:
            return ":("

    def from_str(s):
        if s == ":)":
           return Emoticon(happy=True)
        else:
           return Emoticon(happy=False)

def describe(face: Emoticon):
    print(face.to_str())
    if face.happy:
        print("Happy")
    else:
        print("Sad")

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


        # some non-custom types don't have obvious string representations
        payload = { "foo" : 2,
                    "bar" : 3 }
        func(payload)

        # so you may have to handle the serialization yourself
        node["D"] = co.Exec(wrappedfunc, json.dumps(payload))

        # custom types work, but you need to provide helpers
        param_obj = Emoticon(happy=True)
        node["E"] = co.Exec(describe, param_obj)

    return node


if __name__ == "__main__":
    co.main(default=disambiguate)
