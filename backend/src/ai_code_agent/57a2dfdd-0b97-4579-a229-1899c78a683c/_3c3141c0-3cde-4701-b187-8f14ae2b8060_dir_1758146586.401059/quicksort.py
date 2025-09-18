def quicksort(arr):
    """
    Sorts an array using the quicksort algorithm.
    
    Parameters:
    arr (list): The list to be sorted.
    
    Returns:
    list: The sorted list.
    """
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)

# Example usage
if __name__ == "__main__":
    example_arr = [3, 6, 8, 10, 1, 2, 1]
    sorted_arr = quicksort(example_arr)
    print("Original array:", example_arr)
    print("Sorted array:", sorted_arr)