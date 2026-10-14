import argparse
from rag_engine import ResourceAllocationGraph
from cli_ui import RAGCliApp
from gui_simulator import launch_gui


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Operating Systems Resource Allocation Graph (RAG) Simulator"
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Launch in Terminal / Command-Line Interface (CLI) mode",
    )
    args = parser.parse_args()

    rag = ResourceAllocationGraph()

    if args.cli:
        RAGCliApp(rag).run()
    else:
        launch_gui(rag)


if __name__ == "__main__":
    main()
