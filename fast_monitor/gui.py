from __future__ import annotations

import os
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

from fast_monitor.core import MonitorConfig, default_log_path, get_base_dir, run_monitor


def main() -> None:
    root = tk.Tk()
    root.title("Fast.com speed monitor")
    root.minsize(520, 440)

    mode_var = tk.StringVar(value="normal")
    runs_var = tk.IntVar(value=6)
    interval_var = tk.IntVar(value=10)
    stop_event = threading.Event()

    status_var = tk.StringVar(value="Idle.")
    log_path_var = tk.StringVar(value=str(default_log_path()))

    frm = ttk.Frame(root, padding=10)
    frm.pack(fill="both", expand=True)

    log = scrolledtext.ScrolledText(
        frm, height=14, state="disabled", wrap="word", font=("Segoe UI", 9)
    )

    def append_log_ui(line: str) -> None:
        def _do() -> None:
            log.configure(state="normal")
            log.insert("end", line + "\n")
            log.see("end")
            log.configure(state="disabled")

        root.after(0, _do)

    worker: list[threading.Thread | None] = [None]

    def set_running(running: bool) -> None:
        start_btn.configure(state="disabled" if running else "normal")
        stop_btn.configure(state="normal" if running else "disabled")

    def start_run() -> None:
        stop_event.clear()
        n = runs_var.get()
        m = interval_var.get()
        if n < 1 or m < 0:
            messagebox.showerror(
                "Invalid input", "Runs must be at least 1; interval must be 0 or more."
            )
            return

        mode = mode_var.get()
        config = MonitorConfig(
            num_runs=n,
            interval_sec=m * 60,
            headless=(mode == "headless"),
            minimized=(mode == "minimized"),
            show_toast=True,
        )

        def work() -> None:
            try:
                run_monitor(
                    config,
                    on_line=lambda s: root.after(0, append_log_ui, s),
                    on_progress=lambda c, t: root.after(
                        0,
                        lambda c=c, t=t: status_var.set(f"Run {c} of {t}…"),
                    ),
                    stop_event=stop_event,
                )
            except Exception as e:
                root.after(0, append_log_ui, f"Error: {e}")
            finally:
                root.after(0, lambda: set_running(False))
                root.after(0, lambda: status_var.set("Idle."))

        set_running(True)
        status_var.set("Starting…")
        log.configure(state="normal")
        log.delete("1.0", "end")
        log.configure(state="disabled")
        t = threading.Thread(target=work, daemon=True)
        worker[0] = t
        t.start()

    def stop_run() -> None:
        stop_event.set()
        status_var.set("Stopping…")

    def open_folder() -> None:
        d = get_base_dir()
        d.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(d)
        except OSError as e:
            messagebox.showerror("Open folder", str(e))

    ttk.Label(frm, text="Browser mode").grid(row=0, column=0, sticky="nw", pady=(0, 4))
    mode_frm = ttk.Frame(frm)
    mode_frm.grid(row=1, column=0, columnspan=4, sticky="w")
    ttk.Radiobutton(
        mode_frm, text="Normal window", variable=mode_var, value="normal"
    ).pack(side="left", padx=(0, 12))
    ttk.Radiobutton(
        mode_frm, text="Minimized", variable=mode_var, value="minimized"
    ).pack(side="left", padx=(0, 12))
    ttk.Radiobutton(
        mode_frm, text="Headless", variable=mode_var, value="headless"
    ).pack(side="left")

    ttk.Label(frm, text="Number of runs").grid(row=2, column=0, sticky="w", pady=(10, 0))
    runs_sb = tk.Spinbox(
        frm, from_=1, to=999, textvariable=runs_var, width=8, font=("Segoe UI", 9)
    )
    runs_sb.grid(row=2, column=1, sticky="w", pady=(10, 0), padx=(8, 24))

    ttk.Label(frm, text="Interval (minutes)").grid(row=2, column=2, sticky="w", pady=(10, 0))
    int_sb = tk.Spinbox(
        frm, from_=0, to=999, textvariable=interval_var, width=8, font=("Segoe UI", 9)
    )
    int_sb.grid(row=2, column=3, sticky="w", pady=(10, 0), padx=(8, 0))

    btn_frm = ttk.Frame(frm)
    btn_frm.grid(row=3, column=0, columnspan=4, sticky="w", pady=(14, 8))
    start_btn = ttk.Button(btn_frm, text="Start", command=start_run)
    start_btn.pack(side="left", padx=(0, 8))
    stop_btn = ttk.Button(btn_frm, text="Stop", command=stop_run, state="disabled")
    stop_btn.pack(side="left", padx=(0, 8))
    ttk.Button(btn_frm, text="Open log folder", command=open_folder).pack(
        side="left", padx=(0, 8)
    )

    ttk.Label(frm, textvariable=status_var).grid(
        row=4, column=0, columnspan=4, sticky="w"
    )
    ttk.Label(frm, textvariable=log_path_var, foreground="gray").grid(
        row=5, column=0, columnspan=4, sticky="w", pady=(4, 6)
    )

    log.grid(row=6, column=0, columnspan=4, sticky="nsew")
    frm.rowconfigure(6, weight=1)
    frm.columnconfigure(3, weight=1)

    root.mainloop()


if __name__ == "__main__":
    main()
