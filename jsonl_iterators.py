from typing import Any, Callable, Dict, Iterable, Optional, TextIO, Iterator
from webdataset import filters
from webdataset.handlers import reraise_exception
from webdataset.tariterators import url_opener
import json


def jsonlfile_samples(
    src: Iterable[Dict[str, Any]],
    handler: Callable[[Exception], bool] = reraise_exception
) -> Iterable[Dict[str, Any]]:
    """Generate samples from a stream of jsonl files.

    Args:
        src: Stream of jsonl files.
        handler: Exception handler.

    Returns:
        Stream of samples.
    """
    streams = url_opener(src, handler=handler)
    return jsonl_file_expander(streams, handler)



def jsonl_file_iterator(
    fileobj: TextIO,
    handler: Callable[[Exception], bool] = reraise_exception,
) -> Iterator[Dict[str, Any]]:
    """Iterate over jsonl file, yielding content for the given jsonl stream.

    Args:
        fileobj: the jsonl file stream.
        handler: exception handler. Defaults to reraise_exception.

    Yields:
        a stream of samples.
    """
    for i, jsonl_line in enumerate(fileobj):
        try:
            sample = json.loads(jsonl_line)
            if len(sample.keys()) == 0:
                continue
            sample["__key__"] = str(i)
            yield sample
        except Exception as exn:
            if handler(exn):
                continue
            else:
                break



def jsonl_file_expander(
    data: Iterable[Dict[str, Any]],
    handler: Callable[[Exception], bool] = reraise_exception,
    eof_value: Optional[Any] = {},
) -> Iterator[Dict[str, Any]]:
    """Expand jsonl files.

    Args:
        data: Iterator over opened tar file streams.
        handler: Exception handler.
        eof_value: Value to yield at the end of each shard.

    Yields:
        A stream of samples.
    """
    for source in data:
        url = source["url"]
        local_path = source.get("local_path")
        try:
            assert isinstance(source, dict)
            assert "stream" in source
            for sample in jsonl_file_iterator(
                source["stream"],
                handler=handler
            ):
                assert isinstance(sample, dict), f"sample is not a dict: {sample}"
                sample["__url__"] = url
                if local_path is not None:
                    sample["__local_path__"] = local_path
                yield sample
            # we yield an EOF marker at the end of each shard so that
            # samples from different shards don't get mixed up
            if eof_value is not None:
                yield eof_value
        except Exception as exn:
            exn.args = exn.args + (source.get("stream"), source.get("url"))
            if handler(exn):
                continue
            else:
                break


jsonlfile_to_samples = filters.pipelinefilter(jsonlfile_samples)
