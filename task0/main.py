import csv

def main():
    with open('task2.csv', newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        nodes = set()
        rows = []
        for row in spamreader:
            nodes.update(list(map(int, row)))
            rows.append(row)

        my_matrix = [([0] * len(nodes)) for i in range(len(nodes))]
        for row in rows:
            left, right = list(map(int, row))
            my_matrix[left-1][right-1] = 1

    # print(f'{my_matrix}')
    return my_matrix



if __name__ == '__main__':

    main()
