# Test 2: Memory and Register Operations Test
# Expected output: 42, -10, 42, -51, 205

.text
    .org    0
main:
    # Initialize stack pointer
    li      sp, 0x1000
    
    # Test register move
    li      t0, 42          
    mv      a0, t0           # a0 = 42
    ecall   1                # Print 42
    
    # Store values to memory
    sw      a0, 0(sp)        # MEM[sp] = 42
    addi    sp, -2           # sp = sp - 2
    li      t1, -10
    sw      t1, 0(sp)        # MEM[sp] = -10
    
    # Load values back from memory
    lw      a0, 0(sp)        # a0 = MEM[sp] = -10
    ecall   1                # Print -10
    addi    sp, 2            # sp = sp + 2
    lw      a1, 0(sp)        # a1 = MEM[sp] = 42
    mv      a0, a1
    ecall   1                # Print 42
    
    # Test byte operations
    li      t0, 0xABCD      
    sb      t0, 0(sp)        # MEM[sp] (byte) = 0xCD
    lb      a0, 0(sp)        # a0 = sign-extended 0xCD = -51
    ecall   1                # Print -51
    lbu     a0, 0(sp)        # a0 = zero-extended 0xCD = 205
    ecall   1                # Print 205
    
    # Exit program
    ecall   3

.data
    .org    0x100
