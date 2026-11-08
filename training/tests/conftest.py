import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

RUNNER = Path(__file__).with_name("js_runner.js")


@pytest.fixture
def js():
    def calistir(gorev, metinler, **ek):
        girdi = json.dumps({"gorev": gorev, "metinler": metinler, **ek}, ensure_ascii=False)
        r = subprocess.run(["node", str(RUNNER)], input=girdi.encode(), capture_output=True, check=True)
        return json.loads(r.stdout)

    return calistir
