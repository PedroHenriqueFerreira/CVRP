from time import time

def timer(func):
    def wrapper(*args, **kwargs):
        start = time()
        result = func(*args, **kwargs)
        end = time()
        
        interval = end - start
        
        if isinstance(result, tuple):
            return interval, *result
        
        return interval, result
    
    return wrapper