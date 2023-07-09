from dataclasses import dataclass, field
import importlib
import sys
from types import ModuleType


def reload_addon(name: str):
    graph = Graph(sys.modules[name])

    for node in graph.topological_sort():
        try:
            importlib.reload(node.module)
        except ModuleNotFoundError:
            pass


@dataclass
class Node:
    module: ModuleType
    edges: set["Node"] = field(default_factory=set)

    @property
    def name(self):
        # pylint: disable=no-member
        return self.module.__name__

    def add_edge(self, node: "Node"):
        self.edges.add(node)

    def __hash__(self):
        return hash(self.name)


class Graph:
    _root: ModuleType
    _nodes: dict[str, Node]

    def __init__(self, root: ModuleType):
        self._root = root
        self._nodes = dict()
        self._build(self.get_node(self._root))

    @property
    def root(self):
        return self.get_node(self._root)

    def get_node(self, module: ModuleType):
        return self._nodes.setdefault(module.__name__, Node(module))

    def topological_sort(self):
        return _topological_sort(self.root, set(), [])

    def print(self):
        _print_tree(self.root)

    def _build(self, node: Node):
        for module in _get_dependencies(node.module, self._root):
            dependency = self.get_node(module)
            node.add_edge(dependency)
            self._build(dependency)


def _get_dependencies(module: ModuleType, base_package: ModuleType) -> list[ModuleType]:
    return [
        mod
        for name in dir(module)
        if (mod := getattr(module, name))
        and isinstance(mod, ModuleType)
        and mod.__name__.startswith(base_package.__name__)
    ]


def _topological_sort(start: Node, visited: set[Node], result: list[Node]):
    current = start
    visited.add(current)

    for neighbor in current.edges:
        if neighbor not in visited:
            result = _topological_sort(neighbor, visited, result)

    result.append(current)
    return result


def _print_tree(node: Node, depth=0):
    indent = "  " * depth
    print(indent + node.name)
    for edge in node.edges:
        edge.print(depth + 1)
