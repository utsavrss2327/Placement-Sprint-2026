from typing import List

class Solution:
    def dailyTemperatures(self, temperatures: List[int]) -> List[int]:
        res = [0] * len(temperatures)
        stack = [] # will store pairs of: [temperature, index]
        
        for curr_idx, curr_temp in enumerate(temperatures):
            # While stack is not empty AND current temp is warmer than the top of stack
            while stack and curr_temp < stack[-1][0]:
                stack_temp, stack_idx = stack.pop()
                res[stack_idx] = curr_idx - stack_idx
                
            # Push current day's [temp, index] onto the stack
            stack.append([curr_temp, curr_idx])
            
        return res
    
# --- Test Execution ---
sol = Solution()
test_temps = [80, 70, 60, 50]
print(sol.dailyTemperatures(test_temps))    