# Test 9: Simple Function Call
# Expected output: Sum of 20 + 22 = 42

.text
    .org    0
main:
    # Initialize stack
    lui     sp, 0x10              # sp = 0x1000
    
    # Print message
    lui     a0, %hi(start_msg)
    addi    a0, a0, %lo(start_msg)
    ecall   5
    
    # Set up function arguments
    li      a0, 20                # First argument
    li      a1, 22                # Second argument
    
    # Call function
    jal     ra, add_func
    
    # a0 now contains the result
    
    # Print result message
    lui     t0, %hi(result_msg)
    addi    t0, t0, %lo(result_msg)
    mv      t1, a0                # Save result
    mv      a0, t0                # Load message address
    ecall   5                     # Print result message
    
    # Print sum result
    mv      a0, t1                # Restore result
    ecall   1                     # Print result (should be 42)
    
    # Exit
    ecall   3

# Function to add two numbers
add_func:
    # Arguments in a0, a1. Result returned in a0
    add     a0, a1                # a0 = a0 + a1
    jr      ra                    # Return to caller

.data
    .org    0x100
start_msg:
    .asciiz "Sum of 20 + 22 = "
result_msg:
    .asciiz ""
