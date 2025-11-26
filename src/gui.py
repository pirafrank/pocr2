"""
OCR Query GUI
Graphical interface for searching OCR database.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess
import platform
import threading

from db.database import OCRDatabase
from query import exact_search, fuzzy_search
from process import process
from utils.ocr_processor import ProcessingStatus
from utils.config import (
    DB_FILE,
    get_screenshots_dir,
    get_fuzzy_threshold,
    ensure_dirs,
    get_config_file,
    get_max_workers,
)


class OCRQueryGUI:
    """GUI application for OCR database queries."""

    def __init__(self, root):
        """Initialize the GUI."""
        self.root = root
        self.root.title("OCR Query Tool")
        self.root.geometry("800x600")

        # Ensure all required directories exist
        ensure_dirs()

        # Configuration
        self.screenshots_dir = get_screenshots_dir()

        # Database instance
        self.db = OCRDatabase(DB_FILE)

        # Search mode (1=exact, 2=fuzzy)
        self.search_mode = tk.IntVar(value=1)

        # Fuzzy search threshold
        self.fuzzy_threshold = get_fuzzy_threshold()

        # Setup UI
        self._create_widgets()

    def _create_widgets(self):
        """Create and layout all widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)

        # Search input section
        search_frame = ttk.Frame(main_frame)
        search_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)

        ttk.Label(search_frame, text="Search:").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 5)
        )

        # Entry container with clear button inside
        entry_container = ttk.Frame(search_frame)
        entry_container.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        entry_container.columnconfigure(0, weight=1)

        self.search_entry = ttk.Entry(entry_container)
        self.search_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.search_entry.bind("<Return>", lambda e: self.perform_search())
        self.search_entry.bind("<KeyRelease>", self._on_entry_change)
        self.search_entry.focus()

        # Clear button (⌫ backspace icon) positioned inside the entry
        self.clear_button = tk.Button(
            entry_container,
            text="⌫",
            command=self._clear_search,
            relief=tk.FLAT,
            cursor="hand2",
            fg="gray",
            bg="white",
            font=("TkDefaultFont", 10),
            padx=3,
            pady=1,
            borderwidth=0,
            highlightthickness=0,
        )
        # Initially hidden, will show when text is entered
        self.clear_button.place_forget()

        self.search_button = ttk.Button(
            search_frame, text="▶ Search", command=self.perform_search
        )
        self.search_button.grid(row=0, column=2, sticky=tk.E)

        # Update DB button, it runs OCR processing and updates the database with new content
        self.update_button = ttk.Button(
            search_frame, text="🔄 Update DB", command=self.start_update
        )
        self.update_button.grid(row=0, column=3, sticky=tk.E, padx=(5, 0))

        # Open config button
        self.config_button = ttk.Button(
            search_frame, text="⚙ Config", command=self.open_config
        )
        self.config_button.grid(row=0, column=4, sticky=tk.E, padx=(5, 0))

        # Search mode section
        mode_frame = ttk.LabelFrame(main_frame, text="Search Mode", padding="5")
        mode_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Radiobutton(
            mode_frame, text="Exact Match", variable=self.search_mode, value=1
        ).grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        ttk.Radiobutton(
            mode_frame,
            text=f"Fuzzy Match (threshold: {self.fuzzy_threshold})",
            variable=self.search_mode,
            value=2,
        ).grid(row=0, column=1, sticky=tk.W)

        # Results label
        results_label = ttk.Label(main_frame, text="Results (click to open):")
        results_label.grid(row=2, column=0, sticky=tk.W, pady=(0, 5))

        # Results text area with scrollbar
        results_frame = ttk.Frame(main_frame)
        results_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        self.results_text = tk.Text(results_frame, wrap=tk.WORD, cursor="arrow")
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        scrollbar = ttk.Scrollbar(
            results_frame, orient=tk.VERTICAL, command=self.results_text.yview
        )
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.results_text.config(yscrollcommand=scrollbar.set)

        # Configure text tags for clickable links
        self.results_text.tag_config("link", foreground="blue", underline=1)
        self.results_text.tag_bind("link", "<Button-1>", self._on_link_click)
        self.results_text.tag_bind(
            "link", "<Enter>", lambda e: self.results_text.config(cursor="hand2")
        )
        self.results_text.tag_bind(
            "link", "<Leave>", lambda e: self.results_text.config(cursor="arrow")
        )

        # Status bar
        self.status_label = ttk.Label(
            main_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W
        )
        self.status_label.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

    def _on_entry_change(self, event=None):
        """Show/hide clear button based on entry content."""
        if self.search_entry.get():
            self.clear_button.place(
                in_=self.search_entry, relx=1.0, rely=0.5, anchor=tk.E, x=-3
            )
            self.clear_button.lift()  # Bring to front
        else:
            self.clear_button.place_forget()

    def _clear_search(self):
        """Clear the search entry field."""
        self.search_entry.delete(0, tk.END)
        self.clear_button.place_forget()
        self.search_entry.focus()

    def perform_search(self):
        """Execute the search query."""
        search_term = self.search_entry.get().strip()

        if not search_term:
            messagebox.showinfo("Input Required", "Please enter a search term.")
            return

        # Clear previous results
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)

        # Update status
        mode_name = "exact" if self.search_mode.get() == 1 else "fuzzy"
        self.status_label.config(text=f"Searching ({mode_name})...")
        self.root.update()

        try:
            # Perform search
            if self.search_mode.get() == 2:
                matches = fuzzy_search(
                    self.db, search_term, threshold=self.fuzzy_threshold
                )
            else:
                matches = exact_search(self.db, search_term)

            # Display results
            if matches:
                self.results_text.insert(tk.END, f"Found {len(matches)} match(es):\n\n")

                for filename, _ in matches:
                    # Create clickable filename
                    full_path = os.path.join(self.screenshots_dir, filename)

                    # Insert bullet and filename
                    self.results_text.insert(tk.END, "• ")
                    link_start = self.results_text.index(tk.INSERT)
                    self.results_text.insert(tk.END, f"{filename}\n")
                    link_end = self.results_text.index(f"{link_start} lineend")

                    # Store the full path as a tag (only on filename, not bullet)
                    tag_name = f"link_{filename}"
                    self.results_text.tag_add(tag_name, link_start, link_end)
                    self.results_text.tag_config(
                        tag_name, foreground="blue", underline=1
                    )
                    self.results_text.tag_bind(
                        tag_name,
                        "<Button-1>",
                        lambda e, path=full_path: self._open_file(path),
                    )
                    self.results_text.tag_bind(
                        tag_name,
                        "<Enter>",
                        lambda e: self.results_text.config(cursor="hand2"),
                    )
                    self.results_text.tag_bind(
                        tag_name,
                        "<Leave>",
                        lambda e: self.results_text.config(cursor="arrow"),
                    )

                self.status_label.config(text=f"Found {len(matches)} match(es)")
            else:
                self.results_text.insert(tk.END, "No matches found.")
                self.status_label.config(text="No matches found")

        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {str(e)}")
            self.status_label.config(text="Search failed")

        finally:
            self.results_text.config(state=tk.DISABLED)

    def _on_link_click(self, event):
        """Handle click on a link (deprecated - using individual tag bindings instead)."""
        pass

    def _open_file(self, filepath):
        """Open a file using the system's default application."""
        try:
            if platform.system() == "Windows":
                os.startfile(filepath)
            elif platform.system() == "Darwin":
                subprocess.run(["open", filepath], check=True)
            else:  # Linux
                subprocess.run(["xdg-open", filepath], check=True)
        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to open file:\n{filepath}\n\nError: {str(e)}"
            )

    def open_config(self):
        """Open the config file in the default editor."""
        config_file = get_config_file()

        if not config_file.exists():
            messagebox.showwarning(
                "Config Not Found",
                f"Config file not found at:\n{config_file}\n\nPlease create it first.",
            )
            return

        self._open_file(str(config_file))

    def start_update(self):
        """Start the OCR processing in a background thread."""
        # Disable buttons during processing
        self.update_button.config(state=tk.DISABLED)
        self.search_button.config(state=tk.DISABLED)

        # Clear results area and show starting message
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Starting OCR processing...\n\n")
        self.results_text.config(state=tk.DISABLED)
        self.status_label.config(text="Processing...")

        # Run in background thread
        thread = threading.Thread(target=self._run_update, daemon=True)
        thread.start()

    def _run_update(self):
        """Run the OCR processing and update GUI with progress."""

        screenshots_dir = get_screenshots_dir()
        max_workers = get_max_workers()

        try:
            # Display initial info
            self._append_to_results(f"Processing from: {screenshots_dir}\n")
            self._append_to_results(f"Using {max_workers} threads\n\n")

            # Define progress callback that updates GUI
            def gui_progress_callback(filename: str, status: ProcessingStatus):
                if status == ProcessingStatus.SUCCESS:
                    self._append_to_results(f"✓ {filename}: Successfully processed\n")
                elif status == ProcessingStatus.ALREADY_IN_DB:
                    pass  # Make UI faster: skip printing filename for already processed files
                else:
                    self._append_to_results(f"✗ {filename}: Failed\n")

            # Process using the process.py function
            stats = process(prog_callback=gui_progress_callback)

            # Display summary
            summary = "\n" + "=" * 50 + "\n"
            summary += "Processing Complete!\n"
            summary += "=" * 50 + "\n"
            summary += f"Total files found: {stats['total']}\n"
            summary += f"Successfully processed: {stats['processed']}\n"
            summary += f"Skipped (already in DB): {stats['skipped']}\n"
            summary += f"Failed: {stats['failed']}\n"
            summary += "=" * 50 + "\n"

            self._append_to_results(summary)
            self._update_status(
                f"Complete: {stats['processed']} processed, {stats['skipped']} skipped, {stats['failed']} failed"
            )

        except Exception as e:
            error_msg = f"\n\nError during processing: {str(e)}\n"
            self._append_to_results(error_msg)
            self._update_status("Processing failed")

        finally:
            # Re-enable buttons
            self.root.after(0, lambda: self.update_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.search_button.config(state=tk.NORMAL))

    def _append_to_results(self, text):
        """Safely append text to results area from any thread."""

        def append():
            self.results_text.config(state=tk.NORMAL)
            self.results_text.insert(tk.END, text)
            self.results_text.see(tk.END)  # Auto-scroll to bottom
            self.results_text.config(state=tk.DISABLED)

        self.root.after(0, append)

    def _update_status(self, text):
        """Safely update status label from any thread."""
        self.root.after(0, lambda: self.status_label.config(text=text))

    def close(self):
        """Clean up resources."""
        self.db.close()


def main():
    """Main entry point for the GUI application."""
    root = tk.Tk()
    app = OCRQueryGUI(root)

    # Handle window close
    def on_closing():
        app.close()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
