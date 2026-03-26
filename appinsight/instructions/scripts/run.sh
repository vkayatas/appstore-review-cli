#!/bin/bash
# Wrapper for appstore-reviews CLI.
# Activates the project's virtual environment if needed, then runs the command.
# Usage: bash scripts/run.sh search "Slack"
#        bash scripts/run.sh reviews 618783545 --stars 2 --format text

# Activate venv if appstore-reviews is not already on PATH
if ! command -v appstore-reviews &>/dev/null; then
  for d in .venv venv env; do
    if [ -f "$d/bin/activate" ]; then
      source "$d/bin/activate"
      break
    fi
  done
fi

# Try the CLI entry point first, fall back to python module
if command -v appstore-reviews &>/dev/null; then
  appstore-reviews "$@"
elif python3 -m appinsight --help &>/dev/null 2>&1; then
  python3 -m appinsight "$@"
else
  echo "ERROR: appstore-review-cli is not installed in this environment." >&2
  echo "Ask the user to install it, then try again." >&2
  exit 1
fi
