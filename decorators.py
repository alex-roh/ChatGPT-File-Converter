# Decorators (TODO: Move to a separate file)
import functools

def log_function_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # print(f"Calling function {func.__name__} with args={args} and kwargs={kwargs}")
        print(f"Calling function {func.__name__}...")
        return func(*args, **kwargs)
    return wrapper