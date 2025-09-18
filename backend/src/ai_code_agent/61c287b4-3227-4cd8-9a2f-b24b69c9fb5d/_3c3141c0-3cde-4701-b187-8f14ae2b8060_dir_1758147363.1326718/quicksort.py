def quicksort(arr):
    """
    快速排序函数
    :param arr: 待排序的列表
    :return: 排序后的列表
    """
    # 如果数组长度小于等于1，直接返回
    if len(arr) <= 1:
        return arr
    # 选择基准元素，这里选择中间元素
    pivot = arr[len(arr) // 2]
    # 将数组分为三部分：小于基准、等于基准、大于基准
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    # 递归排序左右部分，并合并
    return quicksort(left) + middle + quicksort(right)

# 示例使用
if __name__ == "__main__":
    example_arr = [3, 6, 8, 10, 1, 2, 1]
    sorted_arr = quicksort(example_arr)
    print("Original array:", example_arr)
    print("Sorted array:", sorted_arr)