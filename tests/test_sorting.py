import pytest
from algorithms.sorting import bubble_sort, merge_sort, quick_sort


@pytest.mark.parametrize("sort_fn", [bubble_sort, merge_sort, quick_sort])
def test_sort_basic(sort_fn):
    assert sort_fn([3, 1, 2]) == [1, 2, 3]


@pytest.mark.parametrize("sort_fn", [bubble_sort, merge_sort, quick_sort])
def test_sort_empty(sort_fn):
    assert sort_fn([]) == []


@pytest.mark.parametrize("sort_fn", [bubble_sort, merge_sort, quick_sort])
def test_sort_single(sort_fn):
    assert sort_fn([42]) == [42]


@pytest.mark.parametrize("sort_fn", [bubble_sort, merge_sort, quick_sort])
def test_sort_duplicates(sort_fn):
    assert sort_fn([3, 1, 2, 1, 3]) == [1, 1, 2, 3, 3]


@pytest.mark.parametrize("sort_fn", [bubble_sort, merge_sort, quick_sort])
def test_sort_already_sorted(sort_fn):
    assert sort_fn([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]


@pytest.mark.parametrize("sort_fn", [bubble_sort, merge_sort, quick_sort])
def test_sort_reverse(sort_fn):
    assert sort_fn([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]
