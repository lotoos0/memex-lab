from __future__ import annotations

import json
from pathlib import Path
from tkinter import StringVar, Tk
from tkinter import messagebox, scrolledtext, ttk

from console.commands import LABEL_CHOICES, OUTCOME_CHOICES, CommandSpec, build_command_sections
from console.runner import CommandResult, CommandRunner
from console.status import collect_status_rows, format_size

REPO_ROOT = Path(__file__).resolve().parents[1]
QUEUE_NOW_V2_PATH = REPO_ROOT / "data" / "review_queue_now_v2.jsonl"
QUEUE_IF_TIME_V2_PATH = REPO_ROOT / "data" / "review_queue_if_time_v2.jsonl"
PIPELINE_HEALTH_PATH = REPO_ROOT / "data" / "reports" / "pipeline_health.json"


class OpsConsoleApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.runner = CommandRunner(REPO_ROOT)
        self.is_closing = False
        self.status_tree: ttk.Treeview | None = None
        self.queue_tree: ttk.Treeview | None = None
        self.log_text: scrolledtext.ScrolledText | None = None
        self.queue_detail_text: scrolledtext.ScrolledText | None = None
        self.status_message = StringVar(value="Ready.")
        self.readiness_state = StringVar(value="Readiness: unknown")
        self.readiness_detail = StringVar(value="pipeline_health.json not found.")
        self.label_mint = StringVar()
        self.label_choice = StringVar(value=LABEL_CHOICES[0])
        self.label_note = StringVar()
        self.outcome_mint = StringVar()
        self.outcome_choice = StringVar(value=OUTCOME_CHOICES[0])
        self.outcome_note = StringVar()
        self.action_buttons: list[ttk.Button] = []
        self.queue_records: list[dict[str, object]] = []
        self.queue_messages: list[str] = []
        self.selected_queue_key: tuple[str, str] | None = None

        self.root.title("memex-lab ops console v0")
        self.root.minsize(1120, 840)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_layout()
        self.refresh_status()
        self._poll_runner()

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=3)
        self.root.columnconfigure(1, weight=2)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=2)
        self.root.rowconfigure(3, weight=2)

        header = ttk.Frame(self.root, padding=12)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=0)

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

        readiness_frame = ttk.LabelFrame(header, text="Readiness", padding=8)
        readiness_frame.grid(row=0, column=1, rowspan=3, sticky="ne", padx=(12, 0))
        readiness_frame.columnconfigure(0, weight=1)

        ttk.Label(
            readiness_frame,
            textvariable=self.readiness_state,
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            readiness_frame,
            textvariable=self.readiness_detail,
            wraplength=260,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(4, 8))
        ttk.Button(
            readiness_frame,
            text="Refresh readiness",
            command=self.refresh_readiness,
        ).grid(row=2, column=0, sticky="w")

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

        self._build_review_queue_section()

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

    def _build_review_queue_section(self) -> None:
        queue_frame = ttk.LabelFrame(self.root, text="Review queue", padding=12)
        queue_frame.grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="nsew",
            padx=12,
            pady=(0, 12),
        )
        queue_frame.columnconfigure(0, weight=2)
        queue_frame.columnconfigure(1, weight=3)
        queue_frame.rowconfigure(1, weight=1)

        controls = ttk.Frame(queue_frame)
        controls.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        controls.columnconfigure(0, weight=0)
        controls.columnconfigure(1, weight=0)
        controls.columnconfigure(2, weight=1)

        ttk.Button(
            controls,
            text="Refresh queues",
            command=self.refresh_review_queue,
        ).grid(row=0, column=0, sticky="w")
        ttk.Button(
            controls,
            text="Next item",
            command=self._select_next_queue_item,
        ).grid(row=0, column=1, sticky="w", padx=(8, 0))
        ttk.Label(
            controls,
            text="Sources: review_queue_now_v2 / review_queue_if_time_v2",
        ).grid(row=0, column=2, sticky="w", padx=(12, 0))

        self.queue_tree = ttk.Treeview(
            queue_frame,
            columns=("queue", "mint", "candidate_class", "quality_band", "score", "label"),
            show="headings",
            height=10,
        )
        self.queue_tree.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
        self.queue_tree.heading("queue", text="Queue")
        self.queue_tree.heading("mint", text="Mint")
        self.queue_tree.heading("candidate_class", text="Class")
        self.queue_tree.heading("quality_band", text="Band")
        self.queue_tree.heading("score", text="Score")
        self.queue_tree.heading("label", text="Label")
        self.queue_tree.column("queue", width=110, anchor="center")
        self.queue_tree.column("mint", width=220, anchor="w")
        self.queue_tree.column("candidate_class", width=115, anchor="center")
        self.queue_tree.column("quality_band", width=85, anchor="center")
        self.queue_tree.column("score", width=70, anchor="center")
        self.queue_tree.column("label", width=100, anchor="center")
        self.queue_tree.bind("<<TreeviewSelect>>", self._on_queue_selection)

        self.queue_detail_text = scrolledtext.ScrolledText(
            queue_frame,
            wrap="word",
            state="disabled",
            font=("Consolas", 10),
            height=10,
        )
        self.queue_detail_text.grid(row=1, column=1, sticky="nsew", padx=(6, 0))

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

        self.refresh_review_queue()
        self.refresh_readiness()
        self.status_message.set("Status refreshed.")

    def refresh_readiness(self) -> None:
        state_text, detail_text = self._load_readiness_summary()
        self.readiness_state.set(state_text)
        self.readiness_detail.set(detail_text)

    def refresh_review_queue(self) -> None:
        previous_selected_key = self.selected_queue_key
        self.queue_records, self.queue_messages = self._load_queue_records()

        if self.queue_tree is None:
            return

        for item_id in self.queue_tree.get_children():
            self.queue_tree.delete(item_id)

        for index, record in enumerate(self.queue_records):
            mint = record.get("mint")
            score_total = record.get("score_total")
            label = record.get("label")
            self.queue_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    record.get("_queue_name", "-"),
                    self._truncate_mint(mint),
                    record.get("candidate_class", "-"),
                    record.get("quality_band", "-"),
                    score_total if score_total is not None else "-",
                    label if isinstance(label, str) and label else "-",
                ),
            )

        selected_index = self._find_queue_record_index(previous_selected_key)
        if selected_index is None and self.queue_records:
            selected_index = 0

        if selected_index is not None:
            item_id = str(selected_index)
            self.queue_tree.selection_set(item_id)
            self.queue_tree.focus(item_id)
            self.queue_tree.see(item_id)
            self._show_queue_record_detail(selected_index)
            return

        self.selected_queue_key = None
        self._show_queue_message()

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

    def _on_queue_selection(self, _event: object) -> None:
        if self.queue_tree is None:
            return

        selected_items = self.queue_tree.selection()
        if not selected_items:
            self._show_queue_message()
            return

        self._show_queue_record_detail(int(selected_items[0]))

    def _select_next_queue_item(self) -> None:
        if self.queue_tree is None or not self.queue_records:
            self._show_queue_message()
            return

        selected_items = self.queue_tree.selection()
        if not selected_items:
            next_index = 0
        else:
            current_index = int(selected_items[0])
            next_index = min(current_index + 1, len(self.queue_records) - 1)

        item_id = str(next_index)
        self.queue_tree.selection_set(item_id)
        self.queue_tree.focus(item_id)
        self.queue_tree.see(item_id)
        self._show_queue_record_detail(next_index)

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

    def _show_queue_record_detail(self, record_index: int) -> None:
        if record_index < 0 or record_index >= len(self.queue_records):
            self.selected_queue_key = None
            self._show_queue_message()
            return

        record = self.queue_records[record_index]
        record_key = self._queue_record_key(record)
        selection_changed = record_key != self.selected_queue_key
        self.selected_queue_key = record_key
        mint = record.get("mint")
        if selection_changed and isinstance(mint, str) and mint:
            self.label_mint.set(mint)
            self.outcome_mint.set(mint)

        detail_parts: list[str] = []
        if self.queue_messages:
            detail_parts.append("Queue messages:")
            detail_parts.extend(f"- {message}" for message in self.queue_messages)
            detail_parts.append("")

        preview_record = {
            key: value for key, value in record.items() if key != "_queue_name"
        }
        detail_parts.append(
            "Selected queue record:\n"
            + json.dumps(preview_record, indent=2, ensure_ascii=False, sort_keys=True)
        )
        self._set_queue_detail("\n".join(detail_parts))

    def _show_queue_message(self) -> None:
        if self.queue_records:
            message = "Select a queue record to preview it."
        elif self.queue_messages:
            message = "\n".join(self.queue_messages)
        else:
            message = "No records found in the v2 review queue files."
        self._set_queue_detail(message)

    def _set_queue_detail(self, text: str) -> None:
        if self.queue_detail_text is None:
            return
        self.queue_detail_text.configure(state="normal")
        self.queue_detail_text.delete("1.0", "end")
        self.queue_detail_text.insert("1.0", text)
        self.queue_detail_text.configure(state="disabled")

    def _load_queue_records(self) -> tuple[list[dict[str, object]], list[str]]:
        queue_records: list[dict[str, object]] = []
        queue_messages: list[str] = []

        for queue_name, path in (
            ("review_now_v2", QUEUE_NOW_V2_PATH),
            ("review_if_time_v2", QUEUE_IF_TIME_V2_PATH),
        ):
            if not path.exists():
                queue_messages.append(f"Queue file not found: {path}")
                continue

            with path.open("r", encoding="utf-8") as handle:
                for line_number, raw_line in enumerate(handle, start=1):
                    line = raw_line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        queue_messages.append(
                            f"Skipped invalid JSON in {path} at line {line_number}."
                        )
                        continue
                    if not isinstance(record, dict):
                        queue_messages.append(
                            f"Skipped non-object JSON in {path} at line {line_number}."
                        )
                        continue
                    enriched_record = dict(record)
                    enriched_record["_queue_name"] = queue_name
                    queue_records.append(enriched_record)

        queue_records.sort(
            key=lambda record: (
                str(record.get("_queue_name", "")),
                str(record.get("mint", "")),
            )
        )
        return queue_records, queue_messages

    def _load_readiness_summary(self) -> tuple[str, str]:
        if not PIPELINE_HEALTH_PATH.exists():
            return ("Readiness: unknown", "pipeline_health.json not found.")

        try:
            with PIPELINE_HEALTH_PATH.open("r", encoding="utf-8") as handle:
                document = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return ("Readiness: unknown", "pipeline_health.json is missing or invalid.")

        if not isinstance(document, dict):
            return ("Readiness: unknown", "pipeline_health.json is missing or invalid.")

        overall_status = document.get("overall_status")
        if not isinstance(overall_status, dict):
            return ("Readiness: unknown", "pipeline_health.json is missing required fields.")

        readiness_state = overall_status.get("readiness_state")
        error_count = overall_status.get("error_count")
        warning_count = overall_status.get("warning_count")
        warnings = document.get("warnings")
        missing_artifacts = document.get("missing_artifacts")

        if not isinstance(readiness_state, str):
            return ("Readiness: unknown", "pipeline_health.json is missing required fields.")
        if not isinstance(error_count, int) or not isinstance(warning_count, int):
            return ("Readiness: unknown", "pipeline_health.json is missing required fields.")

        top_issue = "No issues."
        if isinstance(warnings, list) and warnings and isinstance(warnings[0], str):
            top_issue = warnings[0]
        elif (
            isinstance(missing_artifacts, list)
            and missing_artifacts
            and isinstance(missing_artifacts[0], str)
        ):
            top_issue = f"Missing: {missing_artifacts[0]}"

        return (
            f"Readiness: {readiness_state}",
            f"errors={error_count} warnings={warning_count} top_issue={top_issue}",
        )

    def _find_queue_record_index(
        self,
        record_key: tuple[str, str] | None,
    ) -> int | None:
        if record_key is None:
            return None

        for index, record in enumerate(self.queue_records):
            if self._queue_record_key(record) == record_key:
                return index
        return None

    def _queue_record_key(self, record: dict[str, object]) -> tuple[str, str] | None:
        queue_name = record.get("_queue_name")
        mint = record.get("mint")
        if isinstance(queue_name, str) and queue_name and isinstance(mint, str) and mint:
            return (queue_name, mint)
        return None

    def _truncate_mint(self, value: object) -> str:
        if not isinstance(value, str) or not value:
            return "-"
        if len(value) <= 18:
            return value
        return f"{value[:8]}...{value[-8:]}"

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
