import os
import subprocess
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, Menu

class Z16IDE:
    def __init__(self, root):
        self.root = root
        root.title("Z16 Assembly IDE")
        root.geometry("1000x800")
        
        # Create menu
        menubar = Menu(root)
        root.config(menu=menubar)
        
        # File menu
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.quit)
        
        # Edit menu
        edit_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
        # Run menu
        run_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Run", menu=run_menu)
        run_menu.add_command(label="Run", command=self.run_code)
        
        # Main frame
        main_frame = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left frame - code input and output
        left_frame = ttk.Frame(main_frame)
        main_frame.add(left_frame, weight=3)
        
        # Right frame - register display
        right_frame = ttk.Frame(main_frame)
        main_frame.add(right_frame, weight=1)
        
        # Assembly input
        ttk.Label(left_frame, text="Assembly Text Input").pack(anchor=tk.W)
        self.assembly_input = scrolledtext.ScrolledText(left_frame, height=15)
        self.assembly_input.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Disassembler output
        ttk.Label(left_frame, text="Disassembler Text Output").pack(anchor=tk.W)
        self.disassembler_output = scrolledtext.ScrolledText(left_frame, height=15)
        self.disassembler_output.config(state=tk.DISABLED)
        self.disassembler_output.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Register display
        ttk.Label(right_frame, text="Registers").pack(anchor=tk.W)
        
        # Register table
        cols = ("Register", "Value")
        self.register_table = ttk.Treeview(right_frame, columns=cols, show="headings")
        for col in cols:
            self.register_table.heading(col, text=col)
            self.register_table.column(col, width=70)
        self.register_table.pack(fill=tk.BOTH, expand=True)
        
        # Initialize register display
        registers = ["t0", "ra", "sp", "s0", "s1", "t1", "a0", "a1", "PC"]
        for reg in registers:
            self.register_table.insert("", tk.END, values=(reg, "0x0000"))
        
        # Temporary file paths
        self.asm_file = "temp.asm"
        self.bin_file = "temp.bin"
        self.assembler_path = "GUI_Test\z16asm.exe"
        self.disassembler_path = "GUI_Test\z16sim.exe"
    
    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Assembly Files", "*.asm *.s"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, 'r') as file:
                self.assembly_input.delete(1.0, tk.END)
                self.assembly_input.insert(tk.END, file.read())
    
    def save_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".asm", filetypes=[("Assembly Files", "*.asm *.s"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, 'w') as file:
                file.write(self.assembly_input.get(1.0, tk.END))
    
    def update_output(self, text_widget, text):
        text_widget.config(state=tk.NORMAL)
        text_widget.insert(tk.END, text)
        text_widget.config(state=tk.DISABLED)
        text_widget.see(tk.END)
    
    def run_code(self):
        # Save assembly to temp file
        with open(self.asm_file, 'w') as file:
            file.write(self.assembly_input.get(1.0, tk.END))
        
        # Clear previous output
        self.disassembler_output.config(state=tk.NORMAL)
        self.disassembler_output.delete(1.0, tk.END)
        self.disassembler_output.config(state=tk.DISABLED)
        
        # Run assembler
        try:
            assembler_process = subprocess.Popen(
                [self.assembler_path, self.asm_file, "-o", self.bin_file], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Display assembler output
            for line in assembler_process.stdout:
                self.update_output(self.disassembler_output, line)
            
            assembler_process.wait()
            
            # Run disassembler if assembler succeeded
            if assembler_process.returncode == 0:
                self.run_disassembler()
        except Exception as e:
            self.update_output(self.disassembler_output, f"Error: {str(e)}\n")
    
    def run_disassembler(self):
        try:
            disassembler_process = subprocess.Popen(
                [self.disassembler_path, self.bin_file], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                text=True
            )
            
            in_register_section = False
            output_lines = []
            
            # Collect all output lines
            for line in disassembler_process.stdout:
                output_lines.append(line)
                self.update_output(self.disassembler_output, line)
            
            # Process the collected output for register values
            for i, line in enumerate(output_lines):
                # Check if we're entering the register state section
                if "--- Final Register State ---" in line:
                    in_register_section = True
                    continue
                    
                # Check if we're exiting the register state section
                if in_register_section and "---------------------------" in line:
                    break
                    
                # Parse register values in the register section
                if in_register_section and ":" in line:
                    if line.startswith("PC:"):
                        # Special handling for PC
                        parts = line.split(":")
                        if len(parts) >= 2:
                            pc_value = parts[1].strip().split()[0]  # Get just the hex value
                            
                            # Update PC in table
                            for item_id in self.register_table.get_children():
                                if self.register_table.item(item_id)["values"][0] == "PC":
                                    self.register_table.item(item_id, values=("PC", pc_value))
                    else:
                        # Handle regular register lines like "t0 (x0): 0x000F (15)"
                        parts = line.split(":")
                        if len(parts) >= 2:
                            # Extract register name from format like "t0 (x0)"
                            reg_part = parts[0].strip()
                            reg_name = reg_part.split()[0]  # Get just the register name
                            
                            # Extract hex value from format like "0x000F (15)"
                            val_part = parts[1].strip()
                            reg_value = val_part.split()[0]  # Get just the hex value
                            
                            # Update register in table
                            for item_id in self.register_table.get_children():
                                if self.register_table.item(item_id)["values"][0] == reg_name:
                                    self.register_table.item(item_id, values=(reg_name, reg_value))
                                    
        except Exception as e:
            self.update_output(self.disassembler_output, f"Error: {str(e)}\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = Z16IDE(root)
    root.mainloop()
