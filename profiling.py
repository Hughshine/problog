import os
import subprocess

BASE_DIR = "problog-benchmark/side_channel_benchmarks"
SKIP_DIRS = {"P2", "P8"}
PROBLOG_FILE = "compute.problog.dl"

COMPILATION_MODES = {
    "bdd": ["--knowledge", "bdd"],
    "sdd": ["--knowledge", "sdd"],
    "fbdd": ["--knowledge", "fbdd"],
    "fsdd": ["--knowledge", "fsdd"],
}

def run_benchmark():
    for i in range(1, 20):
        folder = f"P{i}"
        if folder in SKIP_DIRS:
            continue
        full_path = os.path.join(BASE_DIR, folder)
        input_file = os.path.join(full_path, PROBLOG_FILE)
        if not os.path.exists(input_file):
            print(f"Missing file in {folder}, skipping...")
            continue
        for mode_name, args in COMPILATION_MODES.items():
            print(f"Running {folder} in {mode_name} mode...")
            out_file = os.path.join(full_path, f"{mode_name}_profiling.json")
            command = [
                "python", "-m", "problog.tasks.probability", "--profiling-out", out_file,
                *args,
                input_file
            ]
            try:
                subprocess.run(command, timeout=60, check=True)
            except subprocess.TimeoutExpired:
                print(f"{folder} {mode_name} timed out.")
            except subprocess.CalledProcessError as e:
                print(f"Error running {folder} {mode_name}:\n{e}")

if __name__ == "__main__":
    run_benchmark()
