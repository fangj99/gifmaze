# -*- coding: utf-8 -*-

import heapq
import random
from collections import deque
from operator import itemgetter
from .maze import Maze


def prim(maze, start):
    """Maze by Prim's algorithm."""
    queue = [(0, start, v) for v in maze.get_neighbors(start)]
    maze.mark_cell(start, Maze.TREE)

    while len(queue) > 0:
        _, parent, child = heapq.heappop(queue)
        if maze.in_tree(child):
            continue
        maze.mark_cell(child, Maze.TREE)
        maze.mark_space(parent, child, Maze.TREE)
        for v in maze.get_neighbors(child):
            # assign a weight to this edge only when it's needed.
            weight = random.random()
            heapq.heappush(queue, (weight, child, v))

        maze.anim.refresh_frame()
    maze.anim.clear_remaining_changes()



def random_dfs(maze, start):
    """Maze by random depth-first search."""
    stack = [(start, v) for v in maze.get_neighbors(start)]
    maze.mark_cell(start, Maze.TREE)

    while len(stack) > 0:
        parent, child = stack.pop()
        if maze.in_tree(child):
            continue
        maze.mark_cell(child, Maze.TREE)
        maze.mark_space(parent, child, Maze.TREE)
        neighbors = maze.get_neighbors(child)
        random.shuffle(neighbors)
        for v in neighbors:
            stack.append((child, v))

        maze.anim.refresh_frame()
    maze.anim.clear_remaining_changes()


def kruskal(maze):
    """Maze by Kruskal's algorithm."""
    parent = {v: v for v in maze.cells}
    rank = {v: 0 for v in maze.cells}
    edges = [(random.random(), u, v) for u in maze.cells \
             for v in maze.get_neighbors(u) if u < v]

    #---
    def find(v):
        """find the root of the subtree that v belongs to."""
        while parent[v] != v:
            v = parent[v]
        return v

    for _, u, v in sorted(edges, key=itemgetter(0)):
        root1 = find(u)
        root2 = find(v)
        if root1 != root2:
            if rank[root1] > rank[root2]:
                parent[root2] = root1
            elif rank[root1] < rank[root2]:
                parent[root1] = root2
            else:
                parent[root1] = root2
                rank[root2] += 1

            maze.mark_cell(u, Maze.TREE)
            maze.mark_cell(v, Maze.TREE)
            maze.mark_space(u, v, Maze.TREE)
            maze.anim.refresh_frame()

    maze.anim.clear_remaining_changes()


def wilson(maze, root):
    """
    Maze by Wilson's algorithm.
    The algorithm runs as follows:

    Given a finite, connected and undirected graph G:

    1. Choose any vertex v as the root and maintain a tree T. Initially T={v}.

    2. For any vertex v that is not in T, start a loop erased random walk from
       v until the walk hits T, then add the resulting path to T.

    3. Repeat step 2 until all vertices of G are in T.

    Reference:
        "Probability on Trees and Networks", by Russell Lyons and Yuval Peres.
    """
    maze.loop_erased_walk_path = []  # hold the path of the loop erased random walk.

    def add_to_path(cell):
        """Add a cell to the path of current random walk."""
        maze.mark_cell(cell, Maze.PATH)
        maze.mark_space(maze.loop_erased_walk_path[-1], cell, Maze.PATH)
        maze.loop_erased_walk_path.append(cell)

    def erase_loop(cell):
        """
        When a cell is visited twice then a loop is created, erase it.
        """
        index = maze.loop_erased_walk_path.index(cell)
        # erase the loop
        maze.mark_path(maze.loop_erased_walk_path[index:], Maze.WALL)
        maze.mark_cell(maze.loop_erased_walk_path[index], Maze.PATH)
        maze.loop_erased_walk_path = maze.loop_erased_walk_path[:index+1]

    # the algorithm begins here.
    # initially the tree contains only the root.
    maze.mark_cell(root, Maze.TREE)

    # for each cell that is not in the tree,
    # start a loop erased random walk from this cell until the walk hits the tree.
    for cell in maze.cells:
        if not maze.in_tree(cell):
            maze.loop_erased_walk_path = [cell]
            maze.mark_cell(cell, Maze.PATH)
            current_cell = cell

            while not maze.in_tree(current_cell):
                next_cell = random.choice(maze.get_neighbors(current_cell))
                if maze.in_path(next_cell):  # if it's already in the path then a loop is found.
                    erase_loop(next_cell)
                elif maze.in_tree(next_cell):  # if the walk hits the tree then finish the walk.
                    add_to_path(next_cell)
                    # `add_to_path` will change the cell to `PATH` so we need to reset it.
                    maze.mark_cell(next_cell, Maze.TREE)
                else:  # continue the walk from this new cell.
                    add_to_path(next_cell)
                current_cell = next_cell

                maze.anim.refresh_frame()

            # once the walk hits the tree then add its path to the tree.
            maze.mark_path(maze.loop_erased_walk_path, Maze.TREE)

    maze.anim.clear_remaining_changes()



# ------------------------
# maze solving algorithms.
# ------------------------

# a helper function
def retrieve_path(came_from, start, end):
    """Get the path between the start and the end."""
    path = [end]
    v = end
    while v != start:
        v = came_from[v]
        path.append(v)
    return path


def bfs(maze, start, end):
    """Solve the maze by breadth-first search."""

    # a helper function
    def dist_to_color(distance):
        """
        Map the distance of a cell to the start to a color index.
        This is because we must make sure that the assigned number of each cell
        lies between 0 and the total number of colors in the image,
        otherwise the initial dict of the encoder cannot recognize it.
        """
        return max(distance % maze.anim.num_colors, 3)

    dist = 0
    came_from = {start: start}
    queue = deque([(start, dist)])
    maze.mark_cell(start, dist_to_color(dist))
    visited = set([start])

    while len(queue) > 0:
        child, dist = queue.popleft()
        parent = came_from[child]
        maze.mark_cell(child, dist_to_color(dist))
        maze.mark_space(parent, child, dist_to_color(dist))

        for next_cell in maze.get_neighbors(child):
            if (next_cell not in visited) and (not maze.barrier(child, next_cell)):
                came_from[next_cell] = child
                queue.append((next_cell, dist + 1))
                visited.add(next_cell)

        maze.anim.refresh_frame()
    maze.anim.clear_remaining_changes()

    # retrieve the path
    path = retrieve_path(came_from, start, end)
    maze.mark_path(path, Maze.PATH)
    # show the path
    maze.anim.clear_remaining_changes()


def dfs(maze, start, end):
    """Solve the maze by depth-first search."""

    def dist_to_color(distance):
        return max(distance % maze.anim.num_colors, 3)

    dist = 0
    came_from = {start: start}  # a dict to remember each step.
    stack = [(start, dist)]
    maze.mark_cell(start, dist_to_color(dist))
    visited = set([start])

    while len(stack) > 0:
        child, dist = stack.pop()
        parent = came_from[child]
        maze.mark_cell(child, dist_to_color(dist))
        maze.mark_space(parent, child, dist_to_color(dist))
        for next_cell in maze.get_neighbors(child):
            if (next_cell not in visited) and (not maze.barrier(child, next_cell)):
                came_from[next_cell] = child
                stack.append((next_cell, dist + 1))
                visited.add(next_cell)

        maze.anim.refresh_frame()
    maze.anim.clear_remaining_changes()

    path = retrieve_path(came_from, start, end)
    maze.mark_path(path, Maze.PATH)
    maze.anim.clear_remaining_changes()


def astar(maze, start, end):
    """Solve the maze by A* search."""
    weighted_edges = {(u, v): 1.0 for u in maze.cells for v in maze.get_neighbors(u)}
    queue = [(0, start)]
    came_from = {start: start}
    cost_so_far = {start: 0}

    def manhattan(u, v):
        """The heuristic distance between two cells."""
        return abs(u[0] - v[0]) + abs(u[1] - v[1])

    while len(queue) > 0:
        _, child = heapq.heappop(queue)
        parent = came_from[child]
        maze.mark_cell(child, Maze.FILL)
        maze.mark_space(parent, child, Maze.FILL)
        if child == end:
            break

        for next_cell in maze.get_neighbors(child):
            new_cost = cost_so_far[parent] + weighted_edges[(child, next_cell)]
            if (next_cell not in cost_so_far or new_cost < cost_so_far[next_cell]) \
               and (not maze.barrier(next_cell, child)):
                cost_so_far[next_cell] = new_cost
                came_from[next_cell] = child
                priority = new_cost + manhattan(next_cell, end)
                heapq.heappush(queue, (priority, next_cell))

        maze.anim.refresh_frame()
    maze.anim.clear_remaining_changes()

    path = retrieve_path(came_from, start, end)
    maze.mark_path(path, Maze.PATH)
    maze.anim.clear_remaining_changes()
