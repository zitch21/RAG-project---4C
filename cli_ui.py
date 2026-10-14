import sys
import time
from typing import List
from rag_engine import ResourceAllocationGraph


class RAGCliApp:
    def __init__(self, rag: ResourceAllocationGraph = None):
        self.rag = rag or ResourceAllocationGraph()

    def print_banner(self) -> None:
        print("=" * 78)
        print("   OPERATING SYSTEMS — RESOURCE ALLOCATION GRAPH (RAG) CLI SIMULATOR")
        print("=" * 78)

    def display_state(self) -> None:
        mode_label = (
            "AUTOMATIC (Auto-Grant Free Resources)"
            if self.rag.auto_grant
            else "MANUAL (Requests Stay P->R Until Granted)"
        )
        print(f"\n--- CURRENT RAG STATE [Allocation Mode: {mode_label}] ---")
        procs = sorted(self.rag.processes)
        res = sorted(self.rag.resources.keys())
        print(f"Processes ({len(procs)}): {', '.join(procs) if procs else 'None'}")

        if not res:
            print("Resources (0): None")
        else:
            res_summary = [
                f"{r} (Total: {self.rag.resources[r]}, Free: {self.rag.available_instances(r)})"
                for r in res
            ]
            print(f"Resources ({len(res)}): " + " | ".join(res_summary))

        print("\nAllocation Edges (Resource -> Process):")
        has_alloc = False
        for r in res:
            for p in procs:
                count = self.rag.allocations[r].get(p, 0)
                if count > 0:
                    has_alloc = True
                    print(f"  [ALLOCATED]  {r} ──({count})──> {p}")
        if not has_alloc:
            print("  (None)")

        print("\nRequest Edges (Process -> Resource):")
        has_req = False
        for p in procs:
            for r in res:
                count = self.rag.requests[p].get(r, 0)
                if count > 0:
                    has_req = True
                    print(f"  [WAITING]    {p} ──({count})──> {r}")
        if not has_req:
            print("  (None)")
        print("-" * 60)

    def run_deadlock_analysis(self) -> None:
        if not self.rag.processes and not self.rag.resources:
            print("\n>> Graph is currently empty. Add processes and resources first.")
            return

        result = self.rag.detect_deadlock()
        print("\n=== DEADLOCK DETECTION & GRAPH REDUCTION TRACE ===")
        for idx, step in enumerate(result["steps"], 1):
            print(f"  Step {idx}: {step}")

        cycles = result["cycles"]
        if cycles:
            print("\nDetected Cycles in Graph:")
            for c in cycles:
                print("  Cycle: " + " -> ".join(c))
        else:
            print("\nDetected Cycles in Graph: None")

        if result["deadlocked"]:
            print(
                f"\n[STATUS: DEADLOCKED] Deadlocked Processes: {', '.join(result['deadlocked_processes'])}"
            )
        else:
            print("\n[STATUS: SAFE] System is free from deadlock.")
        print("=" * 55)

    def execute_steps_interactive(self, steps: List[str]) -> None:
        if not steps:
            print(">> No simulation steps to run.")
            return

        print(f"\nQueued {len(steps)} simulation step(s):")
        for i, s in enumerate(steps, 1):
            print(f"  {i}. {s}")

        mode = input(
            "\nSelect Execution Mode — (A)utomatic Timed or (M)anual Step-by-Step [A/M]: "
        ).strip().upper()

        delay = 1.0
        if mode == "A":
            d_str = input("Enter delay in seconds between automatic steps: ").strip()
            try:
                delay = float(d_str) if d_str else 1.0
            except ValueError:
                delay = 1.0

        print("\n--- STARTING USER SIMULATION ---")
        for idx, cmd in enumerate(steps, 1):
            if mode != "A":
                user_in = input(
                    f"\n[Manual Step {idx}/{len(steps)}] Press ENTER to run '{cmd}' (or 'q' to stop): "
                ).strip().lower()
                if user_in == "q":
                    print(">> Simulation stopped by user.")
                    break
            else:
                print(f"\n[Auto Step {idx}/{len(steps)}] Executing: {cmd}")
                time.sleep(delay)

            _, msg = self.rag.execute_command(cmd)
            print(f"  Result: {msg}")
            res = self.rag.detect_deadlock()
            status = (
                f"DEADLOCKED ({', '.join(res['deadlocked_processes'])})"
                if res["deadlocked"]
                else "SAFE"
            )
            print(f"  Live Deadlock Monitor: {status}")

        print("\n--- SIMULATION COMPLETE ---")
        self.display_state()

    def run_custom_simulation_builder(self) -> None:
        print("\n=== CUSTOM SIMULATION BUILDER ===")
        print("How would you like to input your simulation?")
        print("  1. Guided Builder (Prompt for Processes, Resources, and Operations)")
        print("  2. Command Script Input (Type/paste commands directly)")
        print("  3. Load Script from a .txt File")
        sub = input("Select (1, 2, or 3): ").strip()

        steps: List[str] = []

        if sub == "1":
            clear_first = input("Clear current graph before starting? (y/n): ").strip().lower()
            if clear_first == "y":
                steps.append("CLEAR")

            p_in = input("Enter Process IDs separated by space or comma: ").strip()
            if p_in:
                steps.append(f"P {p_in}")

            r_in = input("Enter Resources as ID:Instances separated by space: ").strip()
            if r_in:
                steps.append(f"R {r_in}")

            print(
                "\nEnter your simulation operations one per line.\n"
                "Available operation formats:\n"
                "  REQ <PID> <RID> <COUNT>    (Process requests resource)\n"
                "  GRANT <PID> <RID> <COUNT>  (Manually grant pending request)\n"
                "  ALLOC <RID> <PID> <COUNT>  (Directly allocate resource to process)\n"
                "  REL <PID> <RID> <COUNT>    (Process releases resource)\n"
                "  CANCEL <PID> <RID>         (Cancel pending request)\n"
                "  MODE AUTO | MODE MANUAL    (Switch allocation mode)\n"
                "  CHECK                      (Run deadlock analysis)\n"
                "Type 'DONE' on a new line when finished:"
            )
            while True:
                line = input("  Operation > ").strip()
                if line.upper() == "DONE" or not line:
                    break
                steps.append(line)

        elif sub == "2":
            print(
                "\nType or paste commands (one per line, or separated by ';').\n"
                "Type 'DONE' on a new line when finished:"
            )
            lines = []
            while True:
                line = input("  Command > ").strip()
                if line.upper() == "DONE":
                    break
                lines.append(line)
            steps = self.rag.parse_simulation_script("\n".join(lines))

        elif sub == "3":
            filepath = input("Enter path to .txt script file to load: ").strip()
            ok, msg, content = self.rag.load_script_from_file(filepath)
            print(f">> {msg}")
            if not ok:
                return
            steps = self.rag.parse_simulation_script(content)

        else:
            print(">> Cancelled.")
            return

        if not steps:
            print(">> No simulation steps were entered.")
            return

        if sub in ("1", "2"):
            save_ans = input("\nSave this custom simulation script to a .txt file? (y/n): ").strip().lower()
            if save_ans == "y":
                filepath = input("Enter filename to save (e.g., my_simulation.txt): ").strip()
                _, save_msg = self.rag.save_script_to_file(filepath, "\n".join(steps))
                print(f">> {save_msg}")

        self.execute_steps_interactive(steps)

    def save_current_graph_to_file(self) -> None:
        if not self.rag.processes and not self.rag.resources:
            print(">> Graph is currently empty. Nothing to save.")
            return
        script_text = self.rag.export_current_state_as_script()
        print("\nExported Script Preview:")
        print("-" * 40)
        print(script_text)
        print("-" * 40)
        filepath = input("Enter filename to save (e.g., saved_graph.txt): ").strip()
        _, msg = self.rag.save_script_to_file(filepath, script_text)
        print(f">> {msg}")

    def load_and_run_file(self) -> None:
        filepath = input("Enter filename/path to load (e.g., saved_graph.txt): ").strip()
        ok, msg, content = self.rag.load_script_from_file(filepath)
        print(f">> {msg}")
        if not ok:
            return
        steps = self.rag.parse_simulation_script(content)
        self.execute_steps_interactive(steps)

    def run(self) -> None:
        self.print_banner()
        while True:
            mode_str = "AUTOMATIC" if self.rag.auto_grant else "MANUAL"
            print(
                f"\nMenu Options (Current Allocation Mode: {mode_str}):\n"
                "  1. Add Process                     9. Show Current RAG State\n"
                "  2. Add Resource                   10. Run Deadlock Detection Trace\n"
                "  3. Request Resource (P -> R)      11. Toggle Auto / Manual Allocation Mode\n"
                "  4. Manually Grant Request (R->P)  12. Custom Simulation Builder (Auto/Manual)\n"
                "  5. Direct Allocate (R -> P)       13. Save Current Graph State to .txt File\n"
                "  6. Release Resource               14. Load & Run Simulation Script from .txt File\n"
                "  7. Cancel Pending Request         15. Clear / Reset Graph\n"
                "  8. Remove Process or Resource      0. Exit CLI"
            )
            choice = input("\nSelect an option (0-15): ").strip()

            if choice == "1":
                pid = input("Enter Process ID: ").strip()
                _, msg = self.rag.add_process(pid)
                print(f">> {msg}")

            elif choice == "2":
                rid = input("Enter Resource ID: ").strip()
                inst_str = input("Enter number of instances: ").strip()
                instances = int(inst_str) if inst_str.isdigit() else 1
                _, msg = self.rag.add_resource(rid, instances)
                print(f">> {msg}")

            elif choice == "3":
                pid = input("Enter requesting Process ID: ").strip()
                rid = input("Enter target Resource ID: ").strip()
                cnt_str = input("Enter instance count: ").strip()
                count = int(cnt_str) if cnt_str.isdigit() else 1
                _, msg = self.rag.request_resource(pid, rid, count)
                print(f">> {msg}")

            elif choice == "4":
                pid = input("Enter Process ID with pending request: ").strip()
                rid = input("Enter Resource ID to grant: ").strip()
                cnt_str = input("Enter instance count (blank for all pending): ").strip()
                count = int(cnt_str) if cnt_str.isdigit() else None
                _, msg = self.rag.grant_pending_request(pid, rid, count)
                print(f">> {msg}")

            elif choice == "5":
                rid = input("Enter Resource ID to allocate: ").strip()
                pid = input("Enter receiving Process ID: ").strip()
                cnt_str = input("Enter instance count: ").strip()
                count = int(cnt_str) if cnt_str.isdigit() else 1
                _, msg = self.rag.force_allocate(rid, pid, count)
                print(f">> {msg}")

            elif choice == "6":
                pid = input("Enter Process ID releasing resource: ").strip()
                rid = input("Enter Resource ID to release: ").strip()
                cnt_str = input("Enter instance count: ").strip()
                count = int(cnt_str) if cnt_str.isdigit() else 1
                _, msg = self.rag.release_resource(pid, rid, count)
                print(f">> {msg}")

            elif choice == "7":
                pid = input("Enter Process ID: ").strip()
                rid = input("Enter Resource ID: ").strip()
                _, msg = self.rag.cancel_request(pid, rid)
                print(f">> {msg}")

            elif choice == "8":
                sub = input("Remove (P)rocess or (R)esource? ").strip().upper()
                if sub == "P":
                    pid = input("Enter Process ID to remove: ").strip()
                    _, msg = self.rag.remove_process(pid)
                    print(f">> {msg}")
                elif sub == "R":
                    rid = input("Enter Resource ID to remove: ").strip()
                    _, msg = self.rag.remove_resource(rid)
                    print(f">> {msg}")
                else:
                    print(">> Invalid selection.")

            elif choice == "9":
                self.display_state()

            elif choice == "10":
                self.run_deadlock_analysis()

            elif choice == "11":
                msg = self.rag.set_auto_grant(not self.rag.auto_grant)
                print(f">> {msg}")

            elif choice == "12":
                self.run_custom_simulation_builder()

            elif choice == "13":
                self.save_current_graph_to_file()

            elif choice == "14":
                self.load_and_run_file()

            elif choice == "15":
                self.rag.clear()
                print(">> Graph cleared.")

            elif choice == "0":
                print("Exiting RAG CLI Simulator.")
                sys.exit(0)
            else:
                print(">> Invalid option. Choose 0-15.")


if __name__ == "__main__":
    app = RAGCliApp()
    app.run()
