import argparse

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="entangle")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # entangle run ...
    p_run = sub.add_parser("run", help="Run experiments")
    p_run.add_argument("--config", required=True)
    p_run.add_argument("--set", action="append", default=[], help="Override key=value")
    p_run.add_argument("--dry-run", action="store_true")

    # entangle analyze ...
    p_an = sub.add_parser("analyze", help="Aggregate runs")
    p_an.add_argument("--in", dest="in_dir", required=True)
    p_an.add_argument("--out", required=True)

    # entangle report ...
    p_rep = sub.add_parser("report", help="Generate report")
    p_rep.add_argument("--analysis", required=True)
    p_rep.add_argument("--out", required=True)
    p_rep.add_argument("--format", choices=["md"], default="md")

    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.cmd == "run":
        print("RUN", args.config, args.set, args.dry_run)
    elif args.cmd == "analyze":
        print("ANALYZE", args.in_dir, args.out)
    elif args.cmd == "report":
        print("REPORT", args.analysis, args.out, args.format)

if __name__ == "__main__":
    main()
