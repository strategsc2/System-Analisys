from typing import List, Tuple, Set, DefaultDict
from collections import defaultdict
import sys
import copy
import json

# Определение функций принадлежности для температуры
T_FUNC = '''{
  "температура": [
      {
      "id": "холодно",
      "points": [
          [0,1],
          [18,1],
          [22,0],
          [50,0]
      ]
      },
      {
      "id": "комфортно",
      "points": [
          [18,0],
          [22,1],
          [24,1],
          [26,0]
      ]
      },
      {
      "id": "жарко",
      "points": [
          [0,0],
          [24,0],
          [26,1],
          [50,1]
      ]
      }
  ]
}'''

# Определение функций принадлежности для интенсивности нагрева
TERM_FUNC = '''{
  "температура": [
      {
        "id": "слабый",
        "points": [
            [0,0],
            [0,1],
            [5,1],
            [8,0]
        ]
      },
      {
        "id": "умеренный",
        "points": [
            [5,0],
            [8,1],
            [13,1],
            [16,0]
        ]
      },
      {
        "id": "интенсивный",
        "points": [
            [13,0],
            [18,1],
            [23,1],
            [26,0]
        ]
      }
  ]
}'''

# Правила нечеткого вывода
DIRECT_MAP = '''[
    ["холодно", "интенсивно"],
    ["нормально", "умеренно"],
    ["комфортно", "умеренно"],
    ["жарко", "слабо"]
]'''

def get_membership(x: float, points: List[List[float]]) -> float:
    """
    Вычисляет степень принадлежности точки x к нечеткому множеству.
    Использует линейную интерполяцию между заданными точками.

    :param x: Входное значение
    :param points: Опорные точки функции принадлежности
    :return: Значение принадлежности от 0.0 до 1.0
    """
    if not points:
        return 0.0

    # Сортировка точек по оси X
    points.sort(key=lambda p: p[0])

    # Проверка границ области определения
    if x < points[0][0] or x > points[-1][0]:
        return 0.0

    # Поиск отрезка, содержащего точку x
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i+1]

        if x1 <= x <= x2:
            # Обработка вертикального отрезка
            if x1 == x2:
                return max(y1, y2)

            # Линейная интерполяция
            slope = (y2 - y1) / (x2 - x1)
            y = y1 + slope * (x - x1)
            return y

    return 0.0

def get_trapezoid(level: float, points: List[List[float]]) -> List[List[float]]:
    """
    Вычисляет усеченную трапециевидную функцию принадлежности.
    Возвращает точки, лежащие на уровне level или ниже.

    :param level: Уровень активации (усечения)
    :param points: Исходные точки функции принадлежности
    :return: Усеченная функция в виде списка точек
    """
    trapezoid_points: List[List[float]] = []
    x0, y0 = points[0]

    # Начальная точка усечения
    if y0 > level:
        trapezoid_points.append([x0, level])

    # Построение усеченной функции
    for point in points:
        x1, y1 = point

        # Пересечение с уровнем активации
        if (y1 - level) * (y0 - level) < 0:
            # Вычисление точки пересечения
            y = level
            x = x1 + (y - y1) * (x0 - x1) / (y0 - y1)
            trapezoid_points.append([x, y])

        # Добавление точек ниже уровня активации
        if y1 <= level:
            trapezoid_points.append([x1, y1])

        # Обновление предыдущей точки
        x0, y0 = x1, y1

    # Конечная точка усечения
    if y1 > level:
        trapezoid_points.append([x0, level])

    return trapezoid_points


def main(
    temperature_mfs_json: str,
    heating_mfs_json: str,
    rules_json: str,
    temperature_value: float
) -> float:
    """
    Основная функция нечеткого вывода по Мамдани.

    :param temperature_mfs_json: Функции принадлежности для температуры (вход)
    :param heating_mfs_json: Функции принадлежности для нагрева (выход)
    :param rules_json: Правила нечеткого вывода
    :param temperature_value: Текущее значение температуры
    :return: Оптимальное управляющее воздействие
    """
    # 1. Парсинг входных данных
    input_mfs = json.loads(temperature_mfs_json)["температура"]
    output_mfs = json.loads(heating_mfs_json)["температура"]
    rules = json.loads(rules_json)

    # 2. Фаззификация - вычисление степеней принадлежности
    input_degrees = {}
    for element in input_mfs:
        term = element["id"]
        degree = get_membership(temperature_value, element["points"])
        input_degrees[term] = degree

    # 3. Применение правил нечеткого вывода
    # Определение уровней активации выходных термов
    output_levels = {}
    for input_term, output_term_raw in rules:
        # Приведение формы прилагательного
        output_term = (output_term_raw[:-1] + "ый") if output_term_raw[-1] == "о" else output_term_raw
        activation_level = input_degrees.get(input_term, 0.0)

        # Агрегация по правилу MAX (логическое ИЛИ)
        current_level = output_levels.get(output_term, 0.0)
        output_levels[output_term] = max(current_level, activation_level)

    # 4. Построение усеченных выходных функций
    activations: DefaultDict[str, List[List[float]]] = defaultdict(list)
    for element in output_mfs:
        term_id = element["id"]
        level = output_levels.get(term_id, 0.0)
        activations[term_id] = get_trapezoid(level, element["points"])

    # 5. Дефаззификация методом первого максимума
    left_max = []
    for term_id, point_list in activations.items():
        for point in point_list:
            if not left_max:
                left_max = copy.deepcopy(point)
            elif (left_max[1] < point[1]) or ((left_max[1] == point[1]) and (left_max[0] > point[0])):
                left_max[1] = point[1]
                left_max[0] = point[0]

    return left_max[0]


if __name__ == "__main__":
    # Пример использования с температурой 19 градусов
    print(main(T_FUNC, TERM_FUNC, DIRECT_MAP, 19))