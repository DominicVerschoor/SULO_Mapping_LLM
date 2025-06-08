 # Header
        ttk.Label(self, text="This is a new window").pack(pady=(10, 5))

        # Instruction
        ttk.Label(self, text="Select options:").pack(anchor="w", padx=10)

        # BooleanVars to hold checkbox state
        self.var_a = tk.BooleanVar()
        self.var_b = tk.BooleanVar()
        self.var_c = tk.BooleanVar()

        # Checkboxes
        ttk.Checkbutton(self, text="Option A", variable=self.var_a).pack(anchor="w", padx=20, pady=2)
        ttk.Checkbutton(self, text="Option B", variable=self.var_b).pack(anchor="w", padx=20, pady=2)
        ttk.Checkbutton(self, text="Option C", variable=self.var_c).pack(anchor="w", padx=20, pady=2)

        # Submit button
        ttk.Button(self, text="Submit", command=self.on_submit).pack(pady=(15,10))