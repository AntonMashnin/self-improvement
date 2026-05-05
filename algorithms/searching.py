def linear_search(arr: list, target) -> int:
    for i, val in enumerate(arr):
        if val == target:
            return i
    return -1


def binary_search(arr: list, target) -> int:
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
