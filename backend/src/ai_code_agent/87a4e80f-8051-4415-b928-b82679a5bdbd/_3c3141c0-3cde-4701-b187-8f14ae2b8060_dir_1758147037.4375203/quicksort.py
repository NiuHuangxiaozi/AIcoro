def quicksort(arr):
    """
    Sorts an array using the QuickSort algorithm.
    
    Parameters:
    arr (list): The list to be sorted.
    
    Returns:
    list: The sorted list.
    """
    # Base case: if the array has 1 or 0 elements, it is already sorted
    if len(arr) <= 1:
        return arr
    
    # Choose the middle element as pivot
    pivot = arr[len(arr) // 2]
    
    # Partition the array into elements less than, equal to, and greater than the pivot
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    # Recursively sort the left and right partitions and combine with the middle
    return quicksort(left) + middle + quicksort(right)

# Example usage (commented out to avoid execution when imported)
# if __name__ == "__main__":
#     example_arr = [3, 6, 8, 10, 1, 2, 1]
#     sorted_arr = quicksort(example_arr)
#     print("Sorted array:", sorted_arr)