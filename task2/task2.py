from typing import List, Tuple, Set, DefaultDict
from collections import defaultdict
import copy
import math


def transpose(A: List[List[bool]]) -> List[List[bool]]:
    """
    Транспонирование квадратной булевой матрицы A (in-place для переданного списка).

    Важно: функция меняет матрицу A на месте (так как result = A).
    Если нужен вариант без изменения исходной матрицы — передавайте copy.deepcopy(A).
    """
    result = A
    for i, _ in enumerate(result):
        for j, _ in enumerate(result[i]):
            # меняем местами элементы ниже главной диагонали с элементами выше диагонали
            if i > j:
                result[i][j], result[j][i] = result[j][i], result[i][j]
    return result


def bool_multiplication(A: List[List[bool]], B: List[List[bool]]) -> List[List[bool]]:
    """
    Булево умножение матриц (композиция отношений).

    (A ∘ B)[i][j] = OR_k ( A[i][k] AND B[k][j] )

    Используется для нахождения транзитивного замыкания отношения:
    R^2 = R ∘ R, R^3 = R^2 ∘ R, ...
    """
    result = copy.deepcopy(A)
    N = len(A)
    for i in range(N):
        for j in range(N):
            result[i][j] = False
            for k in range(N):
                result[i][j] |= A[i][k] and B[k][j]
    return result


def bool_sum(A: List[List[bool]], B: List[List[bool]]) -> List[List[bool]]:
    """
    Булева сумма матриц (объединение отношений).

    (A ∪ B)[i][j] = A[i][j] OR B[i][j]

    Важно: функция меняет A на месте (так как result = A).
    """
    result = A
    N = len(A)
    for i in range(N):
        for j in range(N):
            result[i][j] |= B[i][j]
    return result


class graph:
    """
    Граф оргструктуры (дерево/ориентированная структура после удаления "родителя").

    Входные ребра задаются как "a,b" построчно. Изначально ребра добавляются в обе стороны
    (как неориентированные), затем выполняется remove_root, которая превращает структуру
    в "направленное дерево" от root (удаляется ссылка обратно на родителя при обходе).

    После remove_root для каждой вершины node в self.nodes[node] лежит множество её "детей"
    (т.е. тех, кем она непосредственно управляет).
    """

    def __init__(self, data: str, root: str):
        """
        data: строки вида "u,v\\n u,w\\n ..."
        root: корневая вершина (верхний руководитель)
        """
        self.root = root

        # список смежности: node -> set(neighbors)
        self.nodes: DefaultDict[str, Set[str]] = defaultdict(set)

        # кеши матриц отношений (чтобы не пересчитывать многократно)
        self.direct_management_relationship = None
        self.direct_subordination_relationship = None
        self.transitive_management_relationship = None
        self.transitive_subordination_relationship = None
        self.single_level_subordination_matrix = None

        # читаем пары "a,b" и добавляем ребро в обе стороны
        for pair in list(map(str, data.split('\n'))):
            self.append_edge(tuple(pair.split(',')))

        # удаляем "обратные" ребра к родителю, получая иерархию от root вниз
        self.remove_root(root, None)

        # отладочная печать
        #print(self)

    def __str__(self) -> str:
        return f'root: {self.root}, nodes: {self.nodes}\n'

    def append_edge(self, edge: Tuple[str, str]):
        """
        Добавление ребра между двумя вершинами.
        На этом этапе граф хранится как неориентированный.
        """
        self.nodes[edge[0]].add(edge[1])
        self.nodes[edge[1]].add(edge[0])

    def remove_root(self, node: str, root: str):
        """
        Рекурсивный обход, который удаляет ссылку на родителя root из множества соседей node.

        Идея:
          - из неориентированного графа делаем ориентированную иерархию от корня:
            у каждого узла остаются только "дети", родитель выкидывается.
        """
        if root is not None:
            self.nodes[node].discard(root)

        # важно: после discard(root) в self.nodes[node] остаются дети
        for child_id in self.nodes[node]:
            self.remove_root(child_id, node)

    def get_direct_management_relationship(self) -> List[List[bool]]:
        """
        Матрица прямого управления R1.

        R1[i][j] = True, если i непосредственно управляет j (j — ребёнок i).

        Индексация вершин задаётся сортировкой ключей self.nodes.
        """
        if self.direct_management_relationship is not None:
            return self.direct_management_relationship

        # отображение: id_вершины -> индекс в матрице
        key_map = {k: i for i, k in enumerate(sorted(self.nodes.keys()))}
        N = len(key_map)

        self.direct_management_relationship = [[False] * N for _ in range(N)]

        for id1 in self.nodes:
            for id2 in self.nodes[id1]:
                self.direct_management_relationship[key_map[id1]][key_map[id2]] = True

        return self.direct_management_relationship

    def get_direct_subordination_relationship(self) -> List[List[bool]]:
        """
        Матрица прямого подчинения R2.

        Это просто транспонирование матрицы управления:
          R2 = R1^T

        R2[i][j] = True, если i непосредственно подчинён j.
        """
        if self.direct_subordination_relationship is not None:
            return self.direct_subordination_relationship

        # транспонируем копию, чтобы не испортить исходную матрицу управления
        self.direct_subordination_relationship = transpose(
            copy.deepcopy(self.get_direct_management_relationship())
        )
        return self.direct_subordination_relationship

    def get_transitive_management_relationship(self) -> List[List[bool]]:
        """
        Матрица транзитивного управления R3 (транзитивное замыкание).

        R3[i][j] = True, если i управляет j напрямую или через цепочку подчинения.

        Вычисление идёт через суммирование степеней отношения:
          R ∪ R^2 ∪ ... ∪ R^N
        где произведение — булева композиция.
        """
        if self.transitive_management_relationship is not None:
            return self.transitive_management_relationship

        result = copy.deepcopy(self.get_direct_management_relationship())  # накопление (R ∪ R^2 ∪ ...)
        power = copy.deepcopy(self.get_direct_management_relationship())   # текущая степень R^k
        N = len(result)

        for _ in range(N):
            result = bool_sum(result, power)
            power = bool_multiplication(power, self.get_direct_management_relationship())

        self.transitive_management_relationship = result
        return self.transitive_management_relationship

    def get_transitive_subordination_relationship(self) -> List[List[bool]]:
        """
        Матрица транзитивного подчинения R4.

        Аналогично прямому случаю:
          R4 = (R3)^T
        """
        if self.transitive_subordination_relationship is not None:
            return self.transitive_subordination_relationship

        self.transitive_subordination_relationship = transpose(
            copy.deepcopy(self.get_transitive_management_relationship())
        )
        return self.transitive_subordination_relationship

    def get_single_level_subordination_matrix(self) -> List[List[bool]]:
        """
        Матрица "одноуровневого подчинения" R5.

        В коде вычисляется как:
          R5 = D ∘ Dt
        где:
          D  = R2 (прямое подчинение)
          Dt = R1 (прямое управление)

        Это даёт отношение между вершинами, которые находятся на одном уровне иерархии
        (имеют общего непосредственного руководителя) — т.е. условные "коллеги".

        Затем на диагонали принудительно ставим False (вершина не соотносится сама с собой).
        """
        if self.single_level_subordination_matrix is not None:
            return self.single_level_subordination_matrix

        # важно: direct_management_relationship может быть None, поэтому корректнее брать через getter
        N = len(self.get_direct_management_relationship())
        self.single_level_subordination_matrix = [[False] * N for _ in range(N)]

        D = copy.deepcopy(self.get_direct_subordination_relationship())   # R2
        Dt = copy.deepcopy(self.get_direct_management_relationship())     # R1

        self.single_level_subordination_matrix = bool_multiplication(D, Dt)

        # убираем диагональ
        for k in range(N):
            self.single_level_subordination_matrix[k][k] = False

        return self.single_level_subordination_matrix


def main(s: str, e: str) -> Tuple[float, float]:
    """
    Основная функция:
      s — описание рёбер (строка вида "1,2\\n1,3\\n...")
      e — корень (например, "1")

    Возвращает кортеж из 5 матриц:
      r1 — прямое управление
      r2 — прямое подчинение
      r3 — транзитивное управление (замыкание)
      r4 — транзитивное подчинение (замыкание)
      r5 — одноуровневое подчинение (одинаковый руководитель)
    """
    g = graph(s, e)

    r1 = g.get_direct_management_relationship()
    r2 = g.get_direct_subordination_relationship()
    r3 = g.get_transitive_management_relationship()
    r4 = g.get_transitive_subordination_relationship()
    r5 = g.get_single_level_subordination_matrix()
    
    semiresult: Tuple[List[List[bool]], List[List[bool]], List[List[bool]], List[List[bool]], List[List[bool]]] = (
        r1, r2, r3, r4, r5)

    # Расчёт количества исходящих связей
    connections: List[List[int]] = []
    for relation in semiresult:
        level_sums: List[int] = []
        for row in relation:
            level_sums.append(sum(row))
        
        connections.append(level_sums)
            
    for i, value in enumerate(connections[2]):
        connections[2][i] -= connections[0][i]
        connections[3][i] -= connections[1][i]

    #print(connections)
    
    # Вероятности и частичные энтропии и суммарная энтропия  
    max_connections = float(len(connections[0])-1)
    partial_entropies: List[List[float]] = []
    entropy_sum = 0
    for relations in connections:
        level_partial_entropies: List[float] = []
        for relation in relations:
            p = float(relation) / max_connections
            h_element = 0 if p == 0 else -p * math.log(p, 2)
            level_partial_entropies.append(h_element)
            entropy_sum += h_element
        
        partial_entropies.append(level_partial_entropies)
    
    #print(partial_entropies)
    #print(entropy_sum)
    
    # Нормализация по эталонной мере
    h_ref = float(len(connections[0]) * 5) * 0.5307 # c = 1 / (e*ln2)
    h = entropy_sum / h_ref
    
    return (round(entropy_sum, 1), round(h, 1))


if __name__ == "__main__":
    # пример запуска
    print(main("1,2\n1,3\n3,4\n3,5", "1"))