"""Container entry point: start the Prometheus exporter, then Streamlit.

Starting the exporter first means ``/metrics`` is available as soon as the
container is up, before the first browser session executes ``app.py``.
Any extra command-line arguments are passed through to ``streamlit run``.
"""
import sys
from pathlib import Path

import telemetry

APP_FILE = Path(__file__).resolve().parent / "app.py"


def build_argv(extra_args):
    return ["streamlit", "run", str(APP_FILE), *extra_args]


def main(argv=None):
    extra_args = list(sys.argv[1:] if argv is None else argv)
    telemetry.start_metrics_server()
    from streamlit.web import cli as stcli

    sys.argv = build_argv(extra_args)
    return stcli.main()


if __name__ == "__main__":
    sys.exit(main())
