# QuickSort implementation in Python
# 
# This code implements the QuickSort algorithm using a recursive approach.
# It chooses the middle element as the pivot for balanced partitioning.
# 
# Author: AI Assistant
# Date: Current date

def quicksort(arr):
    """
    Sorts an array using the QuickSort algorithm.
    
    Args:
        arr (list): The list of elements to be sorted. Can contain integers, floats, or other comparable types.
    
    Returns:
        list: The sorted list.
    
    Example:
        >>> quicksort([3, 1, 4, 1, 5])
        [1, 1, 3, 4, 5]
    """
    # Base case: if the array has 1 or 0 elements, it is already sorted
    if len(arr) <= 1:
        return arr
    
    # Choose the middle element as the pivot for better average performance
    pivot = arr[len(arr) // 2]
    
    # Partition the array into elements less than, equal to, and greater than the pivot
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    # Recursively sort the left and right partitions, then combine with the middle
    return quicksort(left) + middle + quicksort(right)

# Example usage for testing
if __name__ == "__main__":
    # Test with a sample array
    example_arr = [3, 6, 8, 10, 1, 2, 1]
    print("Original array:", example_arr)
    sorted_arr = quicksort(example_arr)
    print("Sorted array:", sorted_arr)
    # Expected output: Sorted array: [1, 1, 2, 3, 6, 8, 10]
