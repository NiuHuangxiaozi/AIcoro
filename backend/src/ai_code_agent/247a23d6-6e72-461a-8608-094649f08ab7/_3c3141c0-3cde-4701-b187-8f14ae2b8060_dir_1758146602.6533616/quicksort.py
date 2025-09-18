# Quick sort in-place implementation
def quicksort_inplace(arr, low=0, high=None):
    """
    Sorts the array in-place using quicksort algorithm.
    Args:
        arr: list to be sorted
        low: starting index, default 0
        high: ending index, default len(arr)-1
    """
    if high is None:
        high = len(arr) - 1
    if low < high:
        # partition the array and get the pivot index
        pi = partition(arr, low, high)
        # recursively sort elements before and after partition
        quicksort_inplace(arr, low, pi - 1)
        quicksort_inplace(arr, pi + 1, high)

def partition(arr, low, high):
    """
    Partitions the array around a pivot.
    Args:
        arr: list to partition
        low: starting index
        high: ending index
    Returns:
        index of the pivot after partition
    """
    pivot = arr[high]  # choose the last element as pivot
    i = low - 1  # index of smaller element
    for j in range(low, high):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]  # swap
    arr[i + 1], arr[high] = arr[high], arr[i + 1]  # place pivot in correct position
    return i + 1

# Example usage
if __name__ == "__main__":
    arr = [3, 6, 8, 10, 1, 2, 1]
    print("Original array:", arr)
    quicksort_inplace(arr)
    print("Sorted array:", arr)
