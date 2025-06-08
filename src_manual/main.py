import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import json


class NewWindow(tk.Toplevel):
    def __init__(self, parent, input_class):
        super().__init__(parent)
        self.title("Classification")
        self.geometry("600x600")

        self.input_class = input_class
        self.properties = self.get_relevant_properties()
        self.mapping_vars = {}

        # === Create the scrollable full‐page container ===
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        # Canvas + scrollbar
        canvas = tk.Canvas(container, borderwidth=0)
        v_scroll = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=v_scroll.set)

        v_scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # This frame holds *all* your page content
        self.content = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=self.content, anchor="nw")

        # Whenever the content changes size, update scrollregion
        self.content.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        # Optional: mousewheel support
        self.content.bind_all(
            "<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"),
        )
        # ==================================================

        # Now build *all* widgets inside self.content
        self.build_page()

    def build_page(self):
        ttk.Label(
            self.content,
            text=f"Mapping for class: {self.input_class}",
            font=("TkDefaultFont", 12, "bold"),
        ).pack(pady=(10, 5))

        sulo_classes = json.load(open("data/sulo_data.json"))
        if not self.properties:
            ttk.Label(self.content, text="No properties found.").pack(pady=20)
        else:
            for prop in self.properties:
                prop_name = prop.get("property")
                lf = ttk.LabelFrame(self.content, text=prop_name)
                lf.pack(fill="x", padx=10, pady=5)

                ttk.Label(
                    lf,
                    text="Select ALL SULO classes apply:",
                    wraplength=550,
                ).pack(pady=(0, 10))

                self.mapping_vars[prop_name] = {}
                for sulo in sulo_classes:
                    cls = sulo.get("SULO Class")
                    if cls is not None:
                        var = tk.BooleanVar(value=False)
                        cb = ttk.Checkbutton(lf, text=cls, variable=var)
                        cb.pack(anchor="w", padx=10, pady=2)
                        self.mapping_vars[prop_name][cls] = var

        # 4) Submit button at the very bottom
        ttk.Button(self.content, text="Submit", command=self.on_submit).pack(
            pady=(20, 10)
        )

    def get_relevant_properties(self):
        sphn_context = json.load(open("data/sphn_classes.json"))
        target = self.input_class.replace(" ", "").strip().lower()
        
        for cls_data in sphn_context:
            if cls_data["class"].strip().lower() == target:
                return cls_data.get("properties", [])
        return []

    def on_submit(self):
        result = {
            prop: [cls for cls, var in cls_map.items() if var.get()]
            for prop, cls_map in self.mapping_vars.items()
        }
        print(json.dumps(result, indent=2))
        self.destroy()


def main():
    root = tk.Tk()
    root.title("The Big Bad SULO Translator Helper")
    root.geometry("400x120")

    # 1) Create and place your label and entry *separately*
    class_label = ttk.Label(root, text="Enter your class:")
    class_label.grid(row=0, column=0, sticky="w", padx=5, pady=10)

    class_entry = ttk.Entry(root, width=40)
    class_entry.grid(row=0, column=1, padx=5, pady=10)

    # 2) Define the popup launcher to read from the entry
    def open_popup():
        user_class = class_entry.get().strip()
        if not user_class:
            tk.messagebox.showwarning("Oops", "Please enter a class before continuing.")
            return
        NewWindow(root, user_class)

    # 3) Place the button
    ttk.Button(root, text="Continue to Classification", command=open_popup).grid(
        row=1, column=0, columnspan=2, pady=(0, 10)
    )

    root.mainloop()


if __name__ == "__main__":
    main()
