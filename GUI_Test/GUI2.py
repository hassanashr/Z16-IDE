import sys
import os
import subprocess
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, QPlainTextEdit,
                             QPushButton, QVBoxLayout, QHBoxLayout,
                             QWidget, QLabel, QTableWidget, QTableWidgetItem,
                             QHeaderView, QFileDialog, QMenu, QMenuBar, QAction,
                             QDialog, QLineEdit, QCheckBox)
from PyQt5.QtCore import QProcess, Qt, QRect, QSize
from PyQt5.QtGui import (QTextDocument, QFont, QTextCursor, QTextCharFormat,
                         QColor, QPainter, QTextFormat)


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)


class LineNumberTextEdit(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lineNumberArea = LineNumberArea(self)

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

    def lineNumberAreaWidth(self):
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value //= 10
            digits += 1

        space = 3 + self.fontMetrics().width('9') * digits  # Changed for PyQt5 v5.5
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(
                0, rect.y(), self.lineNumberArea.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(
            QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def highlightCurrentLine(self):
        extraSelections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()  # Use QTextEdit not QPlainTextEdit
            lineColor = QColor(Qt.yellow).lighter(180)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)

        self.setExtraSelections(extraSelections)  # Fixed method name to plural

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QColor(Qt.lightGray).lighter(120))

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(
            block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(Qt.black)
                painter.drawText(0, int(top), self.lineNumberArea.width(), self.fontMetrics().height(),
                                 Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1


class Z16IDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Z16 Assembly IDE")
        self.resize(900, 700)

        # Create menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        edit_menu = menubar.addMenu("Edit")
        run_menu = menubar.addMenu("Run")

        # File menu actions
        open_asm_action = QAction("Open Assembly", self)
        open_asm_action.triggered.connect(self.open_assembly_file)

        open_bin_action = QAction("Open Binary", self)
        open_bin_action.triggered.connect(self.open_binary_file)

        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)

        file_menu.addAction(open_asm_action)
        file_menu.addAction(open_bin_action)
        file_menu.addAction(save_action)

        # Edit menu actions
        undo_action = QAction("Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo)

        redo_action = QAction("Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.redo)

        cut_action = QAction("Cut", self)
        cut_action.setShortcut("Ctrl+X")
        cut_action.triggered.connect(self.cut)

        copy_action = QAction("Copy", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy)

        paste_action = QAction("Paste", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.paste)

        find_replace_action = QAction("Find and Replace", self)
        find_replace_action.setShortcut("Ctrl+F")
        find_replace_action.triggered.connect(self.show_find_replace_dialog)

        edit_menu.addAction(undo_action)
        edit_menu.addAction(redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(cut_action)
        edit_menu.addAction(copy_action)
        edit_menu.addAction(paste_action)
        edit_menu.addSeparator()
        edit_menu.addAction(find_replace_action)

        # Run menu actions
        run_action = QAction("Run", self)
        run_action.setShortcut("F1")
        run_action.triggered.connect(self.run_code)
        run_menu.addAction(run_action)

        # Main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left side - code input and output
        left_layout = QVBoxLayout()

        # Assembly input
        input_label = QLabel("Assembly Text Input")
        self.assembly_input = LineNumberTextEdit()
        left_layout.addWidget(input_label)
        left_layout.addWidget(self.assembly_input)

        # Disassembler output
        output_label = QLabel("Disassembler Text Output")
        self.disassembler_output = QTextEdit()
        self.disassembler_output.setReadOnly(True)
        left_layout.addWidget(output_label)
        left_layout.addWidget(self.disassembler_output)

        # Right side - register display
        right_layout = QVBoxLayout()
        register_label = QLabel("Register")
        register_label.setAlignment(Qt.AlignCenter)
        value_label = QLabel("Value")
        value_label.setAlignment(Qt.AlignCenter)

        header_layout = QHBoxLayout()
        header_layout.addWidget(register_label)
        header_layout.addWidget(value_label)
        right_layout.addLayout(header_layout)

        # Register table
        self.register_table = QTableWidget(9, 2)  # 9 registers including PC
        self.register_table.setHorizontalHeaderLabels(["Register", "Value"])
        self.register_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.register_table.verticalHeader().setVisible(False)

        # Initialize register display
        registers = ["t0", "ra", "sp", "s0", "s1", "t1", "a0", "a1", "PC"]
        for i, reg in enumerate(registers):
            self.register_table.setItem(i, 0, QTableWidgetItem(reg))
            self.register_table.setItem(i, 1, QTableWidgetItem("0x0000"))

        right_layout.addWidget(self.register_table)

        # Add layouts to main layout
        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 1)

        # Temporary file paths
        self.asm_file = "temp.asm"
        self.bin_file = "temp.bin"

        # Get the absolute path based on script location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.assembler_path = os.path.join(script_dir, "z16asm.exe")
        self.disassembler_path = os.path.join(script_dir, "z16sim.exe")

        # Status bar for messages
        self.statusBar().showMessage("Ready")

        # Now apply fonts after all widgets are created
        self.setup_fonts()

    def setup_fonts(self):
        """Configure fonts for the entire application"""
        # Create font objects
        default_font = QFont("Consolas", 10)  # Monospaced font good for code
        title_font = QFont("Segoe UI", 11)
        title_font.setBold(True)
        editor_font = QFont("Consolas", 11)

        # Apply fonts to widgets
        self.setFont(default_font)

        # Make all labels (titles) bold
        for widget in self.findChildren(QLabel):
            widget.setFont(title_font)

        # Editor fonts
        self.assembly_input.setFont(editor_font)
        self.disassembler_output.setFont(editor_font)

        # Table styling
        header_font = QFont("Segoe UI", 10)
        header_font.setBold(True)
        self.register_table.horizontalHeader().setFont(header_font)

        # Apply stylesheet for consistent styling
        self.setStyleSheet("""
            QMainWindow {
                font-family: 'Segoe UI';
                font-size: 10pt;
            }
            QLabel {
                font-family: 'Segoe UI';
                font-size: 11pt;
                font-weight: bold;
            }
            QTextEdit, QPlainTextEdit {
                font-family: 'Consolas';
                font-size: 11pt;
                line-height: 1.2;
            }
            QTableWidget {
                font-family: 'Segoe UI';
                font-size: 10pt;
            }
            QHeaderView::section {
                font-weight: bold;
                background-color: #f0f0f0;
            }
        """)

    def is_valid_instruction(self, line):
        """Check if a line contains a valid Z16 instruction"""
        # Extract the instruction part (before any potential operands)
        parts = line.split()
        if not parts:
            return True  # Empty line is valid

        instruction = parts[0].lower()

        # List of valid Z16 instructions
        valid_instructions = [
            "add", "sub", "slt", "sltu", "sll", "srl", "sra", "or", "and", "xor", "mv", "jr", "jalr",
            "addi", "slti", "sltui", "slli", "srli", "srai", "ori", "andi", "xori", "li",
            "beq", "bne", "bz", "bnz", "blt", "bge", "bltu", "bgeu",
            "lb", "lw", "lbu", "sb", "sw",
            "j", "jal", "lui", "auipc", "ecall"
        ]

        # Valid directives
        valid_directives = [".text", ".data", ".org",
                            ".asciiz", ".byte", ".word", ".space"]

        # Check if it's a label definition (ends with a colon)
        if instruction.endswith(':'):
            return True

        # Check if it's a valid instruction or directive
        return instruction in valid_instructions or instruction in valid_directives

    def undo(self):
        self.assembly_input.undo()

    def redo(self):
        self.assembly_input.redo()

    def cut(self):
        self.assembly_input.cut()

    def copy(self):
        self.assembly_input.copy()

    def paste(self):
        self.assembly_input.paste()

    def show_find_replace_dialog(self):
        """Show the find and replace dialog"""
        find_dialog = QDialog(self)
        find_dialog.setWindowTitle("Find and Replace")
        find_dialog.setFixedSize(400, 200)

        layout = QVBoxLayout()

        # Find section
        find_layout = QHBoxLayout()
        find_label = QLabel("Find:")
        self.find_text = QLineEdit()
        find_layout.addWidget(find_label)
        find_layout.addWidget(self.find_text)

        # Replace section
        replace_layout = QHBoxLayout()
        replace_label = QLabel("Replace:")
        self.replace_text = QLineEdit()
        replace_layout.addWidget(replace_label)
        replace_layout.addWidget(self.replace_text)

        # Buttons
        button_layout = QHBoxLayout()
        find_button = QPushButton("Find Next")
        find_button.clicked.connect(self.find_text_in_editor)
        replace_button = QPushButton("Replace")
        replace_button.clicked.connect(self.replace_text_in_editor)
        replace_all_button = QPushButton("Replace All")
        replace_all_button.clicked.connect(self.replace_all_in_editor)
        button_layout.addWidget(find_button)
        button_layout.addWidget(replace_button)
        button_layout.addWidget(replace_all_button)

        # Case sensitivity option
        self.case_sensitive = QCheckBox("Case sensitive")

        # Add all layouts to main layout
        layout.addLayout(find_layout)
        layout.addLayout(replace_layout)
        layout.addWidget(self.case_sensitive)
        layout.addLayout(button_layout)

        find_dialog.setLayout(layout)
        self.find_dialog = find_dialog  # Store reference to keep dialog alive
        find_dialog.show()

    def find_text_in_editor(self):
        """Find the text in the editor"""
        find_text = self.find_text.text()
        if not find_text:
            return

        # Create a QTextDocument.FindFlags object
        flags = QTextDocument.FindFlag(0)  # Initialize with 0 for PyQt5 v5.5
        if self.case_sensitive.isChecked():
            flags |= QTextDocument.FindCaseSensitively

        # Try to find the text using the document's find method
        cursor = self.assembly_input.textCursor()
        document = self.assembly_input.document()

        # Try to find from current position
        found_cursor = document.find(find_text, cursor, flags)

        if found_cursor.isNull():
            # If not found, try from beginning
            cursor.setPosition(0)
            found_cursor = document.find(find_text, cursor, flags)

        if not found_cursor.isNull():
            self.assembly_input.setTextCursor(found_cursor)

    def replace_text_in_editor(self):
        """Replace the selected text in the editor"""
        cursor = self.assembly_input.textCursor()
        if cursor.hasSelection():
            cursor.insertText(self.replace_text.text())
        else:
            # If no selection, find the next occurrence
            self.find_text_in_editor()

    def replace_all_in_editor(self):
        """Replace all occurrences of the text in the editor"""
        find_text = self.find_text.text()
        replace_text = self.replace_text.text()
        if not find_text:
            return

        # Track replacements
        replacements = 0

        # Create a QTextDocument.FindFlags object
        flags = QTextDocument.FindFlag(0)  # Initialize with 0 for PyQt5 v5.5
        if self.case_sensitive.isChecked():
            flags |= QTextDocument.FindCaseSensitively

        # Start from beginning
        cursor = self.assembly_input.textCursor()
        cursor.setPosition(0)
        self.assembly_input.setTextCursor(cursor)

        # Find and replace all occurrences
        document = self.assembly_input.document()
        cursor = document.find(find_text, 0, flags)

        while not cursor.isNull():
            cursor.insertText(replace_text)
            replacements += 1
            cursor = document.find(find_text, cursor, flags)

        # Show number of replacements
        self.statusBar().showMessage(f"Replaced {replacements} occurrences")

    def open_assembly_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Assembly File", "",
            "Assembly Files (*.asm *.s);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    self.assembly_input.setPlainText(file.read())
                self.statusBar().showMessage(f"Opened {file_path}")
            except Exception as e:
                self.statusBar().showMessage(f"Error opening file: {str(e)}")

    def open_binary_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Binary File", "",
            "Binary Files (*.bin);;All Files (*)"
        )
        if file_path:
            try:
                # Set the binary file path
                self.bin_file = file_path
                self.statusBar().showMessage(
                    f"Opened binary file: {file_path}")

                # Clear previous input and output
                self.assembly_input.clear()
                self.assembly_input.setPlaceholderText(
                    f"Binary file loaded directly: {os.path.basename(file_path)}")
                self.disassembler_output.clear()

                # Reset register values
                for i in range(self.register_table.rowCount()):
                    self.register_table.setItem(
                        i, 1, QTableWidgetItem("0x0000"))

                # Run disassembler directly on the binary file
                self.run_disassembler_on_binary()
            except Exception as e:
                self.disassembler_output.append(
                    f"Error opening binary file: {str(e)}")
                self.statusBar().showMessage("Error opening binary file")

    def save_file(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Assembly File", "",
            "Assembly Files (*.asm *.s);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, 'w') as file:
                    file.write(self.assembly_input.toPlainText())
                self.statusBar().showMessage(f"Saved to {file_path}")
            except Exception as e:
                self.statusBar().showMessage(f"Error saving file: {str(e)}")

    def validate_assembly_code(self, code):
        lines = code.split('\n')
        errors = []

        for i, line in enumerate(lines):
            # Strip comments and whitespace
            line = line.split('#')[0].strip()
            if not line:
                continue

            # Check for valid instructions and syntax
            if not self.is_valid_instruction(line):
                errors.append((i+1, f"Invalid instruction: {line}"))

        return errors

    def run_code(self):
        # Clear previous output
        self.disassembler_output.clear()

        # Check code for syntax errors
        code = self.assembly_input.toPlainText()
        errors = self.validate_assembly_code(code)

        if errors:
            self.disassembler_output.append("Syntax Errors Found:")
            for line_num, error_msg in errors:
                self.disassembler_output.append(
                    f"Line {line_num}: {error_msg}")
            self.statusBar().showMessage("Syntax errors found")
            return

        self.statusBar().showMessage("Running assembly code...")

        # Save assembly to temp file
        try:
            with open(self.asm_file, 'w') as file:
                file.write(self.assembly_input.toPlainText())
        except Exception as e:
            self.disassembler_output.append(
                f"Error creating assembly file: {str(e)}")
            self.statusBar().showMessage("Error running code")
            return

        # Run assembler process
        assembler_process = QProcess()
        assembler_process.setProcessChannelMode(QProcess.MergedChannels)

        # Connect signals
        assembler_process.finished.connect(
            lambda exit_code, exit_status: self.run_disassembler())
        assembler_process.readyReadStandardOutput.connect(
            lambda: self.handle_process_output(assembler_process)
        )

        # Start the assembler
        try:
            assembler_process.start(self.assembler_path, [
                                    self.asm_file, "-o", self.bin_file])
        except Exception as e:
            self.disassembler_output.append(
                f"Error running assembler: {str(e)}")
            self.statusBar().showMessage("Error running assembler")

    def handle_process_output(self, process):
        """Handle output from a QProcess"""
        output = bytes(process.readAllStandardOutput()
                       ).decode('utf-8', errors='replace')

        # Check for error patterns in the output
        error_pattern = re.compile(r'error.*line\s+(\d+)', re.IGNORECASE)
        for line in output.split('\n'):
            match = error_pattern.search(line)
            if match:
                line_num = match.group(1)
                self.highlight_error_line(int(line_num))

        self.disassembler_output.append(output)

    def highlight_error_line(self, line_num):
        """Highlight an error line in the editor"""
        # Create a text cursor
        cursor = self.assembly_input.textCursor()

        # Move to the beginning of the document
        cursor.movePosition(QTextCursor.Start)

        # Move down to the error line
        for _ in range(line_num - 1):
            cursor.movePosition(QTextCursor.Down)

        # Select the line
        cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)

        # Apply formatting (e.g., red background)
        format = QTextCharFormat()
        format.setBackground(QColor("red"))
        format.setForeground(QColor("white"))

        # Apply the format
        cursor.mergeCharFormat(format)

    def run_disassembler(self):
        """Run the disassembler on the generated binary file"""
        self.statusBar().showMessage("Running disassembler...")

        # Run disassembler process
        disassembler_process = QProcess()
        disassembler_process.setProcessChannelMode(QProcess.MergedChannels)

        # Connect signals
        disassembler_process.readyReadStandardOutput.connect(
            lambda: self.process_disassembler_output(disassembler_process)
        )
        disassembler_process.finished.connect(
            lambda exit_code, exit_status: self.statusBar().showMessage("Execution complete")
        )

        # Start the disassembler
        try:
            disassembler_process.start(self.disassembler_path, [self.bin_file])
        except Exception as e:
            self.disassembler_output.append(
                f"Error running disassembler: {str(e)}")
            self.statusBar().showMessage("Error running disassembler")

    def run_disassembler_on_binary(self):
        """Run the disassembler directly on a loaded binary file"""
        self.statusBar().showMessage("Disassembling binary file...")

        # Run disassembler process
        disassembler_process = QProcess()
        disassembler_process.setProcessChannelMode(QProcess.MergedChannels)

        # Connect signals
        disassembler_process.readyReadStandardOutput.connect(
            lambda: self.process_disassembler_output(disassembler_process)
        )
        disassembler_process.finished.connect(
            lambda exit_code, exit_status: self.statusBar().showMessage("Disassembly complete")
        )

        # Start the disassembler
        try:
            disassembler_process.start(self.disassembler_path, [self.bin_file])
        except Exception as e:
            self.disassembler_output.append(
                f"Error running disassembler: {str(e)}")
            self.statusBar().showMessage("Error running disassembler")

    def process_disassembler_output(self, process):
        """Process and display output from the disassembler"""
        output = bytes(process.readAllStandardOutput()
                       ).decode('utf-8', errors='replace')
        self.disassembler_output.append(output)

        # Parse register values from output
        self.parse_register_values(output)

    def parse_register_values(self, output):
        """Parse register values from disassembler output"""
        lines = output.split('\n')

        # Look for final register state section
        in_register_section = False
        for line in lines:
            if "--- Final Register State ---" in line:
                in_register_section = True
                continue

            if in_register_section and ":" in line:
                # Look for register values like "t0 (x0): 0x0000 (0)"
                parts = line.split(':')
                if len(parts) >= 2:
                    reg_part = parts[0].strip()
                    val_part = parts[1].strip().split()[0]  # Get the hex value

                    # Extract register name from format like "t0 (x0)"
                    if "(" in reg_part:
                        reg_name = reg_part.split()[0].strip()
                    else:
                        reg_name = reg_part.strip()

                    # Update register in table
                    self.update_register_value(reg_name, val_part)

            # Exit if reaching the end of register section
            if in_register_section and "---------------------------" in line:
                break

    def update_register_value(self, reg_name, value):
        """Update a register value in the table"""
        for i in range(self.register_table.rowCount()):
            table_reg = self.register_table.item(i, 0).text()
            if table_reg.lower() == reg_name.lower():
                self.register_table.setItem(i, 1, QTableWidgetItem(value))
                break


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Z16IDE()
    window.show()
    sys.exit(app.exec_())  # Note: In PyQt5 it's exec_() with underscore
