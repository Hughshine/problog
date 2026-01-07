# Update (profiling branch: Hughshine + faisalalsayyari)

Simple summary: this branch adds profiling support and evaluation tooling, improves engine behavior for edge cases, and refines CLI/util handling in ProbLog.

## Commits covered
- Hughshine: bdfd350 (2025-04-10) for empty relation; fc4cd6d (2025-04-22) fix fbdd; 02d8b04 (2025-04-23) upd kbest; eccb44b (2025-06-02) trivial; 3744ea4 (2025-06-02) trivial; c3d4fde (2025-07-16) silent fail by default, to support non-derivable queries; 7dd3241 (2025-10-05) dicard input fact's derivations; 95473b4 (2025-11-06) Merge pull request #1 from ML-KULeuven/master; c9af4e4 (2026-01-06) Fix CLI exit codes and flush Timer output
- faisalalsayyari: 84baae8 (2025-08-21) Add benchmark files (flattened); 69c9683 (2025-08-21) Add profiling script; 9f5c0a7 (2025-08-27) log plots for each phase, plotting with matplotlib

## Summary of changes (combined)
- Profiling instrumentation: problog/tasks/probability.py and problog/util.py add phase timing + memory tracking, new --profiling-out dumps JSON/txt; problog/forward.py and problog/bdd_formula.py add BDD stats helpers and per-iteration logging.
- Benchmark and plotting tooling: profiling.py runs side_channel_benchmarks across knowledge modes; plotting.py generates log-scale per-phase and total time/memory charts.
- Engine behavior tweaks: engine.py defaults to silent_fail=True for non-derivable queries and rebuilds formulas to drop derivations for input facts; engine_stack.py always skips unknown nodes; ClauseDB.is_fact helper added.
- CLI/util refinements: tasks/__init__.py normalizes exit codes; Timer prints now flush; kill_proc_tree ignores psutil.NoSuchProcess.
- Misc repo edits: test.pl cycled from tiny example to large generated model then a minimal placeholder; .vscode/launch.json added; sdd_formula.py vtree logging toggled off; formula.py whitespace tweak.
