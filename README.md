# webdataset_jsonliterators
This repository provides a drop-in replacement for [`webdataset.tariterators`](https://github.com/webdataset/webdataset) that supports reading JSON Lines (.jsonl) files as data shards.

## Overview

- **`jsonl_iterators.py`** contains functions to:
  - Open URL streams of `.jsonl` files.
  - Iterate over them.
  - Yield samples from each line in the JSON Lines file.

- **Core usage**: `jsonlfile_to_samples` is a pipeline filter that can be used in place of the default file reader in WebDataset. It leverages the same pipeline approach (just like `wds.tarfile_to_samples`) but for `.jsonl` files instead of TAR files.

## Installation

1. Make sure you have [WebDataset](https://github.com/webdataset/webdataset) installed:
   ```bash
   pip install webdataset
   ```

2. Clone or download this repository. Make sure `jsonl_iterators.py` is accessible in your Python path (e.g., in the same working directory or installed as a local package).

3. Import the functions in your project.

## Usage

Below is an example that demonstrates how to use `jsonlfile_to_samples` in a pipeline. This example also shows how to set up a data loader with WebDataset that processes multiple `.jsonl` shards.

```python
import webdataset as wds
from webdataset.handlers import ignore_and_continue

# import the jsonl reader
from jsonl_iterators import jsonlfile_to_samples

if __name__ == '__main__':
    # Replace these with your actual URLs for .jsonl files
    urls = [
        "https://path/to/your_file_000.jsonl",
        "https://path/to/your_file_001.jsonl",
        "https://path/to/your_file_002.jsonl"
    ]
    
    local_batch_size = 32   # Example: batch size for each worker
    total_steps = 1000      # Example: total steps for the dataset
    transform_fn = lambda x: x  # Example: your data transform function
    handler = ignore_and_continue
    num_workers = 4         # Example: number of workers for data loading

    # Build a DataPipeline
    dataset = wds.DataPipeline(
        wds.SimpleShardList(urls),              # generate list of shards
        wds.shuffle(100),                       # shuffle shard order
        wds.split_by_node,                      # for distributed training (optional)
        wds.split_by_worker,                    # for multi-process reading
        jsonlfile_to_samples(handler=handler),  # <-- drop-in replacement for reading .jsonl
        wds.shuffle(1000),                      # shuffle samples within a shard
        wds.map(transform_fn, handler=handler),
        wds.batched(local_batch_size)
    )
    # Optionally specify an artificial length for the dataset
    dataset = dataset.with_length(total_steps)

    # Create a WebLoader
    data_loader = wds.WebLoader(dataset, batch_size=None, num_workers=num_workers)

    # Example loop
    for batch in data_loader:
        # process your batch here
        print(batch)
```

### Explanation

1. **`urls`**: A list of URLs or local paths to your `.jsonl` shards.
2. **`jsonlfile_to_samples`**: The key part—this replaces `wds.tarfile_to_samples` or other built-in file readers. Under the hood, it:
   - Opens each `.jsonl` file (shard).
   - Iterates over each JSON line.
   - Yields each line (converted to a dictionary) as a separate sample.
3. **Pipeline** steps:
   - **`wds.SimpleShardList(urls)`**: enumerates the list of `.jsonl` shards.
   - **`wds.shuffle(100)`**: shuffles the order of shards.
   - **`wds.split_by_node`** / **`wds.split_by_worker`**: for distributed data loading across nodes and workers.
   - **`jsonlfile_to_samples`**: expands `.jsonl` files into sample streams.
   - **`wds.shuffle(1000)`**: optional sample-level shuffle buffer.
   - **`wds.map(transform_fn)`**: apply your transform function to each sample.
   - **`wds.batched(local_batch_size)`**: group samples into batches.
4. **`dataset.with_length(total_steps)`** (optional): artificially set the length for the dataset.
5. **`wds.WebLoader(dataset, batch_size=None, num_workers=num_workers)`**: Creates a wds.WebLoader instance for iterating over data in seperate worker processes. 
   - Here `batch_size=None` is used because we already batched in the pipeline via `wds.batched`.
