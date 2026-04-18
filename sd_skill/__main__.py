"""Allow `python -m sd_skill <cmd>` invocation."""
from sd_skill.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
