# MergeSortedIterator does not provider stable ordering

When multiple `ChunkFile`s contain values that compare equal, I would expect the `mergeSortedChunks` method to respect the order of the files in the `sortedChunks` parameter. Instead the `MergeSortedIterator` uses a `PriorityQueue` which does not guarantee a stable ordering.
