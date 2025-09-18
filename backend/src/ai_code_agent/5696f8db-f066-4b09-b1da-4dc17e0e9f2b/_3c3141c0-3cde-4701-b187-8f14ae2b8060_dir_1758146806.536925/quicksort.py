# QuickSort Algorithm Implementation

def quicksort(arr):
    """
    Sorts an array using the QuickSort algorithm.
    Parameters:
    arr (list): The list to be sorted.
    Returns:
    list: The sorted list.
    """
    # Base case: arrays with 0 or 1 element are already sorted
    if len(arr) <= 1:
        return arr
    # Select the pivot element (middle element)
    pivot = arr[len(arr) // 2]
    # Partition the array into elements less than, equal to, and greater than the pivot
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    # Recursively apply quicksort to left and right partitions and combine
    return quicksort(left) + middle + quicksort(right)

# Note: This implementation uses list comprehensions for simplicity and is not in-place.
# For in-place sorting, a different approach with partitioning would be needed.