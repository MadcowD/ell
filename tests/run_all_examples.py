import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from colorama import Fore, Style, init
import argparse
import json
import hashlib
import fnmatch
import threading

# Initialize colorama for cross-platform colored output
init()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_arguments():
    parser = argparse.ArgumentParser(description="Run all example scripts in the examples directory and its subdirectories.")
    parser.add_argument("-d", "--directory", default="../examples", help="Root directory containing example scripts (default: ../examples)")
    parser.add_argument("-w", "--workers", type=int, default=4, help="Number of worker threads (default: 4)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--continue-on-error", action="store_true", help="Continue running examples even if one fails")
    parser.add_argument("--cache", action="store_true", help="Use caching to skip previously successful runs")
    return parser.parse_args()

def get_file_hash(file_path):
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def load_cache():
    cache_file = os.path.join(os.path.dirname(__file__), ".example_cache.json")
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    cache_file = os.path.join(os.path.dirname(__file__), ".example_cache.json")
    with open(cache_file, "w") as f:
        json.dump(cache, f)
        f.flush()
        os.fsync(f.fileno())

cache_lock = threading.Lock()

def update_cache(cache, file_hash, status, runtime):
    with cache_lock:
        cache[file_hash] = {"runtime": runtime, "status": status}
        save_cache(cache)

def run_example(example_path, verbose=False, cache=None):
    filename = os.path.basename(example_path)
    file_hash = get_file_hash(example_path)
    
    if cache and file_hash in cache:
        return filename, "CACHED", cache[file_hash]["runtime"], None, "Cached result"
    
    start_time = time.time()
    try:
        # Prepare simulated input based on the example file
        simulated_input = get_simulated_input(filename)
        
        # Run the example with simulated input
        process = subprocess.Popen(
            [sys.executable, example_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(input=simulated_input)
        
        end_time = time.time()
        runtime = end_time - start_time
        
        if cache is not None:
            update_cache(cache, file_hash, "SUCCESS", runtime)
        return filename, "SUCCESS", runtime, None, stdout
    except Exception as e:
        end_time = time.time()
        runtime = end_time - start_time
        if cache is not None:
            update_cache(cache, file_hash, "ERROR", runtime)
        return filename, "ERROR", runtime, str(e), ""

def get_simulated_input(filename):
    # Define simulated inputs for specific examples
    simulated_inputs = {
        "quick_chat.py": "Hello\nHow are you?\nGoodbye\n",
        "chord_progression_writer.py": "C major\n4\n",
        # Add more examples here as needed
    }
    
    return simulated_inputs.get(filename, "")

def load_ignore_patterns():
    ignore_file = os.path.join(os.path.dirname(__file__),  '.exampleignore')
    if os.path.exists(ignore_file):
        with open(ignore_file, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

def should_ignore(file_path, ignore_patterns):
    file_name = os.path.basename(file_path)
    return any(fnmatch.fnmatch(file_name, pattern) for pattern in ignore_patterns)

def get_all_example_files(root_dir, ignore_patterns):
    example_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.py') and not should_ignore(filename, ignore_patterns):
                example_files.append(os.path.join(dirpath, filename))
    return example_files

def run_all_examples(args):
    examples_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), args.directory))
    
    if not os.path.exists(examples_dir):
        logger.error(f"Examples directory not found at {examples_dir}")
        return

    logger.info(f"Running examples in {examples_dir} and its subdirectories")
    
    ignore_patterns = load_ignore_patterns()
    example_files = get_all_example_files(examples_dir, ignore_patterns)
    
    cache = load_cache() if args.cache else None
    
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {}
        for example_path in example_files:
            future = executor.submit(run_example, example_path, args.verbose, cache)
            futures[future] = os.path.relpath(example_path, examples_dir)
            print(f"{Fore.CYAN}Started: {futures[future]}{Style.RESET_ALL}")
        
        for future in as_completed(futures):
            filename, status, runtime, error, output = future.result()
            results.append((futures[future], status, runtime, error))
            print(f"{Fore.CYAN}Finished: {futures[future]}{Style.RESET_ALL}")
            if status == "SUCCESS":
                print(f"{Fore.GREEN}{futures[future]} . (Runtime: {runtime:.2f}s){Style.RESET_ALL}")
            elif status == "CACHED":
                print(f"{Fore.BLUE}{futures[future]} C (Cached Runtime: {runtime:.2f}s){Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}{futures[future]} F (Runtime: {runtime:.2f}s){Style.RESET_ALL}")
                print(f"  Error: {error}")
                print(f"  Full output:")
                print(output)
                if not args.continue_on_error:
                    print(f"\n{Fore.RED}Stopping execution due to failure.{Style.RESET_ALL}")
                    for running_future in futures:
                        if not running_future.done():
                            print(f"{Fore.YELLOW}Cancelling: {futures[running_future]}{Style.RESET_ALL}")
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

    if args.cache:
        save_cache(cache)

    print("\n--- Summary ---")
    total_examples = len(results)
    successful = sum(1 for _, status, _, _ in results if status in {"SUCCESS", "CACHED"})
    failed = sum(1 for _, status, _, _ in results if status == "ERROR")
    skipped = total_examples - successful - failed

    print(f"Total examples: {total_examples}")
    print(f"{Fore.GREEN}Successful: {successful}{Style.RESET_ALL}")
    print(f"{Fore.RED}Failed: {failed}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Skipped: {skipped}{Style.RESET_ALL}")

    if failed > 0:
        print("\nFailed examples:")
        for example, status, runtime, error in results:
            if status == "ERROR":
                print(f"{Fore.RED}{example} (Runtime: {runtime:.2f}s){Style.RESET_ALL}")
                print(f"  Error: {error}")

    average_runtime = sum(runtime for _, _, runtime, _ in results) / len(results)
    print(f"\nAverage runtime: {average_runtime:.2f}s")

    if all(status in {"SUCCESS", "CACHED"} for _, status, _, _ in results):
        print(f"\n{Fore.GREEN}All examples were successful.{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.YELLOW}Some examples did not run successfully. Please review the output above.{Style.RESET_ALL}")

if __name__ == "__main__":
    args = parse_arguments()
    run_all_examples(args)
