def retrieve_all_threads(checkpointer):
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config["configurable"]["thread_id"])  # type: ignore
    return list(all_threads)
