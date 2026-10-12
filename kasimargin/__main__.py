import argparse
import json
from pathlib import Path
from .engine import ContractError
from .jsonio import loads
from .ollama import MODELS
from .receipts import save, verify
from .workflow import decision


def main():
    parser = argparse.ArgumentParser(description="KasiMargin: separate estimated margin from conditional cash headroom")
    parser.add_argument("input", type=Path, nargs="?", help="synthetic fixture wrapper or raw request JSON")
    parser.add_argument("--model", choices=MODELS, help="request locally installed Gemma; never downloads weights")
    parser.add_argument("--save", action="store_true", help="explicitly save a receipt in local-data/decisions")
    parser.add_argument("--data-class", choices=("SYNTHETIC", "OPERATOR_ATTESTED"))
    parser.add_argument("--verify", type=Path, help="reproduce a receipt without model inference")
    parser.add_argument("--serve", action="store_true", help="start the local browser demo on 127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    try:
        if args.serve:
            if args.input or args.verify or args.save or args.model or args.data_class:
                raise ContractError("--serve cannot be combined with input, receipt or model flags")
            from .server import serve
            serve(args.port)
            return
        if args.verify:
            if args.input or args.model or args.save or args.data_class:
                raise ContractError("--verify cannot be combined with input or decision flags")
            result = verify(args.verify)
        else:
            if args.input is None:
                raise ContractError("provide an input file, --serve or --verify")
            value = loads(args.input.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ContractError("input must be an object")
            request = value["input"] if "input" in value else value
            result = decision(request, args.model)
            if args.save:
                data_class = args.data_class or value.get("data_class")
                if data_class is None:
                    raise ContractError("saving a raw request requires --data-class")
                result["receipt_path"] = str(save(request, result, data_class, Path("local-data/decisions")))
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
    except (ContractError, ValueError, KeyError, OSError, TypeError) as exc:
        parser.exit(2, f"Input rejected: {exc}\n")


if __name__ == "__main__":
    main()
