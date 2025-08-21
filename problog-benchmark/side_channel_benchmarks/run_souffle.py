import os
import subprocess
import time
import argparse

tests = [
    'P1',
    'P3',
    'P4',
    'P5',
    'P6',
    'P7',
    # 'P8',
    'P9',
    # 'P10',
    # 'P11',
    # 'P12',
    # 'P13',
    # 'P14',
    # 'P15',
    # 'P16',
    # 'P17',
    # 'P18',
    # 'P19'
]
def run_all_computes(root='.', reset=False):
    timeout = 5 * 60  # 15 minutes
    subdirs = tests
    tmp_file = "souffle_result.tmp"
    final_file = "souffle_result.txt"
    
    completed = set()
    results = []

    # 恢复临时文件状态
    if os.path.exists(tmp_file) and not reset:
        with open(tmp_file, "r") as f:
            for line in f:
                if line.strip() and not line.startswith("Directory"):
                    parts = line.split("\t")
                    if parts:
                        completed.add(parts[0])
            results = f.read().splitlines()
    else:
        results = ["Directory\tStatus\tRunning Time (s)\tOutput"]

    with open(tmp_file, "a") as f:  # 追加模式
        for subdir in subdirs:
            if subdir in completed:
                print(f"Skipping {subdir}, already completed.")
                continue

            compute_path = os.path.join(root, subdir, 'compute')
            print(f'Running {subdir}/compute...')
            start_time = time.time()

            if os.path.isfile(compute_path) and os.access(compute_path, os.X_OK):
                try:
                    result = subprocess.run(
                        ['./compute'],
                        cwd=os.path.join(root, subdir),
                        input='q\n',
                        timeout=timeout,
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    elapsed = time.time() - start_time
                    status = "Success"
                    output = result.stdout.strip().replace('\n', ' ')[:200]
                except subprocess.TimeoutExpired:
                    elapsed = float(timeout)
                    status = "Timeout"
                    output = f"Execution exceeded {timeout/60} minutes"
                except subprocess.CalledProcessError as e:
                    elapsed = time.time() - start_time
                    status = "Error"
                    output = e.stderr.strip().replace('\n', ' ')[:200]
            else:
                status = "Not Executable"
                elapsed = 0.0
                output = "Skipped or missing file"

            line = f"{subdir}\t{status}\t{elapsed:.3f}\t{output}"
            f.write(line + "\n")
            f.flush()
            print(f"{subdir}: {status} ({elapsed:.1f}s)")

    # 保存最终文件
    with open(tmp_file, "r") as f:
        final_content = f.read()
    with open(final_file, "w") as f:
        f.write(final_content)

    print(f"All results written to {final_file}.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--reset', action='store_true', help="Restart all cases from scratch")
    args = parser.parse_args()

    run_all_computes(reset=args.reset)
