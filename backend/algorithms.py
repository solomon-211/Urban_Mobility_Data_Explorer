"""Custom Min-Heap Algorithm for Top-K Zone Selection

This module implements a manual min-heap data structure to find the K busiest
taxi zones without using built-in sorting functions (sorted(), heapq, etc.).

Algorithm: Top-K Selection using Min-Heap
Time Complexity: O(n log k) where n = total zones, k = top zones to find
Space Complexity: O(k) - only stores k items in heap

Why this is better than SQL ORDER BY:
- SQL ORDER BY uses O(n log n) comparison sort
- Our heap approach is O(n log k) which is faster when k << n
- For k=15 and n=263 zones: ~263*4 vs ~263*8 comparisons

Pseudo-code:
1. Create empty min-heap of size k
2. For each zone:
   a. If heap not full, insert zone
   b. If zone count > heap minimum, replace minimum with zone
   c. Restore heap property (bubble up/down)
3. Extract all items and sort descending
"""

class MinHeap:
    def __init__(self, k):
        self.items = []  # Store our top K items
        self.k = k  # How many items to keep
    
    def add(self, count, zone_id, name):
        """Add a zone to our heap"""
        if len(self.items) < self.k:
            # Heap not full yet, just add it
            self.items.append((count, zone_id, name))
            self._fix_up(len(self.items) - 1)
        elif count > self.items[0][0]:
            # This zone is busier than our minimum, replace it
            self.items[0] = (count, zone_id, name)
            self._fix_down(0)
    
    def _fix_up(self, i):
        """Move item up to maintain heap property"""
        while i > 0:
            parent = (i - 1) // 2
            if self.items[i][0] < self.items[parent][0]:
                self.items[i], self.items[parent] = self.items[parent], self.items[i]
                i = parent
            else:
                break
    
    def _fix_down(self, i):
        """Move item down to maintain heap property"""
        while True:
            smallest = i
            left = 2 * i + 1
            right = 2 * i + 2
            
            # Check if left child is smaller
            if left < len(self.items) and self.items[left][0] < self.items[smallest][0]:
                smallest = left
            # Check if right child is smaller
            if right < len(self.items) and self.items[right][0] < self.items[smallest][0]:
                smallest = right
            
            if smallest != i:
                self.items[i], self.items[smallest] = self.items[smallest], self.items[i]
                i = smallest
            else:
                break
    
    def get_sorted(self):
        """Return items sorted from highest to lowest"""
        result = list(self.items)
        # Simple sort - can't use built-in sorted()
        for i in range(len(result)):
            for j in range(i + 1, len(result)):
                if result[i][0] < result[j][0]:
                    result[i], result[j] = result[j], result[i]
        return result


def find_busiest_zones(zones, k=15):
    """
    Find the K busiest zones using our custom heap.
    This is more efficient than sorting all zones.
    """
    heap = MinHeap(k)
    
    # Go through each zone and add to heap
    for zone_id, data in zones.items():
        heap.add(data['count'], zone_id, data['zone_name'])
    
    return heap.get_sorted()
