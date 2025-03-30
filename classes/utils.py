from time import time

def timer(func):
    def wrapper(*args, **kwargs):
        start = time()
        result = func(*args, **kwargs)
        end = time()
        
        if isinstance(result, tuple):
            return end - start, *result
        
        return end - start, result
    
    return wrapper