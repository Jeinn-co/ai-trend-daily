"""Run one full pipeline round locally: python scripts/run_local.py [--skip-llm] [--out DIR]

Needs ANTHROPIC_API_KEY in the environment unless --skip-llm is given.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from pipeline.build import main  # noqa: E402

main()
