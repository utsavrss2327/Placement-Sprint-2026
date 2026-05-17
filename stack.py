def isValid(s: str) -> bool:
    stack = []
    # Map closing brackets to their corresponding opening brackets
    close_to_open = {")": "(", "}": "{", "]": "["}
    
    for char in s:
        # If it's a closing bracket
        if char in close_to_open:
            # Check if stack is not empty and top matches the opening bracket
            if stack and stack[-1] == close_to_open[char]:
                stack.pop() # Match found, remove it
            else:
                return False # Mismatch or closing without an opening
        else:
            # It's an opening bracket, push to stack
            stack.append(char)
            
    # If stack is empty, all brackets matched perfectly
    return len(stack) == 0

# --- Test Cases ---
print(isValid("()[]{}")) # Expected: True
print(isValid("([)]"))   # Expected: False
print(isValid("{[]}"))   # Expected: True