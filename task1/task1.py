def build_matrix(edges):
    matrix = {}
    
    def update_count(index, column):
        if index not in matrix:
            matrix[index] = [0, 0, 0, 0, 0]
        matrix[index][column] += 1
    
    for edge in edges:
        high, low = map(int, edge.split(','))
        high -= 1
        low -= 1
        
        update_count(high, 0)
        update_count(low, 1)

    for edge in edges:
        high, low = map(int, edge.split(','))
        high -= 1
        low -= 1
        
        matrix[high][2] += matrix[low][0]
        matrix[low][3] += matrix[high][1]
        matrix[low][4] += matrix[high][0] - 1

    return [matrix[i] for i in range(len(matrix))]

def task(edges_csv: str):
    edges = edges_csv.split('\n')
    matrix = build_matrix(edges)
    return matrix

if __name__ == "__main__":
    result = task("1,2\n2,3\n2,6\n3,4\n3,5\n6,7\n6,8")
    print(result)
