# Z16 Advanced Test File
# Tests control structures, addressing modes, and edge cases

.text
.org 0
main:
    # Initialize registers with test values
    li t0, 1          # Constant 1 for increments/decrements
    li s0, 64         # Base memory address
    li t1, 7          # Test value
    
    # Setup a simple array in memory
    li a0, 10
    sw a0, 0(s0)      # mem[64] = 10
    li a0, 20
    sw a0, 2(s0)      # mem[66] = 20
    li a0, 30
    sw a0, 4(s0)      # mem[68] = 30
    li a0, 40
    sw a0, 6(s0)      # mem[70] = 40
    li a0, 50
    sw a0, 8(s0)      # mem[72] = 50
    
    # Test nested control structures - find max value
    lw a0, 0(s0)      # Load first element into a0 (current max)
    li s1, 2          # Initialize offset
    li a1, 8          # End offset
    
find_max_loop:
    lw t1, 0(s0)      # Load mem[base+0]
    add s0, s1        # Increment base address by 2
    
    # Compare current value with max
    sub t1, a0        # t1 = t1 - a0
    blt t1, t0, skip_update  # If t1 < 0, don't update max
    add a0, t1        # Update max: a0 = a0 + (t1 - a0) = t1
    
skip_update:
    add s1, s1        # s1 = s1 + s1 (double the offset)
    blt s1, a1, find_max_loop  # Continue if offset < 8
    
    # Print the max value found
    ecall 1           # Print max value
    
    # Test conditional forward and backward jumps
    li s1, 0          # Initialize sum
    li t1, 5          # Limit
    
count_up:
    add s1, t0        # s1 = s1 + 1
    beq s1, t1, exit_up  # If s1 == 5, exit loop
    j count_up
    
exit_up:
    mv a0, s1         # a0 = s1 = 5
    ecall 1           # Print 5
    
    # Test backward jumping
    li s1, 10         # Start value
    
count_down:
    sub s1, t0        # s1 = s1 - 1
    mv a0, s1         # a0 = s1
    ecall 1           # Print current value
    bnz s1, count_down  # If s1 != 0, continue loop
    
    # Test stack operations
    li sp, 200        # Initialize stack pointer
    li a0, 25         # Value to save
    sw a0, 0(sp)      # Push onto stack
    li a0, 0          # Clear a0
    lw a0, 0(sp)      # Pop from stack
    ecall 1           # Print 25
    
    # Call recursive function to calculate factorial
    li a0, 4          # Calculate factorial of 4
    jal ra, factorial
    ecall 1           # Print result (should be 24)
    
    # Final success indicator
    li a0, 99
    ecall 1           # Print 99 (success)
    ecall 3           # Terminate program
    
# Recursive factorial function - iterative implementation
# Input: a0 = n
# Output: a0 = n!
factorial:
    # Save return address
    sub sp, t0        # Decrement stack pointer by 2
    sub sp, t0
    sw ra, 0(sp)      # Save return address
    
    # Base case: if n <= 1, return 1
    li t1, 1
    beq a0, t1, fact_base  # If a0 == 1, return 1
    blt a0, t1, fact_base  # If a0 < 1, return 1
    j factorial_recur      # Otherwise, do recursion
    
fact_base:
    li a0, 1          # Return 1
    j factorial_return
    
factorial_recur:
    # Save n
    sub sp, t0        # Decrement stack pointer
    sub sp, t0
    sw a0, 0(sp)      # Save n
    
    # Calculate (n-1)!
    sub a0, t0        # a0 = n - 1
    jal ra, factorial  # Call factorial(n-1)
    
    # Multiply n * factorial(n-1) using repeated addition
    lw t1, 0(sp)      # Load saved n
    mv a1, a0         # Save factorial(n-1) in a1
    li a0, 0          # Initialize result
    
mul_loop:
    add a0, a1        # a0 = a0 + a1
    sub t1, t0        # t1 = t1 - 1
    bnz t1, mul_loop  # Continue if t1 != 0
    
    # Clean up this stack frame
    add sp, t0        # Restore stack pointer
    add sp, t0
    
factorial_return:
    # Restore return address and return
    lw ra, 0(sp)      # Restore return address
    add sp, t0        # Restore stack pointer
    add sp, t0
    jr ra             # Return