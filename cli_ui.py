import sys
from rag_engine import ResourceAllocationGraph


class RAGCliApp:
    def __init__(self, rag: ResourceAllocationGraph = None):
        self.rag = rag or ResourceAllocationGraph()

    def print_banner(self) -> None:
        print("=" * 68)
        print("   OPERATING SYSTEMS - RESOURCE ALLOCATION GRAPH (RAG) SIMULATOR")
        print("=" * 68)

    def display_state(self) -> None:
        procs = sorted(self.rag.processes)
        res = sorted(self.rag.resources.keys())
        print("\n--- CURRENT GRAPH STATE ---")
        print(f"Processes: {', '.join(procs) if procs else 'None'}")

        if not res:
            print("Resources: None")
        else:
            r_str = " | ".join(
                f"{r} (Total: {self.rag.resources[r]}, Free: {self.rag.available_instances(r)})"
                for r in res
            )
            print(f"Resources: {r_str}")

        print("\nAllocations (Resource -> Process):")
        has_alloc = False
        for r in res:
            for p in procs:
                cnt = self.rag.allocations[r].get(p, 0)
                if cnt > 0:
                    has_alloc = True
                    print(f"  [HELD]    {r} --({cnt})--> {p}")
        if not has_alloc:
            print("  (None)")

        print("\nRequests (Process -> Resource):")
        has_req = False
        for p in procs:
            for r in res:
                cnt = self.rag.requests[p].get(r, 0)
                if cnt > 0:
                    has_req = True
                    print(f"  [WAITING] {p} --({cnt})--> {r}")
        if not has_req:
            print("  (None)")
        print("-" * 50)

    def run_deadlock_detection(self) -> None:
        if not self.rag.processes and not self.rag.resources:
            print("\n>> Graph is empty. Load a preset or add nodes first.")
            return

        res = self.rag.detect_deadlock()
        print("\n=== DEADLOCK DETECTION & GRAPH REDUCTION TRACE ===")
        for idx, step in enumerate(res["steps"], 1):
            print(f"  Step {idx}: {step}")

        cycles = res["cycles"]
        if cycles:
            print("\nDetected Cycles:")
            for c in cycles:
                print("  Cycle: " + " -> ".join(c))
        else:
            print("\nDetected Cycles: None")

        if res["deadlocked"]:
            print(f"\n[STATUS: DEADLOCKED] Blocked Processes: {', '.join(res['deadlocked_processes'])}")
        else:
            seq_str = " -> ".join(res["safe_sequence"]) if res["safe_sequence"] else "None"
            print(f"\n[STATUS: SAFE] No deadlock detected. Safe Sequence: {seq_str}")
        print("=" * 50)

    def run(self) -> None:
        self.print_banner()
        while True:
            print(
                "\nMenu:\n"
                "  1. Load Deadlock Scenario (Circular Wait)\n"
                "  2. Load Safe State Scenario (Resolvable)\n"
                "  3. Load Multi-Instance Cycle Scenario\n"
                "  4. Add Process\n"
                "  5. Add Resource\n"
                "  6. Add Allocation (Resource -> Process)\n"
                "  7. Add Request (Process -> Resource)\n"
                "  8. View Current Graph State\n"
                "  9. Run Deadlock Detection\n"
                "  10. Clear Graph\n"
                "  0. Exit"
            )
            choice = input("\nSelect an option (0-10): ").strip()

            if choice == "1":
                self.rag.load_preset_deadlock()
                print(">> Loaded Deadlock Scenario.")
                self.display_state()
                self.run_deadlock_detection()

            elif choice == "2":
                self.rag.load_preset_safe()
                print(">> Loaded Safe State Scenario.")
                self.display_state()
                self.run_deadlock_detection()

            elif choice == "3":
                self.rag.load_preset_multi_instance_cycle()
                print(">> Loaded Multi-Instance Cycle Scenario.")
                self.display_state()
                self.run_deadlock_detection()

            elif choice == "4":
                pid = input("Enter Process ID (e.g. P1): ").strip()
                _, msg = self.rag.add_process(pid)
                print(f">> {msg}")

            elif choice == "5":
                rid = input("Enter Resource ID (e.g. R1): ").strip()
                units_str = input("Enter number of instances (default 1): ").strip()
                units = int(units_str) if units_str.isdigit() else 1
                _, msg = self.rag.add_resource(rid, units)
                print(f">> {msg}")

            elif choice == "6":
                rid = input("Enter Resource ID: ").strip()
                pid = input("Enter Process ID: ").strip()
                cnt_str = input("Enter instances to allocate (default 1): ").strip()
                cnt = int(cnt_str) if cnt_str.isdigit() else 1
                _, msg = self.rag.add_allocation(rid, pid, cnt)
                print(f">> {msg}")

            elif choice == "7":
                pid = input("Enter Process ID: ").strip()
                rid = input("Enter Resource ID: ").strip()
                cnt_str = input("Enter instances to request (default 1): ").strip()
                cnt = int(cnt_str) if cnt_str.isdigit() else 1
                _, msg = self.rag.add_request(pid, rid, cnt)
                print(f">> {msg}")

            elif choice == "8":
                self.display_state()

            elif choice == "9":
                self.run_deadlock_detection()

            elif choice == "10":
                self.rag.clear()
                print(">> Graph cleared.")

            elif choice == "0":
                print("Exiting RAG Simulator.")
                sys.exit(0)

            else:
                print(">> Invalid option. Enter 0-10.")


if __name__ == "__main__":
    app = RAGCliApp()
    app.run()
