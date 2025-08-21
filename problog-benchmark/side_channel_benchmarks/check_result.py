import os
import argparse
import re
from pathlib import Path

'''
python check_outputs.py --check [all|problog|souffle]
python check_outputs.py --dir /path/to/benchmark --check all
python check_outputs.py --dir /path/to/single/output --check problog --single
'''

def parse_prob_file(filepath, ignore_zero=True):
    """Parse a .prob file and return a dict of key -> probability (as float)"""
    prob_dict = {}
    with open(filepath, 'r') as f:
        for line in f:
            if 'using vtree:' in line:
                continue
            match = re.match(r'\s*([^\s:]+)\s*:\s*([0-9.eE+-]+)', line)
            if match:
                key, prob = match.group(1).strip().lower(), float(match.group(2))
                if ignore_zero and prob == 0:
                    continue
                prob_dict[key] = prob
    return prob_dict


def compare_prob_dicts_verbose(base, target, tolerance=1e-6):
    """Compare two dicts with float values. Return (equal, mismatch_report)."""
    mismatches = []
    base_keys = set(base.keys())
    target_keys = set(target.keys())

    only_in_base = base_keys - target_keys
    only_in_target = target_keys - base_keys
    common_keys = base_keys & target_keys

    for k in only_in_base:
        mismatches.append(f"  - Present in base only: {k}")
    for k in only_in_target:
        mismatches.append(f"  - Present in target only: {k}")
    for k in common_keys:
        if abs(base[k] - target[k]) > tolerance:
            mismatches.append(f"  - Probability mismatch for {k}: base={base[k]:.8f}, target={target[k]:.8f}")

    return len(mismatches) == 0, mismatches


def check_problog_outputs_single(output_dir: Path):
    reprs = ['sdd', 'fsdd', 'bdd', 'fbdd', 'ddnnf', 'kbest']
    sdd_file = output_dir / 'problog.sdd.prob'
    if not sdd_file.exists():
        print(f'[problog] SKIP: {sdd_file} not found')
        return
    base_probs = parse_prob_file(sdd_file)

    for r in reprs:
        file_path = output_dir / f'problog.{r}.prob'
        if not file_path.exists():
            print(f'[problog] {r.upper()}: FILE NOT FOUND')
            continue
        test_probs = parse_prob_file(file_path)
        equal, report = compare_prob_dicts_verbose(base_probs, test_probs)
        if equal:
            print(f'[problog] {r.upper()}: OK')
        else:
            print(f'[problog] {r.upper()}: MISMATCH')
            for line in report:
                print(f'    {line}')


def check_facts_vs_sdd_single(output_dir: Path):
    sdd_file = output_dir / 'problog.sdd.prob'
    facts_file = output_dir / 'facts.prob'
    if not sdd_file.exists():
        print('[souffle] SKIP: problog.sdd.prob not found')
        return
    if not facts_file.exists():
        print('[souffle] SKIP: facts.prob not found')
        return
    sdd_probs = parse_prob_file(sdd_file)
    facts_probs = parse_prob_file(facts_file)
    equal, report = compare_prob_dicts_verbose(sdd_probs, facts_probs)
    if equal:
        print('[souffle] FACTS: OK')
    else:
        print('[souffle] FACTS: MISMATCH')
        for line in report:
            print(f'    {line}')


def run_on_all_cases(base_dir: Path, check_type: str):
    for i in range(1, 20):
        if i == 2:
            continue
        output_dir = base_dir / f'P{i}' / 'output'
        print(f'\n=== Checking P{i} ===')
        if check_type in ('problog', 'all'):
            check_problog_outputs_single(output_dir)
        if check_type in ('souffle', 'all'):
            check_facts_vs_sdd_single(output_dir)


def main():
    parser = argparse.ArgumentParser(description='Check consistency of probabilistic output files.')
    parser.add_argument('--dir', type=str, default='.', help='Base directory or output directory')
    parser.add_argument('--check', type=str, choices=['problog', 'souffle', 'all'], default='all',
                        help='Check type: problog (reprs), souffle (facts), or all')
    parser.add_argument('--single', action='store_true', help='Interpret --dir as a single output directory')
    args = parser.parse_args()

    base_path = Path(args.dir)

    if args.single:
        if args.check in ('problog', 'all'):
            check_problog_outputs_single(base_path)
        if args.check in ('souffle', 'all'):
            check_facts_vs_sdd_single(base_path)
    else:
        run_on_all_cases(base_path, args.check)


if __name__ == '__main__':
    main()
