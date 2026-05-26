from typing import List, Callable, TypeVar

T = TypeVar("T")

def process_batch(items: List[T], batch_size: int, processor: Callable[[List[T]], None]):
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        processor(batch)
