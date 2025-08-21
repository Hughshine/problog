import os
import subprocess
import argparse
import json

results = []
r = [1, 3, 4, 5, 6, 9]  # Final benchmark set
r = [7] # Example for testing a single benchmark

def parse_log_json(json_path, test_name, delta_file, consistency_status):
    """
    Parses a JSON log file to extract timing and other metrics for each stage.
    This version removes memory collection and adds specific metrics for the
    Forward Compilation stage, reading them from the nested 'info' object.
    """
    with open(json_path) as f:
        data = json.load(f)

    turn_data = {1: {}, 2: {}, 3: {}}
    turn_total = {}

    # Maps full stage names to their abbreviated versions
    stage_map = {
        "SEMINAIVE_FULL": "SEM",
        "PRUNING_FULL": "PRN",
        "FORWARD_COMPILATION_FULL": "FC",
        "WEIGHTED_MODEL_COUNTING_FULL": "WMC",
        "SEMINAIVE_INC": "SEM",
        "PRUNING_INC": "PRN",
        "FORWARD_COMPILATION_INC": "FC",
        "WEIGHTED_MODEL_COUNTING_INC": "WMC"
    }

    # Process each turn in the log data
    for turn in data["turns"]:
        t = int(turn["index"])
        turn_total[t] = turn.get("time_seconds")
        current_turn_data = {}
        for stage in turn.get("stages", []):
            stage_short_name = stage_map.get(stage["name"], stage["name"])
            # Collect special metrics for Forward Compilation
            if "FORWARD_COMPILATION" in stage["name"]:
                stage_info = stage.get("info", {})
                current_turn_data[stage_short_name] = (
                    stage.get("time_seconds"),
                    stage_info.get("reordering_runtime"),
                    stage_info.get("live_nodes")
                )
            else:
                # For other stages, only collect time
                current_turn_data[stage_short_name] = (stage.get("time_seconds"),)
        turn_data[t] = current_turn_data

    # Build the output row string
    row = f"{test_name:<5}{delta_file:<15}"
    for t in [1, 2, 3]:  # Corresponds to Full, Deletion, Insertion turns
        row += f"{turn_total.get(t):>11.3f}" if turn_total.get(t) is not None else f"{'N/A':>11}"
        for s in ["SEM", "PRN", "FC", "WMC"]:
            val = turn_data.get(t, {}).get(s)
            if not val:
                # If stage data is missing, fill with N/A placeholders
                if s == "FC":
                    # FC has 3 columns: time, reorder_runtime, live_nodes
                    row += f"{'N/A':>11}{'N/A':>15}{'N/A':>11}"
                else:
                    # Other stages have 1 column: time
                    row += f"{'N/A':>11}"
                continue

            # Add time for the current stage
            time_str = f"{val[0]:.3f}" if val[0] is not None else "N/A"
            row += f"{time_str:>11}"

            # If it's the FC stage, add the extra collected metrics
            if s == "FC":
                # Convert reordering_runtime to float if it's a string
                reorder_val = val[1]
                if reorder_val is not None:
                    try:
                        reorder_val = float(reorder_val)
                        reorder_str = f"{reorder_val:.3f}"
                    except (ValueError, TypeError):
                        reorder_str = "N/A"
                else:
                    reorder_str = "N/A"

                nodes_str = f"{val[2]}" if len(val) > 2 and val[2] is not None else "N/A"
                row += f"{reorder_str:>15}{nodes_str:>11}"

    row += f"{consistency_status:>10}"
    return row

def check_prob_file_consistency(output_dir, tolerance=1e-6):
    """
    Compares two probability output files to check for consistency.
    """
    file1 = os.path.join(output_dir, "facts.prob")
    file2 = os.path.join(output_dir, "fact-inc.prob")
    if not (os.path.exists(file1) and os.path.exists(file2)):
        print(f"[!] Skipped: missing one of {file1} or {file2}")
        return "N/A"

    def parse_prob_lines(filepath):
        result = {}
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if not line or ':' not in line:
                    continue
                key, prob = line.split(':')
                result[key.strip()] = float(prob.strip())
        return result

    data1 = parse_prob_lines(file1)
    data2 = parse_prob_lines(file2)
    keys1 = set(data1.keys())
    keys2 = set(data2.keys())
    all_keys = sorted(keys1.union(keys2))

    differences = []
    for key in all_keys:
        p1 = data1.get(key)
        p2 = data2.get(key)
        if p1 is None:
            differences.append(f"   + {key} : {p2}  (only in fact-inc.prob)")
        elif p2 is None:
            differences.append(f"   - {key} : {p1}  (only in facts.prob)")
        elif abs(p1 - p2) > tolerance:
            differences.append(f"   ≠ {key} : {p1} vs {p2}  (Δ = {abs(p1 - p2):.2e})")

    if differences:
        print(f"[✗] Inconsistency detected in {output_dir}:")
        for diff in differences:
            print(diff)
        return "Fail"
    else:
        print(f"[✓] Consistency passed for {output_dir}")
        return "Pass"

def run_delta_commands(bench_root, souffle_exec="compute"):
    """
    Runs the benchmark for each delta file in the specified directories.
    """
    for i in r:
        bench_dir = os.path.join(bench_root, f"P{i}")
        test_name = f"P{i}"
        delta_dir = os.path.join(bench_dir, "delta")
        _souffle_exec = os.path.realpath(os.path.join(bench_dir, souffle_exec))

        if not os.path.isdir(delta_dir):
            continue

        print(f"[INFO] Processing {bench_dir}...")
        for fname in sorted(os.listdir(delta_dir)):
            if not fname.startswith("inc") or not fname.endswith(".txt"):
                continue
            delta_file = os.path.join(delta_dir, fname)
            print(f"  [✓] Running {fname}")
            try:
                log_prefix = f"log_{test_name}_{os.path.splitext(fname)[0]}"
                result = subprocess.run(
                    [_souffle_exec, "--logfile", log_prefix],
                    input=open(delta_file, 'r').read(),
                    text=True,
                    cwd=bench_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                if result.stderr:
                    print(f"    stderr: {result.stderr[:200]}")

                output_dir = os.path.join(bench_root, f"P{i}", "output")
                consistency_status = check_prob_file_consistency(output_dir)

            except Exception as e:
                print(f"    [!] Error: {e}")
                continue

            matching_logs = [f for f in os.listdir(bench_dir)
                             if f.startswith(log_prefix) and f.endswith(".json")]
            if not matching_logs:
                print(f"    [!] JSON log not found for {fname}")
                continue
            latest_log = max(matching_logs, key=lambda x: os.path.getmtime(os.path.join(bench_dir, x)))
            log_path = os.path.join(bench_dir, latest_log)

            try:
                row = parse_log_json(log_path, test_name, fname, consistency_status)
                results.append(row)
            except Exception as e:
                print(f"    [!] Failed to parse JSON log: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Benchmark root directory")
    parser.add_argument("--exec", default="compute", help="Soufflé executable name or path")
    args = parser.parse_args()

    try:
        run_delta_commands(args.root, args.exec)
    except KeyboardInterrupt:
        print("Interrupted, saving results...")
    finally:
        # Define the new header for the output file
        header = (
            f"{'Test':<5}{'Delta':<15}"
            # Turn 1: Full
            f"{'FullTotal':>11}"
            f"{'FullSEM':>11}{'FullPRN':>11}"
            f"{'FullFC':>11}{'FullFC_Reorder':>15}{'FullFC_Nodes':>11}"
            f"{'FullWMC':>11}"
            # Turn 2: Deletion
            f"{'DelTotal':>11}"
            f"{'DelSEM':>11}{'DelPRN':>11}"
            f"{'DelFC':>11}{'DelFC_Reorder':>15}{'DelFC_Nodes':>11}"
            f"{'DelWMC':>11}"
            # Turn 3: Insertion
            f"{'InsTotal':>11}"
            f"{'InsSEM':>11}{'InsPRN':>11}"
            f"{'InsFC':>11}{'InsFC_Reorder':>15}{'InsFC_Nodes':>11}"
            f"{'InsWMC':>11}"
            # Consistency Check
            f"{'Consistent':>10}"
        )
        with open("delta_results.txt", "w") as out:
            out.write(header + "\n")
            for row in results:
                out.write(row + "\n")
        print("Results saved to delta_results.txt")
