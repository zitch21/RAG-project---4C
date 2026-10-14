import math
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Tuple
from rag_engine import ResourceAllocationGraph


class RAGGuiSimulator:
    def __init__(self, root: tk.Tk, rag: ResourceAllocationGraph = None):
        self.root = root
        self.root.title("Operating Systems — Resource Allocation Graph (RAG) Simulator")
        self.root.geometry("1060x680")
        self.root.minsize(920, 580)

        self.rag = rag or ResourceAllocationGraph()
        self.node_positions: Dict[str, Tuple[float, float]] = {}
        self.drag_data = {"node": None, "x": 0, "y": 0}
        self.last_analysis = None

        self._build_ui()
        # Load default deadlock scenario to immediately show something working
        self.on_load_preset_deadlock()

    def _build_ui(self) -> None:
        # Top Status Banner
        self.banner = tk.Label(
            self.root,
            text="RAG SIMULATOR — READY",
            font=("Helvetica", 12, "bold"),
            bg="#2c3e50",
            fg="white",
            pady=7,
        )
        self.banner.pack(fill=tk.X)

        # Main Split Pane (Left: Controls, Right: Canvas + Results)
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # ----------------- LEFT CONTROL PANEL -----------------
        ctrl_frame = ttk.Frame(main_pane, width=320)
        main_pane.add(ctrl_frame, weight=0)

        # 1. Preset Scenarios
        preset_box = ttk.LabelFrame(ctrl_frame, text="Preset Scenarios", padding=8)
        preset_box.pack(fill=tk.X, pady=4)

        ttk.Button(
            preset_box,
            text="1. Deadlock Scenario (Circular Wait)",
            command=self.on_load_preset_deadlock,
        ).pack(fill=tk.X, pady=2)

        ttk.Button(
            preset_box,
            text="2. Safe State Scenario (Resolvable)",
            command=self.on_load_preset_safe,
        ).pack(fill=tk.X, pady=2)

        ttk.Button(
            preset_box,
            text="3. Multi-Instance Cycle (Safe via Reduction)",
            command=self.on_load_preset_multi,
        ).pack(fill=tk.X, pady=2)

        # 2. Add Process & Resource
        add_box = ttk.LabelFrame(ctrl_frame, text="Add Nodes", padding=8)
        add_box.pack(fill=tk.X, pady=4)

        # Process
        p_row = ttk.Frame(add_box)
        p_row.pack(fill=tk.X, pady=2)
        ttk.Label(p_row, text="Process:").pack(side=tk.LEFT)
        self.proc_entry = ttk.Entry(p_row, width=8)
        self.proc_entry.pack(side=tk.LEFT, padx=4)
        ttk.Button(p_row, text="+ Add Process", command=self.on_add_process).pack(side=tk.RIGHT)

        # Resource
        r_row = ttk.Frame(add_box)
        r_row.pack(fill=tk.X, pady=2)
        ttk.Label(r_row, text="Resource:").pack(side=tk.LEFT)
        self.res_entry = ttk.Entry(r_row, width=8)
        self.res_entry.pack(side=tk.LEFT, padx=4)
        ttk.Label(r_row, text="Units:").pack(side=tk.LEFT)
        self.res_units = ttk.Spinbox(r_row, from_=1, to=10, width=4)
        self.res_units.set(1)
        self.res_units.pack(side=tk.LEFT, padx=2)
        ttk.Button(r_row, text="+ Add Resource", command=self.on_add_resource).pack(side=tk.RIGHT)

        # 3. Add Edges (Allocation or Request)
        edge_box = ttk.LabelFrame(ctrl_frame, text="Add Edge", padding=8)
        edge_box.pack(fill=tk.X, pady=4)

        e_row1 = ttk.Frame(edge_box)
        e_row1.pack(fill=tk.X, pady=2)
        ttk.Label(e_row1, text="Process:").pack(side=tk.LEFT)
        self.edge_proc_combo = ttk.Combobox(e_row1, width=7, state="readonly")
        self.edge_proc_combo.pack(side=tk.LEFT, padx=4)

        ttk.Label(e_row1, text="Resource:").pack(side=tk.LEFT)
        self.edge_res_combo = ttk.Combobox(e_row1, width=7, state="readonly")
        self.edge_res_combo.pack(side=tk.LEFT, padx=4)

        e_row2 = ttk.Frame(edge_box)
        e_row2.pack(fill=tk.X, pady=3)
        ttk.Label(e_row2, text="Type:").pack(side=tk.LEFT)
        self.edge_type_var = tk.StringVar(value="ALLOC")
        ttk.Radiobutton(
            e_row2, text="Allocate (R → P)", variable=self.edge_type_var, value="ALLOC"
        ).pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(
            e_row2, text="Request (P → R)", variable=self.edge_type_var, value="REQ"
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(edge_box, text="+ Connect Edge", command=self.on_add_edge).pack(
            fill=tk.X, pady=4
        )

        # 4. Action Buttons
        act_box = ttk.LabelFrame(ctrl_frame, text="Simulation & Detection", padding=8)
        act_box.pack(fill=tk.X, pady=6)

        detect_btn = tk.Button(
            act_box,
            text="🔍 DETECT DEADLOCK",
            font=("Helvetica", 11, "bold"),
            bg="#27ae60",
            fg="white",
            relief=tk.RAISED,
            pady=6,
            command=self.run_deadlock_detection,
        )
        detect_btn.pack(fill=tk.X, pady=3)

        ttk.Button(act_box, text="↺ Clear Graph", command=self.on_clear_graph).pack(
            fill=tk.X, pady=2
        )

        # ----------------- RIGHT PANEL (Graph + Trace) -----------------
        right_pane = ttk.PanedWindow(main_pane, orient=tk.VERTICAL)
        main_pane.add(right_pane, weight=1)

        # Graph Canvas
        canvas_frame = ttk.LabelFrame(right_pane, text="Resource Allocation Graph Visualizer", padding=4)
        right_pane.add(canvas_frame, weight=3)

        self.canvas = tk.Canvas(canvas_frame, bg="#fafafa", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Configure>", lambda e: self.draw_graph())

        # Trace Log
        trace_frame = ttk.LabelFrame(right_pane, text="Deadlock Detection Trace & Reduction Steps", padding=4)
        right_pane.add(trace_frame, weight=1)

        self.trace_text = tk.Text(trace_frame, height=7, font=("Consolas", 10), state=tk.DISABLED)
        scroll = ttk.Scrollbar(trace_frame, command=self.trace_text.yview)
        self.trace_text.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.trace_text.pack(fill=tk.BOTH, expand=True)

    # ----------------- EVENT HANDLERS -----------------
    def on_load_preset_deadlock(self) -> None:
        self.rag.load_preset_deadlock()
        self._auto_layout_nodes()
        self.run_deadlock_detection()

    def on_load_preset_safe(self) -> None:
        self.rag.load_preset_safe()
        self._auto_layout_nodes()
        self.run_deadlock_detection()

    def on_load_preset_multi(self) -> None:
        self.rag.load_preset_multi_instance_cycle()
        self._auto_layout_nodes()
        self.run_deadlock_detection()

    def on_add_process(self) -> None:
        pid = self.proc_entry.get().strip().upper()
        if not pid:
            messagebox.showwarning("Input Error", "Please enter a Process ID (e.g. P1).")
            return
        ok, msg = self.rag.add_process(pid)
        if not ok:
            messagebox.showwarning("Error", msg)
            return
        self.proc_entry.delete(0, tk.END)
        self._auto_layout_nodes()
        self.refresh_ui()

    def on_add_resource(self) -> None:
        rid = self.res_entry.get().strip().upper()
        if not rid:
            messagebox.showwarning("Input Error", "Please enter a Resource ID (e.g. R1).")
            return
        try:
            units = int(self.res_units.get())
        except ValueError:
            units = 1
        ok, msg = self.rag.add_resource(rid, units)
        if not ok:
            messagebox.showwarning("Error", msg)
            return
        self.res_entry.delete(0, tk.END)
        self._auto_layout_nodes()
        self.refresh_ui()

    def on_add_edge(self) -> None:
        pid = self.edge_proc_combo.get().strip()
        rid = self.edge_res_combo.get().strip()
        if not pid or not rid:
            messagebox.showwarning("Input Error", "Select both a Process and a Resource.")
            return

        edge_type = self.edge_type_var.get()
        if edge_type == "ALLOC":
            ok, msg = self.rag.add_allocation(rid, pid, 1)
        else:
            ok, msg = self.rag.add_request(pid, rid, 1)

        if not ok:
            messagebox.showerror("Cannot Add Edge", msg)
            return

        self.run_deadlock_detection()

    def on_clear_graph(self) -> None:
        self.rag.clear()
        self.node_positions.clear()
        self.last_analysis = None
        self.banner.configure(text="RAG SIMULATOR — GRAPH CLEARED", bg="#2c3e50")
        self._log_trace("Graph cleared. Select a preset or add new nodes.")
        self.refresh_ui()

    def run_deadlock_detection(self) -> None:
        self.last_analysis = self.rag.detect_deadlock()
        res = self.last_analysis

        # Update banner
        if res["deadlocked"]:
            blocked_str = ", ".join(res["deadlocked_processes"])
            self.banner.configure(
                text=f"STATUS: DEADLOCK DETECTED! Processes blocked: {blocked_str}",
                bg="#c0392b",
            )
        else:
            seq_str = " -> ".join(res["safe_sequence"]) if res["safe_sequence"] else "None"
            self.banner.configure(
                text=f"STATUS: SAFE (NO DEADLOCK). Safe Sequence: {seq_str}",
                bg="#27ae60",
            )

        # Log trace steps
        self._log_trace("\n".join(res["steps"]))
        self.refresh_ui()

    def _log_trace(self, text: str) -> None:
        self.trace_text.configure(state=tk.NORMAL)
        self.trace_text.delete("1.0", tk.END)
        self.trace_text.insert(tk.END, text)
        self.trace_text.configure(state=tk.DISABLED)

    # ----------------- GRAPH RENDERING & LAYOUT -----------------
    def _auto_layout_nodes(self) -> None:
        w = max(self.canvas.winfo_width(), 650)
        h = max(self.canvas.winfo_height(), 380)

        procs = sorted(self.rag.processes)
        res = sorted(self.rag.resources.keys())

        # Processes on upper row
        for i, p in enumerate(procs):
            x = (w / (len(procs) + 1)) * (i + 1)
            self.node_positions[p] = (x, h * 0.28)

        # Resources on lower row
        for i, r in enumerate(res):
            x = (w / (len(res) + 1)) * (i + 1)
            self.node_positions[r] = (x, h * 0.72)

    def refresh_ui(self) -> None:
        procs = sorted(self.rag.processes)
        res = sorted(self.rag.resources.keys())

        self.edge_proc_combo["values"] = procs
        if procs and self.edge_proc_combo.get() not in procs:
            self.edge_proc_combo.set(procs[0])
        elif not procs:
            self.edge_proc_combo.set("")

        self.edge_res_combo["values"] = res
        if res and self.edge_res_combo.get() not in res:
            self.edge_res_combo.set(res[0])
        elif not res:
            self.edge_res_combo.set("")

        self.draw_graph()

    def draw_graph(self) -> None:
        self.canvas.delete("all")
        if not self.rag.processes and not self.rag.resources:
            w = max(self.canvas.winfo_width(), 650)
            h = max(self.canvas.winfo_height(), 380)
            self.canvas.create_text(
                w / 2,
                h / 2,
                text="Graph is empty.\nClick a Preset Scenario on the left or add nodes to simulate.",
                font=("Helvetica", 12),
                fill="#888",
                justify=tk.CENTER,
            )
            return

        deadlocked_set = set()
        cycle_edges = set()
        if self.last_analysis and self.last_analysis["deadlocked"]:
            deadlocked_set = set(self.last_analysis["deadlocked_processes"])
            for cycle in self.last_analysis["cycles"]:
                for i in range(len(cycle) - 1):
                    cycle_edges.add((cycle[i], cycle[i + 1]))

        # Draw Edges first so they sit under the nodes
        # 1. Allocation Edges (R -> P)
        for r, allocs in self.rag.allocations.items():
            for p, count in allocs.items():
                if count > 0 and r in self.node_positions and p in self.node_positions:
                    is_cycle = (r, p) in cycle_edges
                    color = "#e74c3c" if is_cycle else "#27ae60"
                    width = 3 if is_cycle else 2
                    self._draw_arrow(
                        self.node_positions[r],
                        self.node_positions[p],
                        color,
                        width,
                        f"Alloc: {count}",
                    )

        # 2. Request Edges (P -> R)
        for p, reqs in self.rag.requests.items():
            for r, count in reqs.items():
                if count > 0 and p in self.node_positions and r in self.node_positions:
                    is_cycle = (p, r) in cycle_edges
                    color = "#e74c3c" if is_cycle else "#d35400"
                    width = 3 if is_cycle else 2
                    self._draw_arrow(
                        self.node_positions[p],
                        self.node_positions[r],
                        color,
                        width,
                        f"Req: {count}",
                    )

        # Draw Nodes
        # Processes = Circles
        for p in self.rag.processes:
            if p not in self.node_positions:
                continue
            x, y = self.node_positions[p]
            is_deadlocked = p in deadlocked_set
            fill_color = "#fadbd8" if is_deadlocked else "#d4e6f1"
            outline_color = "#c0392b" if is_deadlocked else "#2980b9"
            r = 30
            self.canvas.create_oval(
                x - r,
                y - r,
                x + r,
                y + r,
                fill=fill_color,
                outline=outline_color,
                width=3 if is_deadlocked else 2,
                tags=("node", p),
            )
            label = f"{p}\n[DEADLOCKED]" if is_deadlocked else p
            self.canvas.create_text(
                x,
                y,
                text=label,
                font=("Helvetica", 10, "bold"),
                fill="#900" if is_deadlocked else "#1a5276",
                justify=tk.CENTER,
                tags=("node", p),
            )

        # Resources = Squares with instances dots
        for r in self.rag.resources:
            if r not in self.node_positions:
                continue
            x, y = self.node_positions[r]
            total = self.rag.resources[r]
            free = self.rag.available_instances(r)
            w_box, h_box = 44, 40
            self.canvas.create_rectangle(
                x - w_box,
                y - h_box,
                x + w_box,
                y + h_box,
                fill="#fcf3cf",
                outline="#f39c12",
                width=2,
                tags=("node", r),
            )
            self.canvas.create_text(
                x,
                y - 10,
                text=r,
                font=("Helvetica", 11, "bold"),
                fill="#7d6608",
                tags=("node", r),
            )
            self.canvas.create_text(
                x,
                y + 12,
                text=f"Free: {free}/{total}",
                font=("Helvetica", 9),
                fill="#555",
                tags=("node", r),
            )

    def _draw_arrow(
        self,
        from_pos: Tuple[float, float],
        to_pos: Tuple[float, float],
        color: str,
        width: int,
        label: str,
    ) -> None:
        fx, fy = from_pos
        tx, ty = to_pos
        dx = tx - fx
        dy = ty - fy
        dist = math.hypot(dx, dy)
        if dist < 1:
            return

        # Shorten line slightly so arrow doesn't overlap node center
        node_radius = 34
        start_ratio = node_radius / dist
        end_ratio = 1 - (node_radius / dist)
        sx = fx + dx * start_ratio
        sy = fy + dy * start_ratio
        ex = fx + dx * end_ratio
        ey = fy + dy * end_ratio

        self.canvas.create_line(
            sx,
            sy,
            ex,
            ey,
            arrow=tk.LAST,
            arrowshape=(11, 13, 5),
            fill=color,
            width=width,
        )

        # Midpoint label
        mx = (sx + ex) / 2
        my = (sy + ey) / 2
        self.canvas.create_text(
            mx,
            my - 8,
            text=label,
            font=("Helvetica", 8, "bold"),
            fill=color,
        )

    # ----------------- CANVAS DRAG & DROP -----------------
    def on_canvas_click(self, event) -> None:
        items = self.canvas.find_withtag("current")
        if not items:
            return
        tags = self.canvas.gettags(items[0])
        for t in tags:
            if t in self.node_positions:
                self.drag_data["node"] = t
                self.drag_data["x"] = event.x
                self.drag_data["y"] = event.y
                break

    def on_canvas_drag(self, event) -> None:
        node = self.drag_data["node"]
        if not node:
            return
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        ox, oy = self.node_positions[node]
        self.node_positions[node] = (ox + dx, oy + dy)
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        self.draw_graph()

    def on_canvas_release(self, event) -> None:
        self.drag_data["node"] = None


def launch_gui(rag: ResourceAllocationGraph = None) -> None:
    root = tk.Tk()
    app = RAGGuiSimulator(root, rag)
    root.mainloop()
