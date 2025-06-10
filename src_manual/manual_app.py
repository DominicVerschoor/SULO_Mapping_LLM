import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import json
import sys, os

proj_root = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir))
sys.path.insert(0, proj_root)

import src.llm_app as llm_app


class ClassificationWindow(tk.Toplevel):
    shortened_descriptions = {
        "sulo:Capability": "What an entity can do under certain conditions.",
        "sulo:Duration": "Amount of time between two time points.",
        "sulo:EndTime": "Time point marking the end of a process or interval.",
        "sulo:Feature": "A characteristic based on structure or context.",
        "sulo:InformationObject": "A feature that encodes or represents information.",
        "sulo:Object": "An entity with persistent identity that isn't made of processes.",
        "sulo:Process": "An unfolding event in time with temporal parts and participating objects.",
        "sulo:Quality": "An intrinsic characteristic of an entity.",
        "sulo:Quantity": "A value and unit representing a measurable attribute.",
        "sulo:Role": "A context-dependent behavior of an entity.",
        "sulo:Set": "A collection of zero or more items.",
        "sulo:SpatialObject": "An object that occupies space.",
        "sulo:StartTime": "Time point marking the beginning of a process or interval.",
        "sulo:Time": "A measurement of duration or a specific time point.",
        "sulo:TimeInstant": "A single, specific moment in time.",
        "sulo:TimeInterval": " A time span defined by a start and end.",
        "sulo:Unit": "A standard reference for a quantity.",
    }

    def __init__(self, parent, input_class):
        super().__init__(parent)
        self.parent = parent
        self.title("Classification")
        self.geometry("600x600")

        self.input_class = input_class
        self.properties = self.get_relevant_properties()
        self.mapping_vars = {}

        # === Create the scrollable page ===
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(container, borderwidth=0)
        vsb = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set)

        vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # The frame that actually holds all your widgets:
        self.content = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.content, anchor="nw")

        # 1) Keep the scrollregion up to date
        self.content.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # 2) Bind the wheel only to the canvas
        #    On Windows/Mac this is <MouseWheel>; on Linux you might add <Button-4/5>.
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        # ==================================================

        self.build_page()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def build_page(self):
        self.reasons = {}  
        
        def parse_tsv_output(tsv: str):
            mapping = {}
            for raw_line in tsv.splitlines():
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    key, cls, reason = line.split("\t", 2)
                except ValueError:
                    continue

                # if this line is for the class itself, map to "__class__"
                if key.replace(" ", "").strip().lower() == self.input_class.replace(" ", "").strip().lower():
                    prop_key = "__class__"
                else:
                    prop_key = key

                mapping.setdefault(prop_key, []).append((cls, reason))
            return mapping

        # button callback that fills in recommendations
        def get_rec():
            # start a fresh chat
            llm = llm_app.SuloMappingApp()
            instructions = llm.instructions
            chat = llm.get_model().start_chat()

            chat.send_message(f"The class I want to map is: {self.input_class}")
            print("Generating Context…"); chat.send_message(instructions[0])
            print("Learning SULO…"); chat.send_message(instructions[1])
            print("Classifying Properties…"); chat.send_message(instructions[2])

            tsv_instruction = '''
    Output *only* raw TSV lines (no extra text, no JSON, no markdown), one for the input class and then one per property classification.
    Each line must be EXACTLY:

    <input_class>\\t<sulo_class>\\t<one-sentence reasoning>
    <property>\\t<sulo_class>\\t<one-sentence reasoning>

    Examples:
    administrativeCase sulo:Process   Because there is a start and end date meaning a procedure took place.
    hasParticipant    sulo:Process    Because participants denote processes in which the object takes part.
    hasParticipant    sulo:Object     Because participants themselves are treated as objects in the process lifecycle.
    hasDuration       sulo:Time       Because duration directly captures the temporal extent of the event.

    If a property has multiple SULO classes, repeat the property on its own line for each class, with its own reasoning.
    Do **not** include anything else, only those TSV lines.
    '''
            final_resp = chat.send_message(tsv_instruction)
            mapping = parse_tsv_output(final_resp.text)

            # clear everything
            for k, v in self.mapping_vars.items():
                if k == "__class__":
                    v.set("")      # clear radio
                else:
                    for var in v.values():
                        var.set(False)

            # apply recommendations
            for prop, pairs in mapping.items():
                if prop == "__class__":
                    # pick first recommendation for the class (Process vs Object)
                    cls_choice, _ = pairs[0]
                    self.mapping_vars["__class__"].set(cls_choice)
                else:
                    for cls, _ in pairs:
                        cbvar = self.mapping_vars[prop].get(cls)
                        if cbvar:
                            cbvar.set(True)

            self.reasons.clear()
            for prop, pairs in mapping.items():
                self.reasons[prop] = pairs
                    
            self.reason_btn.config(state="normal")
                
        # --- Header ---
        ttk.Label(
            self.content,
            text=f"Mapping for class: {self.input_class}",
            font=("TkDefaultFont", 12, "bold")
        ).pack(pady=(10, 5))

        # load SULO classes for checkboxes
        sulo_classes = json.load(open("data/sulo_data.json"))

        if not self.properties:
            ttk.Label(self.content, text="No properties found.").pack(pady=20)
        else:
            # LLM recommendation button
            ttk.Button(
                self.content,
                text="Get LLM Recommendations",
                command=get_rec
            ).pack(pady=(10, 5))

            self.reason_btn = ttk.Button(
            self.content,
            text="View Reasoning",
            command=self.show_reasons,
            state="disabled"
            )
            self.reason_btn.pack(pady=(0, 10))

            # --- Class-level classification ---
            class_frame = ttk.LabelFrame(self.content, text=f"Class: {self.input_class}")
            class_frame.pack(fill="x", padx=10, pady=5)

            ttk.Label(
                class_frame,
                text="Select the SULO domain for this class:",
                wraplength=550
            ).pack(anchor="w", padx=10, pady=(5,2))

            # radio buttons for Process vs Object
            self.class_var = tk.StringVar(value="")
            for domain in ("sulo:Process", "sulo:Object"):
                rb = ttk.Radiobutton(
                    class_frame,
                    text=domain,
                    variable=self.class_var,
                    value=domain
                )
                rb.pack(anchor="w", padx=20, pady=2)

            # store for on_submit validation
            self.mapping_vars["__class__"] = self.class_var

            # --- Property-level classification ---
            for prop in self.properties:
                prop_name = prop.get("property")
                lf = ttk.LabelFrame(self.content, text=prop_name)
                lf.pack(fill="x", padx=10, pady=5)

                ttk.Label(
                    lf,
                    text="Select ALL SULO classes that apply:",
                    wraplength=550
                ).pack(pady=(0, 10))

                self.mapping_vars[prop_name] = {}
                for sulo in sulo_classes:
                    cls = sulo.get("SULO Class")
                    if cls:
                        des = self.shortened_descriptions.get(cls, cls)
                        var = tk.BooleanVar(value=False)
                        cb = ttk.Checkbutton(
                            lf,
                            text=f"{des} ({cls})",
                            variable=var
                        )
                        cb.pack(anchor="w", padx=10, pady=2)
                        self.mapping_vars[prop_name][cls] = var

        # --- Submit button at the very bottom ---
        ttk.Button(
            self.content,
            text="Submit",
            command=self.on_submit
        ).pack(pady=(20, 10))

    def show_reasons(self):
        """Pop up a window listing each (prop,cls) → reason."""
        win = tk.Toplevel(self)
        win.title("LLM Reasoning")
        win.geometry("400x400")

        txt = tk.Text(win, wrap="word")
        txt.pack(fill="both", expand=True, padx=10, pady=10)

        for prop, pairs in self.reasons.items():
            heading = "Class domain" if prop == "__class__" else prop
            txt.insert("end", f"{heading}:\n")
            for cls, reason in pairs:
                txt.insert("end", f"  • {cls}: {reason}\n")
            txt.insert("end", "\n")

        txt.config(state="disabled")


    def get_relevant_properties(self):
        sphn_context = json.load(open("data/sphn_classes.json"))
        target = self.input_class.replace(" ", "").strip().lower()

        for cls_data in sphn_context:
            if cls_data["class"].strip().lower() == target:
                return cls_data.get("properties", [])
        return []

    def on_submit(self):
        chosen = self.mapping_vars["__class__"].get()
        if not chosen:
            messagebox.showwarning(
                "Oops",
                "Please select either sulo:Process or sulo:Object for the class."
            )
            return
        
        result = {
            prop: [cls for cls, var in cls_map.items() if var.get()]
            for prop, cls_map in self.mapping_vars.items()
            if prop != "__class__"
        }
        
        missing = [p for p, sels in result.items() if not sels]
        if missing:
            messagebox.showwarning(
                "Oops",
                "Please classify all properties before continuing.\n"
                + ", ".join(missing)
            )
            return

        if not result:
            messagebox.showwarning(
                "Oops",
                "There are no properties to classify."
            )
            return

        final = {
            "class_type": chosen,
            "properties": result
        }

        MappingWindow(self.parent, self.input_class, final)
        self.destroy()
        
class MappingWindow(tk.Toplevel):
    def __init__(self, parent, input_class, mapping):
        super().__init__(parent)
        self.title("Mapping Results")
        self.geometry("600x600")
        self.input_class = input_class
        self.mapping = mapping
        final_mappings = self.get_mappings()

        # A scrollable text widget so large mappings still fit
        text = tk.Text(self, wrap="word")
        text.pack(fill="both", expand=True, padx=10, pady=10)
        text.insert("end", "Final SULO Mapping:\n\n")
        text.insert("end", final_mappings)

        text.config(state="disabled")
        
    def get_mappings(self):
        llm = llm_app.SuloMappingApp()
        instructions = llm.instructions
        chat = llm.get_model().start_chat()

        print("Learning SULO…"); chat.send_message(instructions[1])
        print("Learning Classifications…"); chat.send_message(f'''The class I want to map is: {self.input_class} which is a {self.mapping['class_type']}
                                                            The following is a accurate classification of the required properties.
                                                            Remember and use this information in the next steps: {self.mapping['properties']}''')
        print("Determining SULO relations…"); chat.send_message(instructions[3])
        print("Applying SULO Design Patterns…"); out = chat.send_message(instructions[4])
        
        return out.text
        

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
        ClassificationWindow(root, user_class)

    # 3) Place the button
    ttk.Button(root, text="Continue to Classification", command=open_popup).grid(
        row=1, column=0, columnspan=2, pady=(0, 10)
    )

    root.mainloop()


if __name__ == "__main__":
    main()
