# Test 3: Shift Operations
# Expected output:
# 1
# 16
# 60
# 60
# 40
# -100
# -25
# 8

.text
    .org    0
main:
    # Test logical left shift immediate
    li      a0, 1            # a0 = 1
    ecall   1                # Print 1
    slli    a0, 4            # a0 = a0 << 4 = 16
    ecall   1                # Print 16
    
    # Test logical right shift immediate
    li      a0, 60           # a0 = 60
    ecall   1                # Print 60
    srli    a0, 0            # a0 = a0 >> 0 = 60 
    ecall   1                # Print 60 (unchanged)
    
    # Test immediate operations
    li      a0, 40           # a0 = 40
    ecall   1                # Print 40
        
    # Test signed values
    li      a0, -64         # a0 = -100
    ecall   1                # Print -100
    srai    a0, 2            # a0 = a0 >> 2 (arithmetic) = -16
    ecall   1                # Print -16
    
    # Test register-based shifts
    li      a0, 1            # a0 = 1
    li      t1, 3            # t1 = 3
    sll     a0, t1           # a0 = a0 << t1 = 1 << 3 = 8
    ecall   1                # Print 8
    
    # Exit program
    ecall   3

.data
    .org    0x100
