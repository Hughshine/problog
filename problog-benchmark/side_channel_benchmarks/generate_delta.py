import os
import random
import argparse
from collections import defaultdict
from pathlib import Path

def parse_facts(filepath):
    data = []
    with open(filepath, 'r') as f:
        for line in f:
            parts = line.strip().split('\t')
            if parts:
                data.append(tuple(parts))
    return data

def parse_prob(filepath):
    if not os.path.exists(filepath):
        return [1.0]
    with open(filepath, 'r') as f:
        probs = [float(line.strip()) for line in f if line.strip()]
    return probs or [1.0]

def generate_command_file(path, cmds, fact_probs):
    with open(path, 'w') as f:
        for cmd in cmds:
            f.write(cmd + '\n')
        f.write("commit\n")
        for idx, cmd in reversed(list(enumerate(cmds))):
            if cmd.startswith("insert"):
                f.write(cmd.replace("insert", "delete") + '\n')
            elif cmd.startswith("delete"):
                rel, rest = cmd[len("delete "):].split("(", 1)
                fact = rest.rstrip(")")
                prob = fact_probs.get((rel.strip(), fact.strip()), 1.0)
                f.write(f"insert {rel}({fact}) {prob}\n")
        f.write("commit\nq\n")

def weighted_choice(choices, weights):
    total = sum(weights)
    r = random.uniform(0, total)
    upto = 0
    for choice, weight in zip(choices, weights):
        if upto + weight >= r:
            return choice
        upto += weight
    return choices[-1]

def sample_not_in(domain):
    while True:
        n = random.randint(0, 100000000)  # or any large upper bound
        if str(n) not in domain:
            break
    return n

def generate_random_fact(existing_facts, domains, arity):
    for _ in range(100):
        fact = tuple(
            random.choice(domains[i]) if random.random() < 0.8 else str(sample_not_in(domains[i]))
            for i in range(arity)
        )
        if fact not in existing_facts:
            return fact
    return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Root benchmark directory")
    parser.add_argument("--sets", type=int, default=5, help="Number of delta sets per change size")
    args = parser.parse_args()

    change_ratios = [("1", 1), ("3", 0.03), ("5", 0.05), ("10", 0.10), ("20", 0.20)]

    for i in list(range(1, 20)):
        if i == 2:
            continue
        if i > 10:
            continue  # skip those cannot finish the full compilation
        bench_dir = os.path.join(args.root, f"P{i}")
        input_dir = os.path.join(bench_dir, "input")
        delta_dir = os.path.join(bench_dir, "delta")
        os.makedirs(delta_dir, exist_ok=True)

        relation_data = {}
        relation_probs = {}
        relation_domains = {}
        total_facts = 0

        for file in os.listdir(input_dir):
            if file.endswith(".facts"):
                rel = file[:-6]
                fact_path = os.path.join(input_dir, file)
                prob_path = os.path.join(input_dir, f"{rel}.prob")
                facts = parse_facts(fact_path)
                probs = parse_prob(prob_path)
                if not facts:
                    continue
                relation_data[rel] = facts
                relation_probs[rel] = probs
                total_facts += len(facts)

                domains = list(zip(*facts))
                relation_domains[rel] = [list(set(col)) for col in domains]

        if total_facts == 0:
            continue

        rels = list(relation_data.keys())
        rel_sizes = [len(relation_data[rel]) for rel in rels]

        for label, ratio in change_ratios:
            delta_N = max(1, int(total_facts * ratio) if isinstance(ratio, float) else ratio)
            for s in range(args.sets):
                cmds = []
                num_delete = delta_N
                fact_probs = {}

                # prepare deletion
                all_facts = [(rel, f) for rel in rels for f in relation_data[rel]]
                del_targets = random.sample(all_facts, min(num_delete, len(all_facts)))
                for rel, f in del_targets:
                    arglist = ', '.join(f)
                    cmds.append(f"delete {rel}({arglist})")
                    idx = relation_data[rel].index(f)
                    prob = relation_probs[rel][idx] if idx < len(relation_probs[rel]) else 1.0
                    fact_probs[(rel, arglist)] = prob

                suffix = f"_{s+1}" if args.sets > 1 else ""
                out_file = os.path.join(delta_dir, f"inc{label}{suffix}.txt")
                generate_command_file(out_file, cmds, fact_probs)
                print(f"[✓] Generated {out_file}")

if __name__ == "__main__":
    main()
