from __future__ import annotations

from pathlib import Path
from tkinter import StringVar, Tk
from tkinter import messagebox, scrolledtext, ttk

from console.commands import LABEL_CHOICES, OUTCOME_CHOICES, CommandSpec, build_command_sections
from console.runner import CommandResult, CommandRunner
from console.status import collect_status_rows, format_size

REPO_ROOT = Path(__file__).resolve().parents[1]


class OpsConsoleApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.runner = CommandRunner(REPO_ROOT)
        self.is_closing = False
        self.status_tree: ttk.Treeview | None = None
        self.log_text: scrolledtext.ScrolledText | None = None
        self.status_message = StringVar(value="Ready.")
        self.label_mint = StringVar()
        self.label_choice = StringVar(value=LABEL_CHOICES[0])
        self.label_note = StringVar()
        self.outcome_mint = StringVar()
        self.outcome_choice = StringVar(value=OUTCOME_CHOICES[0])
        self.outcome_note = StringVar()
        self.action_buttons: list[ttk.Button] = []

        self.root.title("memex-lab ops console v0")
        self.root.minsize(1120, 760)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_layout()
        self.refresh_status()
        self._poll_runner()

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=3)
        self.root.columnconfigure(1, weight=2)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=2)

        header = ttk.Frame(self.root, padding=12)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="memex-lab ops console v0",
            font=("Segoe UI", 14, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Thin Tkinter wrapper for offline pipeline and review CLI tools.",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Label(header, textvariable=self.status_message).grid(
            row=2, column=0, sticky="w", pady=(8, 0)
        )

        commands_frame = ttk.LabelFrame(self.root, text="Commands", padding=12)
        commands_frame.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=(0, 6))
        command_sections = build_command_sections()
        for section_index in range(len(command_sections)):
            commands_frame.columnconfigure(section_index, weight=1)

        for section_index, (section_name, specs) in enumerate(command_sections):
            section_frame = ttk.LabelFrame(commands_frame, text=section_name, padding=8)
            section_frame.grid(
                row=0,
                column=section_index,
                sticky="nsew",
                padx=4,
            )
            section_frame.columnconfigure(0, weight=1)

            for row_index, spec in enumerate(specs):
                button = ttk.Button(
                    section_frame,
                    text=spec.label,
                    command=lambda current_spec=spec: self._run_command_spec(current_spec),
                )
                button.grid(row=row_index, column=0, sticky="ew", pady=4)
                self.action_buttons.append(button)

        forms_frame = ttk.LabelFrame(self.root, text="Review actions", padding=12)
        forms_frame.grid(row=1, column=1, sticky="nsew", padx=(6, 12), pady=(0, 6))
        forms_frame.columnconfigure(0, weight=1)

        self._build_label_form(forms_frame)
        self._build_outcome_form(forms_frame)

        status_frame = ttk.LabelFrame(self.root, text="File status", padding=12)
        status_frame.grid(row=2, column=0, sticky="nsew", padx=(12, 6), pady=(0, 12))
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(1, weight=1)

        refresh_button = ttk.Button(status_frame, text="Refresh status", command=self.refresh_status)
        refresh_button.grid(row=0, column=0, sticky="w", pady=(0, 8))

        self.status_tree = ttk.Treeview(
            status_frame,
            columns=("name", "path", "state", "size", "modified"),
            show="headings",
            height=14,
        )
        self.status_tree.grid(row=1, column=0, sticky="nsew")
        self.status_tree.heading("name", text="File")
        self.status_tree.heading("path", text="Path")
        self.status_tree.heading("state", text="State")
        self.status_tree.heading("size", text="Size")
        self.status_tree.heading("modified", text="Modified")
        self.status_tree.column("name", width=160, anchor="w")
        self.status_tree.column("path", width=290, anchor="w")
        self.status_tree.column("state", width=90, anchor="center")
        self.status_tree.column("size", width=90, anchor="e")
        self.status_tree.column("modified", width=160, anchor="center")

        log_frame = ttk.LabelFrame(self.root, text="Command log", padding=12)
        log_frame.grid(row=2, column=1, sticky="nsew", padx=(6, 12), pady=(0, 12))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap="word",
            state="disabled",
            font=("Consolas", 10),
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")

    def _build_label_form(self, parent: ttk.LabelFrame) -> None:
        frame = ttk.LabelFrame(parent, text="Set or manage label", padding=8)
        frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Mint").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.label_mint).grid(
            row=0, column=1, sticky="ew", pady=2
        )

        ttk.Label(frame, text="Label").grid(row=1, column=0, sticky="w")
        ttk.Combobox(
            frame,
            textvariable=self.label_choice,
            values=LABEL_CHOICES,
            state="readonly",
        ).grid(row=1, column=1, sticky="ew", pady=2)

        ttk.Label(frame, text="Note").grid(row=2, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.label_note).grid(
            row=2, column=1, sticky="ew", pady=2
        )

        buttons = ttk.Frame(frame)
        buttons.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=1)
        buttons.columnconfigure(2, weight=1)

        set_button = ttk.Button(buttons, text="Set label", command=self._set_label)
        set_button.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        list_button = ttk.Button(buttons, text="List labels", command=self._list_labels)
        list_button.grid(row=0, column=1, sticky="ew", padx=4)
        remove_button = ttk.Button(buttons, text="Remove label", command=self._remove_label)
        remove_button.grid(row=0, column=2, sticky="ew", padx=(4, 0))

        self.action_buttons.extend((set_button, list_button, remove_button))

    def _build_outcome_form(self, parent: ttk.LabelFrame) -> None:
        frame = ttk.LabelFrame(parent, text="Record review outcome", padding=8)
        frame.grid(row=1, column=0, sticky="ew")
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Mint").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.outcome_mint).grid(
            row=0, column=1, sticky="ew", pady=2
        )

        ttk.Label(frame, text="Outcome").grid(row=1, column=0, sticky="w")
        ttk.Combobox(
            frame,
            textvariable=self.outcome_choice,
            values=OUTCOME_CHOICES,
            state="readonly",
        ).grid(row=1, column=1, sticky="ew", pady=2)

        ttk.Label(frame, text="Note").grid(row=2, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.outcome_note).grid(
            row=2, column=1, sticky="ew", pady=2
        )

        save_button = ttk.Button(
            frame,
            text="Store outcome",
            command=self._store_outcome,
        )
        save_button.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        self.action_buttons.append(save_button)

    def refresh_status(self) -> None:
        if self.status_tree is None:
            return

        for item_id in self.status_tree.get_children():
            self.status_tree.delete(item_id)

        for row in collect_status_rows(REPO_ROOT):
            self.status_tree.insert(
                "",
                "end",
                values=(
                    row.label,
                    row.relative_path,
                    "present" if row.exists else "missing",
                    format_size(row.size_bytes),
                    row.modified_at or "-",
                ),
            )

        self.status_message.set("Status refreshed.")

    def _set_label(self) -> None:
        mint = self.label_mint.get().strip()
        label = self.label_choice.get().strip()
        note = self.label_note.get().strip()
        if not mint:
            messagebox.showerror("Missing mint", "Enter a mint before setting a label.")
            return
        if not label:
            messagebox.showerror("Missing label", "Choose a label before continuing.")
            return

        args = ["--mint", mint, "--label", label]
        if note:
            args.extend(["--note", note])

        self._start_module_command("Set label", "reviewkit.label", tuple(args))

    def _list_labels(self) -> None:
        self._start_module_command("List labels", "reviewkit.label", ("--list",))

    def _remove_label(self) -> None:
        mint = self.label_mint.get().strip()
        if not mint:
            messagebox.showerror("Missing mint", "Enter a mint before removing a label.")
            return
        self._start_module_command(
            "Remove label",
            "reviewkit.label",
            ("--remove", mint),
        )

    def _store_outcome(self) -> None:
        mint = self.outcome_mint.get().strip()
        outcome = self.outcome_choice.get().strip()
        note = self.outcome_note.get().strip()
        if not mint:
            messagebox.showerror("Missing mint", "Enter a mint before storing an outcome.")
            return
        if not outcome:
            messagebox.showerror("Missing outcome", "Choose an outcome before continuing.")
            return

        args = ["--mint", mint, "--outcome", outcome]
        if note:
            args.extend(["--note", note])

        self._start_module_command(
            "Store outcome",
            "reviewfeedback.record",
            tuple(args),
        )

    def _run_command_spec(self, spec: CommandSpec) -> None:
        self._start_module_command(spec.label, spec.module, spec.args)

    def _start_module_command(
        self,
        label: str,
        module: str,
        args: tuple[str, ...],
    ) -> None:
        if not self.runner.start(label=label, module=module, args=args):
            messagebox.showinfo(
                "Command running",
                "Wait for the active command to finish before starting another one.",
            )
            return

        self._set_buttons_enabled(False)
        command_text = " ".join((module, *args))
        self.status_message.set(f"Running: python -m {command_text}")
        self._append_log(f"$ {label}\npython -m {command_text}\n")

    def _poll_runner(self) -> None:
        if self.is_closing:
            return

        result = self.runner.get_result_nowait()
        if result is not None:
            self._handle_result(result)
        if not self.is_closing:
            self.root.after(200, self._poll_runner)

    def _handle_result(self, result: CommandResult) -> None:
        self._set_buttons_enabled(True)
        self.refresh_status()
        outcome = "ok" if result.returncode == 0 else "failed"
        self.status_message.set(f"Last command {outcome}: {result.label}")

        log_parts = [
            f"[{result.finished_at}] {result.label} exit_code={result.returncode}",
        ]
        if result.stdout.strip():
            log_parts.append("stdout:")
            log_parts.append(result.stdout.rstrip())
        if result.stderr.strip():
            log_parts.append("stderr:")
            log_parts.append(result.stderr.rstrip())
        self._append_log("\n".join(log_parts) + "\n\n")

    def _set_buttons_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        for button in self.action_buttons:
            button.configure(state=state)

    def _append_log(self, text: str) -> None:
        if self.log_text is None:
            return
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _on_close(self) -> None:
        if self.is_closing:
            return
        self.is_closing = True
        self.root.destroy()


def main() -> None:
    root = Tk()
    OpsConsoleApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
