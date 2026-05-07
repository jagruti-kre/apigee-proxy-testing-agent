import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def retry_with_exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    timeout: int = 30,
    fallback_response: str = "An error occurred. Please try again."
):
    """
    A decorator for retrying a function with exponential backoff.

    Args:
        max_retries (int): Maximum number of retry attempts.
        initial_delay (float): Initial delay in seconds before the first retry.
        backoff_factor (float): Factor by which the delay increases each time.
        timeout (int): Maximum time in seconds to wait for the function to complete.
        fallback_response (str): The response to return if all retries fail.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for i in range(max_retries + 1):
                try:
                    # Simulate a timeout mechanism if the function itself doesn't have one
                    # This is a basic approach; for true timeouts, consider `concurrent.futures`
                    # or `signal` module for Unix-like systems.
                    start_time = time.time()
                    result = func(*args, **kwargs)
                    if (time.time() - start_time) > timeout:
                        raise TimeoutError(f"Function {func.__name__} timed out after {timeout} seconds.")
                    return result
                except Exception as e:
                    logger.warning(f"Attempt {i+1}/{max_retries+1} failed for {func.__name__}: {e}")
                    if i < max_retries:
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(f"All {max_retries+1} attempts failed for {func.__name__}. Returning fallback response.")
                        return fallback_response
        return wrapper
    return decorator

# Example usage (not part of the project, just for illustration)
# @retry_with_exponential_backoff(max_retries=3, timeout=10)
# def unreliable_function():
#     import random
#     if random.random() < 0.7:
#         raise ValueError("Simulated failure")
#     return "Success!"