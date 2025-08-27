import os
import json
import matplotlib.pyplot as plt
import re

BENCHMARK_DIR = os.path.join(os.path.dirname(__file__), 'problog-benchmark', 'side_channel_benchmarks')
PLOTS_DIR = os.path.join(os.path.dirname(__file__), 'Plots')
os.makedirs(PLOTS_DIR, exist_ok=True)

KNOWLEDGE_REPS = ['bdd', 'fbdd', 'fsdd', 'sdd']

# Scrape all <knowledge>_profiling.json files for all P<N>
def collect_profiling_data():
    data = {}  # {phase: {knowledge: [values per P<N>]}}
    total_data = {k: [] for k in KNOWLEDGE_REPS}
    benchmarks = []
    # Find all P<N> folders
    for entry in sorted(os.listdir(BENCHMARK_DIR)):
        subdir = os.path.join(BENCHMARK_DIR, entry)
        if os.path.isdir(subdir) and entry.startswith('P'):
            benchmarks.append(entry)
            for krep in KNOWLEDGE_REPS:
                json_path = os.path.join(subdir, f'{krep}_profiling.json')
                if os.path.isfile(json_path):
                    with open(json_path) as f:
                        prof = json.load(f)
                    # Collect total time/mem
                    total_data[krep].append({
                        'benchmark': entry,
                        'time': prof['total']['time_s'],
                        'mem': prof['total']['end_mem_mb']
                    })
                    # Collect per-phase data
                    for phase in prof['phases']:
                        pname = phase['phase']
                        if pname is None:
                            continue
                        if pname not in data:
                            data[pname] = {k: [] for k in KNOWLEDGE_REPS}
                        data[pname][krep].append({
                            'benchmark': entry,
                            'time': phase['time_s'],
                            'mem': phase['delta_mem_mb']
                        })
                else:
                    # If missing, fill with zero
                    total_data[krep].append({'benchmark': entry, 'time': 0, 'mem': 0})
                    for pname in data:
                        data[pname][krep].append({'benchmark': entry, 'time': 0, 'mem': 0})
    # After collecting all phases, ensure every phase has a value for every benchmark/knowledge rep
    # Find all unique phase names
    all_phases = set(data.keys())
    for pname in all_phases:
        for krep in KNOWLEDGE_REPS:
            # If this phase/knowledge rep is missing for some benchmarks, pad with zeros
            missing = len(benchmarks) - len(data[pname][krep])
            if missing > 0:
                data[pname][krep].extend([{'benchmark': b, 'time': 0, 'mem': 0} for b in benchmarks[-missing:]])
    # Also, if a phase is missing entirely for a knowledge rep, create a zero-filled list
    for pname in all_phases:
        for krep in KNOWLEDGE_REPS:
            if krep not in data[pname]:
                data[pname][krep] = [{'benchmark': b, 'time': 0, 'mem': 0} for b in benchmarks]
    return benchmarks, data, total_data

def numeric_benchmark_sort(benchmarks):
    def extract_n(label):
        m = re.match(r'P(\d+)', label)
        return int(m.group(1)) if m else float('inf')
    return sorted(benchmarks, key=extract_n)

# Plot grouped bar chart for each phase comparing knowledge reps
def plot_phase_comparison(benchmarks, data):
    for phase, krep_data in data.items():
        fig, ax = plt.subplots(figsize=(10, 6))
        bar_width = 0.2
        x = range(len(benchmarks))
        for i, krep in enumerate(KNOWLEDGE_REPS):
            times = [d['time'] for d in krep_data[krep]]
            ax.bar([xi + i*bar_width for xi in x], times, width=bar_width, label=f'{krep.upper()}')
        ax.set_xticks([xi + bar_width*1.5 for xi in x])
        ax.set_xticklabels(benchmarks)
        ax.set_ylabel('Time (s)')
        ax.set_xlabel('Benchmark')
        ax.set_title(f'Phase: {phase} - Time Comparison')
        ax.set_yscale('log')  # <-- Make y-axis logarithmic
        ax.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(PLOTS_DIR, f'phase_{phase.replace(" ", "_").lower()}_time.png'))
        plt.close(fig)
        # Memory plot
        fig, ax = plt.subplots(figsize=(10, 6))
        for i, krep in enumerate(KNOWLEDGE_REPS):
            mems = [d['mem'] for d in krep_data[krep]]
            ax.bar([xi + i*bar_width for xi in x], mems, width=bar_width, label=f'{krep.upper()}')
        ax.set_xticks([xi + bar_width*1.5 for xi in x])
        ax.set_xticklabels(benchmarks)
        ax.set_ylabel('Memory (MB)')
        ax.set_xlabel('Benchmark')
        ax.set_title(f'Phase: {phase} - Memory Comparison')
        ax.set_yscale('log')  # <-- Make y-axis logarithmic
        ax.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(PLOTS_DIR, f'phase_{phase.replace(" ", "_").lower()}_mem.png'))
        plt.close(fig)

# Plot total time and memory for each knowledge rep across benchmarks
def plot_total_comparison(benchmarks, total_data):
    for krep in KNOWLEDGE_REPS:
        times = [d['time'] for d in total_data[krep]]
        mems = [d['mem'] for d in total_data[krep]]
        fig, ax1 = plt.subplots()
        ax1.plot(benchmarks, times, marker='o', label='Total Time (s)')
        ax1.set_ylabel('Time (s)')
        ax1.set_xlabel('Benchmark')
        ax1.set_yscale('log')  # <-- Make y-axis logarithmic
        ax2 = ax1.twinx()
        ax2.plot(benchmarks, mems, marker='s', color='orange', label='Total Memory (MB)')
        ax2.set_ylabel('Memory (MB)')
        ax2.set_yscale('log')  # <-- Make y-axis logarithmic
        plt.title(f'Total Time and Memory Usage - {krep.upper()}')
        fig.tight_layout()
        plt.savefig(os.path.join(PLOTS_DIR, f'total_time_memory_{krep}.png'))
        plt.close(fig)

if __name__ == '__main__':
    benchmarks, phase_data, total_data = collect_profiling_data()
    benchmarks = numeric_benchmark_sort(benchmarks)
    plot_phase_comparison(benchmarks, phase_data)
    plot_total_comparison(benchmarks, total_data)
    print(f'Plots saved to {PLOTS_DIR}')
