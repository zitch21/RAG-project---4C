import os
from collections import defaultdict
from typing import Dict, List, Set, Tuple


class ResourceAllocationGraph:
    """
    Core Resource Allocation Graph (RAG) engine.
    Starts completely empty with no hardcoded nodes or presets.
    Supports:
    - Single-instance and multi-instance resources
    - Automatic vs. Manual allocation mode (auto_grant)
    - User-defined simulation script parsing and step-by-step execution
    - Saving and loading custom simulation scripts (.txt) & exporting live graph state
    - Cycle detection and Graph Reduction deadlock detection
    """

    def __init__(self):
        self.processes: Set[str] = set()
        # resource_id -> total instances
        self.resources: Dict[str, int] = {}
        # allocations[resource_id][process_id] = count of allocated instances (R -> P)
        self.allocations: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        # requests[process_id][resource_id] = count of requested instances (P -> R)
        self.requests: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        # If True, available resources are immediately allocated on request/release.
        # If False, requests remain as P -> R edges until manually granted.
        self.auto_grant: bool = True

    def clear(self) -> None:
        self.processes.clear()
        self.resources.clear()
        self.allocations.clear()
        self.requests.clear()

    def set_auto_grant(self, enabled: bool) -> str:
        self.auto_grant = enabled
        mode_str = "AUTOMATIC" if enabled else "MANUAL"
        granted_logs = []
        if enabled:
            granted_logs = self._try_grant_pending_requests()
        extra = (" " + " ".join(granted_logs)) if granted_logs else ""
        return f"Allocation mode set to {mode_str}.{extra}"

    def add_process(self, pid: str) -> Tuple[bool, str]:
        pid = pid.strip().upper()
        if not pid:
            return False, "Process ID cannot be empty."
        if pid in self.processes:
            return False, f"Process {pid} already exists."
        self.processes.add(pid)
        return True, f"Added Process {pid}."

    def remove_process(self, pid: str) -> Tuple[bool, str]:
        pid = pid.strip().upper()
        if pid not in self.processes:
            return False, f"Process {pid} does not exist."
        self.processes.remove(pid)
        self.requests.pop(pid, None)
        for rid in list(self.allocations.keys()):
            self.allocations[rid].pop(pid, None)
        if self.auto_grant:
            self._try_grant_pending_requests()
        return True, f"Removed Process {pid} and released its held resources."

    def add_resource(self, rid: str, instances: int = 1) -> Tuple[bool, str]:
        rid = rid.strip().upper()
        if not rid:
            return False, "Resource ID cannot be empty."
        if instances < 1:
            return False, "Resource must have at least 1 instance."
        if rid in self.resources:
            return False, f"Resource {rid} already exists."
        self.resources[rid] = instances
        return True, f"Added Resource {rid} with {instances} instance(s)."

    def remove_resource(self, rid: str) -> Tuple[bool, str]:
        rid = rid.strip().upper()
        if rid not in self.resources:
            return False, f"Resource {rid} does not exist."
        del self.resources[rid]
        self.allocations.pop(rid, None)
        for pid in list(self.requests.keys()):
            self.requests[pid].pop(rid, None)
        return True, f"Removed Resource {rid}."

    def available_instances(self, rid: str) -> int:
        if rid not in self.resources:
            return 0
        allocated = sum(self.allocations[rid].values())
        return self.resources[rid] - allocated

    def request_resource(
        self, pid: str, rid: str, count: int = 1, force_auto: bool = None
    ) -> Tuple[bool, str]:
        pid = pid.strip().upper()
        rid = rid.strip().upper()

        if pid not in self.processes:
            return False, f"Process {pid} not found."
        if rid not in self.resources:
            return False, f"Resource {rid} not found."
        if count < 1:
            return False, "Request count must be at least 1."
        if count > self.resources[rid]:
            return (
                False,
                f"Cannot request {count} instances of {rid} (total instances: {self.resources[rid]}).",
            )

        use_auto = self.auto_grant if force_auto is None else force_auto
        avail = self.available_instances(rid)

        if use_auto and avail >= count:
            self.allocations[rid][pid] += count
            return (
                True,
                f"[Auto-Allocated] {count} instance(s) of {rid} -> {pid}.",
            )
        else:
            self.requests[pid][rid] += count
            reason = "Manual Allocation Mode" if not use_auto else f"Only {avail} available"
            return (
                True,
                f"[Request Edge] {pid} -> {rid} ({count} instance(s), {reason}).",
            )

    def grant_pending_request(
        self, pid: str, rid: str, count: int = None
    ) -> Tuple[bool, str]:
        pid = pid.strip().upper()
        rid = rid.strip().upper()
        if pid not in self.processes:
            return False, f"Process {pid} not found."
        if rid not in self.resources:
            return False, f"Resource {rid} not found."

        pending = self.requests[pid].get(rid, 0)
        if pending <= 0:
            return False, f"No pending request from {pid} for {rid}."

        to_grant = pending if count is None else min(count, pending)
        if to_grant < 1:
            return False, "Grant count must be at least 1."

        avail = self.available_instances(rid)
        if avail < to_grant:
            return (
                False,
                f"Cannot grant {to_grant} of {rid} to {pid}: only {avail} available.",
            )

        self.requests[pid][rid] -= to_grant
        if self.requests[pid][rid] <= 0:
            del self.requests[pid][rid]
        self.allocations[rid][pid] += to_grant
        return (
            True,
            f"[Granted] Request {pid} -> {rid} converted to Allocation {rid} -> {pid} ({to_grant} instance(s)).",
        )

    def force_allocate(self, rid: str, pid: str, count: int = 1) -> Tuple[bool, str]:
        pid = pid.strip().upper()
        rid = rid.strip().upper()
        if pid not in self.processes:
            return False, f"Process {pid} not found."
        if rid not in self.resources:
            return False, f"Resource {rid} not found."
        if count < 1:
            return False, "Allocation count must be at least 1."
        avail = self.available_instances(rid)
        if avail < count:
            return False, f"Only {avail} instance(s) of {rid} available."
        self.allocations[rid][pid] += count
        if self.requests[pid].get(rid, 0) > 0:
            fulfilled = min(self.requests[pid][rid], count)
            self.requests[pid][rid] -= fulfilled
            if self.requests[pid][rid] == 0:
                del self.requests[pid][rid]
        return True, f"[Direct Allocation] {count} instance(s) of {rid} -> {pid}."

    def release_resource(self, pid: str, rid: str, count: int = 1) -> Tuple[bool, str]:
        pid = pid.strip().upper()
        rid = rid.strip().upper()
        if pid not in self.processes:
            return False, f"Process {pid} not found."
        if rid not in self.resources:
            return False, f"Resource {rid} not found."
        if count < 1:
            return False, "Release count must be at least 1."

        held = self.allocations[rid].get(pid, 0)
        if held < count:
            return False, f"{pid} only holds {held} instance(s) of {rid}."

        self.allocations[rid][pid] -= count
        if self.allocations[rid][pid] == 0:
            del self.allocations[rid][pid]

        granted_logs = []
        if self.auto_grant:
            granted_logs = self._try_grant_pending_requests()
        msg = f"{pid} released {count} instance(s) of {rid}."
        if granted_logs:
            msg += " " + " ".join(granted_logs)
        return True, msg

    def cancel_request(self, pid: str, rid: str) -> Tuple[bool, str]:
        pid = pid.strip().upper()
        rid = rid.strip().upper()
        if self.requests[pid].get(rid, 0) == 0:
            return False, f"No pending request from {pid} for {rid}."
        del self.requests[pid][rid]
        return True, f"Cancelled pending request {pid} -> {rid}."

    def _try_grant_pending_requests(self) -> List[str]:
        logs = []
        changed = True
        while changed:
            changed = False
            for pid in sorted(self.processes):
                for rid in sorted(list(self.requests[pid].keys())):
                    needed = self.requests[pid][rid]
                    if needed > 0 and self.available_instances(rid) >= needed:
                        self.allocations[rid][pid] += needed
                        del self.requests[pid][rid]
                        logs.append(f"[Auto-Granted {needed} of {rid} to {pid}]")
                        changed = True
        return logs

    def export_current_state_as_script(self) -> str:
        lines: List[str] = ["CLEAR"]
        mode_str = "AUTO" if self.auto_grant else "MANUAL"
        lines.append(f"MODE {mode_str}")

        for pid in sorted(self.processes):
            lines.append(f"ADD_P {pid}")

        for rid in sorted(self.resources.keys()):
            lines.append(f"ADD_R {rid} {self.resources[rid]}")

        for rid in sorted(self.resources.keys()):
            for pid in sorted(self.processes):
                alloc_cnt = self.allocations[rid].get(pid, 0)
                if alloc_cnt > 0:
                    lines.append(f"ALLOC {rid} {pid} {alloc_cnt}")

        has_pending = any(
            self.requests[p].get(r, 0) > 0
            for p in self.processes
            for r in self.resources
        )
        if has_pending and self.auto_grant:
            lines.append("MODE MANUAL")
            for pid in sorted(self.processes):
                for rid in sorted(self.resources.keys()):
                    req_cnt = self.requests[pid].get(rid, 0)
                    if req_cnt > 0:
                        lines.append(f"REQ {pid} {rid} {req_cnt}")
            lines.append("MODE AUTO")
        else:
            for pid in sorted(self.processes):
                for rid in sorted(self.resources.keys()):
                    req_cnt = self.requests[pid].get(rid, 0)
                    if req_cnt > 0:
                        lines.append(f"REQ {pid} {rid} {req_cnt}")

        lines.append("CHECK")
        return "\n".join(lines)

    def save_script_to_file(self, filepath: str, script_text: str) -> Tuple[bool, str]:
        filepath = filepath.strip()
        if not filepath:
            return False, "File path cannot be empty."
        if not os.path.splitext(filepath)[1]:
            filepath += ".txt"
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(script_text.strip() + "\n")
            return True, f"Saved simulation script to '{filepath}'."
        except OSError as e:
            return False, f"Failed to save file '{filepath}': {e}"

    def load_script_from_file(self, filepath: str) -> Tuple[bool, str, str]:
        filepath = filepath.strip()
        if not filepath:
            return False, "File path cannot be empty.", ""
        if not os.path.exists(filepath) and not os.path.splitext(filepath)[1]:
            if os.path.exists(filepath + ".txt"):
                filepath += ".txt"
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            steps = self.parse_simulation_script(content)
            return (
                True,
                f"Loaded {len(steps)} command(s) from '{filepath}'.",
                content,
            )
        except OSError as e:
            return False, f"Failed to load file '{filepath}': {e}", ""

    def parse_simulation_script(self, script_text: str) -> List[str]:
        steps: List[str] = []
        raw_lines = script_text.replace(";", "\n").splitlines()
        for line in raw_lines:
            cleaned = line.strip()
            if not cleaned or cleaned.startswith("#"):
                continue
            steps.append(cleaned)
        return steps

    def execute_command(self, cmd_line: str) -> Tuple[bool, str]:
        parts = cmd_line.strip().split()
        if not parts:
            return False, "Empty command."

        op = parts[0].upper()

        if op == "CLEAR":
            self.clear()
            return True, "Cleared all processes, resources, and edges."

        if op == "MODE" and len(parts) >= 2:
            sub = parts[1].upper()
            if sub in ("AUTO", "AUTOMATIC"):
                return True, self.set_auto_grant(True)
            elif sub in ("MANUAL", "MAN"):
                return True, self.set_auto_grant(False)
            return False, f"Unknown mode '{sub}'. Use MODE AUTO or MODE MANUAL."

        if op in ("ADD_P", "P", "PROCESS", "PROCESSES"):
            tokens = [t.strip(",") for t in parts[1:] if t.strip(",")]
            if not tokens:
                return False, "Specify at least one Process ID."
            msgs = []
            for pid in tokens:
                _, m = self.add_process(pid)
                msgs.append(m)
            return True, " ".join(msgs)

        if op in ("DEL_P", "RM_P"):
            if len(parts) < 2:
                return False, "Usage: DEL_P <ProcessID>"
            return self.remove_process(parts[1])

        if op in ("ADD_R", "R", "RESOURCE", "RESOURCES"):
            if len(parts) == 3 and parts[2].isdigit():
                return self.add_resource(parts[1], int(parts[2]))
            tokens = [t.strip(",") for t in parts[1:] if t.strip(",")]
            if not tokens:
                return False, "Specify Resource ID and instances."
            msgs = []
            for tok in tokens:
                if ":" in tok:
                    r_name, inst_s = tok.split(":", 1)
                    inst = int(inst_s) if inst_s.isdigit() else 1
                    _, m = self.add_resource(r_name, inst)
                else:
                    _, m = self.add_resource(tok, 1)
                msgs.append(m)
            return True, " ".join(msgs)

        if op in ("DEL_R", "RM_R"):
            if len(parts) < 2:
                return False, "Usage: DEL_R <ResourceID>"
            return self.remove_resource(parts[1])

        if op in ("REQ", "REQUEST"):
            if len(parts) < 3:
                return False, "Usage: REQ <ProcessID> <ResourceID> [Count]"
            pid, rid = parts[1], parts[2]
            cnt = int(parts[3]) if len(parts) >= 4 and parts[3].isdigit() else 1
            return self.request_resource(pid, rid, cnt)

        if op == "GRANT":
            if len(parts) < 3:
                return False, "Usage: GRANT <ProcessID> <ResourceID> [Count]"
            pid, rid = parts[1], parts[2]
            cnt = int(parts[3]) if len(parts) >= 4 and parts[3].isdigit() else None
            return self.grant_pending_request(pid, rid, cnt)

        if op in ("ALLOC", "ALLOCATE"):
            if len(parts) < 3:
                return False, "Usage: ALLOC <ResourceID> <ProcessID> [Count]"
            rid, pid = parts[1], parts[2]
            cnt = int(parts[3]) if len(parts) >= 4 and parts[3].isdigit() else 1
            return self.force_allocate(rid, pid, cnt)

        if op in ("REL", "RELEASE"):
            if len(parts) < 3:
                return False, "Usage: REL <ProcessID> <ResourceID> [Count]"
            pid, rid = parts[1], parts[2]
            cnt = int(parts[3]) if len(parts) >= 4 and parts[3].isdigit() else 1
            return self.release_resource(pid, rid, cnt)

        if op == "CANCEL":
            if len(parts) < 3:
                return False, "Usage: CANCEL <ProcessID> <ResourceID>"
            return self.cancel_request(parts[1], parts[2])

        if op in ("CHECK", "DETECT"):
            res = self.detect_deadlock()
            if res["deadlocked"]:
                return (
                    True,
                    f"[CHECK] DEADLOCK DETECTED among: {', '.join(res['deadlocked_processes'])}",
                )
            seq = " -> ".join(res["safe_sequence"]) if res["safe_sequence"] else "None"
            return True, f"[CHECK] SAFE STATE. Reduction sequence: {seq}"

        return False, f"Unrecognized simulation command: '{cmd_line}'"

    def find_cycles(self) -> List[List[str]]:
        adj: Dict[str, List[str]] = defaultdict(list)
        for pid, reqs in self.requests.items():
            for rid, count in reqs.items():
                if count > 0:
                    adj[pid].append(rid)
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
        work: Dict[str, int] = {
            rid: self.available_instances(rid) for rid in sorted(self.resources)
        }
        finish: Dict[str, bool] = {}
        steps: List[str] = []
        safe_sequence: List[str] = []

        steps.append(
            "Initial Available Resources: "
            + (", ".join(f"{r}={w}" for r, w in work.items()) if work else "None")
        )

        for pid in sorted(self.processes):
            holds_any = any(self.allocations[r].get(pid, 0) > 0 for r in self.resources)
            reqs_any = any(self.requests[pid].get(r, 0) > 0 for r in self.resources)
            if not holds_any and not reqs_any:
                finish[pid] = True
                safe_sequence.append(pid)
                steps.append(
                    f"Process {pid} has no held or requested resources -> Marked Finished."
                )
            else:
                finish[pid] = False

        progressed = True
        while progressed:
            progressed = False
            for pid in sorted(self.processes):
                if finish[pid]:
                    continue
                can_satisfy = True
                for rid, req_count in self.requests[pid].items():
                    if req_count > work.get(rid, 0):
                        can_satisfy = False
                        break

                if can_satisfy:
                    released_info = []
                    for rid in sorted(self.resources):
                        held = self.allocations[rid].get(pid, 0)
                        if held > 0:
                            work[rid] += held
                            released_info.append(f"{rid}+{held}")
                    finish[pid] = True
                    safe_sequence.append(pid)
                    progressed = True
                    rel_str = ", ".join(released_info) if released_info else "none"
                    work_str = ", ".join(f"{r}={w}" for r, w in work.items())
                    steps.append(
                        f"Process {pid} requests satisfied -> {pid} finishes & releases ({rel_str}). Available: {work_str}"
                    )

        deadlocked_procs = [pid for pid, done in sorted(finish.items()) if not done]
        cycles = self.find_cycles()

        if deadlocked_procs:
            steps.append(
                f"DEADLOCK DETECTED! Blocked processes unable to finish: {', '.join(deadlocked_procs)}"
            )
        else:
            steps.append(
                "NO DEADLOCK. Graph completely reduced. Safe sequence: "
                + (" -> ".join(safe_sequence) if safe_sequence else "None")
            )

        return {
            "deadlocked": len(deadlocked_procs) > 0,
            "deadlocked_processes": deadlocked_procs,
            "safe_sequence": safe_sequence,
            "steps": steps,
            "cycles": cycles,
        }
