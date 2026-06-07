import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque
import heapq
import random
import math
import time


START_DEFAULT = "531620478"
GOAL_DEFAULT = "012345678"


def string_to_state(s):
    return [
        [int(s[0]), int(s[1]), int(s[2])],
        [int(s[3]), int(s[4]), int(s[5])],
        [int(s[6]), int(s[7]), int(s[8])]
    ]


def state_to_string(state):
    return "".join(str(x) for row in state for x in row)


def clone_state(state):
    return [row[:] for row in state]


def find_zero(state):
    for i in range(3):
        for j in range(3):
            if state[i][j] == 0:
                return i, j
    return None


def get_neighbors(state):
    x, y = find_zero(state)

    moves = [
        ("UP", -1, 0),
        ("DOWN", 1, 0),
        ("LEFT", 0, -1),
        ("RIGHT", 0, 1)
    ]

    result = []

    for action, dx, dy in moves:
        nx = x + dx
        ny = y + dy

        if 0 <= nx < 3 and 0 <= ny < 3:
            new_state = clone_state(state)
            new_state[x][y], new_state[nx][ny] = new_state[nx][ny], new_state[x][y]
            result.append((new_state, action))

    return result


def get_neighbors_with_swap_value(state):
    x, y = find_zero(state)

    moves = [
        ("UP", -1, 0),
        ("DOWN", 1, 0),
        ("LEFT", 0, -1),
        ("RIGHT", 0, 1)
    ]

    result = []

    for action, dx, dy in moves:
        nx = x + dx
        ny = y + dy

        if 0 <= nx < 3 and 0 <= ny < 3:
            swap_value = state[nx][ny]
            new_state = clone_state(state)
            new_state[x][y], new_state[nx][ny] = new_state[nx][ny], new_state[x][y]
            result.append((new_state, action, swap_value))

    return result


def preview_local_list(items, limit=8):
    data = []

    for item in items[:limit]:
        data.append(f"{item['key']} value={item['value']}")

    if len(items) > limit:
        data.append(f"... +{len(items) - limit}")

    return data



def unique_states(states):
    seen = set()
    result = []
    for state in states:
        key = state_to_string(state)
        if key not in seen:
            seen.add(key)
            result.append(state)
    return result


def belief_key(states):
    return "|".join(sorted(state_to_string(state) for state in states))


def format_belief_key(key):
    parts = str(key).split("|")
    lines = []
    for i, part in enumerate(parts, start=1):
        lines.append(f"S{i}: {part}")
        lines.append(format_key_as_matrix(part))
        lines.append("")
    return "\n".join(lines).strip()


def make_possible_states(base_state, count=2):
    result = [clone_state(base_state)]
    for child_state, _ in get_neighbors(base_state):
        if len(result) >= count:
            break
        result.append(child_state)
    return unique_states(result)


def apply_action_to_state(state, action, absorbing_goal_keys=None):
    key = state_to_string(state)
    if absorbing_goal_keys and key in absorbing_goal_keys:
        return clone_state(state)

    x, y = find_zero(state)
    moves = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}
    dx, dy = moves[action]
    nx = x + dx
    ny = y + dy

    if not (0 <= nx < 3 and 0 <= ny < 3):
        return clone_state(state)

    new_state = clone_state(state)
    new_state[x][y], new_state[nx][ny] = new_state[nx][ny], new_state[x][y]
    return new_state


def belief_h_value(states, goal_states, h_metric="MANHATTAN", aggregate="MAX"):
    values = []
    for state in states:
        best = min(metric_value(state, goal_state, h_metric) for goal_state in goal_states)
        values.append(best)
    if not values:
        return 0
    if aggregate == "AVG":
        return sum(values) / len(values)
    return max(values)


def make_belief_trace_item(iteration, current_states, current_key, action, mode, next_states, candidates, reached, node_cost=None):
    return {
        "iteration": iteration,
        "node": current_states,
        "node_key": current_key,
        "action": action,
        "mode": mode,
        "frontier_after": next_states,
        "reached_after": reached,
        "children": candidates,
        "node_cost": node_cost
    }


def is_valid_input(s):
    return len(s) == 9 and "".join(sorted(s)) == "012345678"


def inversion_count(s):
    arr = [int(x) for x in s if x != "0"]
    count = 0

    for i in range(len(arr)):
        for j in range(i + 1, len(arr)):
            if arr[i] > arr[j]:
                count += 1

    return count


def is_solvable(start, goal):
    return inversion_count(start) % 2 == inversion_count(goal) % 2


def misplaced_tiles(state, goal_state):
    count = 0

    for i in range(3):
        for j in range(3):
            if state[i][j] != 0 and state[i][j] != goal_state[i][j]:
                count += 1

    return count


def goal_positions(goal_state):
    pos = {}

    for i in range(3):
        for j in range(3):
            pos[goal_state[i][j]] = (i, j)

    return pos


def manhattan_distance(state, goal_state):
    pos = goal_positions(goal_state)
    total = 0

    for i in range(3):
        for j in range(3):
            value = state[i][j]

            if value != 0:
                gi, gj = pos[value]
                total += abs(i - gi) + abs(j - gj)

    return total


def inversion_metric(state, goal_state):
    goal_order = {}

    for i in range(3):
        for j in range(3):
            goal_order[goal_state[i][j]] = i * 3 + j

    arr = []

    for row in state:
        for value in row:
            if value != 0:
                arr.append(goal_order[value])

    count = 0

    for i in range(len(arr)):
        for j in range(i + 1, len(arr)):
            if arr[i] > arr[j]:
                count += 1

    return count


def swap_metric(state, goal_state):
    current = [value for row in state for value in row]
    goal = [value for row in goal_state for value in row]

    current = current[:]
    swaps = 0

    while current != goal:
        blank_index = current.index(0)

        if goal[blank_index] != 0:
            tile_needed = goal[blank_index]
            tile_index = current.index(tile_needed)
        else:
            tile_index = None

            for i in range(9):
                if current[i] != goal[i] and current[i] != 0:
                    tile_index = i
                    break

            if tile_index is None:
                break

        current[blank_index], current[tile_index] = current[tile_index], current[blank_index]
        swaps += 1

    return swaps


def metric_value(state, goal_state, metric_name):
    if metric_name == "MANHATTAN":
        return manhattan_distance(state, goal_state)

    if metric_name == "INVERSION":
        return inversion_metric(state, goal_state)

    if metric_name == "SWAP":
        return swap_metric(state, goal_state)

    return misplaced_tiles(state, goal_state)


def heuristic_value(state, goal_state, heuristic_name):
    return metric_value(state, goal_state, heuristic_name)


def ui_metric_to_code(name):
    mapping = {
        "Số ô sai": "MISPLACED",
        "Manhattan": "MANHATTAN",
        "Dãy ngược": "INVERSION",
        "Swap": "SWAP"
    }

    return mapping.get(name, "MANHATTAN")


def metric_display_name(metric_code):
    mapping = {
        "MISPLACED": "Số ô sai",
        "MANHATTAN": "Manhattan",
        "INVERSION": "Dãy ngược",
        "SWAP": "Swap"
    }

    return mapping.get(metric_code, metric_code)


def reconstruct_path(goal_key, parent, state_map):
    keys = []
    actions = []
    current = goal_key

    while current is not None:
        keys.append(current)
        info = parent.get(current)

        if info is None:
            break

        parent_key, action = info
        actions.append(action)
        current = parent_key

    keys.reverse()
    actions.reverse()

    return [state_map[k] for k in keys], actions


def make_trace_item(iteration, node_state, node_key, action, mode,
                    frontier_after, reached_after, children, node_cost=None):
    return {
        "iteration": iteration,
        "node": node_state,
        "node_key": node_key,
        "action": action,
        "mode": mode,
        "frontier_after": frontier_after,
        "reached_after": reached_after,
        "children": children,
        "node_cost": node_cost
    }


def preview_plain(keys, limit=8):
    data_all = list(keys)
    data = data_all[:limit]
    if len(data_all) > limit:
        data.append(f"... +{len(data_all) - limit}")
    return data


def preview_frontier_nodes(nodes, limit=8):
    data = [node["key"] for node in list(nodes)[:limit]]
    if len(nodes) > limit:
        data.append(f"... +{len(nodes) - limit}")
    return data


def format_key_as_matrix(key):
    key = str(key)

    if " " in key:
        state_key = key[:9]
        extra = key[9:].strip()
    else:
        state_key = key[:9]
        extra = ""

    if not state_key.isdigit() or len(state_key) != 9:
        return key

    rows = []
    for i in range(0, 9, 3):
        row = state_key[i:i + 3]
        rows.append(" ".join("_" if ch == "0" else ch for ch in row))

    text = "\n".join(rows)

    if extra:
        text += f"   {extra}"

    return text


def format_key_list_as_matrices(items, limit=8):
    if not items:
        return "Rỗng"

    lines = []

    for index, item in enumerate(items[:limit], start=1):
        lines.append(f"#{index}")
        lines.append(format_key_as_matrix(item))
        lines.append("")

    if len(items) > limit:
        lines.append(f"... +{len(items) - limit} trạng thái")

    return "\n".join(lines).strip()


def preview_priority_queue(heap, limit=8):
    ordered = sorted(heap)
    data = []

    for cost, order, node in ordered[:limit]:
        data.append(f"{node['key']} g={cost}")

    if len(heap) > limit:
        data.append(f"... +{len(heap) - limit}")

    return data


def preview_greedy_queue(heap, limit=8):
    ordered = sorted(heap)
    data = []

    for h, order, node in ordered[:limit]:
        data.append(f"{node['key']} h={h}")

    if len(heap) > limit:
        data.append(f"... +{len(heap) - limit}")

    return data


def preview_astar_queue(heap, limit=8):
    ordered = sorted(heap)
    data = []

    for f_value, order, node in ordered[:limit]:
        data.append(f"{node['key']} f={node['f']} g={node['g']} h={node['h']}")

    if len(heap) > limit:
        data.append(f"... +{len(heap) - limit}")

    return data


def bfs_early(start, goal):
    start_key = state_to_string(start)
    goal_key = state_to_string(goal)

    frontier = deque([{
        "key": start_key,
        "state": start,
        "path": [start],
        "actions": [],
        "action": "START"
    }])

    reached = {start_key}
    trace = []
    nodes_expanded = 0

    while frontier:
        node = frontier.popleft()
        nodes_expanded += 1

        children_info = []

        if node["key"] == goal_key:
            trace.append(make_trace_item(
                nodes_expanded,
                node["state"],
                node["key"],
                node["action"],
                "BFS: Queue FIFO, kiểm tra child trước khi thêm frontier",
                preview_frontier_nodes(frontier),
                preview_plain(reached),
                children_info
            ))

            return {
                "path": node["path"],
                "actions": node["actions"],
                "nodes": nodes_expanded,
                "depth": len(node["actions"]),
                "cost": len(node["actions"]),
                "trace": trace
            }

        for child_state, action in get_neighbors(node["state"]):
            child_key = state_to_string(child_state)

            if child_key not in reached:
                reached.add(child_key)

                frontier.append({
                    "key": child_key,
                    "state": child_state,
                    "path": node["path"] + [child_state],
                    "actions": node["actions"] + [action],
                    "action": action
                })

                status = "ADD"
            else:
                status = "SKIP"

            children_info.append({
                "state": child_state,
                "key": child_key,
                "action": action,
                "status": status
            })

        if len(trace) < 1000:
            trace.append(make_trace_item(
                nodes_expanded,
                node["state"],
                node["key"],
                node["action"],
                "BFS: Queue FIFO, kiểm tra child trước khi thêm frontier",
                preview_frontier_nodes(frontier),
                preview_plain(reached),
                children_info
            ))

    return None


def bfs_late(start, goal):
    start_key = state_to_string(start)
    goal_key = state_to_string(goal)

    frontier = deque([{
        "key": start_key,
        "state": start,
        "path": [start],
        "actions": [],
        "action": "START"
    }])

    reached = set()
    trace = []
    nodes_expanded = 0
    iteration = 0

    while frontier:
        node = frontier.popleft()
        iteration += 1

        children_info = []

        if node["key"] in reached:
            children_info.append({
                "state": node["state"],
                "key": node["key"],
                "action": "SKIP",
                "status": "Đã có trong reached"
            })

            if len(trace) < 1000:
                trace.append(make_trace_item(
                    iteration,
                    node["state"],
                    node["key"],
                    node["action"],
                    "BFS cách 2: lấy node ra rồi mới kiểm tra reached",
                    preview_frontier_nodes(frontier),
                    preview_plain(reached),
                    children_info
                ))

            continue

        reached.add(node["key"])
        nodes_expanded += 1

        if node["key"] == goal_key:
            trace.append(make_trace_item(
                iteration,
                node["state"],
                node["key"],
                node["action"],
                "BFS cách 2: lấy node ra rồi mới kiểm tra reached",
                preview_frontier_nodes(frontier),
                preview_plain(reached),
                children_info
            ))

            return {
                "path": node["path"],
                "actions": node["actions"],
                "nodes": nodes_expanded,
                "depth": len(node["actions"]),
                "cost": len(node["actions"]),
                "trace": trace
            }

        for child_state, action in get_neighbors(node["state"]):
            child_key = state_to_string(child_state)

            frontier.append({
                "key": child_key,
                "state": child_state,
                "path": node["path"] + [child_state],
                "actions": node["actions"] + [action],
                "action": action
            })

            children_info.append({
                "state": child_state,
                "key": child_key,
                "action": action,
                "status": "ADD"
            })

        if len(trace) < 1000:
            trace.append(make_trace_item(
                iteration,
                node["state"],
                node["key"],
                node["action"],
                "BFS cách 2: lấy node ra rồi mới kiểm tra reached",
                preview_frontier_nodes(frontier),
                preview_plain(reached),
                children_info
            ))

    return None


def uniform_cost_search(start, goal, g_metric="MISPLACED"):
    start_key = state_to_string(start)
    goal_key = state_to_string(goal)

    order = 0
    start_node = {
        "key": start_key,
        "state": start,
        "path": [start],
        "actions": [],
        "action": "START",
        "cost": 0
    }

    frontier = [(0, order, start_node)]
    order += 1

    frontier_best_cost = {start_key: 0}
    reached_cost = {}
    trace = []
    nodes_expanded = 0

    while frontier:
        cost, _, node = heapq.heappop(frontier)

        if frontier_best_cost.get(node["key"]) != cost:
            continue

        frontier_best_cost.pop(node["key"], None)

        if node["key"] in reached_cost and reached_cost[node["key"]] <= cost:
            continue

        reached_cost[node["key"]] = cost
        nodes_expanded += 1

        children_info = []

        if node["key"] == goal_key:
            trace.append(make_trace_item(
                nodes_expanded,
                node["state"],
                node["key"],
                node["action"],
                f"UCS: Priority Queue theo g(n), g(node)={cost}",
                preview_priority_queue(frontier),
                [f"{k} g={v}" for k, v in list(reached_cost.items())[:8]],
                children_info,
                node_cost=cost
            ))

            return {
                "path": node["path"],
                "actions": node["actions"],
                "nodes": nodes_expanded,
                "depth": len(node["actions"]),
                "cost": cost,
                "trace": trace
            }

        for child_state, action in get_neighbors(node["state"]):
            child_key = state_to_string(child_state)
            new_cost = cost + metric_value(child_state, goal, g_metric)

            child_info = {
                "state": child_state,
                "key": child_key,
                "action": action,
                "status": "",
                "cost": new_cost
            }

            if child_key in reached_cost and reached_cost[child_key] <= new_cost:
                child_info["status"] = "SKIP"
                children_info.append(child_info)
                continue

            if child_key not in frontier_best_cost or new_cost < frontier_best_cost[child_key]:
                child_node = {
                    "key": child_key,
                    "state": child_state,
                    "path": node["path"] + [child_state],
                    "actions": node["actions"] + [action],
                    "action": action,
                    "cost": new_cost
                }

                frontier_best_cost[child_key] = new_cost
                heapq.heappush(frontier, (new_cost, order, child_node))
                order += 1
                child_info["status"] = "ADD/UPDATE"
            else:
                child_info["status"] = "SKIP"

            children_info.append(child_info)

        if len(trace) < 1000:
            trace.append(make_trace_item(
                nodes_expanded,
                node["state"],
                node["key"],
                node["action"],
                f"UCS: g(child) = g(parent) + {metric_display_name(g_metric)} của child",
                preview_priority_queue(frontier),
                [f"{k} g={v}" for k, v in list(reached_cost.items())[:8]],
                children_info,
                node_cost=cost
            ))

    return None


def greedy_search(start, goal, heuristic_name="MISPLACED"):
    start_key = state_to_string(start)
    goal_key = state_to_string(goal)

    order = 0
    h_start = heuristic_value(start, goal, heuristic_name)

    start_node = {
        "key": start_key,
        "state": start,
        "path": [start],
        "actions": [],
        "action": "START",
        "h": h_start
    }

    frontier = [(h_start, order, start_node)]
    order += 1

    frontier_keys = {start_key}
    reached = set()
    trace = []
    nodes_expanded = 0

    while frontier:
        h_value, _, node = heapq.heappop(frontier)

        if node["key"] not in frontier_keys:
            continue

        frontier_keys.remove(node["key"])

        if node["key"] in reached:
            continue

        nodes_expanded += 1
        children_info = []

        if node["key"] == goal_key:
            trace.append(make_trace_item(
                nodes_expanded,
                node["state"],
                node["key"],
                node["action"],
                f"Greedy Search: chọn node có h(n) nhỏ nhất. h(node)={h_value}",
                preview_greedy_queue(frontier),
                preview_plain(reached),
                children_info,
                node_cost=h_value
            ))

            return {
                "path": node["path"],
                "actions": node["actions"],
                "nodes": nodes_expanded,
                "depth": len(node["actions"]),
                "cost": len(node["actions"]),
                "trace": trace
            }

        reached.add(node["key"])

        for child_state, action in get_neighbors(node["state"]):
            child_key = state_to_string(child_state)
            h_child = heuristic_value(child_state, goal, heuristic_name)

            child_info = {
                "state": child_state,
                "key": child_key,
                "action": action,
                "status": "",
                "cost": h_child
            }

            if child_key not in reached and child_key not in frontier_keys:
                child_node = {
                    "key": child_key,
                    "state": child_state,
                    "path": node["path"] + [child_state],
                    "actions": node["actions"] + [action],
                    "action": action,
                    "h": h_child
                }

                heapq.heappush(frontier, (h_child, order, child_node))
                order += 1
                frontier_keys.add(child_key)
                child_info["status"] = "ADD"
            else:
                child_info["status"] = "SKIP"

            children_info.append(child_info)

        if len(trace) < 1000:
            trace.append(make_trace_item(
                nodes_expanded,
                node["state"],
                node["key"],
                node["action"],
                f"Greedy Search: Frontier chọn h(n) nhỏ nhất, heuristic={heuristic_name}",
                preview_greedy_queue(frontier),
                preview_plain(reached),
                children_info,
                node_cost=h_value
            ))

    return None



def simple_hill_climbing_swap(start, goal, max_steps=80):
    goal_key = state_to_string(goal)

    current_state = start
    current_key = state_to_string(current_state)
    current_value = 0

    path = [current_state]
    actions = []
    trace = []
    nodes_expanded = 0
    reached = {current_key}

    for step in range(1, max_steps + 1):
        children_info = []
        chosen = None
        all_neighbors = []

        if current_key == goal_key:
            trace.append(make_trace_item(
                step,
                current_state,
                current_key,
                actions[-1] if actions else "START",
                "Leo đồi đơn giản: đã gặp Goal",
                [],
                preview_plain(reached),
                children_info,
                node_cost=current_value
            ))

            return {
                "path": path,
                "actions": actions,
                "nodes": nodes_expanded,
                "depth": len(actions),
                "cost": current_value,
                "trace": trace,
                "solved": True,
                "message": "Đã tìm thấy Goal"
            }

        nodes_expanded += 1

        for child_state, action, swap_value in get_neighbors_with_swap_value(current_state):
            child_key = state_to_string(child_state)
            all_neighbors.append({"key": child_key, "value": swap_value})

            if child_key in reached:
                status = f"SKIP reached, swap={swap_value}"
            elif swap_value > current_value:
                status = f"CHỌN NGAY vì {swap_value} > {current_value}"
                chosen = (child_state, action, swap_value, child_key)
            else:
                status = f"KHÔNG CHỌN vì {swap_value} <= {current_value}"

            children_info.append({
                "state": child_state,
                "key": child_key,
                "action": action,
                "status": status,
                "cost": swap_value
            })

            if chosen is not None:
                break

        trace.append(make_trace_item(
            step,
            current_state,
            current_key,
            actions[-1] if actions else "START",
            "Leo đồi đơn giản: xét các trạng thái lân cận theo thứ tự sinh con mặc định; gặp trạng thái đầu tiên có value lớn hơn current thì chọn",
            preview_local_list(all_neighbors),
            preview_plain(reached),
            children_info,
            node_cost=current_value
        ))

        if chosen is None:
            return {
                "path": path,
                "actions": actions,
                "nodes": nodes_expanded,
                "depth": len(actions),
                "cost": current_value,
                "trace": trace,
                "solved": False,
                "message": "Dừng tại local maximum"
            }

        current_state, action, current_value, current_key = chosen
        path.append(current_state)
        actions.append(action)
        reached.add(current_key)

    return {
        "path": path,
        "actions": actions,
        "nodes": nodes_expanded,
        "depth": len(actions),
        "cost": current_value,
        "trace": trace,
        "solved": False,
        "message": "Dừng vì vượt quá số bước giới hạn"
    }


def steepest_hill_climbing_swap(start, goal, max_steps=80):
    goal_key = state_to_string(goal)

    current_state = start
    current_key = state_to_string(current_state)
    current_value = 0

    path = [current_state]
    actions = []
    trace = []
    nodes_expanded = 0
    reached = {current_key}

    for step in range(1, max_steps + 1):
        children_info = []
        candidates = []

        if current_key == goal_key:
            trace.append(make_trace_item(
                step,
                current_state,
                current_key,
                actions[-1] if actions else "START",
                "Leo núi dốc nhất: đã gặp Goal",
                [],
                preview_plain(reached),
                children_info,
                node_cost=current_value
            ))

            return {
                "path": path,
                "actions": actions,
                "nodes": nodes_expanded,
                "depth": len(actions),
                "cost": current_value,
                "trace": trace,
                "solved": True,
                "message": "Đã tìm thấy Goal"
            }

        nodes_expanded += 1

        for child_state, action, swap_value in get_neighbors_with_swap_value(current_state):
            child_key = state_to_string(child_state)

            if child_key in reached:
                status = f"SKIP reached, swap={swap_value}"
            else:
                status = f"ỨNG VIÊN, swap={swap_value}"
                candidates.append({
                    "state": child_state,
                    "key": child_key,
                    "action": action,
                    "value": swap_value
                })

            children_info.append({
                "state": child_state,
                "key": child_key,
                "action": action,
                "status": status,
                "cost": swap_value
            })

        best = None

        if candidates:
            best = max(candidates, key=lambda item: item["value"])

        if best is not None and best["value"] > current_value:
            for child in children_info:
                if child["key"] == best["key"]:
                    child["status"] = f"CHỌN TỐT NHẤT value={best['value']} > {current_value}"
                    break

        trace.append(make_trace_item(
            step,
            current_state,
            current_key,
            actions[-1] if actions else "START",
            "Leo núi dốc nhất: xét hết tất cả trạng thái lân cận rồi chọn node có value lớn nhất",
            preview_local_list(candidates),
            preview_plain(reached),
            children_info,
            node_cost=current_value
        ))

        if best is None or best["value"] <= current_value:
            return {
                "path": path,
                "actions": actions,
                "nodes": nodes_expanded,
                "depth": len(actions),
                "cost": current_value,
                "trace": trace,
                "solved": False,
                "message": "Dừng tại local maximum"
            }

        current_state = best["state"]
        current_key = best["key"]
        current_value = best["value"]
        path.append(current_state)
        actions.append(best["action"])
        reached.add(current_key)

    return {
        "path": path,
        "actions": actions,
        "nodes": nodes_expanded,
        "depth": len(actions),
        "cost": current_value,
        "trace": trace,
        "solved": False,
        "message": "Dừng vì vượt quá số bước giới hạn"
    }







def simple_hill_climbing_h(start, goal, h_metric="MANHATTAN", max_steps=80):
    goal_key = state_to_string(goal)
    current_state = start
    current_key = state_to_string(current_state)
    current_h = metric_value(current_state, goal, h_metric)
    path = [current_state]
    actions = []
    trace = []
    reached = {current_key}
    nodes_expanded = 0

    for step in range(1, max_steps + 1):
        children_info = []
        if current_key == goal_key:
            trace.append(make_trace_item(step, current_state, current_key, actions[-1] if actions else "START", f"Leo đồi đơn giản: đã gặp Goal, h={current_h}", [], preview_plain(reached), children_info, node_cost=current_h))
            return {"path": path, "actions": actions, "nodes": nodes_expanded, "depth": len(actions), "cost": current_h, "trace": trace, "solved": True, "message": "Đã tìm thấy Goal"}

        nodes_expanded += 1
        chosen = None
        candidates = []

        for child_state, action in get_neighbors(current_state):
            child_key = state_to_string(child_state)
            h_child = metric_value(child_state, goal, h_metric)
            candidates.append({"key": child_key, "value": h_child})

            if child_key in reached:
                status = f"SKIP reached, h={h_child}"
            elif h_child < current_h:
                status = f"CHỌN NGAY vì h={h_child} < current_h={current_h}"
                chosen = {"state": child_state, "key": child_key, "action": action, "value": h_child}
            else:
                status = f"KHÔNG CHỌN vì h={h_child} >= current_h={current_h}"

            children_info.append({"state": child_state, "key": child_key, "action": action, "status": status, "cost": h_child})

            if chosen is not None:
                break

        trace.append(make_trace_item(step, current_state, current_key, actions[-1] if actions else "START", f"Leo đồi đơn giản: dùng h(n)={metric_display_name(h_metric)}, h càng nhỏ càng tốt; gặp neighbor đầu tiên tốt hơn thì chọn", preview_local_list(candidates), preview_plain(reached), children_info, node_cost=current_h))

        if chosen is None:
            return {"path": path, "actions": actions, "nodes": nodes_expanded, "depth": len(actions), "cost": current_h, "trace": trace, "solved": False, "message": "Dừng tại local optimum"}

        current_state = chosen["state"]
        current_key = chosen["key"]
        current_h = chosen["value"]
        path.append(current_state)
        actions.append(chosen["action"])
        reached.add(current_key)

    return {"path": path, "actions": actions, "nodes": nodes_expanded, "depth": len(actions), "cost": current_h, "trace": trace, "solved": False, "message": "Dừng vì vượt quá số bước giới hạn"}


def steepest_hill_climbing_h(start, goal, h_metric="MANHATTAN", max_steps=80):
    goal_key = state_to_string(goal)
    current_state = start
    current_key = state_to_string(current_state)
    current_h = metric_value(current_state, goal, h_metric)
    path = [current_state]
    actions = []
    trace = []
    reached = {current_key}
    nodes_expanded = 0

    for step in range(1, max_steps + 1):
        children_info = []
        if current_key == goal_key:
            trace.append(make_trace_item(step, current_state, current_key, actions[-1] if actions else "START", f"Leo núi dốc nhất: đã gặp Goal, h={current_h}", [], preview_plain(reached), children_info, node_cost=current_h))
            return {"path": path, "actions": actions, "nodes": nodes_expanded, "depth": len(actions), "cost": current_h, "trace": trace, "solved": True, "message": "Đã tìm thấy Goal"}

        nodes_expanded += 1
        candidates = []

        for child_state, action in get_neighbors(current_state):
            child_key = state_to_string(child_state)
            h_child = metric_value(child_state, goal, h_metric)

            if child_key in reached:
                status = f"SKIP reached, h={h_child}"
            else:
                status = f"ỨNG VIÊN h={h_child}"
                candidates.append({"state": child_state, "key": child_key, "action": action, "value": h_child})

            children_info.append({"state": child_state, "key": child_key, "action": action, "status": status, "cost": h_child})

        best = min(candidates, key=lambda item: item["value"]) if candidates else None

        if best is not None and best["value"] < current_h:
            for child in children_info:
                if child["key"] == best["key"]:
                    child["status"] = f"CHỌN TỐT NHẤT vì h={best['value']} < current_h={current_h}"
                    break

        trace.append(make_trace_item(step, current_state, current_key, actions[-1] if actions else "START", f"Leo núi dốc nhất: dùng h(n)={metric_display_name(h_metric)}, sinh hết neighbor rồi chọn h nhỏ nhất", preview_local_list(candidates), preview_plain(reached), children_info, node_cost=current_h))

        if best is None or best["value"] >= current_h:
            return {"path": path, "actions": actions, "nodes": nodes_expanded, "depth": len(actions), "cost": current_h, "trace": trace, "solved": False, "message": "Dừng tại local optimum"}

        current_state = best["state"]
        current_key = best["key"]
        current_h = best["value"]
        path.append(current_state)
        actions.append(best["action"])
        reached.add(current_key)

    return {"path": path, "actions": actions, "nodes": nodes_expanded, "depth": len(actions), "cost": current_h, "trace": trace, "solved": False, "message": "Dừng vì vượt quá số bước giới hạn"}


def stochastic_hill_climbing(start, goal, h_metric="MANHATTAN", max_steps=80, seed=7):
    random.seed(seed)
    goal_key = state_to_string(goal)
    current_state = start
    current_key = state_to_string(current_state)
    current_h = metric_value(current_state, goal, h_metric)
    path = [current_state]
    actions = []
    trace = []
    reached = {current_key}
    nodes_expanded = 0

    for step in range(1, max_steps + 1):
        children_info = []
        if current_key == goal_key:
            trace.append(make_trace_item(step, current_state, current_key, actions[-1] if actions else "START", "Leo núi ngẫu nhiên: đã gặp Goal", [], preview_plain(reached), children_info, node_cost=current_h))
            return {"path": path, "actions": actions, "nodes": nodes_expanded, "depth": len(actions), "cost": current_h, "trace": trace, "solved": True, "message": "Đã tìm thấy Goal"}

        nodes_expanded += 1
        better_neighbors = []
        for child_state, action in get_neighbors(current_state):
            child_key = state_to_string(child_state)
            h_child = metric_value(child_state, goal, h_metric)
            if child_key in reached:
                status = f"SKIP reached, h={h_child}"
            elif h_child < current_h:
                status = f"BETTER h={h_child} < {current_h}"
                better_neighbors.append({"state": child_state, "key": child_key, "action": action, "value": h_child})
            else:
                status = f"KHÔNG TỐT HƠN h={h_child} >= {current_h}"
            children_info.append({"state": child_state, "key": child_key, "action": action, "status": status, "cost": h_child})

        chosen = random.choice(better_neighbors) if better_neighbors else None
        if chosen:
            for child in children_info:
                if child["key"] == chosen["key"]:
                    child["status"] = f"CHỌN NGẪU NHIÊN trong Better_Neighbors, h={chosen['value']}"
                    break

        trace.append(make_trace_item(step, current_state, current_key, actions[-1] if actions else "START", f"Leo núi ngẫu nhiên: lọc neighbor có h nhỏ hơn current, heuristic={metric_display_name(h_metric)}", preview_local_list(better_neighbors), preview_plain(reached), children_info, node_cost=current_h))
        if chosen is None:
            return {"path": path, "actions": actions, "nodes": nodes_expanded, "depth": len(actions), "cost": current_h, "trace": trace, "solved": False, "message": "Dừng tại local optimum"}

        current_state = chosen["state"]
        current_key = chosen["key"]
        current_h = chosen["value"]
        path.append(current_state)
        actions.append(chosen["action"])
        reached.add(current_key)

    return {"path": path, "actions": actions, "nodes": nodes_expanded, "depth": len(actions), "cost": current_h, "trace": trace, "solved": False, "message": "Dừng vì vượt quá số bước giới hạn"}


def random_restart_hill_climbing(start, goal, h_metric="MANHATTAN", max_restart=8, max_steps=80, seed=7):
    random.seed(seed)
    goal_key = state_to_string(goal)
    all_trace = []
    total_nodes = 0
    best_result = None

    for restart in range(1, max_restart + 1):
        current_state = clone_state(start)
        if restart > 1:
            last = None
            opposite = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}
            for _ in range(5 + restart):
                neighbors = get_neighbors(current_state)
                if last:
                    filtered = [(s, a) for s, a in neighbors if a != opposite[last]]
                    if filtered:
                        neighbors = filtered
                current_state, last = random.choice(neighbors)

        current_key = state_to_string(current_state)
        current_h = metric_value(current_state, goal, h_metric)
        path = [current_state]
        actions = []
        reached = {current_key}
        local_nodes = 0

        for step in range(1, max_steps + 1):
            children_info = []
            if current_key == goal_key:
                all_trace.append(make_trace_item(len(all_trace)+1, current_state, current_key, actions[-1] if actions else f"RESTART {restart}", f"Leo núi lặp lại ngẫu nhiên: restart={restart}, đã gặp Goal", [], preview_plain(reached), children_info, node_cost=current_h))
                return {"path": path, "actions": actions, "nodes": total_nodes + local_nodes, "depth": len(actions), "cost": current_h, "trace": all_trace, "solved": True, "message": f"Đã tìm thấy Goal ở restart {restart}"}

            local_nodes += 1
            better_neighbors = []
            for child_state, action in get_neighbors(current_state):
                child_key = state_to_string(child_state)
                h_child = metric_value(child_state, goal, h_metric)
                if child_key in reached:
                    status = f"SKIP reached, h={h_child}"
                elif h_child < current_h:
                    status = f"BETTER h={h_child} < {current_h}"
                    better_neighbors.append({"state": child_state, "key": child_key, "action": action, "value": h_child})
                else:
                    status = f"KHÔNG TỐT HƠN h={h_child} >= {current_h}"
                children_info.append({"state": child_state, "key": child_key, "action": action, "status": status, "cost": h_child})

            chosen = random.choice(better_neighbors) if better_neighbors else None
            if chosen:
                for child in children_info:
                    if child["key"] == chosen["key"]:
                        child["status"] = f"CHỌN NGẪU NHIÊN, h={chosen['value']}"
                        break

            if len(all_trace) < 1000:
                all_trace.append(make_trace_item(len(all_trace)+1, current_state, current_key, actions[-1] if actions else f"RESTART {restart}", f"Leo núi lặp lại ngẫu nhiên: restart={restart}, heuristic={metric_display_name(h_metric)}", preview_local_list(better_neighbors), preview_plain(reached), children_info, node_cost=current_h))

            if chosen is None:
                total_nodes += local_nodes
                candidate = {"path": path, "actions": actions, "nodes": total_nodes, "depth": len(actions), "cost": current_h, "trace": all_trace, "solved": False, "message": f"Restart {restart} bị kẹt"}
                if best_result is None or candidate["cost"] < best_result["cost"]:
                    best_result = candidate
                break

            current_state = chosen["state"]
            current_key = chosen["key"]
            current_h = chosen["value"]
            path.append(current_state)
            actions.append(chosen["action"])
            reached.add(current_key)

    if best_result:
        best_result["trace"] = all_trace
        best_result["message"] = "Hết số lần restart, trả về trạng thái tốt nhất đã gặp"
        return best_result
    return None


def local_beam_search(start, goal, h_metric="MANHATTAN", k=2, max_rounds=60):
    goal_key = state_to_string(goal)
    start_key = state_to_string(start)
    current_set = [{"state": start, "key": start_key, "path": [start], "actions": [], "h": metric_value(start, goal, h_metric)}]
    temp_state = clone_state(start)
    last = None
    opposite = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}

    for i in range(k - 1):
        for _ in range(i + 1):
            neighbors = get_neighbors(temp_state)
            if last:
                filtered = [(s, a) for s, a in neighbors if a != opposite[last]]
                if filtered:
                    neighbors = filtered
            temp_state, last = neighbors[i % len(neighbors)]
        key = state_to_string(temp_state)
        current_set.append({"state": temp_state, "key": key, "path": [start, temp_state] if key != start_key else [start], "actions": ["INIT"] if key != start_key else [], "h": metric_value(temp_state, goal, h_metric)})

    trace = []
    total_nodes = 0
    best_seen = min(current_set, key=lambda item: item["h"])

    for round_index in range(1, max_rounds + 1):
        neighbor_states = []
        children_info = []
        for item in current_set:
            if item["key"] == goal_key:
                return {"path": item["path"], "actions": item["actions"], "nodes": total_nodes, "depth": len(item["actions"]), "cost": item["h"], "trace": trace, "solved": True, "message": "Đã tìm thấy Goal"}
            total_nodes += 1
            for child_state, action in get_neighbors(item["state"]):
                child_key = state_to_string(child_state)
                h_child = metric_value(child_state, goal, h_metric)
                child_item = {"state": child_state, "key": child_key, "path": item["path"] + [child_state], "actions": item["actions"] + [action], "h": h_child}
                neighbor_states.append(child_item)
                status = f"NEIGHBOR h={h_child}"
                if child_key == goal_key:
                    status = f"GOAL h={h_child}"
                children_info.append({"state": child_state, "key": child_key, "action": f"{item['key']} -> {action}", "status": status, "cost": h_child})

        if not neighbor_states:
            return {"path": best_seen["path"], "actions": best_seen["actions"], "nodes": total_nodes, "depth": len(best_seen["actions"]), "cost": best_seen["h"], "trace": trace, "solved": False, "message": "Không còn neighbor, trả về trạng thái tốt nhất"}

        for item in neighbor_states:
            if item["key"] == goal_key:
                trace.append(make_trace_item(len(trace)+1, item["state"], item["key"], item["actions"][-1] if item["actions"] else "START", f"Local Beam Search: k={k}, tìm thấy Goal trong Neighbor_States", [f"{x['key']} h={x['h']}" for x in current_set], [f"{x['key']} h={x['h']}" for x in current_set], children_info, node_cost=item["h"]))
                return {"path": item["path"], "actions": item["actions"], "nodes": total_nodes, "depth": len(item["actions"]), "cost": item["h"], "trace": trace, "solved": True, "message": "Đã tìm thấy Goal"}

        neighbor_states.sort(key=lambda item: item["h"])
        current_set = neighbor_states[:k]
        if current_set[0]["h"] < best_seen["h"]:
            best_seen = current_set[0]

        trace.append(make_trace_item(len(trace)+1, current_set[0]["state"], current_set[0]["key"], f"ROUND {round_index}", f"Local Beam Search: sinh neighbor của tất cả current, sắp xếp h tăng dần, lấy k={k} trạng thái tốt nhất", [f"{x['key']} h={x['h']}" for x in current_set], [f"{x['key']} h={x['h']}" for x in current_set], children_info, node_cost=current_set[0]["h"]))

    return {"path": best_seen["path"], "actions": best_seen["actions"], "nodes": total_nodes, "depth": len(best_seen["actions"]), "cost": best_seen["h"], "trace": trace, "solved": False, "message": "Hết số vòng, trả về trạng thái tốt nhất đã gặp"}



def simulated_annealing_search(start, goal, h_metric="MANHATTAN", t0=10.0, t_min=0.05, alpha=0.80, max_steps=120, seed=7):
    random.seed(seed)
    goal_key = state_to_string(goal)
    current_state = start
    current_key = state_to_string(current_state)
    current_h = metric_value(current_state, goal, h_metric)
    path = [current_state]
    actions = []
    trace = []
    nodes_expanded = 0
    T = float(t0)

    for step in range(1, max_steps + 1):
        children_info = []
        if current_key == goal_key:
            trace.append(make_trace_item(step, current_state, current_key, actions[-1] if actions else "START", "Simulated Annealing: đã gặp Goal", [], [], children_info, node_cost=current_h))
            return {"path": path, "actions": actions, "nodes": nodes_expanded, "depth": len(actions), "cost": current_h, "trace": trace, "solved": True, "message": "Đã tìm thấy Goal"}

        neighbors = get_neighbors(current_state)
        if not neighbors:
            break

        next_state, action = random.choice(neighbors)
        next_key = state_to_string(next_state)
        next_h = metric_value(next_state, goal, h_metric)
        delta = next_h - current_h
        probability = 1.0 if delta <= 0 else math.exp(-delta / T)
        random_value = random.random()

        if delta < 0:
            accept = True
            status = f"ACCEPT chắc chắn vì Δ={delta} < 0"
        elif random_value < probability:
            accept = True
            status = f"ACCEPT xác suất vì r={random_value:.3f} < p={probability:.3f}"
        else:
            accept = False
            status = f"REJECT vì r={random_value:.3f} >= p={probability:.3f}"

        children_info.append({"state": next_state, "key": next_key, "action": action, "status": status, "cost": next_h})
        trace.append(make_trace_item(step, current_state, current_key, actions[-1] if actions else "START", f"Simulated Annealing: T={T:.3f}, h_current={current_h}, h_next={next_h}, Δ={delta}, p={probability:.3f}", [next_key], [], children_info, node_cost=current_h))
        nodes_expanded += 1

        if accept:
            current_state = next_state
            current_key = next_key
            current_h = next_h
            path.append(current_state)
            actions.append(action)

        T = alpha * T
        if T <= t_min:
            break

    return {"path": path, "actions": actions, "nodes": nodes_expanded, "depth": len(actions), "cost": current_h, "trace": trace, "solved": current_key == goal_key, "message": "Dừng vì nhiệt độ T đã nhỏ hoặc hết số bước"}


def belief_greedy_search(start, goal, h_metric="MANHATTAN", aggregate="MAX", belief_size=2, goal_set_mode=False, max_steps=80, seed=7):
    random.seed(seed)
    start_states = make_possible_states(start, belief_size)
    goal_states = make_possible_states(goal, belief_size) if goal_set_mode else [goal]
    goal_keys = {state_to_string(state) for state in goal_states}

    def is_goal_belief(states):
        # Chỉ dừng khi TẤT CẢ state/board trong belief state đều thuộc Goal Set.
        return all(state_to_string(state) in goal_keys for state in states)

    current_states = unique_states(start_states)
    current_key = belief_key(current_states)
    current_h = belief_h_value(current_states, goal_states, h_metric, aggregate)
    path = [current_states[0]]
    belief_path = [current_states]
    actions = []
    trace = []
    reached = {current_key}
    nodes_expanded = 0

    for step in range(1, max_steps + 1):
        candidates = []
        if is_goal_belief(current_states):
            trace.append(make_belief_trace_item(step, current_states, current_key, actions[-1] if actions else "START", f"Belief Search: đã đạt Goal Belief: tất cả board đều là Goal, h={current_h}", [], candidates, list(reached), node_cost=current_h))
            return {"path": path, "actions": actions, "nodes": nodes_expanded, "depth": len(actions), "cost": current_h, "trace": trace, "solved": True, "message": "Tất cả trạng thái trong belief state đã đạt Goal"}

        nodes_expanded += 1
        for action in ["UP", "DOWN", "LEFT", "RIGHT"]:
            next_states = unique_states([apply_action_to_state(state, action, absorbing_goal_keys=goal_keys) for state in current_states])
            next_key = belief_key(next_states)
            next_h = belief_h_value(next_states, goal_states, h_metric, aggregate)
            status = f"CANDIDATE h={next_h:.2f}"
            if next_key in reached:
                status = f"SKIP reached, h={next_h:.2f}"
            if is_goal_belief(next_states):
                status = f"GOAL BELIEF h={next_h:.2f}"
            candidates.append({"states": next_states, "key": next_key, "action": action, "status": status, "cost": next_h})

        valid_candidates = [c for c in candidates if "SKIP" not in c["status"]]
        if not valid_candidates:
            return {"path": path, "actions": actions, "nodes": nodes_expanded, "depth": len(actions), "cost": current_h, "trace": trace, "solved": False, "message": "Không còn belief state mới để mở rộng"}

        best_h = min(c["cost"] for c in valid_candidates)
        best_candidates = [c for c in valid_candidates if c["cost"] == best_h]
        chosen = random.choice(best_candidates)
        for c in candidates:
            if c["key"] == chosen["key"]:
                c["status"] = f"CHỌN belief tốt nhất cost={chosen['cost']:.2f}"
                break

        trace.append(make_belief_trace_item(step, current_states, current_key, actions[-1] if actions else "START", f"Belief Greedy: node là tập trạng thái, h_belief={aggregate}, heuristic={metric_display_name(h_metric)}", [chosen["key"]], candidates, list(reached), node_cost=current_h))
        current_states = chosen["states"]
        current_key = chosen["key"]
        current_h = chosen["cost"]
        reached.add(current_key)
        actions.append(chosen["action"])
        path.append(current_states[0])
        belief_path.append(current_states)

    return {"path": path, "actions": actions, "nodes": nodes_expanded, "depth": len(actions), "cost": current_h, "trace": trace, "solved": False, "message": "Hết số bước, trả về belief state tốt nhất đã gặp"}




def belief_state_search_general(initial_states, goal_states, algorithm_name,
                                h_metric="MANHATTAN", g_metric="MISPLACED", aggregate="MAX", k=2,
                                max_steps=120, seed=7):
    random.seed(seed)

    goal_keys = {state_to_string(state) for state in goal_states}
    current_states = [clone_state(state) for state in initial_states]
    current_key = belief_key(current_states)
    current_h = belief_h_value(current_states, goal_states, h_metric, aggregate)

    trace = []
    reached = {current_key}
    path = [current_states[0]]
    belief_path = [current_states]
    actions = []
    nodes_expanded = 0

    def is_goal_belief(states):
        # Chỉ dừng khi TẤT CẢ state/board trong belief state đều thuộc Goal Set.
        return all(state_to_string(state) in goal_keys for state in states)

    def expand_belief(states):
        candidates = []
        for action in ["UP", "DOWN", "LEFT", "RIGHT"]:
            next_states = [
                apply_action_to_state(state, action, absorbing_goal_keys=goal_keys)
                for state in states
            ]
            key = belief_key(next_states)
            h_value = belief_h_value(next_states, goal_states, h_metric, aggregate)
            g_value = belief_h_value(next_states, goal_states, g_metric, aggregate)

            if algorithm_name == "UCS":
                score_value = g_value
            elif algorithm_name in {"A*", "IDA*"}:
                score_value = g_value + h_value
            else:
                score_value = h_value

            candidates.append({
                "states": next_states,
                "key": key,
                "action": action,
                "cost": score_value,
                "g": g_value,
                "h": h_value,
                "status": f"CANDIDATE cost={score_value:.2f} g(B)={g_value:.2f} h(B)={h_value:.2f}"
            })
        return candidates

    # BFS / DFS / IDS-like global search over belief states
    if algorithm_name in {"BFS Cách 1", "BFS Cách 2", "DFS", "IDS"}:
        if algorithm_name in {"DFS", "IDS"}:
            frontier = [{"states": current_states, "key": current_key, "path": [current_states], "actions": []}]
            pop_index = -1
        else:
            frontier = deque([{"states": current_states, "key": current_key, "path": [current_states], "actions": []}])
            pop_index = None

        while frontier and nodes_expanded < max_steps:
            node = frontier.pop() if pop_index == -1 else frontier.popleft()
            nodes_expanded += 1
            candidates = expand_belief(node["states"])

            if is_goal_belief(node["states"]):
                trace.append(make_belief_trace_item(nodes_expanded, node["states"], node["key"], node["actions"][-1] if node["actions"] else "START", f"Belief {algorithm_name}: đã đạt Goal Belief: tất cả board đều là Goal", [], candidates, list(reached), node_cost=belief_h_value(node["states"], goal_states, h_metric, aggregate)))
                return {"path": [states[0] for states in node["path"]], "belief_path": node["path"], "actions": node["actions"], "nodes": nodes_expanded, "depth": len(node["actions"]), "cost": 0, "trace": trace, "solved": True, "message": f"Môi trường không chắc chắn: {algorithm_name} tìm thấy Goal Set cho tất cả board"}

            for c in candidates:
                if c["key"] in reached:
                    c["status"] = "SKIP reached"
                    continue
                if all(state_to_string(s) in goal_keys for s in c["states"]):
                    c["status"] = "GOAL BELIEF"
                else:
                    c["status"] = "ADD"
                reached.add(c["key"])
                item = {"states": c["states"], "key": c["key"], "path": node["path"] + [c["states"]], "actions": node["actions"] + [c["action"]]}
                frontier.append(item)

            trace.append(make_belief_trace_item(nodes_expanded, node["states"], node["key"], node["actions"][-1] if node["actions"] else "START", f"Belief {algorithm_name}: node là tập trạng thái", [x["key"] for x in list(frontier)[:4]], candidates, list(reached), node_cost=belief_h_value(node["states"], goal_states, h_metric, aggregate)))

        return {"path": path, "belief_path": belief_path, "actions": actions, "nodes": nodes_expanded, "depth": 0, "cost": current_h, "trace": trace, "solved": False, "message": f"Môi trường không chắc chắn: {algorithm_name} dừng"}

    # Local Beam over belief states
    if algorithm_name == "Local Beam Search":
        current_set = [{"states": current_states, "key": current_key, "path": [current_states], "actions": [], "h": current_h}]
        best = current_set[0]

        for step in range(1, max_steps + 1):
            all_candidates = []
            children = []

            for item in current_set:
                if is_goal_belief(item["states"]):
                    item_cost = item.get("h", item.get("cost", 0))
                    return {"path": [states[0] for states in item["path"]], "belief_path": item["path"], "actions": item["actions"], "nodes": nodes_expanded, "depth": len(item["actions"]), "cost": item_cost, "trace": trace, "solved": True, "message": f"Môi trường không chắc chắn: {algorithm_name} tìm thấy Goal Set cho tất cả board"}

                nodes_expanded += 1
                for c in expand_belief(item["states"]):
                    c["path"] = item["path"] + [c["states"]]
                    c["actions"] = item["actions"] + [c["action"]]
                    c["status"] = f"NEIGHBOR score={c['cost']:.2f} h(B)={c.get('h', c['cost']):.2f}"
                    all_candidates.append(c)
                    children.append(c)

            if not all_candidates:
                break

            min_h = min(c["cost"] for c in all_candidates)
            best_group = [c for c in all_candidates if c["cost"] == min_h]
            random.shuffle(best_group)
            all_candidates.sort(key=lambda c: c["cost"])
            current_set = (best_group + [c for c in all_candidates if c not in best_group])[:k]

            for c in children:
                if c in current_set:
                    c["status"] = f"CHỌN trong beam k={k}, score={c['cost']:.2f} h(B)={c.get('h', c['cost']):.2f}"

            current_best_cost = current_set[0].get("cost", current_set[0].get("h", 0))
            if current_best_cost < best["h"]:
                best = {"states": current_set[0]["states"], "key": current_set[0]["key"], "path": current_set[0]["path"], "actions": current_set[0]["actions"], "h": current_best_cost}

            trace.append(make_belief_trace_item(step, current_set[0]["states"], current_set[0]["key"], f"ROUND {step}", f"Belief Local Beam Search: lấy k={k} belief tốt nhất", [x["key"] for x in current_set], children, [x["key"] for x in current_set], node_cost=current_set[0]["cost"]))

        return {"path": [states[0] for states in best["path"]], "belief_path": best["path"], "actions": best["actions"], "nodes": nodes_expanded, "depth": len(best["actions"]), "cost": best["h"], "trace": trace, "solved": False, "message": f"Môi trường không chắc chắn: {algorithm_name} dừng"}

    # Greedy / A* / UCS / IDA* / hill-climbing-ish: choose best next belief by h(B)
    for step in range(1, max_steps + 1):
        if is_goal_belief(current_states):
            trace.append(make_belief_trace_item(step, current_states, current_key, actions[-1] if actions else "START", f"Belief {algorithm_name}: đã đạt Goal Belief: tất cả board đều là Goal", [], [], list(reached), node_cost=current_h))
            return {"path": path, "belief_path": belief_path, "actions": actions, "nodes": nodes_expanded, "depth": len(actions), "cost": current_h, "trace": trace, "solved": True, "message": f"Môi trường không chắc chắn: {algorithm_name} tìm thấy Goal Set cho tất cả board"}

        nodes_expanded += 1
        candidates = expand_belief(current_states)
        valid = [c for c in candidates if c["key"] not in reached]

        if not valid:
            break

        best_h = min(c["cost"] for c in valid)
        best_candidates = [c for c in valid if c["cost"] == best_h]
        chosen = random.choice(best_candidates)

        for c in candidates:
            if c["key"] == chosen["key"]:
                c["status"] = f"CHỌN cost={c['cost']:.2f}"
            elif c["key"] in reached:
                c["status"] = "SKIP reached"

        trace.append(make_belief_trace_item(step, current_states, current_key, actions[-1] if actions else "START", f"Belief {algorithm_name}: h(B)={aggregate}, heuristic={metric_display_name(h_metric)}", [chosen["key"]], candidates, list(reached), node_cost=current_h))

        current_states = chosen["states"]
        current_key = chosen["key"]
        current_h = chosen["cost"]
        reached.add(current_key)
        actions.append(chosen["action"])
        path.append(current_states[0])
        belief_path.append(current_states)

    return {"path": path, "belief_path": belief_path, "actions": actions, "nodes": nodes_expanded, "depth": len(actions), "cost": current_h, "trace": trace, "solved": False, "message": f"Môi trường không chắc chắn: {algorithm_name} dừng"}


def astar_search(start, goal, g_metric="MANHATTAN", h_metric="MANHATTAN"):
    start_key = state_to_string(start)
    goal_key = state_to_string(goal)

    order = 0
    g_start = metric_value(start, goal, g_metric)
    h_start = metric_value(start, goal, h_metric)
    f_start = g_start + h_start

    start_node = {
        "key": start_key,
        "state": start,
        "path": [start],
        "actions": [],
        "action": "START",
        "g": g_start,
        "h": h_start,
        "f": f_start
    }

    frontier = [(f_start, order, start_node)]
    order += 1

    frontier_best_f = {start_key: f_start}
    reached = set()
    trace = []
    nodes_expanded = 0

    while frontier:
        f_value, _, node = heapq.heappop(frontier)

        if frontier_best_f.get(node["key"]) != f_value:
            continue

        frontier_best_f.pop(node["key"], None)

        if node["key"] in reached:
            continue

        nodes_expanded += 1
        children_info = []

        if node["key"] == goal_key:
            trace.append(make_trace_item(
                nodes_expanded,
                node["state"],
                node["key"],
                node["action"],
                f"A*: lấy node có f(n)=g(n)+h(n) nhỏ nhất. g={node['g']}, h={node['h']}, f={node['f']}",
                preview_astar_queue(frontier),
                preview_plain(reached),
                children_info,
                node_cost=node["f"]
            ))

            return {
                "path": node["path"],
                "actions": node["actions"],
                "nodes": nodes_expanded,
                "depth": len(node["actions"]),
                "cost": node["f"],
                "trace": trace
            }

        reached.add(node["key"])

        for child_state, action in get_neighbors(node["state"]):
            child_key = state_to_string(child_state)

            g_child = metric_value(child_state, goal, g_metric)
            h_child = metric_value(child_state, goal, h_metric)
            f_child = g_child + h_child

            child_info = {
                "state": child_state,
                "key": child_key,
                "action": action,
                "status": "",
                "cost": f_child
            }

            if child_key in reached:
                child_info["status"] = "SKIP reached"
                children_info.append(child_info)
                continue

            if child_key not in frontier_best_f:
                child_node = {
                    "key": child_key,
                    "state": child_state,
                    "path": node["path"] + [child_state],
                    "actions": node["actions"] + [action],
                    "action": action,
                    "g": g_child,
                    "h": h_child,
                    "f": f_child
                }

                heapq.heappush(frontier, (f_child, order, child_node))
                order += 1

                frontier_best_f[child_key] = f_child
                child_info["status"] = f"ADD f={f_child} g={g_child} h={h_child}"

            elif f_child < frontier_best_f[child_key]:
                old_f = frontier_best_f[child_key]

                child_node = {
                    "key": child_key,
                    "state": child_state,
                    "path": node["path"] + [child_state],
                    "actions": node["actions"] + [action],
                    "action": action,
                    "g": g_child,
                    "h": h_child,
                    "f": f_child
                }

                heapq.heappush(frontier, (f_child, order, child_node))
                order += 1

                frontier_best_f[child_key] = f_child
                child_info["status"] = f"UPDATE f={old_f}->{f_child} g={g_child} h={h_child}"

            else:
                child_info["status"] = f"SKIP frontier tốt hơn f={frontier_best_f[child_key]}"

            children_info.append(child_info)

        if len(trace) < 1000:
            trace.append(make_trace_item(
                nodes_expanded,
                node["state"],
                node["key"],
                node["action"],
                (
                    f"A*: f(n)=g(n)+h(n), "
                    f"g={metric_display_name(g_metric)}, h={metric_display_name(h_metric)}"
                ),
                preview_astar_queue(frontier),
                preview_plain(reached),
                children_info,
                node_cost=node["f"]
            ))

    return None


def ida_star_search(start, goal, g_metric="MANHATTAN", h_metric="MANHATTAN", max_rounds=80):
    start_key = state_to_string(start)
    goal_key = state_to_string(goal)

    g_start = metric_value(start, goal, g_metric)
    h_start = metric_value(start, goal, h_metric)
    threshold = g_start + h_start

    total_nodes = 0
    all_trace = []
    found_result = None

    def dfs_limited(path, actions, threshold_value, round_index):
        nonlocal total_nodes, all_trace, found_result

        current_state = path[-1]
        current_key = state_to_string(current_state)

        g_value = metric_value(current_state, goal, g_metric)
        h_value = metric_value(current_state, goal, h_metric)
        f_value = g_value + h_value

        total_nodes += 1
        children_info = []

        if f_value > threshold_value:
            return f_value

        if current_key == goal_key:
            found_result = {
                "path": path[:],
                "actions": actions[:],
                "nodes": total_nodes,
                "depth": len(actions),
                "cost": f_value,
                "trace": all_trace
            }

            all_trace.append(make_trace_item(
                total_nodes,
                current_state,
                current_key,
                actions[-1] if actions else "START",
                f"IDA*: tìm thấy Goal với threshold={threshold_value}, f={f_value}",
                [],
                preview_plain([state_to_string(s) for s in path]),
                children_info,
                node_cost=f_value
            ))

            return "FOUND"

        min_over_threshold = float("inf")
        path_keys = {state_to_string(state) for state in path}
        allowed_children = []

        for child_state, action in get_neighbors(current_state):
            child_key = state_to_string(child_state)

            g_child = metric_value(child_state, goal, g_metric)
            h_child = metric_value(child_state, goal, h_metric)
            f_child = g_child + h_child

            if child_key in path_keys:
                status = "SKIP cycle"
            elif f_child > threshold_value:
                status = f"CUT f={f_child} > threshold={threshold_value}"
                min_over_threshold = min(min_over_threshold, f_child)
            else:
                status = f"ADD f={f_child} g={g_child} h={h_child}"
                allowed_children.append((child_state, action))

            children_info.append({
                "state": child_state,
                "key": child_key,
                "action": action,
                "status": status,
                "cost": f_child
            })

        if len(all_trace) < 1000:
            all_trace.append(make_trace_item(
                total_nodes,
                current_state,
                current_key,
                actions[-1] if actions else "START",
                (
                    f"IDA*: round={round_index}, threshold={threshold_value}, "
                    f"f={f_value}, g={g_value}, h={h_value}"
                ),
                [state_to_string(child_state) for child_state, _ in allowed_children],
                preview_plain([state_to_string(s) for s in path]),
                children_info,
                node_cost=f_value
            ))

        for child_state, action in allowed_children:
            result = dfs_limited(path + [child_state], actions + [action], threshold_value, round_index)

            if result == "FOUND":
                return "FOUND"

            if isinstance(result, (int, float)):
                min_over_threshold = min(min_over_threshold, result)

        return min_over_threshold

    for round_index in range(1, max_rounds + 1):
        result = dfs_limited([start], [], threshold, round_index)

        if result == "FOUND":
            found_result["trace"] = all_trace
            return found_result

        if result == float("inf"):
            return None

        threshold = result

    return None



def dfs_search(start, goal):
    start_key = state_to_string(start)
    goal_key = state_to_string(goal)

    state_map = {start_key: start}
    parent = {start_key: None}

    frontier = [start_key]
    frontier_set = {start_key}
    reached = {start_key}
    trace = []
    nodes_expanded = 0

    while frontier:
        current_key = frontier.pop()
        frontier_set.remove(current_key)
        current_state = state_map[current_key]
        nodes_expanded += 1

        parent_info = parent[current_key]
        action_from_parent = parent_info[1] if parent_info else "START"

        children_info = []

        if current_key == goal_key:
            path, actions = reconstruct_path(current_key, parent, state_map)

            trace.append(make_trace_item(
                nodes_expanded,
                current_state,
                current_key,
                action_from_parent,
                "DFS: Stack LIFO",
                preview_plain(reversed(frontier)),
                preview_plain(reached),
                children_info
            ))

            return {
                "path": path,
                "actions": actions,
                "nodes": nodes_expanded,
                "depth": len(actions),
                "cost": len(actions),
                "trace": trace
            }

        for child_state, action in reversed(get_neighbors(current_state)):
            child_key = state_to_string(child_state)

            if child_key not in reached and child_key not in frontier_set:
                reached.add(child_key)
                frontier.append(child_key)
                frontier_set.add(child_key)
                state_map[child_key] = child_state
                parent[child_key] = (current_key, action)
                status = "PUSH"
            else:
                status = "SKIP"

            children_info.append({
                "state": child_state,
                "key": child_key,
                "action": action,
                "status": status
            })

        if len(trace) < 1000:
            trace.append(make_trace_item(
                nodes_expanded,
                current_state,
                current_key,
                action_from_parent,
                "DFS: Stack LIFO",
                preview_plain(list(reversed(frontier))),
                preview_plain(reached),
                children_info
            ))

    return None


def depth_limited_search(start, goal, limit, base_iteration=0):
    start_key = state_to_string(start)
    goal_key = state_to_string(goal)

    frontier = [{
        "key": start_key,
        "state": start,
        "path": [start],
        "actions": [],
        "action": "START",
        "depth": 0,
        "path_keys": [start_key]
    }]

    trace = []
    nodes_expanded = 0
    result = "failure"

    while frontier:
        node = frontier.pop()
        nodes_expanded += 1

        children_info = []

        if node["key"] == goal_key:
            trace.append(make_trace_item(
                base_iteration + nodes_expanded,
                node["state"],
                node["key"],
                node["action"],
                f"IDS / DLS: limit={limit}",
                preview_plain([n["key"] for n in reversed(frontier)]),
                preview_plain(node["path_keys"]),
                children_info
            ))

            return {
                "status": "found",
                "path": node["path"],
                "actions": node["actions"],
                "nodes": nodes_expanded,
                "trace": trace
            }

        if node["depth"] >= limit:
            result = "cutoff"
            children_info.append({
                "state": node["state"],
                "key": node["key"],
                "action": "CUT",
                "status": f"CUTOFF depth={node['depth']}"
            })

            if len(trace) < 1000:
                trace.append(make_trace_item(
                    base_iteration + nodes_expanded,
                    node["state"],
                    node["key"],
                    node["action"],
                    f"IDS / DLS: limit={limit}",
                    preview_plain([n["key"] for n in reversed(frontier)]),
                    preview_plain(node["path_keys"]),
                    children_info
                ))

            continue

        for child_state, action in reversed(get_neighbors(node["state"])):
            child_key = state_to_string(child_state)

            if child_key in node["path_keys"]:
                status = "SKIP cycle"
            else:
                frontier.append({
                    "key": child_key,
                    "state": child_state,
                    "path": node["path"] + [child_state],
                    "actions": node["actions"] + [action],
                    "action": action,
                    "depth": node["depth"] + 1,
                    "path_keys": node["path_keys"] + [child_key]
                })
                status = "PUSH"

            children_info.append({
                "state": child_state,
                "key": child_key,
                "action": action,
                "status": status
            })

        if len(trace) < 1000:
            trace.append(make_trace_item(
                base_iteration + nodes_expanded,
                node["state"],
                node["key"],
                node["action"],
                f"IDS / DLS: limit={limit}",
                preview_plain([n["key"] for n in reversed(frontier)]),
                preview_plain(node["path_keys"]),
                children_info
            ))

    return {
        "status": result,
        "nodes": nodes_expanded,
        "trace": trace
    }


def ids_search(start, goal, max_depth=40):
    total_nodes = 0
    all_trace = []

    for limit in range(max_depth + 1):
        result = depth_limited_search(start, goal, limit, len(all_trace))
        total_nodes += result.get("nodes", 0)
        all_trace.extend(result.get("trace", []))

        if len(all_trace) > 1000:
            all_trace = all_trace[:1000]

        if result["status"] == "found":
            return {
                "path": result["path"],
                "actions": result["actions"],
                "nodes": total_nodes,
                "depth": len(result["actions"]),
                "cost": len(result["actions"]),
                "trace": all_trace
            }

    return None




def parse_state_list_text(text):
    raw = text.replace(',', ' ').replace(';', ' ').replace('|', ' ')
    tokens = [token.strip() for token in raw.split() if token.strip()]
    states = []
    for token in tokens:
        if is_valid_input(token):
            states.append(string_to_state(token))
    return states

def belief_search_custom(start_states, goal_states, h_metric='MANHATTAN', aggregate='MAX', group='BLIND_BFS', k=2, max_steps=250, seed=7):
    random.seed(seed)
    start_states = unique_states(start_states)
    goal_states = unique_states(goal_states)
    goal_keys = {state_to_string(state) for state in goal_states}

    def is_goal_belief(states):
        # Chỉ dừng khi TẤT CẢ state/board trong belief state đều thuộc Goal Set.
        return all(state_to_string(state) in goal_keys for state in states)

    def make_node(states, path=None, actions=None):
        states = unique_states(states)
        return {
            'states': states,
            'key': belief_key(states),
            'path': path if path is not None else [states[0]],
            'actions': actions if actions is not None else [],
            'h': belief_h_value(states, goal_states, h_metric, aggregate)
        }

    def expand_belief(node):
        candidates = []
        for action in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
            next_states = unique_states([
                apply_action_to_state(state, action, absorbing_goal_keys=goal_keys)
                for state in node['states']
            ])
            h_val = belief_h_value(next_states, goal_states, h_metric, aggregate)
            key = belief_key(next_states)
            status = f'CANDIDATE h(B)={h_val:.2f}'
            if is_goal_belief(next_states):
                status = f'GOAL BELIEF h(B)={h_val:.2f}'
            candidates.append({
                'states': next_states,
                'key': key,
                'action': action,
                'status': status,
                'cost': h_val,
                'node': make_node(next_states, node['path'] + [next_states[0]], node['actions'] + [action])
            })
        return candidates

    start_node = make_node(start_states)
    trace = []
    nodes_expanded = 0

    if group == 'BLIND_BFS':
        frontier = deque([start_node])
        reached = {start_node['key']}
        iteration = 0
        while frontier and iteration < max_steps:
            node = frontier.popleft()
            iteration += 1
            nodes_expanded += 1
            candidates = []
            if is_goal_belief(node['states']):
                trace.append(make_belief_trace_item(iteration, node['states'], node['key'], node['actions'][-1] if node['actions'] else 'START', 'Belief BFS: tất cả trạng thái đã nằm trong Goal Set', [], candidates, list(reached), node_cost=node['h']))
                return {'path': node['path'], 'actions': node['actions'], 'nodes': nodes_expanded, 'depth': len(node['actions']), 'cost': node['h'], 'trace': trace, 'solved': True, 'message': 'Belief BFS tìm thấy Goal Set cho tất cả board'}
            for cand in expand_belief(node):
                if cand['key'] in reached:
                    cand['status'] = f"SKIP reached, h(B)={cand['cost']:.2f}"
                else:
                    reached.add(cand['key'])
                    frontier.append(cand['node'])
                    cand['status'] = f"ADD vào Frontier, h(B)={cand['cost']:.2f}"
                candidates.append(cand)
            trace.append(make_belief_trace_item(iteration, node['states'], node['key'], node['actions'][-1] if node['actions'] else 'START', f'Belief BFS: tìm kiếm mù trên belief state, aggregate={aggregate}', [n['key'] for n in list(frontier)[:8]], candidates, list(reached), node_cost=node['h']))
        return {'path': start_node['path'], 'actions': [], 'nodes': nodes_expanded, 'depth': 0, 'cost': start_node['h'], 'trace': trace, 'solved': False, 'message': 'Belief BFS chưa tìm thấy Goal Set cho tất cả board'}

    if group == 'HEURISTIC_GREEDY':
        order = 0
        frontier = [(start_node['h'], random.random(), order, start_node)]
        order += 1
        reached = set()
        iteration = 0
        while frontier and iteration < max_steps:
            _, _, _, node = heapq.heappop(frontier)
            if node['key'] in reached:
                continue
            reached.add(node['key'])
            iteration += 1
            nodes_expanded += 1
            candidates = []
            if is_goal_belief(node['states']):
                trace.append(make_belief_trace_item(iteration, node['states'], node['key'], node['actions'][-1] if node['actions'] else 'START', 'Belief Greedy: đã đạt Goal Set', [], candidates, list(reached), node_cost=node['h']))
                return {'path': node['path'], 'actions': node['actions'], 'nodes': nodes_expanded, 'depth': len(node['actions']), 'cost': node['h'], 'trace': trace, 'solved': True, 'message': 'Belief Greedy tìm thấy Goal Set cho tất cả board'}
            for cand in expand_belief(node):
                if cand['key'] in reached:
                    cand['status'] = f"SKIP reached, h(B)={cand['cost']:.2f}"
                else:
                    heapq.heappush(frontier, (cand['cost'], random.random(), order, cand['node']))
                    order += 1
                    cand['status'] = f"ADD Priority Queue, h(B)={cand['cost']:.2f}"
                candidates.append(cand)
            trace.append(make_belief_trace_item(iteration, node['states'], node['key'], node['actions'][-1] if node['actions'] else 'START', f'Belief Greedy: chọn h(B) nhỏ nhất; h(B)={aggregate}; nếu bằng nhau chọn ngẫu nhiên', [n[3]['key'] for n in sorted(frontier)[:8]], candidates, list(reached), node_cost=node['h']))
        return {'path': start_node['path'], 'actions': [], 'nodes': nodes_expanded, 'depth': 0, 'cost': start_node['h'], 'trace': trace, 'solved': False, 'message': 'Belief Greedy chưa tìm thấy Goal Set cho tất cả board'}

    current_set = [start_node]
    trace_reached = {start_node['key']}
    best_seen = start_node
    for round_index in range(1, max_steps + 1):
        all_candidates = []
        children_info = []
        for node in current_set:
            nodes_expanded += 1
            if is_goal_belief(node['states']):
                return {'path': node['path'], 'actions': node['actions'], 'nodes': nodes_expanded, 'depth': len(node['actions']), 'cost': node['h'], 'trace': trace, 'solved': True, 'message': 'Môi trường không chắc chắn: Local Beam Search tìm thấy Goal Set cho tất cả board'}
            for cand in expand_belief(node):
                cand['action'] = f"{node['key']} -> {cand['action']}"
                if cand['key'] in trace_reached:
                    cand['status'] = f"SKIP reached, h(B)={cand['cost']:.2f}"
                else:
                    cand['status'] = f"BEAM CANDIDATE h(B)={cand['cost']:.2f}"
                    all_candidates.append(cand)
                children_info.append(cand)
        if not all_candidates:
            return {'path': best_seen['path'], 'actions': best_seen['actions'], 'nodes': nodes_expanded, 'depth': len(best_seen['actions']), 'cost': best_seen['h'], 'trace': trace, 'solved': False, 'message': 'Môi trường không chắc chắn: Local Beam Search bị kẹt'}
        random.shuffle(all_candidates)
        all_candidates.sort(key=lambda c: c['cost'])
        chosen_candidates = all_candidates[:k]
        current_set = [cand['node'] for cand in chosen_candidates]
        for cand in chosen_candidates:
            cand['status'] = f"CHỌN vào chùm k={k}, h(B)={cand['cost']:.2f}"
            trace_reached.add(cand['key'])
        best_seen = min(current_set + [best_seen], key=lambda n: n['h'])
        trace.append(make_belief_trace_item(round_index, current_set[0]['states'], current_set[0]['key'], f'ROUND {round_index}', f'Belief Local Beam: sinh candidate của nhiều belief, sắp xếp h(B), lấy k={k}', [node['key'] for node in current_set], children_info, list(trace_reached), node_cost=current_set[0]['h']))
        for node in current_set:
            if is_goal_belief(node['states']):
                return {'path': node['path'], 'actions': node['actions'], 'nodes': nodes_expanded, 'depth': len(node['actions']), 'cost': node['h'], 'trace': trace, 'solved': True, 'message': 'Môi trường không chắc chắn: Local Beam Search tìm thấy Goal Set cho tất cả board'}
    return {'path': best_seen['path'], 'actions': best_seen['actions'], 'nodes': nodes_expanded, 'depth': len(best_seen['actions']), 'cost': best_seen['h'], 'trace': trace, 'solved': False, 'message': 'Môi trường không chắc chắn: Local Beam Search hết số vòng'}


class EightPuzzleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("8-Puzzle Solver")
        self.root.geometry("1120x720")
        self.root.configure(bg="#f7f7f7")

        self.solution_path = []
        self.solution_belief_path = []
        self.solution_actions = []
        self.search_trace = []
        self.belief_solution_path = []
        self.current_index = 0
        self.trace_index = 0
        self.final_status_text = "Solved successfully!"
        self.final_status_color = "#188038"

        self.manual_mode = False
        self.manual_state = None
        self.manual_start_state = None
        self.manual_moves = 0
        self.manual_seconds = 0
        self.manual_timer_id = None
        self.animation_id = None

        self.build_ui()
        self.draw_board(string_to_state(START_DEFAULT))
        self.render_empty_trace()

    def build_ui(self):
        self.create_header()

        self.scroll_canvas = tk.Canvas(
            self.root,
            bg="#f7f7f7",
            highlightthickness=0
        )
        self.scroll_canvas.pack(side="left", fill="both", expand=True)

        self.scrollbar = ttk.Scrollbar(
            self.root,
            orient="vertical",
            command=self.scroll_canvas.yview
        )
        self.scrollbar.pack(side="right", fill="y")

        self.scroll_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.container = tk.Frame(self.scroll_canvas, bg="#f7f7f7")
        self.canvas_window = self.scroll_canvas.create_window(
            (0, 0),
            window=self.container,
            anchor="nw"
        )

        self.container.bind("<Configure>", self.update_scroll_region)
        self.scroll_canvas.bind("<Configure>", self.resize_canvas_window)

        self.root.bind_all("<MouseWheel>", self.on_mousewheel)
        self.root.bind_all("<Button-4>", self.on_mousewheel_linux)
        self.root.bind_all("<Button-5>", self.on_mousewheel_linux)

        self.container.grid_columnconfigure(0, weight=1)

        self.title_frame = tk.Frame(self.container, bg="#f7f7f7")
        self.title_frame.pack(fill="x", padx=70, pady=(28, 18))

        tk.Label(
            self.title_frame,
            text="Home » Projects",
            bg="#f7f7f7",
            fg="#555555",
            font=("Arial", 10)
        ).pack(anchor="w")

        tk.Label(
            self.title_frame,
            text="8 Puzzle Solver",
            bg="#f7f7f7",
            fg="#222222",
            font=("Arial", 30, "bold")
        ).pack(anchor="w", pady=(16, 8))

        tk.Label(
            self.title_frame,
            text="A simple 8-puzzle solver with BFS, UCS, Greedy, Hill Climbing, Local Beam, Simulated Annealing, Belief Search, A*, IDA*, DFS and IDS. Inspect statistics and follow the search trace.",
            bg="#f7f7f7",
            fg="#555555",
            font=("Arial", 12),
            wraplength=760,
            justify="left"
        ).pack(anchor="w")

        tk.Frame(self.title_frame, height=1, bg="#dddddd").pack(fill="x", pady=(20, 0))

        self.main = tk.Frame(self.container, bg="#f7f7f7")
        self.main.pack(fill="x", padx=70)

        self.controls_panel = self.card(self.main, width=270, height=980)
        self.controls_panel.grid(row=0, column=0, padx=(0, 28), sticky="n")

        self.board_panel = tk.Frame(self.main, bg="#f7f7f7")
        self.board_panel.grid(row=0, column=1, padx=(0, 28), sticky="n")

        self.stats_panel = self.card(self.main, width=360, height=430)
        self.stats_panel.grid(row=0, column=2, sticky="n")

        self.build_controls()
        self.build_board()
        self.build_stats()
        self.build_trace()
        self.update_trace_ui_by_algorithm()
        self.update_board_mode_visibility()
        if self.is_belief_mode_active() and hasattr(self, 'belief_start_text'):
            try:
                self.draw_belief_boards(parse_state_list_text(self.belief_start_text.get('1.0', 'end')))
            except Exception:
                pass
        self.refresh_control_visibility()

    def create_header(self):
        tk.Frame(self.root, bg="#1f4542", height=7).pack(fill="x")

        header = tk.Frame(self.root, bg="#ffffff", height=58, highlightbackground="#dddddd", highlightthickness=1)
        header.pack(fill="x")
        header.pack_propagate(False)

        inner = tk.Frame(header, bg="#ffffff")
        inner.pack(fill="both", expand=True, padx=70)

        tk.Label(
            inner,
            text="8-Puzzle Solver",
            bg="#ffffff",
            fg="#222222",
            font=("Arial", 10, "bold")
        ).pack(side="left")

        nav = tk.Frame(inner, bg="#ffffff")
        nav.pack(side="right")

        for text in ["Solver", "Trace", "About"]:
            tk.Label(
                nav,
                text=text,
                bg="#ffffff",
                fg="#444444",
                font=("Arial", 10)
            ).pack(side="left", padx=14)

    def update_scroll_region(self, event=None):
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def resize_canvas_window(self, event):
        self.scroll_canvas.itemconfigure(self.canvas_window, width=event.width)

    def on_mousewheel(self, event):
        self.scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_mousewheel_linux(self, event):
        if event.num == 4:
            self.scroll_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.scroll_canvas.yview_scroll(1, "units")

    def card(self, parent, width, height):
        frame = tk.Frame(
            parent,
            bg="#ffffff",
            width=width,
            height=height,
            highlightbackground="#d6d6d6",
            highlightthickness=1
        )
        frame.pack_propagate(False)
        return frame

    def build_controls(self):
        tk.Button(
            self.controls_panel,
            text="Shuffle Puzzle",
            command=self.shuffle_puzzle,
            bg="#ffffff",
            fg="#222222",
            relief="solid",
            bd=1,
            font=("Arial", 10, "bold")
        ).pack(fill="x", padx=18, pady=(18, 18), ipady=7)

        self.start_entry = self.labeled_entry(
            self.controls_panel,
            "Initial state",
            START_DEFAULT,
            "Enter 9 characters, e.g. 012345678"
        )

        self.goal_entry = self.labeled_entry(
            self.controls_panel,
            "Goal state",
            GOAL_DEFAULT
        )

        tk.Label(
            self.controls_panel,
            text="Search algorithm",
            bg="#ffffff",
            fg="#222222",
            font=("Arial", 10, "bold")
        ).pack(anchor="w", padx=18, pady=(8, 5))

        self.algorithm_var = tk.StringVar(value="DFS")
        self.algorithm_box = ttk.Combobox(
            self.controls_panel,
            textvariable=self.algorithm_var,
            values=[
                "BFS Cách 1",
                "BFS Cách 2",
                "UCS",
                "Greedy",
                "Leo đồi đơn giản",
                "Leo núi dốc nhất",
                "Leo núi ngẫu nhiên",
                "Leo núi lặp lại ngẫu nhiên",
                "Local Beam Search",
                "Simulated Annealing",
                "Môi trường không chắc chắn",
                "A*",
                "IDA*",
                "DFS",
                "IDS"
            ],
            state="readonly"
        )
        self.algorithm_box.pack(fill="x", padx=18, ipady=4)
        self.algorithm_box.bind("<<ComboboxSelected>>", self.refresh_control_visibility)

        metric_values = ["Số ô sai", "Manhattan", "Dãy ngược", "Swap"]

        self.g_metric_label = tk.Label(
            self.controls_panel,
            text="g(n) metric",
            bg="#ffffff",
            fg="#222222",
            font=("Arial", 10, "bold")
        )
        self.g_metric_label.pack(anchor="w", padx=18, pady=(10, 5))

        self.g_metric_var = tk.StringVar(value="Manhattan")
        self.g_metric_box = ttk.Combobox(
            self.controls_panel,
            textvariable=self.g_metric_var,
            values=metric_values,
            state="readonly"
        )
        self.g_metric_box.pack(fill="x", padx=18, ipady=4)

        self.h_metric_label = tk.Label(
            self.controls_panel,
            text="h(n) heuristic",
            bg="#ffffff",
            fg="#222222",
            font=("Arial", 10, "bold")
        )
        self.h_metric_label.pack(anchor="w", padx=18, pady=(10, 5))

        self.h_metric_var = tk.StringVar(value="Manhattan")
        self.h_metric_box = ttk.Combobox(
            self.controls_panel,
            textvariable=self.h_metric_var,
            values=metric_values,
            state="readonly"
        )
        self.h_metric_box.pack(fill="x", padx=18, ipady=4)

        self.beam_k_label = tk.Label(
            self.controls_panel,
            text="Beam k",
            bg="#ffffff",
            fg="#222222",
            font=("Arial", 10, "bold")
        )
        self.beam_k_label.pack(anchor="w", padx=18, pady=(10, 5))

        self.beam_k_var = tk.StringVar(value="2")
        self.beam_k_box = ttk.Combobox(
            self.controls_panel,
            textvariable=self.beam_k_var,
            values=["2", "3", "4", "5"],
            state="readonly"
        )
        self.beam_k_box.pack(fill="x", padx=18, ipady=4)

        self.belief_panel = tk.Frame(self.controls_panel, bg="#ffffff")

        tk.Label(self.belief_panel, text="Uncertain environment", bg="#ffffff", fg="#222222", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10, 5))

        self.belief_mode_var = tk.StringVar(value="Không biết Start - biết Goal")
        self.belief_mode_box = ttk.Combobox(self.belief_panel, textvariable=self.belief_mode_var, values=["Không biết Start - biết Goal", "Toàn phần: không biết Start và Goal"], state="readonly")
        self.belief_mode_box.pack(fill="x", ipady=3, pady=(0, 6))

        self.belief_group_var = tk.StringVar(value="BFS Cách 1")
        self.belief_group_box = ttk.Combobox(self.belief_panel, textvariable=self.belief_group_var, values=["BFS Cách 1", "BFS Cách 2", "UCS", "Greedy", "A*", "IDA*", "DFS", "IDS", "Leo đồi đơn giản", "Leo núi dốc nhất", "Leo núi ngẫu nhiên", "Leo núi lặp lại ngẫu nhiên", "Local Beam Search", "Simulated Annealing"], state="readonly")
        self.belief_group_box.pack(fill="x", ipady=3, pady=(0, 6))
        self.belief_group_box.bind("<<ComboboxSelected>>", lambda e: self.refresh_belief_panel_visibility())

        self.belief_g_metric_label = tk.Label(self.belief_panel, text="g(B) metric", bg="#ffffff", fg="#222222", font=("Arial", 9, "bold"))
        self.belief_g_metric_var = tk.StringVar(value="Manhattan")
        self.belief_g_metric_box = ttk.Combobox(self.belief_panel, textvariable=self.belief_g_metric_var, values=metric_values, state="readonly")

        self.belief_h_metric_label = tk.Label(self.belief_panel, text="h(B) heuristic", bg="#ffffff", fg="#222222", font=("Arial", 9, "bold"))
        self.belief_h_metric_var = tk.StringVar(value="Manhattan")
        self.belief_h_metric_box = ttk.Combobox(self.belief_panel, textvariable=self.belief_h_metric_var, values=metric_values, state="readonly")

        self.belief_h_agg_label = tk.Label(self.belief_panel, text="Cách tính h(B)", bg="#ffffff", fg="#222222", font=("Arial", 9, "bold"))
        self.belief_h_agg_label.pack(anchor="w")
        self.belief_h_agg_var = tk.StringVar(value="MAX")
        self.belief_h_agg_box = ttk.Combobox(self.belief_panel, textvariable=self.belief_h_agg_var, values=["MAX", "AVG"], state="readonly")
        self.belief_h_agg_box.pack(fill="x", ipady=3, pady=(0, 6))

        self.belief_beam_k_label = tk.Label(self.belief_panel, text="Beam k", bg="#ffffff", fg="#222222", font=("Arial", 9, "bold"))
        self.belief_beam_k_var = tk.StringVar(value="2")
        self.belief_beam_k_box = ttk.Combobox(self.belief_panel, textvariable=self.belief_beam_k_var, values=["2", "3", "4", "5"], state="readonly")

        tk.Label(self.belief_panel, text="Initial belief states", bg="#ffffff", fg="#222222", font=("Arial", 9, "bold")).pack(anchor="w")
        self.belief_start_text = tk.Text(self.belief_panel, height=3, bg="#ffffff", fg="#222222", relief="solid", bd=1, font=("Consolas", 8))
        self.belief_start_text.pack(fill="x", pady=(2, 6))
        self.belief_start_text.insert("1.0", "123406758\n123456708")

        tk.Label(self.belief_panel, text="Goal belief states", bg="#ffffff", fg="#222222", font=("Arial", 9, "bold")).pack(anchor="w")
        self.belief_goal_text = tk.Text(self.belief_panel, height=3, bg="#ffffff", fg="#222222", relief="solid", bd=1, font=("Consolas", 8))
        self.belief_goal_text.pack(fill="x", pady=(2, 6))
        self.belief_goal_text.insert("1.0", "123456780")

        tk.Button(
            self.controls_panel,
            text="Solve Puzzle",
            command=self.solve_puzzle,
            bg="#287bdb",
            fg="#ffffff",
            activebackground="#1f65b8",
            activeforeground="#ffffff",
            relief="flat",
            font=("Arial", 10, "bold")
        ).pack(fill="x", padx=18, pady=(18, 12), ipady=7)

        self.error_label = tk.Label(
            self.controls_panel,
            text="",
            bg="#ffffff",
            fg="#c5221f",
            font=("Arial", 9),
            wraplength=230,
            justify="left"
        )
        self.error_label.pack(anchor="w", padx=18)

        note = (
            "Quy ước: 0 là ô trống. BFS dùng Queue FIFO, UCS dùng Priority Queue, "
            "Greedy dùng h(n) tùy chọn, A*/IDA* dùng f(n)=g(n)+h(n). Leo đồi có: đơn giản, dốc nhất, ngẫu nhiên, lặp lại ngẫu nhiên; Local Beam giữ k trạng thái tốt nhất. Simulated Annealing dùng T và xác suất. Môi trường không chắc chắn dùng belief state gồm nhiều node."
        )
        self.note_label = tk.Label(
            self.controls_panel,
            text=note,
            bg="#ffffff",
            fg="#555555",
            font=("Arial", 8),
            wraplength=230,
            justify="left"
        )
        self.note_label.pack(anchor="w", padx=18, pady=(12, 18))

    def labeled_entry(self, parent, label, default, help_text=None):
        tk.Label(
            parent,
            text=label,
            bg="#ffffff",
            fg="#222222",
            font=("Arial", 10, "bold")
        ).pack(anchor="w", padx=18)

        if help_text:
            tk.Label(
                parent,
                text=help_text,
                bg="#ffffff",
                fg="#555555",
                font=("Arial", 8)
            ).pack(anchor="w", padx=18, pady=(0, 5))

        entry = tk.Entry(
            parent,
            bg="#ffffff",
            fg="#222222",
            relief="solid",
            bd=1,
            font=("Arial", 10)
        )
        entry.insert(0, default)
        entry.pack(fill="x", padx=18, pady=(0, 14), ipady=6)
        return entry

    def build_board(self):
        self.board_frame = tk.Frame(
            self.board_panel,
            bg="#222222",
            highlightbackground="#222222",
            highlightthickness=8
        )
        self.board_frame.pack(pady=(0, 12))

        self.tiles = []

        for i in range(3):
            row = []
            for j in range(3):
                label = tk.Label(
                    self.board_frame,
                    text="",
                    width=4,
                    height=2,
                    bg="#f7f7f7",
                    fg="#111111",
                    font=("Arial", 28, "bold"),
                    relief="solid",
                    bd=1
                )
                label.grid(row=i, column=j, padx=3, pady=3)
                row.append(label)
            self.tiles.append(row)

        # Vùng này dùng riêng cho Môi trường không chắc chắn.
        # Khi chọn belief state, nó sẽ thay thế board lớn thông thường.
        self.belief_board_panel = tk.Frame(self.board_panel, bg="#f7f7f7")
        tk.Label(
            self.belief_board_panel,
            text="Belief states đang chạy",
            bg="#f7f7f7",
            fg="#222222",
            font=("Arial", 16, "bold")
        ).pack(anchor="center", pady=(0, 10))
        self.belief_boards_frame = tk.Frame(self.belief_board_panel, bg="#f7f7f7")
        self.belief_boards_frame.pack()
        self.belief_board_panel.pack_forget()

        self.action_label = tk.Label(
            self.board_panel,
            text="Action: Waiting",
            bg="#f7f7f7",
            fg="#555555",
            font=("Arial", 11, "bold")
        )
        self.action_label.pack(pady=(0, 8))

        nav = tk.Frame(self.board_panel, bg="#f7f7f7")
        nav.pack()

        for text, cmd in [
            ("Prev", self.prev_step),
            ("Stop", self.stop_animation),
            ("Next", self.next_step)
        ]:
            tk.Button(
                nav,
                text=text,
                command=cmd,
                bg="#ffffff",
                fg="#222222",
                relief="solid",
                bd=1,
                font=("Arial", 10, "bold")
            ).pack(side="left", padx=5, ipadx=10, ipady=5)

        self.manual_panel = self.card(self.board_panel, width=330, height=130)
        self.manual_panel.pack(pady=(16, 0))

        tk.Label(
            self.manual_panel,
            text="Manual Mode",
            bg="#ffffff",
            fg="#222222",
            font=("Arial", 10, "bold")
        ).pack(pady=(10, 8))

        row = tk.Frame(self.manual_panel, bg="#ffffff")
        row.pack()

        tk.Button(
            row,
            text="Manual Play",
            command=self.start_manual_play,
            bg="#ffffff",
            fg="#222222",
            relief="solid",
            bd=1,
            font=("Arial", 9, "bold")
        ).pack(side="left", padx=5, ipadx=8, ipady=5)

        tk.Button(
            row,
            text="Reset",
            command=self.reset_manual_play,
            bg="#ffffff",
            fg="#222222",
            relief="solid",
            bd=1,
            font=("Arial", 9, "bold")
        ).pack(side="left", padx=5, ipadx=8, ipady=5)

        stat = tk.Frame(self.manual_panel, bg="#ffffff")
        stat.pack(fill="x", padx=14, pady=(10, 0))

        self.moves_label = tk.Label(stat, text="Số bước\n0", bg="#f7f7f7", fg="#222222", font=("Arial", 9, "bold"))
        self.moves_label.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.time_label = tk.Label(stat, text="Thời gian\n0s", bg="#f7f7f7", fg="#222222", font=("Arial", 9, "bold"))
        self.time_label.pack(side="left", fill="x", expand=True, padx=(4, 0))

    def build_stats(self):
        tk.Label(
            self.stats_panel,
            text="Stats",
            bg="#ffffff",
            fg="#222222",
            font=("Arial", 18, "bold")
        ).pack(anchor="w", padx=18, pady=(18, 10))

        self.status_label = tk.Label(
            self.stats_panel,
            text="Pending user input...",
            bg="#ffffff",
            fg="#b06000",
            font=("Arial", 11, "bold")
        )
        self.status_label.pack(anchor="w", padx=18)

        self.runtime_label = self.metric_label("Runtime:")
        self.nodes_label = self.metric_label("Nodes expanded:")
        self.depth_label = self.metric_label("Search depth:")
        self.cost_label = self.metric_label("Path cost:")

        tk.Label(
            self.stats_panel,
            text="▼ Path",
            bg="#ffffff",
            fg="#222222",
            font=("Arial", 11, "bold")
        ).pack(anchor="w", padx=18, pady=(12, 5))

        self.path_text = tk.Text(
            self.stats_panel,
            height=9,
            bg="#f7f7f7",
            fg="#222222",
            relief="solid",
            bd=1,
            font=("Consolas", 9)
        )
        self.path_text.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        self.path_text.insert("1.0", "Chưa có dữ liệu")
        self.path_text.configure(state="disabled")

    def metric_label(self, text):
        label = tk.Label(
            self.stats_panel,
            text=text,
            bg="#ffffff",
            fg="#222222",
            font=("Arial", 10, "bold")
        )
        label.pack(anchor="w", padx=18, pady=(12, 0))
        return label

    def build_trace(self):
        trace_card = tk.Frame(
            self.container,
            bg="#ffffff",
            highlightbackground="#d6d6d6",
            highlightthickness=1
        )
        trace_card.pack(fill="both", expand=True, padx=70, pady=(22, 26))

        header = tk.Frame(trace_card, bg="#ffffff")
        header.pack(fill="x", padx=18, pady=(18, 12))

        tk.Label(
            header,
            text="Search Trace",
            bg="#ffffff",
            fg="#222222",
            font=("Arial", 18, "bold")
        ).pack(side="left")

        self.trace_count_label = tk.Label(
            header,
            text="Trace: 0/0",
            bg="#ffffff",
            fg="#555555",
            font=("Arial", 10)
        )
        self.trace_count_label.pack(side="right")

        table = tk.Frame(trace_card, bg="#ffffff")
        table.pack(fill="both", expand=True, padx=18)

        self.trace_header_labels = []

        for col, name in enumerate(["Node", "Frontier", "Reached"]):
            label = tk.Label(
                table,
                text=name,
                bg="#eeeeee",
                fg="#222222",
                relief="solid",
                bd=1,
                font=("Arial", 10, "bold")
            )
            label.grid(row=0, column=col, sticky="nsew")
            self.trace_header_labels.append(label)

        table.grid_columnconfigure(0, weight=1)
        table.grid_columnconfigure(1, weight=2)
        table.grid_columnconfigure(2, weight=1)

        self.node_text = tk.Text(table, height=12, bg="#ffffff", fg="#222222", relief="solid", bd=1, font=("Consolas", 9))
        self.frontier_text = tk.Text(table, height=12, bg="#ffffff", fg="#222222", relief="solid", bd=1, font=("Consolas", 9))
        self.reached_text = tk.Text(table, height=12, bg="#ffffff", fg="#222222", relief="solid", bd=1, font=("Consolas", 9))

        self.node_text.grid(row=1, column=0, sticky="nsew")
        self.frontier_text.grid(row=1, column=1, sticky="nsew")
        self.reached_text.grid(row=1, column=2, sticky="nsew")

        btns = tk.Frame(trace_card, bg="#ffffff")
        btns.pack(fill="x", padx=18, pady=12)

        tk.Button(btns, text="Prev trace", command=self.prev_trace, bg="#ffffff", relief="solid", bd=1).pack(side="left", padx=(0, 8), ipadx=8, ipady=4)
        tk.Button(btns, text="Next trace", command=self.next_trace, bg="#ffffff", relief="solid", bd=1).pack(side="left", padx=(0, 8), ipadx=8, ipady=4)
        tk.Button(btns, text="Path trace", command=self.show_solution_trace, bg="#ffffff", relief="solid", bd=1).pack(side="left", padx=(0, 8), ipadx=8, ipady=4)

        self.children_text = tk.Text(
            trace_card,
            height=7,
            bg="#f7f7f7",
            fg="#222222",
            relief="solid",
            bd=1,
            font=("Consolas", 9)
        )
        self.children_text.pack(fill="x", padx=18, pady=(0, 18))
        self.children_text.insert("1.0", "Node con sẽ hiện ở đây")
        self.children_text.configure(state="disabled")

    def is_local_algorithm(self):
        algo = self.algorithm_var.get()
        return algo in {
            "Leo đồi đơn giản",
            "Leo núi dốc nhất",
            "Leo núi ngẫu nhiên",
            "Leo núi lặp lại ngẫu nhiên",
            "Local Beam Search",
            "Simulated Annealing"
        }

    def is_belief_algorithm(self):
        return self.algorithm_var.get() == "Môi trường không chắc chắn"

    def update_trace_ui_by_algorithm(self, event=None):
        if not hasattr(self, "trace_header_labels"):
            return

        if self.is_belief_algorithm():
            names = ["Current Belief State", "Next Belief State", "Candidate Beliefs"]
            info = (
                "Uncertain Environment Trace: mỗi node là một belief state gồm nhiều trạng thái. "
                "Bảng sẽ hiển thị Current Belief, Next Belief và các belief candidate."
            )
        elif self.is_local_algorithm():
            names = ["Current Node", "Next Node", "Better Neighbors"]
            info = (
                "Local Search Trace: Current Node | Next Node | Better Neighbors. "
                "Phần dưới hiển thị toàn bộ neighbor và lý do chọn/bỏ qua."
            )
        else:
            names = ["Node", "Frontier", "Reached"]
            info = "Search Trace: Node | Frontier | Reached."

        if hasattr(self, "belief_panel"):
            if self.is_belief_algorithm():
                self.belief_panel.pack(fill="x", padx=18, pady=(10, 0))
            else:
                self.belief_panel.pack_forget()

        for label, name in zip(self.trace_header_labels, names):
            label.configure(text=name)

        if hasattr(self, "children_text"):
            self.set_text(self.children_text, info)

        if self.is_belief_algorithm() and hasattr(self, "refresh_belief_panel_visibility"):
            self.refresh_belief_panel_visibility()

    def format_better_neighbors(self, item):
        better = []

        for child in item.get("children", []):
            status = child.get("status", "")

            if (
                "BETTER" in status
                or "CHỌN" in status
                or "GOAL" in status
                or "ỨNG VIÊN" in status
                or "TỐT NHẤT" in status
            ):
                better.append(child)

        if not better:
            return "Better_Neighbors = rỗng\nKhông có trạng thái lân cận tốt hơn."

        lines = [f"Better_Neighbors ({len(better)}):"]

        for index, child in enumerate(better, start=1):
            lines.append(f"#{index} {child['action']}")

            if child.get("cost") is not None:
                lines.append(f"value/h = {child['cost']}")

            lines.append(child.get("status", ""))
            lines.append(format_key_as_matrix(child["key"]))
            lines.append("")

        return "\n".join(lines).strip()



    def pack_if_hidden(self, widget, **pack_options):
        if widget is not None and not widget.winfo_ismapped():
            widget.pack(**pack_options)

    def hide_widget(self, widget):
        if widget is not None and widget.winfo_ismapped():
            widget.pack_forget()

    def refresh_control_visibility(self, event=None):
        algo = self.algorithm_var.get()
        is_uncertain = algo == "Môi trường không chắc chắn"

        if is_uncertain:
            # Môi trường không chắc chắn dùng panel riêng, ẩn g/h/beam bên ngoài.
            for w in [
                getattr(self, "g_metric_label", None), getattr(self, "g_metric_box", None),
                getattr(self, "h_metric_label", None), getattr(self, "h_metric_box", None),
                getattr(self, "beam_k_label", None), getattr(self, "beam_k_box", None)
            ]:
                self.hide_widget(w)
        else:
            # UCS, A*, IDA* cần g(n)
            if algo in {"UCS", "A*", "IDA*"}:
                self.pack_if_hidden(self.g_metric_label, anchor="w", padx=18, pady=(10, 5))
                self.pack_if_hidden(self.g_metric_box, fill="x", padx=18, ipady=4)
            else:
                self.hide_widget(self.g_metric_label)
                self.hide_widget(self.g_metric_box)

            # Các thuật toán heuristic/local cần h(n), Local Beam cũng cần h(n)
            if algo in {
                "Greedy", "A*", "IDA*",
                "Leo đồi đơn giản", "Leo núi dốc nhất",
                "Leo núi ngẫu nhiên", "Leo núi lặp lại ngẫu nhiên",
                "Local Beam Search", "Simulated Annealing"
            }:
                self.pack_if_hidden(self.h_metric_label, anchor="w", padx=18, pady=(10, 5))
                self.pack_if_hidden(self.h_metric_box, fill="x", padx=18, ipady=4)
            else:
                self.hide_widget(self.h_metric_label)
                self.hide_widget(self.h_metric_box)

            # Local Beam cần cả h(n) và Beam k
            if algo == "Local Beam Search":
                self.pack_if_hidden(self.beam_k_label, anchor="w", padx=18, pady=(10, 5))
                self.pack_if_hidden(self.beam_k_box, fill="x", padx=18, ipady=4)
            else:
                self.hide_widget(self.beam_k_label)
                self.hide_widget(self.beam_k_box)

        self.update_trace_ui_by_algorithm()
        self.update_board_mode_visibility()

        if is_uncertain and hasattr(self, "belief_start_text"):
            try:
                self.draw_belief_boards(parse_state_list_text(self.belief_start_text.get("1.0", "end")))
            except Exception:
                pass


    def refresh_uncertain_visibility(self, event=None):
        if not hasattr(self, "uncertain_algorithm_var"):
            return

        algo = self.uncertain_algorithm_var.get()

        # Trong panel môi trường không chắc chắn:
        # Local Beam chỉ hiện Beam k.
        # Các thuật toán heuristic/local có dùng h(B) thì hiện h(B) và cách gộp h.
        # UCS/A*/IDA* có thể hiện g(B).
        uses_h = algo in {
            "Greedy", "A*", "IDA*",
            "Leo núi ngẫu nhiên", "Leo núi lặp lại ngẫu nhiên",
            "Local Beam Search", "Simulated Annealing"
        }
        uses_g = algo in {"UCS", "A*", "IDA*"}
        uses_beam = algo == "Local Beam Search"

        if hasattr(self, "uncertain_g_label"):
            if uses_g:
                self.pack_if_hidden(self.uncertain_g_label, anchor="w", pady=(8, 3))
                self.pack_if_hidden(self.uncertain_g_box, fill="x", ipady=3)
            else:
                self.hide_widget(self.uncertain_g_label)
                self.hide_widget(self.uncertain_g_box)

        if hasattr(self, "uncertain_h_label"):
            if uses_h and not uses_beam:
                self.pack_if_hidden(self.uncertain_h_label, anchor="w", pady=(8, 3))
                self.pack_if_hidden(self.uncertain_h_box, fill="x", ipady=3)
            else:
                self.hide_widget(self.uncertain_h_label)
                self.hide_widget(self.uncertain_h_box)

        if hasattr(self, "uncertain_agg_label"):
            if uses_h and not uses_beam:
                self.pack_if_hidden(self.uncertain_agg_label, anchor="w", pady=(8, 3))
                self.pack_if_hidden(self.uncertain_agg_box, fill="x", ipady=3)
            else:
                self.hide_widget(self.uncertain_agg_label)
                self.hide_widget(self.uncertain_agg_box)

        if hasattr(self, "uncertain_beam_label"):
            if uses_beam:
                self.pack_if_hidden(self.uncertain_beam_label, anchor="w", pady=(8, 3))
                self.pack_if_hidden(self.uncertain_beam_box, fill="x", ipady=3)
            else:
                self.hide_widget(self.uncertain_beam_label)
                self.hide_widget(self.uncertain_beam_box)


    def refresh_belief_panel_visibility(self):
        if not hasattr(self, "belief_group_var"):
            return

        selected = self.belief_group_var.get()

        widgets = [
            getattr(self, "belief_g_metric_label", None), getattr(self, "belief_g_metric_box", None),
            getattr(self, "belief_h_metric_label", None), getattr(self, "belief_h_metric_box", None),
            getattr(self, "belief_h_agg_label", None), getattr(self, "belief_h_agg_box", None),
            getattr(self, "belief_beam_k_label", None), getattr(self, "belief_beam_k_box", None),
        ]

        for w in widgets:
            if w is not None:
                w.pack_forget()

        uses_g = selected in {"UCS", "A*", "IDA*"}
        uses_h = selected in {
            "Greedy", "A*", "IDA*",
            "Leo đồi đơn giản", "Leo núi dốc nhất",
            "Leo núi ngẫu nhiên", "Leo núi lặp lại ngẫu nhiên",
            "Local Beam Search", "Simulated Annealing"
        }
        uses_beam = selected == "Local Beam Search"

        if uses_g:
            self.belief_g_metric_label.pack(anchor="w", pady=(4, 2))
            self.belief_g_metric_box.pack(fill="x", ipady=3, pady=(0, 6))

        if uses_h:
            self.belief_h_metric_label.pack(anchor="w", pady=(4, 2))
            self.belief_h_metric_box.pack(fill="x", ipady=3, pady=(0, 6))
            self.belief_h_agg_label.pack(anchor="w", pady=(4, 2))
            self.belief_h_agg_box.pack(fill="x", ipady=3, pady=(0, 6))

        if uses_beam:
            self.belief_beam_k_label.pack(anchor="w", pady=(4, 2))
            self.belief_beam_k_box.pack(fill="x", ipady=3, pady=(0, 6))


    def clear_belief_boards(self):
        if hasattr(self, "belief_board_panel"):
            self.belief_board_panel.pack_forget()
        if hasattr(self, "belief_boards_frame"):
            for widget in self.belief_boards_frame.winfo_children():
                widget.destroy()


    def draw_mini_state_board(self, parent, state, title, is_goal=False):
        wrapper = tk.Frame(parent, bg="#f7f7f7")
        wrapper.pack(side="left", padx=6, pady=4)

        tk.Label(
            wrapper,
            text=title,
            bg="#f7f7f7",
            fg="#188038" if is_goal else "#222222",
            font=("Arial", 8, "bold")
        ).pack()

        mini = tk.Frame(wrapper, bg="#222222", highlightbackground="#222222", highlightthickness=3)
        mini.pack()

        for i in range(3):
            for j in range(3):
                value = state[i][j]
                tk.Label(
                    mini,
                    text="" if value == 0 else str(value),
                    width=2,
                    height=1,
                    bg="#d9d9d9" if value == 0 else "#f7f7f7",
                    fg="#111111",
                    font=("Arial", 13, "bold"),
                    relief="solid",
                    bd=1
                ).grid(row=i, column=j, padx=1, pady=1)


    def draw_current_visual_state(self):
        if not self.solution_path:
            return

        if self.is_belief_mode_active():
            self.update_board_mode_visibility()
            if self.solution_belief_path and self.current_index < len(self.solution_belief_path):
                self.draw_belief_boards(self.solution_belief_path[self.current_index])
            elif self.belief_solution_path and self.current_index < len(self.belief_solution_path):
                self.draw_belief_boards(self.belief_solution_path[self.current_index])
            else:
                try:
                    self.draw_belief_boards(parse_state_list_text(self.belief_start_text.get("1.0", "end")))
                except Exception:
                    pass
        else:
            self.update_board_mode_visibility()
            self.draw_board(self.solution_path[self.current_index])


    def is_belief_mode_active(self):
        return hasattr(self, "algorithm_var") and self.algorithm_var.get() == "Môi trường không chắc chắn"

    def show_single_board(self):
        if hasattr(self, "board_frame") and not self.board_frame.winfo_ismapped():
            self.board_frame.pack(pady=(0, 12), before=self.action_label)

    def hide_single_board(self):
        if hasattr(self, "board_frame") and self.board_frame.winfo_ismapped():
            self.board_frame.pack_forget()

    def show_belief_board_area(self):
        if hasattr(self, "belief_board_panel") and not self.belief_board_panel.winfo_ismapped():
            self.belief_board_panel.pack(pady=(0, 12), before=self.action_label)


    def hide_belief_board_area(self):
        if hasattr(self, "belief_board_panel") and self.belief_board_panel.winfo_ismapped():
            self.belief_board_panel.pack_forget()


    def update_board_mode_visibility(self):
        if self.is_belief_mode_active():
            self.hide_single_board()
            self.show_belief_board_area()
        else:
            self.hide_belief_board_area()
            self.show_single_board()


    def draw_one_belief_board(self, parent, state, title, is_goal=False):
        box = tk.Frame(parent, bg="#f7f7f7")
        box.pack(side="left", padx=12, pady=4)

        tk.Label(
            box,
            text=title + (" = Goal" if is_goal else ""),
            bg="#f7f7f7",
            fg="#188038" if is_goal else "#222222",
            font=("Arial", 12, "bold")
        ).pack(pady=(0, 6))

        frame = tk.Frame(
            box,
            bg="#222222",
            highlightbackground="#222222",
            highlightthickness=7
        )
        frame.pack()

        for i in range(3):
            for j in range(3):
                value = state[i][j]
                tk.Label(
                    frame,
                    text="" if value == 0 else str(value),
                    width=4,
                    height=2,
                    bg="#d9d9d9" if value == 0 else "#f7f7f7",
                    fg="#111111",
                    font=("Arial", 24, "bold"),
                    relief="solid",
                    bd=1
                ).grid(row=i, column=j, padx=3, pady=3)

    def draw_belief_boards(self, belief_states=None):
        if not hasattr(self, "belief_boards_frame"):
            return

        for child in self.belief_boards_frame.winfo_children():
            child.destroy()

        if not belief_states:
            return

        goal_keys = set()
        if hasattr(self, "belief_goal_text"):
            try:
                for state in parse_state_list_text(self.belief_goal_text.get("1.0", "end")):
                    goal_keys.add(state_to_string(state))
            except Exception:
                pass

        # Nhập bao nhiêu Start trong Initial belief states thì vẽ/chạy bấy nhiêu bảng.
        # Mỗi hàng tối đa 3 bảng để giao diện không bị tràn ngang.
        row_frame = None
        for index, state in enumerate(belief_states, start=1):
            if (index - 1) % 3 == 0:
                row_frame = tk.Frame(self.belief_boards_frame, bg="#f7f7f7")
                row_frame.pack(anchor="center", pady=6)

            self.draw_one_belief_board(
                row_frame,
                state,
                f"S{index}",
                state_to_string(state) in goal_keys
            )


    def get_current_belief_states_for_display(self):
        if not getattr(self, "belief_solution_path", None):
            return None

        index = min(self.current_index, len(self.belief_solution_path) - 1)
        return self.belief_solution_path[index]

    def draw_board(self, state):
        zero_pos = find_zero(state)

        for i in range(3):
            for j in range(3):
                value = state[i][j]
                label = self.tiles[i][j]
                label.configure(text="" if value == 0 else str(value))

                if value == 0:
                    label.configure(bg="#d9d9d9")
                else:
                    label.configure(bg="#f7f7f7")

                label.unbind("<Button-1>")

                if self.manual_mode and value != 0 and abs(i - zero_pos[0]) + abs(j - zero_pos[1]) == 1:
                    label.configure(highlightbackground="#287bdb", highlightthickness=3)
                    label.bind("<Button-1>", lambda e, x=i, y=j: self.manual_tile_click(x, y))
                else:
                    label.configure(highlightthickness=0)

        self.update_action_label()

    def update_action_label(self):
        if not self.solution_path:
            if self.manual_mode:
                self.action_label.configure(text="Action: Người chơi tự di chuyển")
            else:
                self.action_label.configure(text="Action: Waiting")
        elif self.current_index == 0:
            self.action_label.configure(text="Action: Start")
        else:
            self.action_label.configure(text=f"Action: Move {self.solution_actions[self.current_index - 1]}")

    def validate_inputs(self):
        start = self.start_entry.get().strip()
        goal = self.goal_entry.get().strip()

        self.error_label.configure(text="")

        if not is_valid_input(start) or not is_valid_input(goal):
            self.error_label.configure(text="Input phải gồm đúng 9 số từ 0 đến 8.")
            return None, None

        if not is_solvable(start, goal):
            self.error_label.configure(text="Trạng thái này không thể giải được.")
            return None, None

        return start, goal


    def parse_state_lines(self, text):
        states = []
        for raw in text.splitlines():
            s = raw.strip().replace(" ", "")
            if not s:
                continue
            if not is_valid_input(s):
                raise ValueError(f"State không hợp lệ: {s}")
            states.append(string_to_state(s))
        if not states:
            raise ValueError("Danh sách belief state đang rỗng.")
        return states


    def solve_uncertain_environment(self, start, goal, h_metric):
        try:
            initial_states = self.parse_state_lines(self.belief_start_text.get("1.0", "end"))
            goal_states = self.parse_state_lines(self.belief_goal_text.get("1.0", "end"))
        except Exception as exc:
            self.error_label.configure(text=str(exc))
            return None

        selected_algo = self.belief_group_var.get()
        aggregate = self.belief_h_agg_var.get() if hasattr(self, "uncertain_agg_var") else "MAX"

        if selected_algo == "Local Beam Search":
            try:
                k = int(self.belief_beam_k_var.get())
            except Exception:
                k = 2
        else:
            try:
                k = int(self.beam_k_var.get())
            except Exception:
                k = 2

        result = belief_state_search_general(
            initial_states,
            goal_states,
            selected_algo,
            h_metric=h_metric,
            aggregate=aggregate,
            k=k
        )

        if result is not None:
            if result.get("solved", False):
                result["message"] = f"Môi trường không chắc chắn: {selected_algo} tìm thấy Goal Set cho tất cả board"
            else:
                result["message"] = f"Môi trường không chắc chắn: {selected_algo} chưa tìm thấy Goal Set cho tất cả board"

        return result

    def solve_puzzle(self):
        self.stop_animation()
        self.stop_manual_timer()
        self.manual_mode = False

        algo = self.algorithm_var.get()

        if algo == "Môi trường không chắc chắn":
            self.error_label.configure(text="")
            start_states = parse_state_list_text(self.belief_start_text.get("1.0", "end"))
            goal_states = parse_state_list_text(self.belief_goal_text.get("1.0", "end"))

            if not start_states:
                self.error_label.configure(text="Initial belief states phải có ít nhất 1 trạng thái hợp lệ.")
                return

            if not goal_states:
                goal_str = self.goal_entry.get().strip()
                if not is_valid_input(goal_str):
                    self.error_label.configure(text="Goal belief states hoặc Goal state phải hợp lệ.")
                    return
                goal_states = [string_to_state(goal_str)]

            start = start_states[0]
            goal = goal_states[0]
        else:
            start_str, goal_str = self.validate_inputs()
            if not start_str:
                return
            start = string_to_state(start_str)
            goal = string_to_state(goal_str)
            start_states = None
            goal_states = None

        self.refresh_control_visibility()

        display_algo = algo
        if algo == "Môi trường không chắc chắn" and hasattr(self, "belief_group_var"):
            display_algo = f"Môi trường không chắc chắn - {self.belief_group_var.get()}"
        self.status_label.configure(text=f"Đang chạy {display_algo}...", fg="#b06000")
        self.root.update_idletasks()

        start_time = time.perf_counter()

        g_metric = ui_metric_to_code(self.g_metric_var.get())
        h_metric = ui_metric_to_code(self.h_metric_var.get())

        if algo == "Môi trường không chắc chắn":
            selected_tmp = self.belief_group_var.get()
            if selected_tmp in {"UCS", "A*", "IDA*"} and hasattr(self, "belief_g_metric_var"):
                g_metric = ui_metric_to_code(self.belief_g_metric_var.get())
            if selected_tmp in {
                "Greedy", "A*", "IDA*",
                "Leo đồi đơn giản", "Leo núi dốc nhất",
                "Leo núi ngẫu nhiên", "Leo núi lặp lại ngẫu nhiên",
                "Local Beam Search", "Simulated Annealing"
            } and hasattr(self, "belief_h_metric_var"):
                h_metric = ui_metric_to_code(self.belief_h_metric_var.get())

        if algo == "BFS Cách 1":
            result = bfs_early(start, goal)
        elif algo == "BFS Cách 2":
            result = bfs_late(start, goal)
        elif algo == "UCS":
            result = uniform_cost_search(start, goal, g_metric)
        elif algo == "Greedy":
            result = greedy_search(start, goal, h_metric)
        elif algo == "Leo đồi đơn giản":
            result = simple_hill_climbing_h(start, goal, h_metric)
        elif algo == "Leo núi dốc nhất":
            result = steepest_hill_climbing_h(start, goal, h_metric)
        elif algo == "Leo núi ngẫu nhiên":
            result = stochastic_hill_climbing(start, goal, h_metric)
        elif algo == "Leo núi lặp lại ngẫu nhiên":
            result = random_restart_hill_climbing(start, goal, h_metric)
        elif algo == "Local Beam Search":
            try:
                beam_k = int(self.beam_k_var.get())
            except Exception:
                beam_k = 2
            result = local_beam_search(start, goal, h_metric, beam_k)
        elif algo == "Simulated Annealing":
            result = simulated_annealing_search(start, goal, h_metric)
        elif algo == "Môi trường không chắc chắn":
            selected_belief_algo = self.belief_group_var.get()
            aggregate = self.belief_h_agg_var.get()
            try:
                if selected_belief_algo == "Local Beam Search" and hasattr(self, "belief_beam_k_var"):
                    belief_k = int(self.belief_beam_k_var.get())
                else:
                    belief_k = int(self.beam_k_var.get())
            except Exception:
                belief_k = 2
            result = belief_state_search_general(
                start_states,
                goal_states,
                selected_belief_algo,
                h_metric=h_metric,
                g_metric=g_metric,
                aggregate=aggregate,
                k=belief_k
            )
            if result is not None:
                if result.get("solved", False):
                    result["message"] = f"Môi trường không chắc chắn: {selected_belief_algo} tìm thấy Goal Set cho tất cả board"
                else:
                    result["message"] = f"Môi trường không chắc chắn: {selected_belief_algo} chưa tìm thấy Goal Set cho tất cả board"
        elif algo == "A*":
            result = astar_search(start, goal, g_metric, h_metric)
        elif algo == "IDA*":
            result = ida_star_search(start, goal, g_metric, h_metric)
        elif algo == "DFS":
            result = dfs_search(start, goal)
        else:
            result = ids_search(start, goal)

        if algo == "Môi trường không chắc chắn" and result is not None:
            if "belief_path" not in result or not result.get("belief_path"):
                belief_path = []
                seen_bp = set()
                for trace_item in result.get("trace", []):
                    states = trace_item.get("node")
                    if isinstance(states, list) and states and isinstance(states[0], list):
                        key = belief_key(states)
                        if key not in seen_bp:
                            seen_bp.add(key)
                            belief_path.append(states)
                if not belief_path and start_states:
                    belief_path = [start_states]
                result["belief_path"] = belief_path
                result["path"] = [states[0] for states in belief_path if states]
            selected_name = self.belief_group_var.get() if hasattr(self, "belief_group_var") else "Belief Search"
            if result.get("solved", False):
                result["message"] = f"Môi trường không chắc chắn: {selected_name} tìm thấy Goal Set cho tất cả board"
            else:
                result["message"] = f"Môi trường không chắc chắn: {selected_name} chưa tìm thấy Goal Set cho tất cả board"

        runtime = (time.perf_counter() - start_time) * 1000

        if result is None:
            self.status_label.configure(text="Không tìm thấy lời giải", fg="#c5221f")
            return

        self.solution_belief_path = result.get("belief_path", [])
        if algo == "Môi trường không chắc chắn" and self.solution_belief_path:
            self.solution_path = [states[0] for states in self.solution_belief_path if states]
        else:
            self.solution_path = result["path"]
        self.solution_actions = result["actions"]
        self.search_trace = result["trace"]
        self.belief_solution_path = result.get("belief_path", [])
        self.current_index = 0
        self.trace_index = 0
        self.final_status_text = result.get("message", "Solved successfully!")
        self.final_status_color = "#188038" if result.get("solved", True) else "#b06000"

        self.runtime_label.configure(text=f"Runtime: {runtime:.3f} ms")
        self.nodes_label.configure(text=f"Nodes expanded: {result['nodes']}")
        self.depth_label.configure(text=f"Search depth: {result['depth']}")
        self.cost_label.configure(text=f"Path cost: {result['cost']}")

        self.write_path_text()
        self.draw_current_visual_state()
        self.render_trace(0)

        if len(self.solution_path) <= 100:
            self.status_label.configure(text="Đang mô phỏng đường đi...", fg="#b06000")
            self.animate_solution()
        else:
            self.status_label.configure(text=self.final_status_text, fg=self.final_status_color)

    def write_path_text(self):
        self.path_text.configure(state="normal")
        self.path_text.delete("1.0", "end")

        lines = []

        if self.is_belief_mode_active() and self.solution_belief_path:
            for i, states in enumerate(self.solution_belief_path[:180]):
                if i == 0:
                    lines.append("Step 0")
                else:
                    action = self.solution_actions[i - 1] if i - 1 < len(self.solution_actions) else ""
                    lines.append(f"Step {i} - Move {action}")

                lines.append("Belief states:")
                for b_index, b_state in enumerate(states, start=1):
                    lines.append(f"  S{b_index}: {state_to_string(b_state)}")
                lines.append("")

            if len(self.solution_belief_path) > 180:
                lines.append(f"... còn {len(self.solution_belief_path) - 180} step nữa")
        else:
            for i, state in enumerate(self.solution_path[:180]):
                if i == 0:
                    lines.append("Step 0")
                else:
                    lines.append(f"Step {i} - Move {self.solution_actions[i - 1]}")

                lines.append(state_to_string(state))
                lines.append("")

            if len(self.solution_path) > 180:
                lines.append(f"... còn {len(self.solution_path) - 180} step nữa")

        self.path_text.insert("1.0", "\n".join(lines))
        self.path_text.configure(state="disabled")


    def animate_solution(self):
        self.stop_animation()

        def step():
            total_steps = len(self.solution_belief_path) if self.is_belief_mode_active() and self.solution_belief_path else len(self.solution_path)

            if self.current_index < total_steps - 1:
                self.current_index += 1
                self.draw_current_visual_state()
                self.show_solution_trace()
                self.animation_id = self.root.after(650, step)
            else:
                self.status_label.configure(text=self.final_status_text, fg=self.final_status_color)

        self.animation_id = self.root.after(650, step)


    def stop_animation(self):
        if self.animation_id:
            self.root.after_cancel(self.animation_id)
            self.animation_id = None

    def next_step(self):
        self.stop_animation()
        if not self.solution_path and not self.solution_belief_path:
            return

        total_steps = len(self.solution_belief_path) if self.is_belief_mode_active() and self.solution_belief_path else len(self.solution_path)

        if self.current_index < total_steps - 1:
            self.current_index += 1
            self.draw_current_visual_state()
            self.show_solution_trace()


    def prev_step(self):
        self.stop_animation()
        if not self.solution_path and not self.solution_belief_path:
            return

        if self.current_index > 0:
            self.current_index -= 1
            self.draw_current_visual_state()
            self.show_solution_trace()


    def render_empty_trace(self):
        self.update_trace_ui_by_algorithm()
        self.set_text(self.node_text, "")
        self.set_text(self.frontier_text, "")
        self.set_text(self.reached_text, "")
        self.set_text(self.children_text, "Bấm Solve Puzzle để xem bảng quá trình tìm kiếm.")
        self.trace_count_label.configure(text="Trace: 0/0")

    def render_trace(self, index):
        if not self.search_trace:
            return

        index = max(0, min(index, len(self.search_trace) - 1))
        self.trace_index = index
        item = self.search_trace[index]

        mode_text = item.get("mode", "")
        is_belief_trace = "Belief" in mode_text
        is_local_trace = (
            "Leo đồi" in mode_text
            or "Leo núi" in mode_text
            or "Local Beam" in mode_text
            or "Simulated Annealing" in mode_text
        )

        if is_belief_trace:
            self.render_belief_trace_item(item)
            self.trace_count_label.configure(text=f"Trace: {self.trace_index + 1}/{len(self.search_trace)}")
            return

        if is_local_trace:
            self.render_local_trace_item(item)
            self.trace_count_label.configure(text=f"Trace: {self.trace_index + 1}/{len(self.search_trace)}")
            return

        if hasattr(self, "trace_header_labels"):
            for label, name in zip(self.trace_header_labels, ["Node", "Frontier", "Reached"]):
                label.configure(text=name)

        node_lines = [
            f"State: {item['node_key']}",
            f"Action: {item['action']}",
            f"Iteration: {item['iteration']}"
        ]

        if item.get("node_cost") is not None:
            node_lines.append(f"value: {item['node_cost']}")

        node_lines.append("")
        node_lines.extend(self.format_state(item["node"]))

        self.set_text(self.node_text, "\n".join(node_lines))
        self.set_text(
            self.frontier_text,
            format_key_list_as_matrices(item.get("frontier_after", []), limit=8)
        )
        self.set_text(
            self.reached_text,
            format_key_list_as_matrices(item.get("reached_after", []), limit=8)
        )

        child_lines = [item.get("mode", "")]

        for child in item.get("children", [])[:12]:
            line = f"{child['action']:>5} | {child['status']}"

            if child.get("cost") is not None:
                line += f" | value={child['cost']}"

            child_lines.append(line)
            child_lines.append(format_key_as_matrix(child["key"]))
            child_lines.append("")

        self.set_text(self.children_text, "\n".join(child_lines))
        self.trace_count_label.configure(text=f"Trace: {self.trace_index + 1}/{len(self.search_trace)}")


    def render_belief_trace_item(self, item):
        if hasattr(self, "trace_header_labels"):
            names = ["Current Belief State", "Next Belief State", "Candidate Beliefs"]
            for label, name in zip(self.trace_header_labels, names):
                label.configure(text=name)

        current_lines = [
            "CURRENT BELIEF STATE",
            "Belief key:",
            item["node_key"],
            f"Action: {item['action']}",
            f"Iteration: {item['iteration']}"
        ]
        if item.get("node_cost") is not None:
            current_lines.append(f"h(B): {item['node_cost']:.2f}")
        current_lines.append("")
        for index, state in enumerate(item["node"], start=1):
            current_lines.append(f"S{index}: {state_to_string(state)}")
            current_lines.extend(self.format_state(state))
            current_lines.append("")

        chosen_key = item.get("frontier_after", [""])[0] if item.get("frontier_after") else ""
        next_lines = ["NEXT BELIEF STATE"]
        chosen_candidate = None
        for child in item.get("children", []):
            if child.get("key") == chosen_key or "CHỌN" in child.get("status", ""):
                chosen_candidate = child
                break

        if chosen_candidate:
            next_lines.append(f"Action: {chosen_candidate['action']}")
            next_lines.append(f"Status: {chosen_candidate['status']}")
            next_lines.append(f"h(B): {chosen_candidate['cost']:.2f}")
            next_lines.append("")
            next_lines.append(format_belief_key(chosen_candidate["key"]))
        else:
            next_lines.append("Không có belief state mới.")

        candidate_lines = [item.get("mode", ""), "", "CANDIDATE BELIEFS:"]
        for index, child in enumerate(item.get("children", [])[:8], start=1):
            candidate_lines.append(f"#{index} Action={child['action']} | {child['status']} | h(B)={child['cost']:.2f}")
            candidate_lines.append(format_belief_key(child["key"]))
            candidate_lines.append("")

        bottom_lines = [
            "Giải thích:",
            "- Mỗi node là một belief state gồm nhiều trạng thái có thể xảy ra.",
            "- Một action được áp dụng lên toàn bộ các trạng thái trong belief state.",
            "- Nếu một trạng thái đã là Goal thì được giữ nguyên như trạng thái hấp thụ.",
            "- h(B) lấy theo max hoặc trung bình tùy thuật toán đã chọn. Nếu h bằng nhau thì chọn ngẫu nhiên."
        ]

        self.set_text(self.node_text, "\n".join(current_lines))
        self.set_text(self.frontier_text, "\n".join(next_lines))
        self.set_text(self.reached_text, "\n".join(candidate_lines))
        self.set_text(self.children_text, "\n".join(bottom_lines))

    def render_local_trace_item(self, item):
        if hasattr(self, "trace_header_labels"):
            names = ["Current Node", "Next Node", "Better Neighbors"]

            for label, name in zip(self.trace_header_labels, names):
                label.configure(text=name)

        current_lines = [
            "CURRENT NODE",
            f"State: {item['node_key']}",
            f"Action: {item['action']}",
            f"Iteration: {item['iteration']}"
        ]

        if item.get("node_cost") is not None:
            current_lines.append(f"value/h: {item['node_cost']}")

        current_lines.append("")
        current_lines.extend(self.format_state(item["node"]))

        chosen_child = None

        for child in item.get("children", []):
            status = child.get("status", "")

            if (
                "CHỌN" in status
                or "GOAL" in status
                or "TỐT NHẤT" in status
            ):
                chosen_child = child
                break

        next_lines = ["NEXT NODE"]

        if chosen_child is not None:
            next_lines.append(f"Action: {chosen_child['action']}")
            next_lines.append(f"Status: {chosen_child['status']}")

            if chosen_child.get("cost") is not None:
                next_lines.append(f"value/h: {chosen_child['cost']}")

            next_lines.append("")
            next_lines.append(format_key_as_matrix(chosen_child["key"]))
        else:
            next_lines.append("Không có Next tốt hơn.")
            next_lines.append("Dừng tại local optimum / local maximum.")

        better_text = self.format_better_neighbors(item)

        neighbor_lines = [item.get("mode", ""), "", "Tất cả Neighbor sinh ra:"]

        for child in item.get("children", [])[:16]:
            line = f"{child['action']:>18} | {child['status']}"

            if child.get("cost") is not None:
                line += f" | value/h={child['cost']}"

            neighbor_lines.append(line)
            neighbor_lines.append(format_key_as_matrix(child["key"]))
            neighbor_lines.append("")

        self.set_text(self.node_text, "\n".join(current_lines))
        self.set_text(self.frontier_text, "\n".join(next_lines))
        self.set_text(self.reached_text, better_text)
        self.set_text(self.children_text, "\n".join(neighbor_lines))

    def format_state(self, state):
        return [" ".join(str(x) if x != 0 else "_" for x in row) for row in state]

    def set_text(self, widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def next_trace(self):
        if self.search_trace and self.trace_index < len(self.search_trace) - 1:
            self.render_trace(self.trace_index + 1)

    def prev_trace(self):
        if self.search_trace and self.trace_index > 0:
            self.render_trace(self.trace_index - 1)

    def show_solution_trace(self):
        if not self.search_trace or not self.solution_path:
            return

        key = state_to_string(self.solution_path[self.current_index])
        belief_key_now = None
        if self.solution_belief_path and self.current_index < len(self.solution_belief_path):
            belief_key_now = belief_key(self.solution_belief_path[self.current_index])

        for i, item in enumerate(self.search_trace):
            if item["node_key"] == key or (belief_key_now and item["node_key"] == belief_key_now):
                self.render_trace(i)
                break

    def shuffle_puzzle(self):
        self.stop_animation()
        self.stop_manual_timer()
        self.manual_mode = False

        goal_str = self.goal_entry.get().strip()

        if not is_valid_input(goal_str):
            self.error_label.configure(text="Goal không hợp lệ.")
            return

        state = string_to_state(goal_str)
        last = None
        opposite = {
            "UP": "DOWN",
            "DOWN": "UP",
            "LEFT": "RIGHT",
            "RIGHT": "LEFT"
        }

        for _ in range(14):
            neighbors = get_neighbors(state)

            if last:
                filtered = [(s, a) for s, a in neighbors if a != opposite[last]]
                if filtered:
                    neighbors = filtered

            state, last = random.choice(neighbors)

        start_str = state_to_string(state)
        self.start_entry.delete(0, "end")
        self.start_entry.insert(0, start_str)

        self.solution_path = []
        self.solution_belief_path = []
        self.solution_actions = []
        self.search_trace = []
        self.current_index = 0
        self.trace_index = 0

        self.draw_board(state)
        self.clear_belief_boards()
        self.render_empty_trace()

        self.status_label.configure(text="Pending user input...", fg="#b06000")
        self.runtime_label.configure(text="Runtime:")
        self.nodes_label.configure(text="Nodes expanded:")
        self.depth_label.configure(text="Search depth:")
        self.cost_label.configure(text="Path cost:")

        self.path_text.configure(state="normal")
        self.path_text.delete("1.0", "end")
        self.path_text.insert("1.0", "Chưa có dữ liệu")
        self.path_text.configure(state="disabled")

    def start_manual_play(self):
        self.stop_animation()

        start_str, goal_str = self.validate_inputs()
        if not start_str:
            return

        self.manual_mode = True
        self.manual_state = string_to_state(start_str)
        self.manual_start_state = clone_state(self.manual_state)
        self.manual_moves = 0
        self.manual_seconds = 0

        self.solution_path = []
        self.solution_belief_path = []
        self.solution_actions = []
        self.search_trace = []

        self.draw_board(self.manual_state)
        self.clear_belief_boards()
        self.update_manual_labels()
        self.start_manual_timer()

        self.status_label.configure(text="Manual Mode", fg="#188038")
        self.path_text.configure(state="normal")
        self.path_text.delete("1.0", "end")
        self.path_text.insert("1.0", "Đang ở chế độ tự chơi thủ công. Người chơi tự di chuyển các ô.")
        self.path_text.configure(state="disabled")

    def reset_manual_play(self):
        if not self.manual_start_state:
            self.start_manual_play()
            return

        self.manual_mode = True
        self.manual_state = clone_state(self.manual_start_state)
        self.manual_moves = 0
        self.manual_seconds = 0
        self.draw_board(self.manual_state)
        self.clear_belief_boards()
        self.update_manual_labels()
        self.start_manual_timer()

    def manual_tile_click(self, i, j):
        if not self.manual_mode or not self.manual_state:
            return

        zx, zy = find_zero(self.manual_state)

        if abs(i - zx) + abs(j - zy) != 1:
            return

        self.manual_state[zx][zy], self.manual_state[i][j] = self.manual_state[i][j], self.manual_state[zx][zy]
        self.manual_moves += 1

        self.draw_board(self.manual_state)
        self.clear_belief_boards()
        self.update_manual_labels()
        self.action_label.configure(text=f"Action: Player Move {self.manual_moves}")

        if state_to_string(self.manual_state) == self.goal_entry.get().strip():
            self.manual_mode = False
            self.stop_manual_timer()
            self.status_label.configure(text="Bạn đã thắng!", fg="#188038")
            self.action_label.configure(text="Action: Goal reached!")

    def start_manual_timer(self):
        self.stop_manual_timer()

        def tick():
            if self.manual_mode:
                self.manual_seconds += 1
                self.update_manual_labels()
                self.manual_timer_id = self.root.after(1000, tick)

        self.manual_timer_id = self.root.after(1000, tick)

    def stop_manual_timer(self):
        if self.manual_timer_id:
            self.root.after_cancel(self.manual_timer_id)
            self.manual_timer_id = None

    def update_manual_labels(self):
        self.moves_label.configure(text=f"Số bước\n{self.manual_moves}")
        self.time_label.configure(text=f"Thời gian\n{self.manual_seconds}s")


if __name__ == "__main__":
    root = tk.Tk()
    app = EightPuzzleApp(root)
    root.mainloop()
