from collections import defaultdict
from typing import Dict, List, Set, Tuple


class ResourceAllocationGraph:
    """
    Operating Systems Resource Allocation Graph (RAG) Engine.
    Handles processes, single/multi-instance resources, allocation edges (R -> P),
    request edges (P -> R), cycle detection, and graph reduction deadlock detection.
    """

    def __init__(self):
        self.processes: Set[str] = set()
        # resource_id -> total instances
        self.resources: Dict[str, int] = {}
        # allocations[resource_id][process_id] = count (R -> P)
        self.allocations: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        # requests[process_id][resource_id] = count (P -> R)
        self.requests: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def clear(self) -> None:
        self.processes.clear()
        self.resources.clear()
        self.allocations.clear()
        self.requests.clear()

    def add_process(self, pid: str) -> Tuple[bool, str]:
        pid = pid.strip().upper()
        if not pid:
            return False, "Process ID cannot be empty."
        if pid in self.processes:
            return False, f"Process {pid} already exists."
        self.processes.add(pid)
        return True, f"Added Process {pid}."

    def add_resource(self, rid: str, instances: int = 1) -> Tuple[bool, str]:
        rid = rid.strip().upper()
        if not rid:
            return False, "Resource ID cannot be empty."
        if instances < 1:
            return False, "Instances must be at least 1."
        if rid in self.resources:
            return False, f"Resource {rid} already exists."
        self.resources[rid] = instances
        return True, f"Added Resource {rid} ({instances} instance(s))."

    def available_instances(self, rid: str) -> int:
        if rid not in self.resources:
            return 0
        allocated = sum(self.allocations[rid].values())
        return self.resources[rid] - allocated

    def add_allocation(self, rid: str, pid: str, count: int = 1) -> Tuple[bool, str]:
        """Allocates resource instances to a process (Resource -> Process edge)."""
        rid = rid.strip().upper()
        pid = pid.strip().upper()
        if rid not in self.resources:
            return False, f"Resource {rid} does not exist."
        if pid not in self.processes:
            return False, f"Process {pid} does not exist."
        if count < 1:
            return False, "Count must be at least 1."

        avail = self.available_instances(rid)
        if count > avail:
            return False, f"Cannot allocate {count} of {rid}: only {avail} free instance(s)."

        self.allocations[rid][pid] += count
        # If process had a pending request for this resource, fulfill it
        if self.requests[pid].get(rid, 0) > 0:
            fulfilled = min(self.requests[pid][rid], count)
            self.requests[pid][rid] -= fulfilled
            if self.requests[pid][rid] == 0:
                del self.requests[pid][rid]

        return True, f"Allocated {count} instance(s) of {rid} -> {pid}."

    def add_request(self, pid: str, rid: str, count: int = 1) -> Tuple[bool, str]:
        """Process requests resource instances (Process -> Resource edge)."""
        pid = pid.strip().upper()
        rid = rid.strip().upper()
        if pid not in self.processes:
            return False, f"Process {pid} does not exist."
        if rid not in self.resources:
            return False, f"Resource {rid} does not exist."
        if count < 1:
            return False, "Count must be at least 1."

        held = self.allocations[rid].get(pid, 0)
        existing_req = self.requests[pid].get(rid, 0)
        total = self.resources[rid]
        if held + existing_req + count > total:
            return (
                False,
                f"Request ({existing_req + count}) + held ({held}) exceeds total capacity ({total}) for {rid}.",
            )

        self.requests[pid][rid] += count
        return True, f"Added request: {pid} -> {rid} ({count} instance(s))."

    def remove_process(self, pid: str) -> Tuple[bool, str]:
        pid = pid.strip().upper()
        if pid not in self.processes:
            return False, f"Process {pid} does not exist."
        self.processes.remove(pid)
        self.requests.pop(pid, None)
        for rid in list(self.allocations.keys()):
            self.allocations[rid].pop(pid, None)
        return True, f"Removed Process {pid}."

    def remove_resource(self, rid: str) -> Tuple[bool, str]:
        rid = rid.strip().upper()
        if rid not in self.resources:
            return False, f"Resource {rid} does not exist."
        del self.resources[rid]
        self.allocations.pop(rid, None)
        for pid in list(self.requests.keys()):
            self.requests[pid].pop(rid, None)
        return True, f"Removed Resource {rid}."

    def find_cycles(self) -> List[List[str]]:
        """Finds directed cycles in the RAG."""
        adj: Dict[str, List[str]] = defaultdict(list)
        # Request edges: Process -> Resource
        for pid, reqs in self.requests.items():
            for rid, count in reqs.items():
                if count > 0:
                    adj[pid].append(rid)
        # Allocation edges: Resource -> Process
        for rid, allocs in self.allocations.items():
            for pid, count in allocs.items():
                if count > 0:
                    adj[rid].append(pid)

        cycles: List[List[str]] = []
        visited_global: Set[str] = set()
        nodes = sorted(list(self.processes) + list(self.resources.keys()))

        for start_node in nodes:
            if start_node in visited_global:
                continue
            path: List[str] = []
            on_path: Set[str] = set()

            def dfs(curr: str):
                visited_global.add(curr)
                path.append(curr)
                on_path.add(curr)

                for nxt in adj.get(curr, []):
                    if nxt not in on_path:
                        if nxt not in visited_global:
                            dfs(nxt)
                    else:
                        idx = path.index(nxt)
                        cycle = path[idx:] + [nxt]
                        cycles.append(cycle)

                path.pop()
                on_path.remove(curr)

            dfs(start_node)
        return cycles

    def detect_deadlock(self) -> Dict[str, object]:
        """
        Executes standard Graph Reduction deadlock detection.
        Returns:
            - deadlocked: bool
            - deadlocked_processes: List[str]
            - safe_sequence: List[str]
            - steps: List[str] (step-by-step trace)
            - cycles: List[List[str]]
        """
        work = {rid: self.available_instances(rid) for rid in sorted(self.resources)}
        finish: Dict[str, bool] = {}
        steps: List[str] = []
        safe_sequence: List[str] = []

        avail_desc = ", ".join(f"{r}={w}" for r, w in work.items()) if work else "None"
        steps.append(f"Available Resource Instances: {avail_desc}")

        # Mark processes that have no requests and hold no resources as finished
        for pid in sorted(self.processes):
            holds = any(self.allocations[r].get(pid, 0) > 0 for r in self.resources)
            reqs = any(self.requests[pid].get(r, 0) > 0 for r in self.resources)
            if not holds and not reqs:
                finish[pid] = True
                safe_sequence.append(pid)
                steps.append(f"{pid} is idle (no requests or held resources) -> Finished.")
            else:
                finish[pid] = False

        progressed = True
        while progressed:
            progressed = False
            for pid in sorted(self.processes):
                if finish[pid]:
                    continue

                # Can process requests be satisfied by current work/available?
                can_satisfy = True
                for rid, count in self.requests[pid].items():
                    if count > work.get(rid, 0):
                        can_satisfy = False
                        break

                if can_satisfy:
                    released = []
                    for rid in sorted(self.resources):
                        held = self.allocations[rid].get(pid, 0)
                        if held > 0:
                            work[rid] += held
                            released.append(f"{rid}+{held}")
                    finish[pid] = True
                    safe_sequence.append(pid)
                    progressed = True

                    rel_str = ", ".join(released) if released else "none"
                    work_str = ", ".join(f"{r}={w}" for r, w in work.items())
                    steps.append(
                        f"{pid} requests satisfied -> runs, completes & releases ({rel_str}). Available: {work_str}"
                    )

        deadlocked_procs = [pid for pid, done in sorted(finish.items()) if not done]
        cycles = self.find_cycles()

        if deadlocked_procs:
            steps.append(f"DEADLOCK DETECTED! Deadlocked processes: {', '.join(deadlocked_procs)}")
        else:
            seq_str = " -> ".join(safe_sequence) if safe_sequence else "None"
            steps.append(f"NO DEADLOCK. Graph successfully reduced. Safe Sequence: {seq_str}")

        return {
            "deadlocked": len(deadlocked_procs) > 0,
            "deadlocked_processes": deadlocked_procs,
            "safe_sequence": safe_sequence,
            "steps": steps,
            "cycles": cycles,
        }

    # Built-in Preset Scenarios for instant demonstration
    def load_preset_deadlock(self) -> None:
        """Loads a classic Circular Wait deadlock (P1 holds R1, requests R2; P2 holds R2, requests R1)."""
        self.clear()
        self.add_process("P1")
        self.add_process("P2")
        self.add_resource("R1", 1)
        self.add_resource("R2", 1)
        self.add_allocation("R1", "P1", 1)
        self.add_allocation("R2", "P2", 1)
        self.add_request("P1", "R2", 1)
        self.add_request("P2", "R1", 1)

    def load_preset_safe(self) -> None:
        """Loads a safe state scenario where processes can complete sequentially without deadlock."""
        self.clear()
        self.add_process("P1")
        self.add_process("P2")
        self.add_resource("R1", 1)
        self.add_resource("R2", 1)
        self.add_allocation("R1", "P1", 1)
        self.add_request("P2", "R1", 1)
        self.add_allocation("R2", "P2", 1)

    def load_preset_multi_instance_cycle(self) -> None:
        """Loads a multi-instance scenario with a cycle, but safe because P3 can finish and release instances."""
        self.clear()
        self.add_process("P1")
        self.add_process("P2")
        self.add_process("P3")
        self.add_resource("R1", 2)
        self.add_resource("R2", 2)
        self.add_allocation("R1", "P1", 1)
        self.add_allocation("R1", "P2", 1)
        self.add_allocation("R2", "P2", 1)
        self.add_allocation("R2", "P3", 1)
        self.add_request("P1", "R2", 1)
        self.add_request("P2", "R1", 1)
