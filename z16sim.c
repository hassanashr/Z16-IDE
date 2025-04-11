/*
 * Z16 Instruction Set Simulator (ISS)
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at:
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * This simulator accepts a Z16 binary machine code file (with a .bin extension) and assumes that
 * the first instruction is located at memory address 0x0000. It decodes each 16-bit instruction into a
 * human-readable string and prints it, then executes the instruction by updating registers, memory,
 * or performing I/O via ecall.
 *
 * Supported ecall services:
 * - ecall 1: Print an integer (value in register a0).
 * - ecall 5: Print a NULL-terminated string (address in register a0).
 * - ecall 3: Terminate the simulation.
 *
 * Usage:
 * rvsim <machine_code_file_name>
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <stddef.h>
#define MEM_SIZE 65536 // 64KB memory
// Global simulated memory and register file.
unsigned char memory[MEM_SIZE];
uint16_t regs[8]; // 8 registers (16-bit each): x0, x1, x2, x3, x4, x5, x6, x7
uint16_t pc = 0; // Program counter (16-bit)

// Register ABI names for display (x0 = t0, x1 = ra, x2 = sp, x3 = s0, x4 = s1, x5 = t1, x6 = a0, x7 = a1)
const char *regNames[8] = {"t0", "ra", "sp", "s0", "s1", "t1", "a0", "a1"};

// -----------------------
// Disassembly Function
// -----------------------
//
// Decodes a 16-bit instruction 'inst' (fetched at address 'pc') and writes a human-readable
// string to 'buf' (of size bufSize). This decoder uses the opcode (bits [2:0]) to distinguish
// among R-, I-, B-, L-, J-, U-, and System instructions.
void disassemble(uint16_t inst, uint16_t pc, char *buf, size_t bufSize) {
    uint8_t opcode = inst & 0x7;
    
    switch(opcode) {
        case 0x0: { 
            uint8_t funct4 = (inst >> 12) & 0xF;
            uint8_t rs2 = (inst >> 9) & 0x7;
            uint8_t rd_rs1 = (inst >> 6) & 0x7;
            uint8_t funct3 = (inst >> 3) & 0x7;
            
            if (funct3 == 0x0) {
                if (funct4 == 0x0) 
                    snprintf(buf, bufSize, "add %s, %s", regNames[rd_rs1], regNames[rs2]);
                else if (funct4 == 0x1)
                    snprintf(buf, bufSize, "sub %s, %s", regNames[rd_rs1], regNames[rs2]);
                else if (funct4 == 0x4)
                    snprintf(buf, bufSize, "jr %s", regNames[rs2]);
                else if (funct4 == 0x8)
                    snprintf(buf, bufSize, "jalr %s", regNames[rs2]);
                else
                    snprintf(buf, bufSize, "Unknown R-type");
            } else if (funct3 == 0x1) {
                snprintf(buf, bufSize, "slt %s, %s", regNames[rd_rs1], regNames[rs2]);
            } else if (funct3 == 0x2) {
                snprintf(buf, bufSize, "sltu %s, %s", regNames[rd_rs1], regNames[rs2]);
            } else if (funct3 == 0x3) {
                if (funct4 == 0x2)
                    snprintf(buf, bufSize, "sll %s, %s", regNames[rd_rs1], regNames[rs2]);
                else if (funct4 == 0x4)
                    snprintf(buf, bufSize, "srl %s, %s", regNames[rd_rs1], regNames[rs2]);
                else if (funct4 == 0x8)
                    snprintf(buf, bufSize, "sra %s, %s", regNames[rd_rs1], regNames[rs2]);
                else
                    snprintf(buf, bufSize, "Unknown shift");
            } else if (funct3 == 0x4) {
                snprintf(buf, bufSize, "or %s, %s", regNames[rd_rs1], regNames[rs2]);
            } else if (funct3 == 0x5) {
                snprintf(buf, bufSize, "and %s, %s", regNames[rd_rs1], regNames[rs2]);
            } else if (funct3 == 0x6) {
                snprintf(buf, bufSize, "xor %s, %s", regNames[rd_rs1], regNames[rs2]);
            } else if (funct3 == 0x7) {
                snprintf(buf, bufSize, "mv %s, %s", regNames[rd_rs1], regNames[rs2]);
            } else {
                snprintf(buf, bufSize, "Unknown R-type");
            }
            break;
        }
        
        case 0x1: { 
            uint8_t imm7 = (inst >> 9) & 0x7F;
            uint8_t rd_rs1 = (inst >> 6) & 0x7;
            uint8_t funct3 = (inst >> 3) & 0x7;
            int16_t simm = (imm7 & 0x40) ? (imm7 | 0xFF80) : imm7; // Sign extend
            
            if (funct3 == 0x0)
                snprintf(buf, bufSize, "addi %s, %d", regNames[rd_rs1], simm);
            else if (funct3 == 0x1)
                snprintf(buf, bufSize, "slti %s, %d", regNames[rd_rs1], simm);
            else if (funct3 == 0x2)
                snprintf(buf, bufSize, "sltui %s, %d", regNames[rd_rs1], simm);
            else if (funct3 == 0x3) {
    uint8_t shift_type = (imm7 >> 4) & 0x7;
    uint8_t shamt = imm7 & 0xF;
    
    if (shift_type == 0x1)
        snprintf(buf, bufSize, "slli %s, %d", regNames[rd_rs1], shamt);
    else if (shift_type == 0x2)
        snprintf(buf, bufSize, "srli %s, %d", regNames[rd_rs1], shamt);
    else if (shift_type == 0x4)
        snprintf(buf, bufSize, "srai %s, %d", regNames[rd_rs1], shamt);
    else
        snprintf(buf, bufSize, "Unknown shift immediate");
}
            else if (funct3 == 0x4)
                snprintf(buf, bufSize, "ori %s, %d", regNames[rd_rs1], simm);
            else if (funct3 == 0x5)
                snprintf(buf, bufSize, "andi %s, %d", regNames[rd_rs1], simm);
            else if (funct3 == 0x6)
                snprintf(buf, bufSize, "xori %s, %d", regNames[rd_rs1], simm);
            else if (funct3 == 0x7)
                snprintf(buf, bufSize, "li %s, %d", regNames[rd_rs1], simm);
            else
                snprintf(buf, bufSize, "Unknown I-type");
            break;
        }
        
       case 0x2: { // B-type (branch): [15:12] imm[4:1] | [11:9] rs2 | [8:6] rs1 | [5:3] funct3 | [2:0] opcode
    uint8_t offset_hi = (inst >> 12) & 0xF;
    uint8_t rs2 = (inst >> 9) & 0x7;
    uint8_t rs1 = (inst >> 6) & 0x7;
    uint8_t funct3 = (inst >> 3) & 0x7;
    int16_t offset = offset_hi << 1; // Shift left by 1 (multiply by 2)
    if (offset & 0x10) offset |= 0xFFF0; // Sign extend from 5 bits to 16 bits
    uint16_t target = pc + offset;
    
    if (funct3 == 0x0)
        snprintf(buf, bufSize, "beq %s, %s, 0x%04X", regNames[rs1], regNames[rs2], target);
    else if (funct3 == 0x1)
        snprintf(buf, bufSize, "bne %s, %s, 0x%04X", regNames[rs1], regNames[rs2], target);
    else if (funct3 == 0x2)
        snprintf(buf, bufSize, "bz %s, 0x%04X", regNames[rs1], target);
    else if (funct3 == 0x3)
        snprintf(buf, bufSize, "bnz %s, 0x%04X", regNames[rs1], target);
    else if (funct3 == 0x4)
        snprintf(buf, bufSize, "blt %s, %s, 0x%04X", regNames[rs1], regNames[rs2], target);
    else if (funct3 == 0x5)
        snprintf(buf, bufSize, "bge %s, %s, 0x%04X", regNames[rs1], regNames[rs2], target);
    else if (funct3 == 0x6)
        snprintf(buf, bufSize, "bltu %s, %s, 0x%04X", regNames[rs1], regNames[rs2], target);
    else if (funct3 == 0x7)
        snprintf(buf, bufSize, "bgeu %s, %s, 0x%04X", regNames[rs1], regNames[rs2], target);
    else
        snprintf(buf, bufSize, "Unknown B-type");
    break;
}        
        case 0x3: { // S-type (store): [15:12] imm[3:0] | [11:9] rs2 | [8:6] rs1 | [5:3] funct3 | [2:0] opcode
    uint8_t imm = (inst >> 12) & 0xF;
    uint8_t rs2 = (inst >> 9) & 0x7;
    uint8_t rs1 = (inst >> 6) & 0x7;
    uint8_t funct3 = (inst >> 3) & 0x7;
    
    if (funct3 == 0x0)
        snprintf(buf, bufSize, "sb %s, %d(%s)", regNames[rs2], imm, regNames[rs1]);
    else if (funct3 == 0x1)
        snprintf(buf, bufSize, "sw %s, %d(%s)", regNames[rs2], imm, regNames[rs1]);
    else
        snprintf(buf, bufSize, "Unknown S-type");
    break;
}
case 0x4: { // L-type (load): [15:12] imm[3:0] | [11:9] rs2 | [8:6] rd | [5:3] funct3 | [2:0] opcode
    uint8_t imm = (inst >> 12) & 0xF;
    uint8_t rs2 = (inst >> 9) & 0x7;
    uint8_t rd = (inst >> 6) & 0x7;
    uint8_t funct3 = (inst >> 3) & 0x7;
    
    if (funct3 == 0x0)
        snprintf(buf, bufSize, "lb %s, %d(%s)", regNames[rd], imm, regNames[rs2]);
    else if (funct3 == 0x1)
        snprintf(buf, bufSize, "lw %s, %d(%s)", regNames[rd], imm, regNames[rs2]);
    else if (funct3 == 0x4)
        snprintf(buf, bufSize, "lbu %s, %d(%s)", regNames[rd], imm, regNames[rs2]);
    else
        snprintf(buf, bufSize, "Unknown L-type");
    break;
}       
        case 0x5: { // J-type (jump): [15] f | [14:9] offset[9:4] | [8:6] rd | [5:3] offset[3:1] | [2:0] opcode
            uint8_t f = (inst >> 15) & 0x1;
            uint8_t offset_hi = (inst >> 9) & 0x3F;
            uint8_t rd = (inst >> 6) & 0x7;
            uint8_t offset_lo = (inst >> 3) & 0x7;
            int16_t offset = ((offset_hi << 3) | offset_lo) << 1; // Construct and multiply by 2
            if (offset & 0x400) offset |= 0xF800; // Sign extend
            uint16_t target = pc + offset;
            
            if (f == 0)
                snprintf(buf, bufSize, "j 0x%04X", target);
            else
                snprintf(buf, bufSize, "jal %s, 0x%04X", regNames[rd], target);
            break;
        }
        
     case 0x6: { // U-type: [15] f | [14:10] imm[15:10] | [9:6] rd | [5:3] imm[9:7] | [2:0] opcode
    uint8_t f = (inst >> 15) & 0x1;
    uint8_t imm_hi = (inst >> 10) & 0x3F;
    uint8_t rd = (inst >> 6) & 0x7;
    uint8_t imm_lo = (inst >> 3) & 0x7;
    uint16_t imm = ((imm_hi << 6) | imm_lo) << 4; // Construct 12-bit immediate and shift left by 4

    if (f == 0)
        snprintf(buf, bufSize, "lui %s, 0x%04X", regNames[rd], imm);
    else
        snprintf(buf, bufSize, "auipc %s, 0x%04X", regNames[rd], imm);
    break;
}


        
        case 0x7: { // System instruction (ecall): [15:11] service | [10:3] funct8 | [2:0] opcode
uint16_t service = (inst >> 6) & 0x3FF;
            uint8_t funct3 = (inst >> 3) & 7;
            
            snprintf(buf, bufSize, "ecall %d", service);
            break;
        }
        
        default:
            snprintf(buf, bufSize, "Unknown opcode 0x%X", opcode);
            break;
    }
}
// -----------------------
// Instruction Execution
// -----------------------
//
// Executes the instruction 'inst' (a 16-bit word) by updating registers, memory, and PC.
// Returns 1 to continue simulation or 0 to terminate (if ecall 3 is executed).
int executeInstruction(uint16_t inst) {
    uint8_t opcode = inst & 0x7;
    int pcUpdated = 0; // flag: if instruction updated PC directly
    
    switch(opcode) {
        case 0x0: { // R-type
            uint8_t funct4 = (inst >> 12) & 0xF;
            uint8_t rs2 = (inst >> 9) & 0x7;
            uint8_t rd_rs1 = (inst >> 6) & 0x7;
            uint8_t funct3 = (inst >> 3) & 0x7;
            
            if (funct3 == 0x0) {
                if (funct4 == 0x0) // add
                    regs[rd_rs1] = regs[rd_rs1] + regs[rs2];
                else if (funct4 == 0x1) // sub
                    regs[rd_rs1] = regs[rd_rs1] - regs[rs2];
                else if (funct4 == 0x4) { // jr
                    pc = regs[rs2];
                    pcUpdated = 1;
                } else if (funct4 == 0x8) { // jalr
                    uint16_t next_pc = pc + 2;
                    pc = regs[rs2];
                    regs[rd_rs1] = next_pc;
                    pcUpdated = 1;
                }
            } else if (funct3 == 0x1) { // slt
                regs[rd_rs1] = ((int16_t)regs[rd_rs1] < (int16_t)regs[rs2]) ? 1 : 0;
            } else if (funct3 == 0x2) { // sltu
                regs[rd_rs1] = (regs[rd_rs1] < regs[rs2]) ? 1 : 0;
            } else if (funct3 == 0x3) {
                if (funct4 == 0x2) // sll
                    regs[rd_rs1] = regs[rd_rs1] << (regs[rs2] & 0xF);
                else if (funct4 == 0x4) // srl
                    regs[rd_rs1] = regs[rd_rs1] >> (regs[rs2] & 0xF);
                else if (funct4 == 0x8) // sra
                    regs[rd_rs1] = (int16_t)regs[rd_rs1] >> (regs[rs2] & 0xF);
            } else if (funct3 == 0x4) { // or
                regs[rd_rs1] = regs[rd_rs1] | regs[rs2];
            } else if (funct3 == 0x5) { // and
                regs[rd_rs1] = regs[rd_rs1] & regs[rs2];
            } else if (funct3 == 0x6) { // xor
                regs[rd_rs1] = regs[rd_rs1] ^ regs[rs2];
            } else if (funct3 == 0x7) { // mv
                regs[rd_rs1] = regs[rs2];
            }
            break;
        }
        
        case 0x1: { // I-type
            uint8_t imm7 = (inst >> 9) & 0x7F;
            uint8_t rd_rs1 = (inst >> 6) & 0x7;
            uint8_t funct3 = (inst >> 3) & 0x7;
            int16_t simm = (imm7 & 0x40) ? (imm7 | 0xFF80) : imm7; // Sign extend
            
            if (funct3 == 0x0) // addi
                regs[rd_rs1] = regs[rd_rs1] + simm;
            else if (funct3 == 0x1) // slti
                regs[rd_rs1] = ((int16_t)regs[rd_rs1] < simm) ? 1 : 0;
            else if (funct3 == 0x2) // sltui
                regs[rd_rs1] = (regs[rd_rs1] < (uint16_t)simm) ? 1 : 0;
            else if (funct3 == 0x3) { // Shift instructions
    uint8_t shift_type = (imm7 >> 4) & 0x7;
    uint8_t shamt = imm7 & 0xF;
    
    if (shift_type == 0x1)
        regs[rd_rs1] = regs[rd_rs1] << shamt; // slli
    else if (shift_type == 0x2)
        regs[rd_rs1] = regs[rd_rs1] >> shamt; // srli
    else if (shift_type == 0x4)
        regs[rd_rs1] = (int16_t)regs[rd_rs1] >> shamt; // srai
}
            else if (funct3 == 0x4) // ori
                regs[rd_rs1] = regs[rd_rs1] | simm;
            else if (funct3 == 0x5) // andi
                regs[rd_rs1] = regs[rd_rs1] & simm;
            else if (funct3 == 0x6) // xori
                regs[rd_rs1] = regs[rd_rs1] ^ simm;
            else if (funct3 == 0x7) // li
                regs[rd_rs1] = simm;
            break;
        }
        
        case 0x2: { // B-type (branch)
            uint8_t offset_hi = (inst >> 12) & 0xF;
            uint8_t rs2 = (inst >> 9) & 0x7;
            uint8_t rs1 = (inst >> 6) & 0x7;
            uint8_t funct3 = (inst >> 3) & 0x7;
            int16_t offset = offset_hi << 1; // Shift left by 1 (multiply by 2)
            if (offset & 0x10) offset |= 0xFFF0; // Sign extend from 5 bits to 16 bits
    
            int take_branch = 0;
            if (funct3 == 0x0) // beq
                take_branch = (regs[rs1] == regs[rs2]);
            else if (funct3 == 0x1) // bne
                take_branch = (regs[rs1] != regs[rs2]);
            else if (funct3 == 0x2) // bz
                take_branch = (regs[rs1] == 0);
            else if (funct3 == 0x3) // bnz
                take_branch = (regs[rs1] != 0);
            else if (funct3 == 0x4) // blt
                take_branch = ((int16_t)regs[rs1] < (int16_t)regs[rs2]);
            else if (funct3 == 0x5) // bge
                take_branch = ((int16_t)regs[rs1] >= (int16_t)regs[rs2]);
            else if (funct3 == 0x6) // bltu
                take_branch = (regs[rs1] < regs[rs2]);
            else if (funct3 == 0x7) // bgeu
                take_branch = (regs[rs1] >= regs[rs2]);
                
            if (take_branch) {
                pc = pc + offset;
                pcUpdated = 1;
            }
            break;
        }
        
        case 0x3: { // S-type (store): [15:12] imm[3:0] | [11:9] rs2 | [8:6] rs1 | [5:3] funct3 | [2:0] opcode
    uint8_t imm = (inst >> 12) & 0xF;
    uint8_t rs2 = (inst >> 9) & 0x7;
    uint8_t rs1 = (inst >> 6) & 0x7;
    uint8_t funct3 = (inst >> 3) & 0x7;
    uint16_t addr = regs[rs1] + imm;
    
    if (funct3 == 0x0) { // sb
        memory[addr] = regs[rs2] & 0xFF;
    } else if (funct3 == 0x1) { // sw
        memory[addr] = regs[rs2] & 0xFF;
        memory[addr + 1] = (regs[rs2] >> 8) & 0xFF;
    }
    break;
}

case 0x4: { // L-type (load): [15:12] imm[3:0] | [11:9] rs2 | [8:6] rd | [5:3] funct3 | [2:0] opcode
    uint8_t imm = (inst >> 12) & 0xF;
    uint8_t rs2 = (inst >> 9) & 0x7;
    uint8_t rd = (inst >> 6) & 0x7;
    uint8_t funct3 = (inst >> 3) & 0x7;
    uint16_t addr = regs[rs2] + imm;
    
    if (funct3 == 0x0) { // lb
        int8_t val = memory[addr]; // Sign-extended byte load
        regs[rd] = (int16_t)val;
    } else if (funct3 == 0x1) { // lw
        regs[rd] = memory[addr] | (memory[addr + 1] << 8);
    } else if (funct3 == 0x4) { // lbu
        regs[rd] = memory[addr]; // Zero-extended byte load
    }
    break;
}
        
        case 0x5: { // J-type (jump)
    uint8_t f = (inst >> 15) & 0x1;
    uint8_t offset_hi = (inst >> 9) & 0x3F;
    uint8_t rd = (inst >> 6) & 0x7;
    uint8_t offset_lo = (inst >> 3) & 0x7;
    int16_t offset = ((offset_hi << 3) | offset_lo) << 1; // Construct and multiply by 2
    if (offset & 0x400) offset |= 0xF800; // Sign extend
    
    if (f == 1) // jal
        regs[rd] = pc + 2;
        
    pc = offset + pc;  // This is the correct calculation
    pcUpdated = 1;
    break;
}
        
        case 0x6: { // U-type: [15] f | [14:10] imm[15:10] | [9:6] rd | [5:3] imm[9:7] | [2:0] opcode
   uint8_t f = (inst >> 15) & 0x1;
    uint8_t imm_hi = (inst >> 10) & 0x1F;  // Extract 5 bits for imm[15:11]
    uint8_t rd = (inst >> 6) & 0x7;        // Extract 3 bits for rd
    uint8_t imm_lo = (inst >> 3) & 0x7;    // Extract 3 bits for imm[10:8]
    uint16_t imm = ((imm_hi << 3) | imm_lo) << 7; // Construct immediate with bits [15:7]
    if (f == 0) // lui
        regs[rd] = imm;
    else // auipc
        regs[rd] = pc + imm;
    break;
}

        
        case 0x7: { // System instruction (ecall)
uint16_t service = (inst >> 6) & 0x3FF;
            if (service == 1) { // Print integer
                printf("%d\n", (int16_t)regs[6]); // a0 is register 6
            } else if (service == 5) { // Print string
    uint16_t addr = regs[6]; // a0 is register 6
    while (memory[addr] != 0) {
        putchar(memory[addr]);
        addr++;
    }
    printf("\n"); // Add newline for better output formatting
}
             else if (service == 3) { // Terminate
                return 0;
            }
            break;
        }
        
        default:
            printf("Unknown instruction opcode 0x%X\n", opcode);
            break;
    }
    
    if (!pcUpdated)
        pc += 2; // default: move to next instruction
    
    return 1;
}
// -----------------------
// Memory Loading
// -----------------------
//
// Loads the binary machine code image from the specified file into simulated memory.
void loadMemoryFromFile(const char *filename) {
    FILE *fp = fopen(filename, "rb");
    if(!fp) {
        perror("Error opening binary file");
        exit(1);
    }
    size_t n = fread(memory, 1, MEM_SIZE, fp);
    fclose(fp);
    printf("Loaded %zu bytes into memory\n", n);
}

void printRegisterState() {
    printf("\n--- Final Register State ---\n");
    for (int i = 0; i < 8; i++) {
printf("%s (x%d): 0x%04X (%d)\n", regNames[i], i, regs[i], (int16_t)regs[i]);
    }
    printf("PC: 0x%04X\n", pc);
    printf("---------------------------\n");
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <machine_code_file_name>\n", argv[0]);
        exit(1);
    }

    loadMemoryFromFile(argv[1]);
    memset(regs, 0, sizeof(regs)); // initialize registers to 0
    pc = 0; // starting at address 0
    char disasmBuf[128];
    
    // Added loop counter to prevent infinite loops
    int instruction_count = 0;
    #define MAX_INSTRUCTIONS 100000 // Define a reasonable limit for instructions
    
        while (pc < MEM_SIZE && instruction_count < MAX_INSTRUCTIONS) {
        // Check if we're about to read past memory bounds
        if (pc + 1 >= MEM_SIZE) {
            fprintf(stderr, "Reached end of memory at 0x%04X\n", pc);
            break;
        }

        // Fetch a 16-bit instruction from memory (little-endian)
        uint16_t inst = memory[pc] | (memory[pc+1] << 8);
        
        // Sanity check for zero instruction (potential halt condition)
        if (inst == 0) {
            fprintf(stderr, "Encountered zero instruction at 0x%04X\n", pc);
            break;
        }

        disassemble(inst, pc, disasmBuf, sizeof(disasmBuf));
        printf("0x%04X: %04X %s\n", pc, inst, disasmBuf);
        
        int exec_result = executeInstruction(inst);
        if (!exec_result) {
            printf("Simulation terminated by ecall\n");
            break;
        } else if (exec_result < 0) {
            fprintf(stderr, "Invalid instruction execution at 0x%04X\n", pc);
            break;
        }

        instruction_count++;
    }
if (instruction_count >= MAX_INSTRUCTIONS) {
        fprintf(stderr, "Simulation terminated: Exceeded maximum instruction count (%d)\n", MAX_INSTRUCTIONS);
    }
    printRegisterState();
    return 0;
}
