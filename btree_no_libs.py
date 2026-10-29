def find_index(keys, key):
    low = 0
    high = len(keys)
    while low < high:
        middle = (low + high) // 2
        if keys[middle] < key:
            low = middle + 1
        else:
            high = middle
    return low


def make_node(leaf):
    return {"keys": [], "values": [], "children": [], "leaf": leaf}


def make_tree(t=3):
    if t < 2:
        raise ValueError("t must be at least 2")
    return {"t": t, "root": make_node(True), "size": 0}


def find(tree, key):
    node = tree["root"]
    while True:
        i = find_index(node["keys"], key)
        if i < len(node["keys"]) and node["keys"][i] == key:
            return node, i
        if node["leaf"]:
            return None
        node = node["children"][i]


def contains(tree, key):
    return find(tree, key) is not None


def get(tree, key, default=None):
    found = find(tree, key)
    if found is None:
        return default
    node, i = found
    return node["values"][i]


def split_child(t, parent, i):
    full = parent["children"][i]
    right = make_node(full["leaf"])

    middle_key = full["keys"][t - 1]
    middle_value = full["values"][t - 1]

    right["keys"] = full["keys"][t:]
    right["values"] = full["values"][t:]
    full["keys"] = full["keys"][:t - 1]
    full["values"] = full["values"][:t - 1]

    if not full["leaf"]:
        right["children"] = full["children"][t:]
        full["children"] = full["children"][:t]

    parent["keys"].insert(i, middle_key)
    parent["values"].insert(i, middle_value)
    parent["children"].insert(i + 1, right)


def insert_into(t, node, key, value):
    i = find_index(node["keys"], key)

    if node["leaf"]:
        node["keys"].insert(i, key)
        node["values"].insert(i, value)
        return

    if len(node["children"][i]["keys"]) == 2 * t - 1:
        split_child(t, node, i)
        if key > node["keys"][i]:
            i += 1

    insert_into(t, node["children"][i], key, value)


def insert(tree, key, value=None):
    found = find(tree, key)
    if found is not None:
        node, i = found
        node["values"][i] = value
        return

    t = tree["t"]

    if len(tree["root"]["keys"]) == 2 * t - 1:
        new_root = make_node(False)
        new_root["children"].append(tree["root"])
        split_child(t, new_root, 0)
        tree["root"] = new_root

    insert_into(t, tree["root"], key, value)
    tree["size"] += 1


def smallest(node):
    while not node["leaf"]:
        node = node["children"][0]
    return node["keys"][0], node["values"][0]


def biggest(node):
    while not node["leaf"]:
        node = node["children"][-1]
    return node["keys"][-1], node["values"][-1]


def merge(node, i):
    left = node["children"][i]
    right = node["children"].pop(i + 1)

    left["keys"].append(node["keys"].pop(i))
    left["values"].append(node["values"].pop(i))
    left["keys"].extend(right["keys"])
    left["values"].extend(right["values"])
    left["children"].extend(right["children"])


def borrow_from_left(node, i):
    child = node["children"][i]
    left = node["children"][i - 1]

    child["keys"].insert(0, node["keys"][i - 1])
    child["values"].insert(0, node["values"][i - 1])
    node["keys"][i - 1] = left["keys"].pop()
    node["values"][i - 1] = left["values"].pop()

    if not child["leaf"]:
        child["children"].insert(0, left["children"].pop())


def borrow_from_right(node, i):
    child = node["children"][i]
    right = node["children"][i + 1]

    child["keys"].append(node["keys"][i])
    child["values"].append(node["values"][i])
    node["keys"][i] = right["keys"].pop(0)
    node["values"][i] = right["values"].pop(0)

    if not child["leaf"]:
        child["children"].append(right["children"].pop(0))


def fill(t, node, i):
    has_left = i > 0
    has_right = i < len(node["children"]) - 1

    if has_left and len(node["children"][i - 1]["keys"]) >= t:
        borrow_from_left(node, i)
    elif has_right and len(node["children"][i + 1]["keys"]) >= t:
        borrow_from_right(node, i)
    elif has_right:
        merge(node, i)
    else:
        merge(node, i - 1)
        i -= 1

    return i


def delete_from(t, node, key):
    i = find_index(node["keys"], key)
    key_is_here = i < len(node["keys"]) and node["keys"][i] == key

    if key_is_here and node["leaf"]:
        node["keys"].pop(i)
        node["values"].pop(i)
        return True

    if key_is_here:
        left = node["children"][i]
        right = node["children"][i + 1]

        if len(left["keys"]) >= t:
            prev_key, prev_value = biggest(left)
            node["keys"][i] = prev_key
            node["values"][i] = prev_value
            return delete_from(t, left, prev_key)

        if len(right["keys"]) >= t:
            next_key, next_value = smallest(right)
            node["keys"][i] = next_key
            node["values"][i] = next_value
            return delete_from(t, right, next_key)

        merge(node, i)
        return delete_from(t, left, key)

    if node["leaf"]:
        return False

    if len(node["children"][i]["keys"]) < t:
        i = fill(t, node, i)

    return delete_from(t, node["children"][i], key)


def delete(tree, key):
    if not delete_from(tree["t"], tree["root"], key):
        raise KeyError(key)
    tree["size"] -= 1

    root = tree["root"]
    if len(root["keys"]) == 0 and not root["leaf"]:
        tree["root"] = root["children"][0]


def collect(node, result):
    for i in range(len(node["keys"])):
        if not node["leaf"]:
            collect(node["children"][i], result)
        result.append((node["keys"][i], node["values"][i]))
    if not node["leaf"]:
        collect(node["children"][-1], result)


def items(tree):
    result = []
    collect(tree["root"], result)
    return result


def keys(tree):
    return [key for key, value in items(tree)]


def collect_range(node, low, high, result):
    for i in range(len(node["keys"])):
        key = node["keys"][i]
        if not node["leaf"] and key >= low:
            collect_range(node["children"][i], low, high, result)
        if low <= key <= high:
            result.append((key, node["values"][i]))
        if key > high:
            return
    if not node["leaf"]:
        collect_range(node["children"][-1], low, high, result)


def range_query(tree, low, high):
    result = []
    collect_range(tree["root"], low, high, result)
    return result


def height(tree):
    result = 1
    node = tree["root"]
    while not node["leaf"]:
        node = node["children"][0]
        result += 1
    return result


def check_node(t, node, is_root, depth, low, high, leaf_depths):
    count = len(node["keys"])

    assert count <= 2 * t - 1
    if not is_root:
        assert count >= t - 1
    assert node["keys"] == sorted(node["keys"])
    assert len(node["values"]) == count

    for key in node["keys"]:
        assert low is None or key > low
        assert high is None or key < high

    if node["leaf"]:
        leaf_depths.add(depth)
        return

    assert len(node["children"]) == count + 1
    bounds = [low] + node["keys"] + [high]
    for i, child in enumerate(node["children"]):
        check_node(t, child, False, depth + 1, bounds[i], bounds[i + 1], leaf_depths)


def validate(tree):
    leaf_depths = set()
    check_node(tree["t"], tree["root"], True, 1, None, None, leaf_depths)
    assert len(leaf_depths) == 1


def next_random(state, limit):
    state["value"] = (state["value"] * 1103515245 + 12345) % 2147483648
    return (state["value"] >> 8) % limit


def main():
    tree = make_tree(t=2)
    for key in [10, 20, 5, 6, 12, 30, 7, 17]:
        insert(tree, key, f"v{key}")

    print("keys:", keys(tree), "height:", height(tree))
    print("12 ->", get(tree, 12))
    print("99 in tree:", contains(tree, 99))
    print("range 6..17:", range_query(tree, 6, 17))

    delete(tree, 6)
    print("after delete 6:", keys(tree))

    for t in [2, 3, 5, 16]:
        state = {"value": t}
        tree = make_tree(t)
        expected = {}

        for _ in range(20000):
            key = next_random(state, 2001)
            if next_random(state, 100) < 60:
                insert(tree, key, key * 2)
                expected[key] = key * 2
            elif key in expected:
                delete(tree, key)
                del expected[key]

        validate(tree)
        assert tree["size"] == len(expected)
        assert items(tree) == sorted(expected.items())
        print(f"t={t}: OK, size={tree['size']}, height={height(tree)}")


if __name__ == "__main__":
    main()
