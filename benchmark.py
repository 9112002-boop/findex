import time
import os
import psutil
from pathlib import Path
from findex.index import InvertedIndex, build_partial

def run_benchmark(executor_type: str, workers: int, files: list[Path]):
    num_workers = workers if workers > 0 else os.cpu_count() or 1
    chunk_size = (len(files) + num_workers - 1) // num_workers
    chunks = [files[i:i + chunk_size] for i in range(0, len(files), chunk_size)]
    process = psutil.Process(os.getpid())
    start_wall = time.perf_counter()
    start_cpu = time.process_time()
    partials = []
    if executor_type == "serial":
        for i, chunk in enumerate(chunks):
            partials.append(build_partial(chunk, start_doc_id=i * chunk_size))
    elif executor_type == "threads":
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=num_workers) as pool:
            futures = [pool.submit(build_partial, chunk, i * chunk_size) for i, chunk in enumerate(chunks)]
            partials = [f.result() for f in futures]
    elif executor_type == "processes":
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=num_workers) as pool:
            futures = [pool.submit(build_partial, chunk, i * chunk_size) for i, chunk in enumerate(chunks)]
            partials = [f.result() for f in futures]
    merge_start = time.perf_counter()
    final_index = InvertedIndex.merge(partials)
    merge_time = time.perf_counter() - merge_start
    end_wall = time.perf_counter()
    end_cpu = time.process_time()
    return {
        "executor": executor_type,
        "workers": num_workers,
        "wall": end_wall - start_wall,
        "cpu": end_cpu - start_cpu,
        "rss": process.memory_info().rss / (1024 * 1024),
        "merge": merge_time,
    }

if __name__ == "__main__":
    data_dir = Path("data")
    files = sorted(data_dir.glob("*.txt"))
    if not files:
        print("No files found.")
        exit(1)
    print(f"Benchmarking on {len(files)} files...")
    print(f"{'Executor':<10} | {'Workers':<7} | {'Wall (s)':<8} | {'CPU (s)':<8} | {'RSS (MB)':<8} | {'Merge (s)':<9}")
    print("-" * 70)
    for w in [1, 2, 4, 8, os.cpu_count()]:
        if w is None: continue
        res_serial = run_benchmark("serial", 1, files)
        print(f"{res_serial['executor']:<10} | {res_serial['workers']:<7} | {res_serial['wall']:<8.3f} | {res_serial['cpu']:<8.3f} | {res_serial['rss']:<8.1f} | {res_serial['merge']:<9.3f}")
        res_threads = run_benchmark("threads", w, files)
        print(f"{res_threads['executor']:<10} | {res_threads['workers']:<7} | {res_threads['wall']:<8.3f} | {res_threads['cpu']:<8.3f} | {res_threads['rss']:<8.1f} | {res_threads['merge']:<9.3f}")
        res_processes = run_benchmark("processes", w, files)
        print(f"{res_processes['executor']:<10} | {res_processes['workers']:<7} | {res_processes['wall']:<8.3f} | {res_processes['cpu']:<8.3f} | {res_processes['rss']:<8.1f} | {res_processes['merge']:<9.3f}")
        print("-" * 70)
