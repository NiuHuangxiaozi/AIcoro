def quicksort(arr):
    """
    快速排序函数
    参数: arr - 待排序的列表
    返回: 排序后的列表
    """
    if len(arr) <= 1:
        return arr  # 基本情况：如果数组长度小于等于1，直接返回
    pivot = arr[len(arr) // 2]  # 选择中间元素作为基准点
    left = [x for x in arr if x < pivot]  # 所有小于基准的元素
    middle = [x for x in arr if x == pivot]  # 所有等于基准的元素
    right = [x for x in arr if x > pivot]  # 所有大于基准的元素
    return quicksort(left) + middle + quicksort(right)  # 递归排序并合并

if __name__ == "__main__":
    # 示例使用
    example_arr = [3, 6, 8, 10, 1, 2, 1]
    sorted_arr = quicksort(example_arr)
    print("Original array:", example_arr)
    print("Sorted array:", sorted_arr)