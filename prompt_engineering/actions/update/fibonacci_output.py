def fibonacci(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    fib_sequence = [0, 1]
    for i in range(2, n):
        next_num = fib_sequence[-1] + fib_sequence[-2]
        fib_sequence.append(next_num)
    
    return fib_sequence

print(fibonacci(10))

# Explanation:
# 1. We first handle base cases for n <= 0, n == 1, and n == 2.
# 2. For n > 2, we initialize the sequence with [0, 1].
# 3. We then use a loop to generate the next numbers in the sequence.
# 4. Each new number is the sum of the two preceding numbers.
# 5. We append each new number to the sequence.
# 6. Finally, we return the complete Fibonacci sequence.

# The print statement will output the first 10 numbers of the Fibonacci sequence:
# [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]