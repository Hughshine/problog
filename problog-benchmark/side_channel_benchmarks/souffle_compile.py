import os
import subprocess
import argparse
from pathlib import Path
from multiprocessing import Pool, cpu_count

# allow parallel souffle jobs, like -j4
def run_souffle_in_folder(folder: str):
    print(f"[{folder}] Starting...")
    command_template = [
        "souffle",
        "--online",
        "-F./input",
        "-D./output",
        "compute.souffle.dl",
        "-o",
        "compute"
    ]
    
    try:
        original_dir = os.getcwd()
        os.chdir(folder)

        result = subprocess.run(command_template,
                                check=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True)

        output = f"[{folder}] Output:\n{result.stdout}"
        if result.stderr:
            output += f"\n[{folder}] Errors:\n{result.stderr}"
    except subprocess.CalledProcessError as e:
        output = f"[{folder}] Command failed: {e}"
    except FileNotFoundError:
        output = f"[{folder}] Folder not found."
    except Exception as e:
        output = f"[{folder}] Unexpected error: {e}"
    finally:
        os.chdir(original_dir)
    
    return output

def main():
    parser = argparse.ArgumentParser(description="Run Soufflé on multiple folders concurrently.")
    parser.add_argument("-j", type=int, default=1, help="Number of parallel jobs (default 1)")
    args = parser.parse_args()

    jobs = max(1, args.j)
    max_jobs = cpu_count()
    if jobs > max_jobs:
        print(f"Requested -j{jobs}, but only {max_jobs} CPUs available. Using -j{max_jobs}.")
        jobs = max_jobs

    # defaultly we omit those larger benchmarks that full compilation cannot finish in time (for both problog and souffle)
    folders = [f"P{i}" for i in range(1, 10) if i != 2 and i != 8]
    
    print(f"Running Soufflé on {len(folders)} folders with {jobs} parallel jobs...\n")
    
    with Pool(processes=jobs) as pool:
        results = pool.map(run_souffle_in_folder, folders)

    for res in results:
        print(res)
        print("-" * 60)

if __name__ == "__main__":
    main()
