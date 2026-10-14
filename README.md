# Operating Systems - Resource Allocation Graph (RAG) Simulator

A simple, interactive simulator for Operating Systems **Resource Allocation Graphs (RAG)** and **Deadlock Detection** using the **Graph Reduction Algorithm** and **Cycle Detection**.

Built with standard Python (`tkinter`) - **no external dependencies or `pip install` required.**

---

## 🚀 How to Run the Program

### Method 1: Web Standalone Version (Works on ANY Device & OS)
* **`index.html`** - **Double-click to open in any web browser** (Chrome, Edge, Safari, Firefox). Works on Windows, Mac, Linux, Chromebooks, iPads, and phones! Zero installation, 100% offline.

### Method 2: Portable Windows Executable (For Flash Drives)
* **`RAG_Simulator.exe`** - **Runs on ANY Windows PC directly from your flash drive.** No Python or external software required! Just double-click it.

### Method 3: Double-Click Launcher (If Python is installed)
* **`run_gui.bat`** - Launches the interactive Visual GUI window.
* **`run_cli.bat`** - Launches the terminal Command-Line mode.

---

### Method 2: Command Line (PowerShell / Command Prompt)
Open a terminal in this folder (`c:\Users\emman\OneDrive\Desktop\RAG project - 4C`) and run:

* **Visual GUI Simulator (Default):**
  ```powershell
  python main.py
  ```

* **Terminal CLI Mode:**
  ```powershell
  python main.py --cli
  ```

---

### Method 3: In VS Code
1. Open the project folder in **Visual Studio Code**.
2. Open `main.py`.
3. Click the **Run** button (play icon at the top right) or press `F5`.

---

## 🖥️ How to Use the Visual GUI Simulator

When you launch the GUI, the window provides two main sections:
* **Left Panel:** Controls for presets, adding nodes, adding edges, and running detection.
* **Right Panel:** The live visual graph canvas and the step-by-step reduction log.

```
+-------------------------------------------------------------------------------+
|  STATUS BANNER: [GREEN: SAFE] or [RED: DEADLOCK DETECTED]                     |
+--------------------------+----------------------------------------------------+
|                          |                                                    |
|  1. Preset Scenarios     |  Visual Graph Canvas                               |
|     - Deadlock Scenario  |  - Processes: Circles                              |
|     - Safe State         |  - Resources: Squares (Free/Total units)           |
|     - Multi-Instance     |  - Green Arrows: Allocations (R -> P)              |
|                          |  - Orange Arrows: Requests (P -> R)                |
|  2. Add Nodes            |  - Red Highlights: Deadlocked nodes & cycles       |
|     - Process ID (P1)    |                                                    |
|     - Resource ID (R1)   |----------------------------------------------------|
|                          |  Deadlock Detection Trace Log                      |
|  3. Add Edges            |  - Available instances trace                       |
|     - Allocate (R -> P)  |  - Step-by-step reduction                          |
|     - Request (P -> R)   |  - Safe sequence / Deadlocked processes            |
|                          |                                                    |
|  4. [DETECT DEADLOCK]    |                                                    |
|     [Clear Graph]        |                                                    |
+--------------------------+----------------------------------------------------+
```

### 1. Trying Built-in Presets (1-Click)
Click any preset button on the top-left to load a scenario immediately:
* **1. Deadlock Scenario (Circular Wait):**
  Loads a classic circular wait ($P_1 \to R_2 \to P_2 \to R_1 \to P_1$). Both processes are blocked waiting for each other's held resource.
* **2. Safe State Scenario (Resolvable):**
  Loads a system where processes can be satisfied sequentially and finish without deadlock.
* **3. Multi-Instance Cycle:**
  Demonstrates that a cycle in a multi-instance resource graph is **not always a deadlock**. Process $P_3$ finishes first and releases its instance, breaking the bottleneck and allowing all processes to finish safely.

### 2. Building a Custom Graph
1. **Add Processes:** Type a process name (e.g. `P1`, `P2`) in the **Process** box and click **`+ Add Process`**.
2. **Add Resources:** Type a resource name (e.g. `R1`), choose the number of available units (e.g. `1` or `2`), and click **`+ Add Resource`**.
3. **Connect Edges:**
   * Select a **Process** and a **Resource** from the dropdowns.
   * Choose **`Allocate (R → P)`** if the process already holds this resource.
   * Choose **`Request (P → R)`** if the process is currently waiting/requesting this resource.
   * Click **`+ Connect Edge`**.
4. **Move Nodes:** Click and drag any circle or square on the canvas to rearrange them.

### 3. Detecting Deadlock
Click the green **`🔍 DETECT DEADLOCK`** button:
* The **Top Banner** updates to:
  * 🟢 **`SAFE (NO DEADLOCK)`** with the safe execution sequence.
  * 🔴 **`DEADLOCK DETECTED!`** listing which processes are stuck.
* On the canvas:
  * Deadlocked processes turn **Red**.
  * Circular wait edges turn **Bold Red**.
* In the **Trace Log** (bottom right):
  * Read the step-by-step reduction trace showing which process could be satisfied, what resources it released back to the system, and the final verdict.

---

## ⌨️ How to Use the CLI Mode

If you prefer running in the terminal:
```powershell
python main.py --cli
```

### Menu Options:
```
  1. Load Deadlock Scenario (Circular Wait)
  2. Load Safe State Scenario (Resolvable)
  3. Load Multi-Instance Cycle Scenario
  4. Add Process
  5. Add Resource
  6. Add Allocation (Resource -> Process)
  7. Add Request (Process -> Resource)
  8. View Current Graph State
  9. Run Deadlock Detection
  10. Clear Graph
  11. Remove Process
  12. Remove Resource
  0. Exit
```

Type a number (`0` to `12`) and press **Enter**.

---

## 📁 File Structure

| File | Description |
| :--- | :--- |
| **`index.html`** | **Standalone Web Version.** Opens in any browser on any device (Windows, Mac, Linux, iPad, Android). |
| **`RAG_Simulator.exe`** | **Standalone Windows executable.** Runs on any PC directly from a flash drive without installing Python. |
| **`main.py`** | Application entry point. Launches GUI by default, or CLI with `--cli`. |
| **`rag_engine.py`** | Core RAG data structure, cycle finder (DFS), and Graph Reduction algorithm. |
| **`gui_simulator.py`** | Interactive visual simulator window built with Python `tkinter`. |
| **`cli_ui.py`** | Terminal Command-Line Interface. |
| **`run_gui.bat`** | Windows shortcut to double-click and launch the GUI. |
| **`run_cli.bat`** | Windows shortcut to double-click and launch the CLI. |
| **`README.md`** | Complete user documentation and instructions. |

---

## 📚 Operating Systems Theory Reference

* **Allocation Edge ($R_j \to P_i$):** An instance of resource $R_j$ is currently held by process $P_i$.
* **Request Edge ($P_i \to R_j$):** Process $P_i$ is blocked and waiting for an instance of resource $R_j$.
* **Deadlock Conditions:**
  * **Single-instance resources:** A directed cycle in the graph is a **necessary and sufficient** condition for deadlock.
  * **Multi-instance resources:** A cycle is **necessary but not sufficient**. The simulator applies the **Graph Reduction Algorithm** (Banker's style reduction):
    1. Look for a process whose current requests can be satisfied by currently available resources ($Request_i \le Available$).
    2. If found, simulate its execution: the process terminates and returns all allocated resources back to the pool ($Available = Available + Allocation_i$).
    3. Repeat until no more processes can be satisfied.
    4. If any processes remain unfinished, those processes are in **Deadlock**.
