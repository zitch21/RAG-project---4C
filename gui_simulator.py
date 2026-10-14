import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Tuple
from rag_engine import ResourceAllocationGraph


class RAGGuiSimulator:
    def __init__(self, root: tk.Tk, rag: ResourceAllocationGraph = None):
        self.root = root
        self.root.title("OS Project — Resource Allocation Graph (RAG) Interactive Simulator")
        self.root.geometry("1280x820")
        self.root.minsize(1080, 720)

        self.rag = rag or ResourceAllocationGraph()
        self.node_positions: Dict[str, Tuple[float, float]] = {}
        self.drag_data = {"node": None, "x": 0, "y": 0}

        self.sim_steps: List[str] = []
        self.sim_index: int = 0
        self.sim_running: bool = False
        self.sim_after_id = None

        self._build_ui()
        self._log("Simulator ready. Add nodes, build a queue, or Load a .txt simulation script.")
        self.refresh_all()

    def _build_ui(self) -> None:
        self.status_banner = tk.Label(
            self.root,
            text="[AUTO-ALLOC] SYSTEM STATUS: EMPTY GRAPH",
            font=("Helvetica", 13, "bold"),
            bg="#2c3e50",
            fg="white",
            pady=8,
        )
        self.status_banner.pack(fill=tk.X)

        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        ctrl_frame = ttk.Frame(main_pane, width=420)
        main_pane.add(ctrl_frame, weight=0)

        right_pane = ttk.PanedWindow(main_pane, orient=tk.VERTICAL)
        main_pane.add(right_pane, weight=1)

        mode_box = ttk.LabelFrame(
            ctrl_frame, text="1. Resource Allocation Mode (Automatic vs. Manual)", padding=6
        )
        mode_box.pack(fill=tk.X, padx=4, pady=3)

        self.auto_grant_var = tk.BooleanVar(value=True)
        ttk.Radiobutton(
            mode_box,
            text="Automatic (Allocate immediately if instances are free)",
            variable=self.auto_grant_var,
            value=True,
            command=self.on_toggle_alloc_mode,
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            mode_box,
            text="Manual (Keep P -> R request edge until manually granted)",
            variable=self.auto_grant_var,
            value=False,
            command=self.on_toggle_alloc_mode,
        ).pack(anchor=tk.W)

        node_box = ttk.LabelFrame(
            ctrl_frame, text="2. Create Processes & Resources", padding=6
        )
        node_box.pack(fill=tk.X, padx=4, pady=3)

        ttk.Label(node_box, text="Process ID:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.proc_entry = ttk.Entry(node_box, width=10)
        self.proc_entry.grid(row=0, column=1, padx=4, pady=2)
        ttk.Button(node_box, text="Add Now", command=self.on_add_process).grid(
            row=0, column=2, padx=2, pady=2
        )
        ttk.Button(node_box, text="+ Queue", command=self.on_queue_add_proc).grid(
            row=0, column=3, padx=2, pady=2
        )

        ttk.Label(node_box, text="Resource ID:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.res_entry = ttk.Entry(node_box, width=10)
        self.res_entry.grid(row=1, column=1, padx=4, pady=2)

        ttk.Label(node_box, text="Instances:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.res_inst_spin = ttk.Spinbox(node_box, from_=1, to=20, width=8)
        self.res_inst_spin.set(1)
        self.res_inst_spin.grid(row=2, column=1, padx=4, pady=2)
        ttk.Button(node_box, text="Add Now", command=self.on_add_resource).grid(
            row=1, column=2, rowspan=2, padx=2, pady=2
        )
        ttk.Button(node_box, text="+ Queue", command=self.on_queue_add_res).grid(
            row=1, column=3, rowspan=2, padx=2, pady=2
        )

        edge_box = ttk.LabelFrame(
            ctrl_frame, text="3. Resource Operations (Execute Now or Add to Queue)", padding=6
        )
        edge_box.pack(fill=tk.X, padx=4, pady=3)

        ttk.Label(edge_box, text="Action:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.op_type_combo = ttk.Combobox(
            edge_box,
            width=25,
            state="readonly",
            values=[
                "REQ (Process Requests Resource)",
                "GRANT (Grant Pending Request)",
                "ALLOC (Direct Allocate R -> P)",
                "REL (Process Releases Resource)",
                "CANCEL (Cancel Pending Request)",
            ],
        )
        self.op_type_combo.current(0)
        self.op_type_combo.grid(row=0, column=1, columnspan=3, sticky=tk.EW, padx=3, pady=2)

        ttk.Label(edge_box, text="Process:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.op_proc_combo = ttk.Combobox(edge_box, width=9)
        self.op_proc_combo.grid(row=1, column=1, padx=3, pady=2)

        ttk.Label(edge_box, text="Resource:").grid(row=1, column=2, sticky=tk.W, pady=2)
        self.op_res_combo = ttk.Combobox(edge_box, width=9)
        self.op_res_combo.grid(row=1, column=3, padx=3, pady=2)

        ttk.Label(edge_box, text="Instances:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.op_cnt_spin = ttk.Spinbox(edge_box, from_=1, to=20, width=8)
        self.op_cnt_spin.set(1)
        self.op_cnt_spin.grid(row=2, column=1, padx=3, pady=2)

        op_btns = ttk.Frame(edge_box)
        op_btns.grid(row=3, column=0, columnspan=4, pady=4)
        ttk.Button(op_btns, text="Execute Action Now", command=self.on_execute_selected_op).grid(
            row=0, column=0, padx=3, pady=2
        )
        ttk.Button(op_btns, text="+ Add Action to Queue", command=self.on_queue_selected_op).grid(
            row=0, column=1, padx=3, pady=2
        )
        ttk.Button(op_btns, text="Remove Node", command=self.on_remove_selected).grid(
            row=0, column=2, padx=3, pady=2
        )

        sim_box = ttk.LabelFrame(
            ctrl_frame,
            text="4. User Simulation Queue (Save/Load & Auto/Manual Run)",
            padding=6,
        )
        sim_box.pack(fill=tk.BOTH, expand=True, padx=4, pady=3)

        ttk.Label(
            sim_box,
            text="Enter commands (P, R, REQ, GRANT, ALLOC, REL, CHECK) or Load a .txt file:",
        ).pack(anchor=tk.W)

        script_frame = ttk.Frame(sim_box)
        script_frame.pack(fill=tk.BOTH, expand=True, pady=3)

        self.script_text = tk.Text(script_frame, height=7, width=38, font=("Courier", 9))
        s_scroll = ttk.Scrollbar(script_frame, command=self.script_text.yview)
        self.script_text.configure(yscrollcommand=s_scroll.set)
        s_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.script_text.pack(fill=tk.BOTH, expand=True)

        file_btns = ttk.Frame(sim_box)
        file_btns.pack(fill=tk.X, pady=2)
        ttk.Button(file_btns, text="Save Queue (.txt)", command=self.on_save_script_file).grid(
            row=0, column=0, padx=2, pady=2
        )
        ttk.Button(file_btns, text="Load Queue (.txt)", command=self.on_load_script_file).grid(
            row=0, column=1, padx=2, pady=2
        )
        ttk.Button(
            file_btns, text="Export Graph -> Queue", command=self.on_export_graph_to_queue
        ).grid(row=0, column=2, padx=2, pady=2)

        self.sim_progress_lbl = ttk.Label(
            sim_box, text="Simulation Status: Idle", font=("Helvetica", 9, "bold")
        )
        self.sim_progress_lbl.pack(anchor=tk.W, pady=2)

        sim_btns = ttk.Frame(sim_box)
        sim_btns.pack(fill=tk.X, pady=2)

        self.btn_auto_play = ttk.Button(
            sim_btns, text="▶ Run Auto", command=self.on_sim_auto_play
        )
        self.btn_auto_play.grid(row=0, column=0, padx=2, pady=2)

        self.btn_pause = ttk.Button(
            sim_btns, text="⏸ Pause", command=self.on_sim_pause, state=tk.DISABLED
        )
        self.btn_pause.grid(row=0, column=1, padx=2, pady=2)

        self.btn_step = ttk.Button(
            sim_btns, text="⏭ Next Step (Manual)", command=self.on_sim_step_manual
        )
        self.btn_step.grid(row=0, column=2, padx=2, pady=2)

        ttk.Button(sim_btns, text="↺ Reset Pointer", command=self.on_sim_reset).grid(
            row=0, column=3, padx=2, pady=2
        )

        speed_frame = ttk.Frame(sim_box)
        speed_frame.pack(fill=tk.X, pady=2)
        ttk.Label(speed_frame, text="Auto Step Delay (ms):").pack(side=tk.LEFT)
        self.speed_spin = ttk.Spinbox(
            speed_frame, from_=200, to=5000, increment=200, width=7
        )
        self.speed_spin.set(1000)
        self.speed_spin.pack(side=tk.LEFT, padx=4)
        ttk.Button(
            speed_frame,
            text="Clear Queue",
            command=self.on_clear_queue,
        ).pack(side=tk.RIGHT)

        util_box = ttk.LabelFrame(
            ctrl_frame, text="5. Deadlock Analysis & Graph Controls", padding=6
        )
        util_box.pack(fill=tk.X, padx=4, pady=3)

        u_grid = ttk.Frame(util_box)
        u_grid.pack(fill=tk.X)
        ttk.Button(
            u_grid, text="Run Deadlock Reduction Trace", command=self.on_run_trace
        ).grid(row=0, column=0, padx=2, pady=2, sticky=tk.EW)
        ttk.Button(
            u_grid, text="Auto-Arrange Nodes", command=self.on_rearrange
        ).grid(row=0, column=1, padx=2, pady=2, sticky=tk.EW)
        ttk.Button(
            u_grid, text="Clear Graph", command=self.on_clear
        ).grid(row=0, column=2, padx=2, pady=2, sticky=tk.EW)

        canvas_container = ttk.Frame(right_pane)
        right_pane.add(canvas_container, weight=3)

        self.canvas = tk.Canvas(canvas_container, bg="#f8f9fa", highlightthickness=1)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Configure>", lambda e: self.draw_graph())

        log_container = ttk.LabelFrame(
            right_pane, text="Live Simulation & Deadlock Reduction Log", padding=4
        )
        right_pane.add(log_container, weight=1)

        self.log_text = tk.Text(
            log_container, height=8, font=("Courier", 10), state=tk.DISABLED
        )
        scroll = ttk.Scrollbar(log_container, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _log(self, text: str) -> None:
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"> {text}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _append_script_line(self, cmd: str) -> None:
        current = self.script_text.get("1.0", tk.END).strip()
        if current:
            self.script_text.insert(tk.END, f"\n{cmd}")
        else:
            self.script_text.insert("1.0", cmd)
        self.script_text.see(tk.END)
        self._log(f"Added to simulation queue: {cmd}")

    def _auto_layout_nodes(self) -> None:
        w = max(self.canvas.winfo_width(), 760)
        h = max(self.canvas.winfo_height(), 440)

        procs = sorted(self.rag.processes)
        res = sorted(self.rag.resources.keys())

        for idx, pid in enumerate(procs):
            x = (w / (len(procs) + 1)) * (idx + 1)
            self.node_positions[pid] = (x, h * 0.26)

        for idx, rid in enumerate(res):
            x = (w / (len(res) + 1)) * (idx + 1)
            self.node_positions[rid] = (x, h * 0.74)

    def _ensure_node_positions(self) -> None:
        valid_nodes = self.rag.processes.union(self.rag.resources.keys())
        for k in list(self.node_positions.keys()):
            if k not in valid_nodes:
                del self.node_positions[k]

        need_layout = False
        for pid in self.rag.processes:
            if pid not in self.node_positions:
                need_layout = True
        for rid in self.rag.resources:
            if rid not in self.node_positions:
                need_layout = True
        if need_layout:
            self._auto_layout_nodes()

    def refresh_all(self) -> None:
        self._ensure_node_positions()
        procs = sorted(self.rag.processes)
        res = sorted(self.rag.resources.keys())
        self.op_proc_combo["values"] = procs
        if procs and self.op_proc_combo.get() not in procs:
            self.op_proc_combo.set(procs[0])
        elif not procs:
            self.op_proc_combo.set("")

        self.op_res_combo["values"] = res
        if res and self.op_res_combo.get() not in res:
            self.op_res_combo.set(res[0])
        elif not res:
            self.op_res_combo.set("")

        self.draw_graph()

    def draw_graph(self) -> None:
        self.canvas.delete("all")
        mode_tag = "AUTO-ALLOC" if self.rag.auto_grant else "MANUAL-ALLOC"

        if not self.rag.processes and not self.rag.resources:
            self.status_banner.configure(
                text=f"[{mode_tag}] SYSTEM STATUS: EMPTY GRAPH — Add nodes or run your simulation queue",
                bg="#2c3e50",
            )
            w = max(self.canvas.winfo_width(), 760)
            h = max(self.canvas.winfo_height(), 440)
            self.canvas.create_text(
                w / 2,
                h / 2,
                text="Graph is empty.\nUse the left panel to add Processes & Resources, build a Queue, or Load a .txt Script.",
                font=("Helvetica", 12),
                fill="#7f8c8d",
                justify=tk.CENTER,
            )
            return

        analysis = self.rag.detect_deadlock()
        deadlocked_procs = set(analysis["deadlocked_processes"])

        if analysis["deadlocked"]:
            self.status_banner.configure(
                text=f"[{mode_tag}] SYSTEM STATUS: DEADLOCK DETECTED! Blocked: {', '.join(sorted(deadlocked_procs))}",
                bg="#c0392b",
            )
        else:
            safe_seq = (
                " -> ".join(analysis["safe_sequence"])
                if analysis["safe_sequence"]
                else "None"
            )
            self.status_banner.configure(
                text=f"[{mode_tag}] SYSTEM STATUS: SAFE (Reduction Order: {safe_seq})",
                bg="#1e8449",
            )

        for rid in sorted(self.rag.resources):
            for pid, count in self.rag.allocations[rid].items():
                if count > 0 and rid in self.node_positions and pid in self.node_positions:
                    x1, y1 = self.node_positions[rid]
                    x2, y2 = self.node_positions[pid]
                    self._draw_curved_arrow(
                        x1,
                        y1,
                        x2,
                        y2,
                        color="#27ae60",
                        dash=None,
                        label=f"Alloc ({count})" if count > 1 else "Alloc",
                        offset=-18,
                    )

        for pid in sorted(self.rag.processes):
            for rid, count in self.rag.requests[pid].items():
                if count > 0 and pid in self.node_positions and rid in self.node_positions:
                    x1, y1 = self.node_positions[pid]
                    x2, y2 = self.node_positions[rid]
                    edge_color = "#e74c3c" if pid in deadlocked_procs else "#e67e22"
                    self._draw_curved_arrow(
                        x1,
                        y1,
                        x2,
                        y2,
                        color=edge_color,
                        dash=(6, 4),
                        label=f"Req ({count})" if count > 1 else "Req",
                        offset=18,
                    )

        r_proc = 30
        for pid in sorted(self.rag.processes):
            x, y = self.node_positions[pid]
            is_dead = pid in deadlocked_procs
            fill_color = "#fadbd8" if is_dead else "#d6eaf8"
            outline_color = "#c0392b" if is_dead else "#2980b9"
            self.canvas.create_oval(
                x - r_proc,
                y - r_proc,
                x + r_proc,
                y + r_proc,
                fill=fill_color,
                outline=outline_color,
                width=3,
                tags=("node", pid),
            )
            self.canvas.create_text(
                x,
                y,
                text=pid,
                font=("Helvetica", 12, "bold"),
                fill="#2c3e50",
                tags=("node", pid),
            )

        w_res, h_res = 42, 34
        for rid, total_inst in sorted(self.rag.resources.items()):
            x, y = self.node_positions[rid]
            avail = self.rag.available_instances(rid)
            self.canvas.create_rectangle(
                x - w_res,
                y - h_res,
                x + w_res,
                y + h_res,
                fill="#eaecee",
                outline="#5d6d7e",
                width=3,
                tags=("node", rid),
            )
            self.canvas.create_text(
                x,
                y - 14,
                text=f"{rid} ({avail}/{total_inst})",
                font=("Helvetica", 10, "bold"),
                fill="#2c3e50",
                tags=("node", rid),
            )
            dot_spacing = min(14, (w_res * 1.6) / max(total_inst, 1))
            start_x = x - ((total_inst - 1) * dot_spacing) / 2
            for i in range(total_inst):
                dx = start_x + i * dot_spacing
                dy = y + 10
                dot_fill = "#2ecc71" if i < avail else "#7f8c8d"
                self.canvas.create_oval(
                    dx - 4,
                    dy - 4,
                    dx + 4,
                    dy + 4,
                    fill=dot_fill,
                    outline="#2c3e50",
                    tags=("node", rid),
                )

    def _draw_curved_arrow(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        color: str,
        dash: Tuple[int, int] = None,
        label: str = "",
        offset: float = 16.0,
    ) -> None:
        dx = x2 - x1
        dy = y2 - y1
        dist = math.hypot(dx, dy)
        if dist < 1e-3:
            return

        ux, uy = dx / dist, dy / dist
        nx, ny = -uy, ux

        margin = 34
        sx = x1 + ux * margin
        sy = y1 + uy * margin
        ex = x2 - ux * margin
        ey = y2 - uy * margin

        mx = (sx + ex) / 2 + nx * offset
        my = (sy + ey) / 2 + ny * offset

        line_kwargs = {
            "fill": color,
            "width": 2.5,
            "arrow": tk.LAST,
            "arrowshape": (12, 15, 5),
            "smooth": True,
        }
        if dash:
            line_kwargs["dash"] = dash

        self.canvas.create_line(sx, sy, mx, my, ex, ey, **line_kwargs)
        if label:
            self.canvas.create_text(
                mx,
                my - 8,
                text=label,
                font=("Helvetica", 9, "bold"),
                fill=color,
            )

    def on_save_script_file(self) -> None:
        script_content = self.script_text.get("1.0", tk.END).strip()
        if not script_content:
            if self.rag.processes or self.rag.resources:
                ask = messagebox.askyesno(
                    "Queue Empty",
                    "The simulation queue is empty, but the graph has nodes.\nExport current graph state and save it?",
                )
                if ask:
                    script_content = self.rag.export_current_state_as_script()
                    self.script_text.insert("1.0", script_content)
                else:
                    return
            else:
                messagebox.showwarning(
                    "Nothing to Save", "Enter or queue simulation commands before saving."
                )
                return

        filepath = filedialog.asksaveasfilename(
            title="Save Simulation Script",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if not filepath:
            return
        ok, msg = self.rag.save_script_to_file(filepath, script_content)
        self._log(msg)
        if not ok:
            messagebox.showerror("Save Error", msg)

    def on_load_script_file(self) -> None:
        filepath = filedialog.askopenfilename(
            title="Load Simulation Script",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if not filepath:
            return
        ok, msg, content = self.rag.load_script_from_file(filepath)
        self._log(msg)
        if not ok:
            messagebox.showerror("Load Error", msg)
            return

        self.on_sim_pause()
        self.script_text.delete("1.0", tk.END)
        self.script_text.insert("1.0", content.strip())
        self.sim_steps = self.rag.parse_simulation_script(content)
        self.sim_index = 0
        self.sim_progress_lbl.configure(
            text=f"Loaded {len(self.sim_steps)} steps (Ready: Click Run Auto or Next Step)"
        )

    def on_export_graph_to_queue(self) -> None:
        if not self.rag.processes and not self.rag.resources:
            messagebox.showinfo("Graph Empty", "Add processes and resources to the graph first.")
            return
        script_content = self.rag.export_current_state_as_script()
        self.on_sim_pause()
        self.script_text.delete("1.0", tk.END)
        self.script_text.insert("1.0", script_content)
        self.sim_steps = self.rag.parse_simulation_script(script_content)
        self.sim_index = 0
        self.sim_progress_lbl.configure(
            text=f"Exported {len(self.sim_steps)} steps from current graph"
        )
        self._log("Exported live graph state into the simulation queue.")

    def _prepare_sim_steps_if_needed(self) -> bool:
        raw_script = self.script_text.get("1.0", tk.END)
        parsed = self.rag.parse_simulation_script(raw_script)
        if not parsed:
            messagebox.showinfo(
                "Simulation Queue Empty",
                "Add, type, or load commands in Section 4 before running the simulation.",
            )
            return False
        if self.sim_steps != parsed or self.sim_index >= len(parsed):
            self.sim_steps = parsed
            self.sim_index = 0
        return True

    def _execute_next_sim_step(self) -> bool:
        if self.sim_index >= len(self.sim_steps):
            self.sim_progress_lbl.configure(
                text=f"Simulation Complete ({len(self.sim_steps)}/{len(self.sim_steps)} steps)"
            )
            self.on_sim_pause()
            return False

        cmd = self.sim_steps[self.sim_index]
        self.sim_index += 1
        _, msg = self.rag.execute_command(cmd)
        self.auto_grant_var.set(self.rag.auto_grant)
        self._log(f"[Step {self.sim_index}/{len(self.sim_steps)}] {cmd}  ==>  {msg}")
        self.sim_progress_lbl.configure(
            text=f"Step {self.sim_index}/{len(self.sim_steps)}: {cmd}"
        )
        self.refresh_all()

        if self.sim_index >= len(self.sim_steps):
            self.sim_progress_lbl.configure(
                text=f"Simulation Finished ({len(self.sim_steps)}/{len(self.sim_steps)}): Last='{cmd}'"
            )
            self.on_sim_pause()
            return False
        return True

    def on_sim_auto_play(self) -> None:
        if not self._prepare_sim_steps_if_needed():
            return
        self.sim_running = True
        self.btn_auto_play.configure(state=tk.DISABLED)
        self.btn_pause.configure(state=tk.NORMAL)
        self._schedule_next_auto_step()

    def _schedule_next_auto_step(self) -> None:
        if not self.sim_running:
            return
        has_more = self._execute_next_sim_step()
        if has_more and self.sim_running:
            try:
                delay_ms = max(100, int(self.speed_spin.get()))
            except ValueError:
                delay_ms = 1000
            self.sim_after_id = self.root.after(delay_ms, self._schedule_next_auto_step)

    def on_sim_pause(self) -> None:
        self.sim_running = False
        if self.sim_after_id is not None:
            self.root.after_cancel(self.sim_after_id)
            self.sim_after_id = None
        self.btn_auto_play.configure(state=tk.NORMAL)
        self.btn_pause.configure(state=tk.DISABLED)

    def on_sim_step_manual(self) -> None:
        self.on_sim_pause()
        if not self._prepare_sim_steps_if_needed():
            return
        self._execute_next_sim_step()

    def on_sim_reset(self) -> None:
        self.on_sim_pause()
        self.sim_index = 0
        self.sim_progress_lbl.configure(
            text="Simulation Status: Pointer reset to Step 1"
        )
        self._log("Reset simulation queue pointer to Step 1.")

    def on_clear_queue(self) -> None:
        self.on_sim_pause()
        self.script_text.delete("1.0", tk.END)
        self.sim_steps = []
        self.sim_index = 0
        self.sim_progress_lbl.configure(text="Simulation Status: Queue cleared")

    def _build_selected_op_command(self) -> str:
        op_label = self.op_type_combo.get()
        op_code = op_label.split()[0].upper()
        pid = self.op_proc_combo.get().strip().upper() or self.proc_entry.get().strip().upper()
        rid = self.op_res_combo.get().strip().upper() or self.res_entry.get().strip().upper()
        cnt = self.op_cnt_spin.get().strip() or "1"

        if not pid or not rid:
            messagebox.showwarning(
                "Missing Input", "Specify both a Process ID and a Resource ID."
            )
            return ""

        if op_code == "ALLOC":
            return f"ALLOC {rid} {pid} {cnt}"
        elif op_code == "CANCEL":
            return f"CANCEL {pid} {rid}"
        else:
            return f"{op_code} {pid} {rid} {cnt}"

    def on_execute_selected_op(self) -> None:
        cmd = self._build_selected_op_command()
        if not cmd:
            return
        _, msg = self.rag.execute_command(cmd)
        self._log(msg)
        self.refresh_all()

    def on_queue_selected_op(self) -> None:
        cmd = self._build_selected_op_command()
        if not cmd:
            return
        self._append_script_line(cmd)

    def on_queue_add_proc(self) -> None:
        pid = self.proc_entry.get().strip().upper()
        if not pid:
            messagebox.showwarning("Missing Input", "Enter a Process ID first.")
            return
        self._append_script_line(f"ADD_P {pid}")
        self.proc_entry.delete(0, tk.END)

    def on_queue_add_res(self) -> None:
        rid = self.res_entry.get().strip().upper()
        inst = self.res_inst_spin.get().strip() or "1"
        if not rid:
            messagebox.showwarning("Missing Input", "Enter a Resource ID first.")
            return
        self._append_script_line(f"ADD_R {rid} {inst}")
        self.res_entry.delete(0, tk.END)

    def on_toggle_alloc_mode(self) -> None:
        enabled = self.auto_grant_var.get()
        msg = self.rag.set_auto_grant(enabled)
        self._log(msg)
        self.refresh_all()

    def on_canvas_click(self, event) -> None:
        items = self.canvas.find_overlapping(
            event.x - 4, event.y - 4, event.x + 4, event.y + 4
        )
        for item in reversed(items):
            tags = self.canvas.gettags(item)
            if "node" in tags and len(tags) >= 2:
                self.drag_data["node"] = tags[1]
                self.drag_data["x"] = event.x
                self.drag_data["y"] = event.y
                break

    def on_canvas_drag(self, event) -> None:
        node = self.drag_data["node"]
        if node:
            self.node_positions[node] = (event.x, event.y)
            self.draw_graph()

    def on_canvas_release(self, event) -> None:
        self.drag_data["node"] = None

    def on_add_process(self) -> None:
        pid = self.proc_entry.get().strip().upper()
        ok, msg = self.rag.add_process(pid)
        self._log(msg)
        if ok:
            self._auto_layout_nodes()
            self.proc_entry.delete(0, tk.END)
        self.refresh_all()

    def on_add_resource(self) -> None:
        rid = self.res_entry.get().strip().upper()
        try:
            inst = int(self.res_inst_spin.get())
        except ValueError:
            inst = 1
        ok, msg = self.rag.add_resource(rid, inst)
        self._log(msg)
        if ok:
            self._auto_layout_nodes()
            self.res_entry.delete(0, tk.END)
        self.refresh_all()

    def on_remove_selected(self) -> None:
        pid = self.op_proc_combo.get().strip().upper()
        rid = self.op_res_combo.get().strip().upper()
        if not pid and not rid:
            messagebox.showinfo("Remove Node", "Select a Process or Resource first.")
            return
        choice = messagebox.askquestion(
            "Remove Node",
            f"Click 'Yes' to remove Process ({pid or 'None'}), or 'No' to remove Resource ({rid or 'None'}).",
        )
        if choice == "yes" and pid:
            _, msg = self.rag.remove_process(pid)
            self.node_positions.pop(pid, None)
            self._log(msg)
        elif rid:
            _, msg = self.rag.remove_resource(rid)
            self.node_positions.pop(rid, None)
            self._log(msg)
        self.refresh_all()

    def on_run_trace(self) -> None:
        if not self.rag.processes and not self.rag.resources:
            self._log("Graph is empty. Add processes and resources first.")
            return
        res = self.rag.detect_deadlock()
        self._log("=== GRAPH REDUCTION TRACE ===")
        for step in res["steps"]:
            self._log(f"  {step}")
        if res["cycles"]:
            for cyc in res["cycles"]:
                self._log("  Cycle: " + " -> ".join(cyc))
        self.refresh_all()

    def on_rearrange(self) -> None:
        self._auto_layout_nodes()
        self.draw_graph()

    def on_clear(self) -> None:
        self.on_sim_pause()
        self.rag.clear()
        self.node_positions.clear()
        self._log("Cleared all processes, resources, and edges.")
        self.refresh_all()


def launch_gui(rag: ResourceAllocationGraph = None) -> None:
    root = tk.Tk()
    RAGGuiSimulator(root, rag)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
