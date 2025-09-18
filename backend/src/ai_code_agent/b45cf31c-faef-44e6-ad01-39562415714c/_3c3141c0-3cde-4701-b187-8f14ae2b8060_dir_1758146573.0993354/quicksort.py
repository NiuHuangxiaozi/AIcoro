def quicksort(arr):
    """
    快速排序函数
    参数:
        arr: 列表，需要排序的数组
    返回:
        排序后的列表
    """
    # 如果数组长度小于等于1，直接返回
    if len(arr) <= 1:
        return arr
    # 选择基准元素，这里选择中间元素
    pivot = arr[len(arr) // 2]
    # 分区：小于基准的放左边，等于的放中间，大于的放右边
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    # 递归排序左右部分，并合并
    return quicksort(left) + middle + quicksort(right)

# 示例用法
if __name__ == "__main__":
    example_arr = [3, 6, 8, 10, 1, 2, 1]
    sorted_arr = quicksort(example_arr)
    print('原始数组:', example_arr)
    print('排序后数组:', sorted_arr)