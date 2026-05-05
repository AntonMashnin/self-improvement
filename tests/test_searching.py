import pytest
from algorithms.searching import linear_search, binary_search


def test_linear_search_found():
    assert linear_search([1, 2, 3, 4, 5], 3) == 2


def test_linear_search_not_found():
    assert linear_search([1, 2, 3], 99) == -1


def test_linear_search_empty():
    assert linear_search([], 1) == -1


def test_linear_search_first():
    assert linear_search([7, 2, 3], 7) == 0


def test_binary_search_found():
    assert binary_search([1, 2, 3, 4, 5], 3) == 2


def test_binary_search_not_found():
    assert binary_search([1, 2, 3, 4, 5], 99) == -1


def test_binary_search_empty():
    assert binary_search([], 1) == -1


def test_binary_search_first():
    assert binary_search([1, 2, 3, 4, 5], 1) == 0


def test_binary_search_last():
    assert binary_search([1, 2, 3, 4, 5], 5) == 4
