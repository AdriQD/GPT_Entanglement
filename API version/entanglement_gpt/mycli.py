import argparse

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="entangle" )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # entanglement synthesis run ...
    p_run = sub.add_parser("run", help="Run experiments")
    p_run.add_argument("--config", required=True)
    p_run.add_argument("--set", action="append", default=[], help="Override key=value")