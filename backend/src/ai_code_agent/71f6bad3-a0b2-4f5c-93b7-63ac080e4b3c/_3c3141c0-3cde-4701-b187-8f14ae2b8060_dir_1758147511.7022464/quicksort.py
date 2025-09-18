# 快速排序实现

def quicksort(arr):
    # 如果数组长度小于等于1，直接返回
    if len(arr) <= 1:
        return arr
    # 选择中间元素作为基准
    pivot = arr[len(arr) // 2]
    # 分区：小于基准、等于基准、大于基准
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    # 递归排序并合并
    return quicksort(left) + middle + quicksort(right)

# 示例用法
if __name__ == "__main__":
    example_arr = [3, 6, 8, 10, 1, 2, 1]
    print("Original array:", example_arr)
    sorted_arr = quicksort(example_arr)
    print("Sorted array:", sorted_arr)
