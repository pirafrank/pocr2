"""
OCR Query GUI
Graphical interface for searching OCR database.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess
import platform

from db.database import OCRDatabase
from query import exact_search, fuzzy_search


# Configuration
DB_FILE = "ocr_screenshots.db"
SCREENSHOTS_DIR = (
    r"C:\\Users\\francesco\\OneDrive - Leonardo S.p.a. - Div Cyber Security\\Screenshots"
)


class OCRQueryGUI:
    """GUI application for OCR database queries."""

    def __init__(self, root):
        """Initialize the GUI."""
        self.root = root
        self.root.title("OCR Query Tool")
        self.root.geometry("800x600")

        # Database instance
        self.db = OCRDatabase(DB_FILE)

        # Search mode (1=exact, 2=fuzzy)
        self.search_mode = tk.IntVar(value=1)

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
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        self.search_entry.bind("<Return>", lambda e: self.perform_search())

        self.search_button = ttk.Button(
            search_frame, text="▶ Search", command=self.perform_search
        )
        self.search_button.grid(row=0, column=2, sticky=tk.E)

        # Search mode section
        mode_frame = ttk.LabelFrame(main_frame, text="Search Mode", padding="5")
        mode_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Radiobutton(
            mode_frame, text="Exact Match", variable=self.search_mode, value=1
        ).grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        ttk.Radiobutton(
            mode_frame,
            text="Fuzzy Match (threshold: 0.5)",
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

    def perform_search(self):
        """Execute the search query."""
        search_term = self.search_entry.get().strip()

        if not search_term:
            messagebox.showwarning("Input Required", "Please enter a search term.")
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
                matches = fuzzy_search(self.db, search_term, threshold=0.5)
            else:
                matches = exact_search(self.db, search_term)

            # Display results
            if matches:
                self.results_text.insert(tk.END, f"Found {len(matches)} match(es):\n\n")

                for filename, _ in matches:
                    # Create clickable filename
                    full_path = os.path.join(SCREENSHOTS_DIR, filename)

                    # Insert filename as clickable link
                    start_idx = self.results_text.index(tk.END)
                    self.results_text.insert(tk.END, f"• {filename}\n")
                    end_idx = self.results_text.index(f"{start_idx} lineend")

                    # Store the full path as a tag
                    tag_name = f"link_{filename}"
                    self.results_text.tag_add(tag_name, start_idx, end_idx)
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
