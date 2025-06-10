"""
Custom decorators for demo purposes.
"""

from typing import Callable


def simulate_failure(failure_count: int = 3) -> Callable:
    """
    Decorator that simulates failure for a specified number of times.

    Args:
        failure_count (int): Number of times the function should fail before succeeding

    Returns:
        Decorated function that will raise an exception for the first `failure_count` calls,
        then execute normally afterwards.
    """

    def decorator(func):
        call_count = 0

        def wrapper(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count <= failure_count:
                raise RuntimeError(
                    f"Simulated failure {call_count}/{failure_count} for function '{func.__name__}'"
                )

            return func(*args, **kwargs)

        # Preserve function metadata
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__

        return wrapper

    return decorator
