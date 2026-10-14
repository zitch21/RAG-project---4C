import argparse
from rag_engine import ResourceAllocationGraph
from cli_ui import RAGCliApp
from gui_simulator import launch_gui


def main() -> None:
    parser = argparse.ArgumentParser(
        description="OS Resource Allocation Graph (RAG) Project — CLI & GUI Simulator"
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Launch the interactive Command-Line Interface (CLI) mode",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the interactive Tkinter GUI Visual Simulator",
    )
    args = parser.parse_args()

    rag = ResourceAllocationGraph()

    if args.cli:
        RAGCliApp(rag).run()
    elif args.gui:
        launch_gui(rag)
    else:
        print("OS Resource Allocation Graph (RAG) Simulator")
        print("  1. Launch Interactive Visual GUI Simulator")
        print("  2. Launch Interactive CLI Mode")
        choice = input("Select mode (1 or 2, default 1): ").strip()
        if choice == "2":
            RAGCliApp(rag).run()
        else:
            launch_gui(rag)


if __name__ == "__main__":
    main()
