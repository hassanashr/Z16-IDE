# Test 1: Basic Arithmetic and Logic Operations
# Expected output: 10, 30, 50, 20, 255

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
    li      a0, 0x0F         # a0 = 0000 1111
    li      a1, 0xF0         # a1 = 1111 0000
    mv      t0, a0           # t0 = a0 = 0x0F
    and     t0, a1           # t0 = t0 & a1 = 0
    or      t0, a0           # t0 = t0 | a0 = 0x0F
    or      t0, a1           # t0 = t0 | a1 = 0xFF
    mv      a0, t0
    ecall   1                # Print -1
    
    # Exit program
    ecall   3

.data
    .org    0x100
