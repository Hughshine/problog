"""
ProbLog command-line interface.

Copyright 2015 KU Leuven, DTAI Research Group

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import stat
import sys
import traceback
import json
import psutil

from .. import get_evaluatable, get_evaluatables, library_paths
from ..engine import DefaultEngine
from ..errors import process_error
from ..evaluator import SemiringLogProbability, SemiringProbability, SemiringSymbolic
from ..program import PrologFile, SimpleProgram
from ..util import (
    Timer,
    start_timer,
    stop_timer,
    init_logger,
    format_dictionary,
    format_value,
)
from ..version import version as problog_version


def get_memory_mb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def print_result(d, output, debug=False, precision=8):
    """Pretty print result.

    :param d: result from run_problog
    :param output: output file
    :param precision:
    :return:
    """
    success, d = d
    if success:
        print(format_dictionary(d, precision), file=output)
        return 0
    else:
        print(process_error(d, debug=debug), file=output)
        return 1


def print_result_prolog(d, output, debug=False, precision=8):
    success, d = d
    if success:
        for k, v in d.items():
            print("problog_result(%s, %s)." % (k, v), file=output)
        return 0
    else:
        print(process_error(d, debug=debug), file=output)
        return 1


def print_result_json(d, output, precision=8):
    """Pretty print result.

    :param d: result from run_problog
    :param output: output file
    :param precision:
    :return:
    """
    import json

    result = {}
    success, d = d
    if success:
        result["SUCCESS"] = True
        result["probs"] = [
            [str(n), format_value(p, precision), n.loc[1], n.loc[2]]
            for n, p in d.items()
        ]
    else:
        result["SUCCESS"] = False
        result["err"] = vars(d)
        result["err"]["message"] = str(process_error(d))
    print(json.dumps(result), file=output)
    return 0


def execute(
    filename,
    knowledge=None,
    semiring=None,
    combine=False,
    profile=False,
    trace=False,
    timer=None,
    **kwdargs
):
    """Run ProbLog with detailed phase profiling."""
    try:
        if timer is None:
            timer = Timer()
        if combine:
            timer.start_phase("Load model")
            model = SimpleProgram()
            for i, fn in enumerate(filename):
                filemodel = PrologFile(fn)
                for line in filemodel:
                    model += line
                if i == 0:
                    model.source_root = filemodel.source_root
            timer.end_phase()
        else:
            timer.start_phase("Load model")
            model = PrologFile(filename)
            timer.end_phase()
        if profile or trace:
            from problog.debug import EngineTracer
            profiler = EngineTracer(keep_trace=trace)
            kwdargs["debugger"] = profiler
        else:
            profiler = None
        timer.start_phase("Prepare engine")
        engine = DefaultEngine(**kwdargs)
        db = engine.prepare(model)
        timer.end_phase()
        timer.start_phase("Semiring setup")
        db_semiring = db.get_data("semiring")
        if db_semiring is not None:
            semiring = db_semiring
        timer.end_phase()
        timer.start_phase("Knowledge compilation")
        if knowledge is None or type(knowledge) == str:
            knowledge = get_evaluatable(knowledge, semiring=semiring)
        formula = knowledge.create_from(db, engine=engine, database=db, **kwdargs)
        timer.end_phase()
        timer.start_phase("Evaluation")
        result = formula.evaluate(semiring=semiring, **kwdargs)
        timer.end_phase()
        # Update location information on result terms
        for n, p in result.items():
            if not n.location or not n.location[0]:
                n.loc = model.lineno(n.location)
        if profiler is not None:
            if trace:
                print(profiler.show_trace())
            if profile:
                print(profiler.show_profile(kwdargs.get("profile_level", 0)))
        return True, result
    except KeyboardInterrupt as err:
        trace = traceback.format_exc()
        err.trace = trace
        return False, err
    except SystemError as err:
        trace = traceback.format_exc()
        err.trace = trace
        return False, err
    except Exception as err:
        trace = traceback.format_exc()
        err.trace = trace
        return False, err


def argparser():
    """Create the default argument parser for ProbLog.
    :return: argument parser
    :rtype: argparse.ArgumentParser
    """
    import argparse

    class InputFile(str):
        """Stub class for file input arguments."""

        pass

    class OutputFile(str):
        """Stub class for file output arguments."""

        pass

    description = f"""ProbLog {problog_version} command line interface

    The arguments listed below are for the default mode.
    ProbLog also supports the following alternative modes:

      - (default): inference
      - bn: export program to Bayesian network (see bn --help)
      - install: run the installer
      - dt: decision theoretic ProbLog (see dt --help)
      - explain: compute the probability of a query and explain how to get there
      - ground: generate ground program (see ground --help)
      - lfi: learn parameters from data (see lfi --help)
      - mpe: most probable explanation (see mpe --help)
      - map: maximum a posteriori (see map --help)
      - sample: generate samples from the model (see sample --help)
      - unittest: run the testsuite

    Select a mode by adding one of these keywords as first argument (e.g. problog-cli.py install).
    """

    parser = argparse.ArgumentParser(
        description=description, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("filenames", metavar="MODEL", nargs="*", type=InputFile)
    parser.add_argument("--verbose", "-v", action="count", help="Verbose output")
    parser.add_argument(
        "--knowledge",
        "-k",
        dest="koption",
        choices=get_evaluatables(),
        default=None,
        help="Knowledge compilation tool.",
    )
    parser.add_argument(
        "--combine", help="Combine input files into single model.", action="store_true"
    )
    # parser.add_argument('--grounder', choices=['yap', 'default', 'yap_debug'], default=None)

    # Evaluation semiring
    ls_group = parser.add_mutually_exclusive_group()
    ls_group.add_argument(
        "--logspace",
        action="store_true",
        help="Use log space evaluation (default).",
        default=True,
    )
    ls_group.add_argument(
        "--nologspace",
        dest="logspace",
        action="store_false",
        help="Use normal space evaluation.",
    )
    ls_group.add_argument(
        "--symbolic",
        dest="symbolic",
        action="store_true",
        help="Use symbolic computations.",
    )

    parser.add_argument(
        "--output", "-o", help="Output file (default stdout)", type=OutputFile
    )
    parser.add_argument(
        "--recursion-limit",
        help="Set Python recursion limit. (default: %d)" % sys.getrecursionlimit(),
        default=sys.getrecursionlimit(),
        type=int,
    )
    parser.add_argument(
        "--timeout",
        "-t",
        type=int,
        default=0,
        help="Set timeout (in seconds, default=off).",
    )
    parser.add_argument(
        "--compile-timeout",
        type=int,
        default=0,
        help="Set timeout for compilation (in seconds, default=off).",
    )
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Enable debug mode (print full errors).",
    )
    parser.add_argument("--full-trace", "-T", action="store_true", help="Full tracing.")
    parser.add_argument("--web", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "-a",
        "--arg",
        dest="args",
        action="append",
        help="Pass additional arguments to the cmd_args builtin.",
    )
    parser.add_argument("--profile", action="store_true", help="output runtime profile")
    parser.add_argument("--trace", action="store_true", help="output runtime trace")
    parser.add_argument("--profile-level", type=int, default=0)
    parser.add_argument("--format", choices=["text", "prolog"])
    parser.add_argument(
        "-L", "--library", action="append", help="Add to ProbLog library search path"
    )
    parser.add_argument(
        "--profiling-out",
        help="Output profiling information to a file (json or txt format).",
        type=str,
    )

    # Additional arguments (passed through)
    parser.add_argument("--engine-debug", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--propagate-evidence",
        action="store_true",
        dest="propagate_evidence",
        default=True,
        help="Enable evidence propagation",
    )
    parser.add_argument(
        "--dont-propagate-evidence",
        action="store_false",
        dest="propagate_evidence",
        default=False,
        help="Disable evidence propagation",
    )
    parser.add_argument(
        "--propagate-weights",
        action="store_true",
        default=None,
        help="Enable weight propagation",
    )
    parser.add_argument(
        "--convergence",
        "-c",
        type=float,
        default=argparse.SUPPRESS,
        help="stop anytime when bounds are within this range",
    )
    parser.add_argument(
        "--unbuffered",
        "-u",
        action="store_true",
        default=argparse.SUPPRESS,
        help=argparse.SUPPRESS,
    )

    # SDD garbage collection
    sdd_auto_gc_group = parser.add_mutually_exclusive_group()
    sdd_auto_gc_group.add_argument(
        "--sdd-auto-gc",
        action="store_true",
        dest="sdd_auto_gc",
        default=argparse.SUPPRESS,
        help=argparse.SUPPRESS,
    )
    sdd_auto_gc_group.add_argument(
        "--sdd-no-auto-gc",
        action="store_false",
        dest="sdd_auto_gc",
        default=argparse.SUPPRESS,
        help=argparse.SUPPRESS,
    )

    sdd_fixvars_group = parser.add_mutually_exclusive_group()
    sdd_fixvars_group.add_argument(
        "--sdd-preset-variables",
        action="store_true",
        dest="sdd_preset_variables",
        default=argparse.SUPPRESS,
        help=argparse.SUPPRESS,
    )
    sdd_fixvars_group.add_argument(
        "--sdd-no-preset-variables",
        action="store_false",
        dest="sdd_preset_variables",
        default=argparse.SUPPRESS,
        help=argparse.SUPPRESS,
    )

    return parser


def main_result(argv):
    """ Equivalent to the main method, but it returns the result rather than success/failure. """
    return main(argv, result_handler=lambda result, output: result)


def main(argv, result_handler=None):
    parser = argparser()
    args = parser.parse_args(argv)

    if args.library:
        for path in args.library:
            library_paths.append(path)

    if result_handler is None:
        if args.web:
            result_handler = print_result_json
        elif args.format == "prolog":
            result_handler = lambda *a: print_result_prolog(*a, debug=args.debug)
        else:
            result_handler = lambda *a: print_result(*a, debug=args.debug)

    init_logger(args.verbose)

    if args.output is None:
        output = sys.stdout
    else:
        output = open(args.output, "w")

    if args.timeout:
        start_timer(args.timeout)

    if len(args.filenames) == 0:
        mode = os.fstat(0).st_mode
        if stat.S_ISFIFO(mode) or stat.S_ISREG(mode):
            args.filenames = ["-"]
        else:
            print("ERROR: Expected a file or stream as input.\n", file=sys.stderr)
            parser.print_help()
            sys.exit(1)

    if args.logspace:
        semiring = SemiringLogProbability()
    else:
        semiring = SemiringProbability()

    if args.symbolic:
        args.koption = "nnf"
        semiring = SemiringSymbolic()

    if args.propagate_weights:
        args.propagate_weights = semiring

    # --- Profiling logic ---
    profiling_out = getattr(args, 'profiling_out', None)
    timer = Timer()
    retcode = 0
    result = None
    if args.combine:
        timer.start_phase("Total execution")
        result = execute(args.filenames, args.koption, semiring, timer=timer, **vars(args))
        timer.end_phase()
        retcode = result_handler(result, output)
    else:
        for filename in args.filenames:
            if len(args.filenames) > 1:
                print("Results for %s:" % filename)
            timer.start_phase("Total execution")
            result = execute(filename, args.koption, semiring, timer=timer, **vars(args))
            timer.end_phase()
            retcode = result_handler(result, output)

    if args.output is not None:
        output.close()

    if profiling_out:
        timer.dump(profiling_out)

    if args.timeout:
        stop_timer()
    return retcode


if __name__ == "__main__":
    main(sys.argv[1:])
