# 快速排序实现
# 使用递归方式，选择第一个元素作为pivot

def quicksort(arr):
    # 基线条件：如果数组为空或只有一个元素，直接返回
    if len(arr) <= 1:
        return arr
    
    # 选择pivot（这里选择第一个元素）
    pivot = arr[0]
    
    # 分区：创建左子数组（所有小于等于pivot的元素）和右子数组（所有大于pivot的元素）
    left = [x for x in arr[1:] if x <= pivot]
    right = [x for x in arr[1:] if x > pivot]
    
    # 递归排序左子和右子数组，然后合并结果
    return quicksort(left) + [pivot] + quicksort(right)

# 示例用法（注释掉，实际使用时取消注释）
# if __name__ == "__main__":
#     example_arr = [3, 6, 8, 10, 1, 2, 1]
#     sorted_arr = quicksort(example_arr)
#     print("Sorted array:", sorted_arr)