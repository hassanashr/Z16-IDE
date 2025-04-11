# RARS-like Z16 Simulator

## Team Members
- Hassan Ashraf
- Omar Hagras 

*Under supervision of Dr. Mohamed Shalan*

## Overview
Z16 Assembly IDE is a graphical user interface application designed for developing, assembling, and simulating programs written in the Z16 assembly language. The IDE provides an integrated environment that connects the Z16 assembler and simulator tools, offering a streamlined workflow for Z16 programming.

Refer to Dr. Shalan's github for more information on Z16: https://github.com/shalan/z16/blob/main/README.md

## Features
- **Code Editor**: Write Z16 assembly code with syntax highlighting
- **Assembler Integration**: Compile assembly code directly within the IDE
- **Simulator Integration**: Run and test your programs within the IDE
- **Register Display**: View the state of all Z16 registers in real-time
- **Binary File Support**: Open and disassemble existing binary files
- **Text Editing Tools**: Find/Replace functionality, undo/redo, copy/paste
- **File Management**: Open and save assembly files

## Installation

### Prerequisites
- Windows operating system
- No additional dependencies are required as the application is bundled as a standalone executable

### Installation Steps
1. Download the Z16_Assembly_IDE.exe file
2. Place it in any directory of your choice
3. Run the executable in "dist" folder

## Usage Instructions

### Basic Interface
- **Assembly Text Input**: The upper-left panel is where you write your assembly code
- **Disassembler Text Output**: The lower-left panel displays assembler and simulator output
- **Register Display**: The right panel shows the current values of all registers

### Writing and Running Code
1. Enter your Z16 assembly code in the input area
2. Press F1 or select Run → Run from the menu
3. The assembler will process your code and create a binary file
4. The simulator will automatically run the binary and display the results
5. Register values will be updated in the register display panel

### File Operations
- **Open Assembly File**: File → Open Assembly
- **Open Binary File**: File → Open Binary (directly loads and disassembles)
- **Save Assembly File**: File → Save

### Editing Features
- **Undo/Redo**: Edit → Undo/Redo or Ctrl+Z/Ctrl+Y
- **Cut/Copy/Paste**: Edit → Cut/Copy/Paste or Ctrl+X/Ctrl+C/Ctrl+V
- **Find and Replace**: Edit → Find and Replace or Ctrl+F

## Z16 Assembly Language
The Z16 instruction set is inspired by the RISC-V architecture and based on RISC principles. It includes several instruction types:
- **R-Type**: Register operations (add, sub, slt, and, or, xor, etc.)
- **I-Type**: Immediate operations (addi, li, etc.)
- **B-Type**: Branch operations (beq, bne, bz, bnz, etc.)
- **L-Type**: Load operations (lb, lw, lbu)
- **S-Type**: Store operations (sb, sw)
- **J-Type**: Jump operations (j, jal)
- **U-Type**: Upper immediate operations (lui, auipc)
- **System calls**: ecall for I/O and program termination

## Example Program
```assembly
# Test 1: Basic Arithmetic Operations
# Expected output: 10, 30, 50, 20, 15

.text
    .org    0
main:
    # Test immediate loading and arithmetic
    li      a0, 10           # a0 = 10
    ecall   1                # Print 10
    
    li      a1, 20           # a1 = 20
    add     a0, a1           # a0 = a0 + a1 = 30
    ecall   1                # Print 30
    
    # Test subtraction
    li      t0, 50
    mv      a0, t0           # a0 = 50
    ecall   1                # Print 50
    
    li      t1, 30
    sub     a0, t1           # a0 = a0 - t1 = 20
    ecall   1                # Print 20
    
    # Test logical operations
    li      a0, 15           # a0 = 0000 1111 = 15
    ecall   1                # Print 15
    
    # Exit program
    ecall   3

.data
    .org    0x100
