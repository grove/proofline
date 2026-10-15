# Distinct option doesn't work with a small size of file

When and an input file is small enough to fit in a single chunk, distinct option doesn't remove duplicated items.

The reason seems because ExternalMergeSort#mergeSortedChunksNoPartialMerge(List<File> sortedChunks)   doesn't honor config.distinct as you see below.

        if (sortedChunks.size() == 1) {
            File sortedChunk = sortedChunks.get(0);
            return new ChunkFile<T>(sortedChunk, serializer, comparator, config.cleanup);
        } else {
            List<ChunkFile<T>> cfs = new ArrayList<ChunkFile<T>>(sortedChunks.size());
            for  (File file : sortedChunks) {
                cfs.add(new ChunkFile<T>(file, serializer, comparator, config.cleanup));
            }
            return new MergeSortedIterator<T,ChunkFile<T>>(cfs, comparator, config.distinct);
        }

It works fine if you eliminate the above optimizing if-true section.
