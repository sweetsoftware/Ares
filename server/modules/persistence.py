

def run(target, operation):
    target["out"].put("persistence")
    target["out"].put(operation)
    print target["in"].get()
    target["out"].put("")
