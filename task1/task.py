from typing import List, Tuple, Set, DefaultDict
from collections import defaultdict
import sys
import copy

def transpose(A: List[List[bool]]) -> List[List[bool]]:
    result = A
    for i, v1 in enumerate(result):
        for j, v2 in enumerate(result[i]):
            if i > j:
                result[i][j], result[j][i] = result[j][i], result[i][j]

    return result

def bool_multiplication(A: List[List[bool]], B: List[List[bool]]) -> List[List[bool]]:
    result = copy.deepcopy(A)
    N = len(A)
    for i in range(N):
        for j in range(N):
            result[i][j] = False
            for k in range(N):
                result[i][j] |= A[i][k] and B[k][j]

    return result

def bool_sum(A: List[List[bool]], B: List[List[bool]]) -> List[List[bool]]:
    result = A
    N = len(A)
    for i in range(N):
        for j in range(N):
            result[i][j] |= B[i][j]

    return result


class graph:
    def __init__(self, data: str, root: str):
        self.root = root
        self.nodes: DefaultDict[str, Set[str]] = defaultdict(set)
        self.direct_management_relationship = None
        self.direct_subordination_relationship = None
        self.transitive_management_relationship = None
        self.transitive_subordination_relationship = None
        self.single_level_subordination_matrix = None

        for pair in list(map(str, data.split('\n'))):
            self.append_edge(tuple(pair.split(',')))

        self.remove_root(root, None)
        print(self)

    def __str__(self) -> str:
        return f'root: {self.root}, nodes: {self.nodes}\n'

    def append_edge(self, edge: Tuple[str, str]):
        self.nodes[edge[0]].add(edge[1])
        self.nodes[edge[1]].add(edge[0])

    def remove_root(self, node: str, root: str):
        if root is not None:
            self.nodes[node].discard(root)

        for id in self.nodes[node]:
            self.remove_root(id, node)

    def get_direct_management_relationship(self) -> List[List[bool]]:
        if self.direct_management_relationship is not None:
            return self.direct_management_relationship

        key_map = {k: i for i, k in enumerate(sorted(self.nodes.keys()))}
        N = len(key_map)
        self.direct_management_relationship = [[False] * N for _ in range(N)]

        for id1 in self.nodes:
            for id2 in self.nodes[id1]:
                self.direct_management_relationship[key_map[id1]][key_map[id2]] = True

        return self.direct_management_relationship

    def get_direct_subordination_relationship(self) -> List[List[bool]]:
        if self.direct_subordination_relationship is not None:
            return self.direct_subordination_relationship

        # Транспонируем матрицу управления
        self.direct_subordination_relationship = transpose(copy.deepcopy(self.get_direct_management_relationship()))
        return self.direct_subordination_relationship

    def get_transitive_management_relationship(self) -> List[List[bool]]:
        if self.transitive_management_relationship is not None:
            return self.transitive_management_relationship

        result = copy.deepcopy(self.get_direct_management_relationship())
        power = copy.deepcopy(self.get_direct_management_relationship())
        N = len(result)
        for _ in range(N):
            result = bool_sum(result, power)
            power = bool_multiplication(power, self.get_direct_management_relationship())

        self.transitive_management_relationship = result
        return self.transitive_management_relationship

    def get_transitive_subordination_relationship(self) -> List[List[bool]]:
        if self.transitive_subordination_relationship is not None:
            return self.transitive_subordination_relationship

        # Транспонируем матрицу управления
        self.transitive_subordination_relationship = transpose(copy.deepcopy(self.get_transitive_management_relationship()))
        return self.transitive_subordination_relationship

    def get_single_level_subordination_matrix(self) -> List[List[bool]]:
        if self.single_level_subordination_matrix is not None:
            return self.single_level_subordination_matrix

        N = len(self.direct_management_relationship)
        self.single_level_subordination_matrix = [[False] * N for _ in range(N)]
        D = copy.deepcopy(self.get_direct_subordination_relationship())
        Dt = copy.deepcopy(self.get_direct_management_relationship())
        self.single_level_subordination_matrix = bool_multiplication(D, Dt)
        for k in range(N):
            self.single_level_subordination_matrix[k][k] = False

        return self.single_level_subordination_matrix


def main(s: str, e: str) -> Tuple[
    List[List[bool]],
    List[List[bool]],
    List[List[bool]],
    List[List[bool]],
    List[List[bool]]
]:
    g = graph(s, e)

    r1 = g.get_direct_management_relationship()
    r2 = g.get_direct_subordination_relationship()
    r3 = g.get_transitive_management_relationship()
    r4 = g.get_transitive_subordination_relationship()
    r5 = g.get_single_level_subordination_matrix()
    result: Tuple[List[List[bool]]] = (r1, r2, r3, r4, r5)

    print(result)

if __name__ == "__main__":
    main("1,2\n1,3\n3,4\n3,5\n5,6\n6,7", "1")