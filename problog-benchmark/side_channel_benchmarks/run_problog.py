#!/usr/bin/env python3

# python3 problog_eval.py
# # 或只跑特定组合
# python3 problog_eval.py --only P6:bdd P9:fsdd
import os
import subprocess
import time
import re
import glob
import argparse
import resource
import threading
import platform

# 所有支持的 knowledge 表示（不包括 sddx）
KNOWLEDGE_TYPES = ["sdd", "bdd", "ddnnf", "fsdd", "fbdd", "kbest"]

def run_problog_with_knowledge(file_path, knowledge):
    """
    使用指定 knowledge 模式运行 ProbLog，记录最大内存（MB）、运行时间和结果。
    支持 timeout 检测和 macOS/Linux 内存单位识别。
    """
    start_time = time.time()
    timeout = 30 * 60  # 30分钟

    command = ['problog', '--knowledge', knowledge, file_path]
    is_macos = platform.system() == 'Darwin'
    timeout_triggered = False

    try:
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # 超时杀进程
        def kill_proc():
            nonlocal timeout_triggered
            timeout_triggered = True
            try:
                proc.kill()
            except Exception:
                pass

        timer = threading.Timer(timeout, kill_proc)
        timer.start()

        # 等待子进程结束
        try:
            pid, status, rusage = os.wait4(proc.pid, 0)
            timer.cancel()
        except ChildProcessError:
            timer.cancel()
            return {
                'status': 'timeout',
                'output': f'Execution timed out after {timeout} seconds',
                'time': float(timeout)
            }

        stdout, stderr = proc.communicate()
        end_time = time.time()

        returncode = os.waitstatus_to_exitcode(status)
        raw_peak_mem = rusage.ru_maxrss

        # 单位转换
        if is_macos:
            peak_memory_mb = raw_peak_mem / (1024 * 1024)  # macOS: ru_maxrss in bytes
        else:
            peak_memory_mb = raw_peak_mem / 1024           # Linux: ru_maxrss in KB

        # 输出路径
        dict_path = os.path.join(os.path.dirname(file_path), "output")
        os.makedirs(dict_path, exist_ok=True)
        prob_path = os.path.join(dict_path, f'problog.{knowledge}.prob')
        with open(prob_path, 'w') as f:
            f.write(stdout)

        # 根据是否是 timer kill 判断结果
        if returncode == 0:
            return {
                'status': 'success',
                'output': stdout,
                'time': end_time - start_time,
                'peak_memory_mb': round(peak_memory_mb, 2)
            }
        elif timeout_triggered:
            return {
                'status': 'timeout',
                'output': f'Execution timed out after {timeout} seconds',
                'time': end_time - start_time,
                'peak_memory_mb': round(peak_memory_mb, 2)
            }
        else:
            return {
                'status': 'error',
                'output': stdout if stdout else stderr or "Unknown error",
                'time': end_time - start_time,
                'peak_memory_mb': round(peak_memory_mb, 2)
            }

    except Exception as e:
        return {
            'status': 'error',
            'output': f'Exception occurred: {str(e)}',
            'time': time.time() - start_time
        }


def parse_problog_output(output):
    """
    提取 ProbLog 输出中的有效查询结果
    """
    result_lines = []
    for line in output.split('\n'):
        if ':' in line and not line.startswith('WARNING') and not line.startswith('INFO'):
            result_lines.append(line.strip())
    return '\n'.join(result_lines)

def get_directory_number(directory):
    """
    提取目录名中的数字用于排序
    """
    match = re.match(r'P(\d+)', directory)
    if match:
        return int(match.group(1))
    return 0

def load_completed_results(results_file):
    """
    从已有结果文件中提取已完成的 (directory, knowledge) 组合
    """
    completed = set()
    if os.path.exists(results_file):
        with open(results_file, 'r') as f:
            for line in f:
                if line.startswith("Directory"):
                    continue
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    completed.add((parts[0], parts[1]))
    return completed

def parse_only_arguments(only_args):
    """
    将 --only 参数解析为 (directory, knowledge) 集合
    """
    only_set = set()
    for entry in only_args:
        if ':' in entry:
            directory, knowledge = entry.split(':', 1)
            only_set.add((directory.strip(), knowledge.strip()))
    return only_set

def main():
    parser = argparse.ArgumentParser(description="Evaluate ProbLog with various knowledge representations.")
    parser.add_argument('--only', nargs='*', help='Only run specific directory:knowledge pairs (e.g. P6:bdd)')
    parser.add_argument('--reset', action='store_true', help='Start fresh by deleting previous results')
    args = parser.parse_args()

    # 检查互斥参数
    if args.reset and args.only:
        print("Error: --reset and --only cannot be used together.")
        return

    results_file = "problog_results_all_knowledge.txt"
    if args.reset and os.path.exists(results_file):
        print("Reset mode: deleting existing results...")
        os.remove(results_file)

    only_mode = args.only is not None and len(args.only) > 0
    only_set = parse_only_arguments(args.only) if only_mode else None

    problog_files = glob.glob("P*/compute.problog.dl")
    sorted_files = sorted(problog_files, key=lambda x: get_directory_number(os.path.dirname(x)))
    results_file = "problog_results_all_knowledge.txt"

    completed_pairs = load_completed_results(results_file)
    mode = 'a' if os.path.exists(results_file) else 'w'
        
    with open(results_file, mode) as f:
        if mode == 'w':
            f.write("Directory\tKnowledge\tStatus\tRunning Time (s)\tOutput\n")

        for file_path in sorted_files:
            directory = os.path.dirname(file_path)
            dir_num = get_directory_number(directory)
            if dir_num == 2:
                continue  # 跳过 P2

            for knowledge in KNOWLEDGE_TYPES:
                pair = (directory, knowledge)

                if only_mode and pair not in only_set:
                    continue
                if not only_mode and pair in completed_pairs:
                    print(f"Skipping {pair} (already done)")
                    continue

                print(f"Running {directory} with knowledge={knowledge}")
                result = run_problog_with_knowledge(file_path, knowledge)
                print(result)
                if result['status'] == 'success':
                    output_content = parse_problog_output(result['output'])
                else:
                    output_content = result['output']

                f.write(f"{directory}\t{knowledge}\t{result['status']}\t{result['time']:.4f}\t{output_content.replace(chr(10), ' ')}\n")
                f.flush()
                print(f"  Status: {result['status']}, Time: {result['time']:.4f}s")
            print("----------------------------")

    print(f"Results written to {results_file}")

if __name__ == "__main__":
    main()