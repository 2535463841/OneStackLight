from typing import List


class Solution:

    def maxArea(self, height: List[int]) -> int:
        for left in height:
            for right in height[left + 1 :]:
                print(left, right)


s = Solution()
s.maxArea([1,8,6,2,5,4,8,3,7])


