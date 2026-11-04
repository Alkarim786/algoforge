"""Independent solutions for the flagship problems, used as an oracle to check seed content."""
import heapq
import sys
from collections import Counter, deque

# Some test trees are 1000 levels deep, past Python's default limit for the recursive solutions here.
sys.setrecursionlimit(20_000)


def two_sum(nums, target):
    seen = {}
    for i, value in enumerate(nums):
        if target - value in seen:
            return [seen[target - value], i]
        seen[value] = i


def maximum_subarray(nums):
    best = current = nums[0]
    for value in nums[1:]:
        current = max(value, current + value)
        best = max(best, current)
    return best


def number_of_1_bits(n):
    count = 0
    while n:
        n &= n - 1
        count += 1
    return count


def counting_bits(n):
    bits = [0] * (n + 1)
    for i in range(1, n + 1):
        bits[i] = bits[i >> 1] + (i & 1)
    return bits


def climbing_stairs(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def coin_change(coins, amount):
    best = [0] + [amount + 1] * amount
    for total in range(1, amount + 1):
        for coin in coins:
            if coin <= total:
                best[total] = min(best[total], best[total - coin] + 1)
    return -1 if best[amount] > amount else best[amount]


def course_schedule(num_courses, prerequisites):
    indegree = [0] * num_courses
    next_courses = [[] for _ in range(num_courses)]
    for course, prerequisite in prerequisites:
        indegree[course] += 1
        next_courses[prerequisite].append(course)
    queue = deque(i for i in range(num_courses) if indegree[i] == 0)
    done = 0
    while queue:
        done += 1
        for course in next_courses[queue.popleft()]:
            indegree[course] -= 1
            if indegree[course] == 0:
                queue.append(course)
    return done == num_courses


def number_of_islands(grid):
    land = {(r, c) for r, row in enumerate(grid) for c, cell in enumerate(row) if cell == "1"}
    islands = 0
    while land:
        islands += 1
        stack = [land.pop()]
        while stack:
            r, c = stack.pop()
            for cell in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if cell in land:
                    land.remove(cell)
                    stack.append(cell)
    return islands


def merge_intervals(intervals):
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


def insert_interval(intervals, new_interval):
    return merge_intervals(intervals + [new_interval])


def reverse_linked_list(values):
    return values[::-1]


def merge_two_sorted_lists(a, b):
    return list(heapq.merge(a, b))


def set_matrix_zeroes(matrix):
    rows = {r for r, row in enumerate(matrix) if 0 in row}
    cols = {c for row in matrix for c, value in enumerate(row) if value == 0}
    return [[0 if r in rows or c in cols else v for c, v in enumerate(row)] for r, row in enumerate(matrix)]


def rotate_image(matrix):
    return [list(row) for row in zip(*matrix[::-1])]


def longest_substring(s):
    last_seen = {}
    start = best = 0
    for i, char in enumerate(s):
        if last_seen.get(char, -1) >= start:
            start = last_seen[char] + 1
        last_seen[char] = i
        best = max(best, i - start + 1)
    return best


def valid_parentheses(s):
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []
    for char in s:
        if char in pairs:
            if not stack or stack.pop() != pairs[char]:
                return False
        else:
            stack.append(char)
    return not stack


def _tree_children(values):
    """Map level-order index -> (left index, right index), following the omit-children-of-null format."""
    children = {}
    next_index = 1
    for i, value in enumerate(values):
        if value is None:
            continue
        left = next_index if next_index < len(values) and values[next_index] is not None else None
        right = next_index + 1 if next_index + 1 < len(values) and values[next_index + 1] is not None else None
        children[i] = (left, right)
        next_index += 2
    return children


def maximum_depth(values):
    if not values:
        return 0
    children = _tree_children(values)

    def depth(i):
        return 0 if i is None else 1 + max(depth(children[i][0]), depth(children[i][1]))

    return depth(0)


def validate_bst(values):
    children = _tree_children(values)

    def valid(i, low, high):
        if i is None:
            return True
        if not low < values[i] < high:
            return False
        return valid(children[i][0], low, values[i]) and valid(children[i][1], values[i], high)

    return valid(0, float("-inf"), float("inf"))


def top_k_frequent(nums, k):
    return sorted(value for value, _ in Counter(nums).most_common(k))


def find_median(operations):
    low, high, results = [], [], []
    for operation in operations:
        if operation[0] == "add":
            heapq.heappush(high, -heapq.heappushpop(low, -operation[1]))
            if len(high) > len(low):
                heapq.heappush(low, -heapq.heappop(high))
        else:
            results.append(float(-low[0]) if len(low) > len(high) else (-low[0] + high[0]) / 2)
    return results


def best_time_to_buy_and_sell(prices):
    lowest, best = float("inf"), 0
    for price in prices:
        lowest = min(lowest, price)
        best = max(best, price - lowest)
    return best


def contains_duplicate(nums):
    return len(set(nums)) != len(nums)


def product_except_self(nums):
    n = len(nums)
    result = [1] * n
    left = 1
    for i in range(n):
        result[i] = left
        left *= nums[i]
    right = 1
    for i in range(n - 1, -1, -1):
        result[i] *= right
        right *= nums[i]
    return result


def maximum_product_subarray(nums):
    best = high = low = nums[0]
    for value in nums[1:]:
        candidates = (value, high * value, low * value)
        high, low = max(candidates), min(candidates)
        best = max(best, high)
    return best


def find_min_rotated(nums):
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] > nums[hi]:
            lo = mid + 1
        else:
            hi = mid
    return nums[lo]


def search_rotated(nums, target):
    return nums.index(target) if target in nums else -1


def three_sum(nums):
    found = set()
    seen_first = set()
    for i, first in enumerate(nums):
        if first in seen_first:
            continue
        seen_first.add(first)
        seen = set()
        for second in nums[i + 1:]:
            third = -first - second
            if third in seen:
                found.add(tuple(sorted((first, second, third))))
            seen.add(second)
    return sorted(list(triplet) for triplet in found)


def container_with_most_water(height):
    lo, hi, best = 0, len(height) - 1, 0
    while lo < hi:
        best = max(best, (hi - lo) * min(height[lo], height[hi]))
        if height[lo] < height[hi]:
            lo += 1
        else:
            hi -= 1
    return best


def sum_of_two_integers(a, b):
    return a + b


def missing_number(nums):
    n = len(nums)
    return n * (n + 1) // 2 - sum(nums)


def reverse_bits(n):
    return int(f"{n:032b}"[::-1], 2)


def longest_increasing_subsequence(nums):
    from bisect import bisect_left

    tails = []
    for value in nums:
        i = bisect_left(tails, value)
        if i == len(tails):
            tails.append(value)
        else:
            tails[i] = value
    return len(tails)


def longest_common_subsequence(a, b):
    previous = [0] * (len(b) + 1)
    for x in a:
        current = [0]
        for j, y in enumerate(b):
            current.append(previous[j] + 1 if x == y else max(previous[j + 1], current[j]))
        previous = current
    return previous[-1]


def word_break(s, words):
    lengths = {len(word) for word in words}
    vocabulary = set(words)
    ok = [True] + [False] * len(s)
    for end in range(1, len(s) + 1):
        ok[end] = any(length <= end and ok[end - length] and s[end - length:end] in vocabulary for length in lengths)
    return ok[-1]


def combination_sum_iv(nums, target):
    ways = [1] + [0] * target
    for total in range(1, target + 1):
        ways[total] = sum(ways[total - value] for value in nums if value <= total)
    return ways[target]


def house_robber(nums):
    take = skip = 0
    for value in nums:
        take, skip = skip + value, max(take, skip)
    return max(take, skip)


def house_robber_ii(nums):
    if len(nums) == 1:
        return nums[0]
    return max(house_robber(nums[1:]), house_robber(nums[:-1]))


def decode_ways(s):
    previous, current = 1, 1 if s[0] != "0" else 0
    for i in range(1, len(s)):
        single = current if s[i] != "0" else 0
        double = previous if 10 <= int(s[i - 1 : i + 1]) <= 26 else 0
        previous, current = current, single + double
    return current


def unique_paths(m, n):
    from math import comb

    return comb(m + n - 2, m - 1)


def jump_game(nums):
    reach = 0
    for i, jump in enumerate(nums):
        if i > reach:
            return False
        reach = max(reach, i + jump)
    return True


def erase_overlap_intervals(intervals):
    kept, last_end = 0, float("-inf")
    for start, end in sorted(intervals, key=lambda interval: interval[1]):
        if start >= last_end:
            kept += 1
            last_end = end
    return len(intervals) - kept


def can_attend_meetings(intervals):
    ordered = sorted(intervals)
    return all(ordered[i][0] >= ordered[i - 1][1] for i in range(1, len(ordered)))


def min_meeting_rooms(intervals):
    events = sorted([(start, 1) for start, _ in intervals] + [(end, -1) for _, end in intervals])
    rooms = best = 0
    for _, change in events:  # at equal times the -1 sorts first: a room frees up before it's reused
        rooms += change
        best = max(best, rooms)
    return best


def spiral_order(matrix):
    result = []
    top, bottom, left, right = 0, len(matrix) - 1, 0, len(matrix[0]) - 1
    while top <= bottom and left <= right:
        result += [matrix[top][c] for c in range(left, right + 1)]
        result += [matrix[r][right] for r in range(top + 1, bottom + 1)]
        if top < bottom:
            result += [matrix[bottom][c] for c in range(right - 1, left - 1, -1)]
        if left < right:
            result += [matrix[r][left] for r in range(bottom - 1, top, -1)]
        top, bottom, left, right = top + 1, bottom - 1, left + 1, right - 1
    return result


def word_search(board, word):
    from collections import Counter

    rows, cols = len(board), len(board[0])
    available = Counter(cell for row in board for cell in row)
    if any(available[char] < count for char, count in Counter(word).items()):
        return False

    def dfs(r, c, i):
        if i == len(word):
            return True
        if not (0 <= r < rows and 0 <= c < cols) or board[r][c] != word[i]:
            return False
        board[r][c] = "#"
        found = any(dfs(r + dr, c + dc, i + 1) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        board[r][c] = word[i]
        return found

    return any(dfs(r, c, 0) for r in range(rows) for c in range(cols))


def linked_list_cycle(values, position):
    return position >= 0


def merge_k_sorted_lists(lists):
    return sorted(value for values in lists for value in values)


def remove_nth_from_end(values, n):
    index = len(values) - n
    return values[:index] + values[index + 1:]


def reorder_list(values):
    result, lo, hi = [], 0, len(values) - 1
    while lo <= hi:
        result.append(values[lo])
        if lo != hi:
            result.append(values[hi])
        lo, hi = lo + 1, hi - 1
    return result


def clone_graph(adjacency):
    return adjacency


def pacific_atlantic(heights):
    rows, cols = len(heights), len(heights[0])

    def flow(starts):
        reached, stack = set(starts), list(starts)
        while stack:
            r, c = stack.pop()
            for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in reached and heights[nr][nc] >= heights[r][c]:
                    reached.add((nr, nc))
                    stack.append((nr, nc))
        return reached

    pacific = flow([(0, c) for c in range(cols)] + [(r, 0) for r in range(rows)])
    atlantic = flow([(rows - 1, c) for c in range(cols)] + [(r, cols - 1) for r in range(rows)])
    return sorted([r, c] for r, c in pacific & atlantic)


def longest_consecutive(nums):
    values, best = set(nums), 0
    for value in values:
        if value - 1 not in values:
            length = 1
            while value + length in values:
                length += 1
            best = max(best, length)
    return best


def alien_order(words):
    import heapq

    letters = {char for word in words for char in word}
    after = {char: set() for char in letters}
    for first, second in zip(words, words[1:]):
        for a, b in zip(first, second):
            if a != b:
                after[a].add(b)
                break
        else:
            if len(first) > len(second):
                return ""
    waiting = {char: 0 for char in letters}
    for char in letters:
        for nxt in after[char]:
            waiting[nxt] += 1
    ready = [char for char in letters if waiting[char] == 0]
    heapq.heapify(ready)
    order = []
    while ready:
        char = heapq.heappop(ready)
        order.append(char)
        for nxt in after[char]:
            waiting[nxt] -= 1
            if waiting[nxt] == 0:
                heapq.heappush(ready, nxt)
    return "".join(order) if len(order) == len(letters) else ""


def graph_valid_tree(n, edges):
    if len(edges) != n - 1:
        return False
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra == rb:
            return False
        parent[ra] = rb
    return True


def count_components(n, edges):
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    components = n
    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
            components -= 1
    return components


def character_replacement(s, k):
    counts = Counter()
    start = top = best = 0
    for end, char in enumerate(s):
        counts[char] += 1
        top = max(top, counts[char])
        if end - start + 1 - top > k:
            counts[s[start]] -= 1
            start += 1
        best = max(best, end - start + 1)
    return best


def minimum_window(s, t):
    need = Counter(t)
    missing = len(t)
    start = best_start = 0
    best_length = float("inf")
    for end, char in enumerate(s):
        if need[char] > 0:
            missing -= 1
        need[char] -= 1
        while missing == 0:
            if end - start + 1 < best_length:
                best_start, best_length = start, end - start + 1
            need[s[start]] += 1
            if need[s[start]] > 0:
                missing += 1
            start += 1
    return "" if best_length == float("inf") else s[best_start:best_start + best_length]


def valid_anagram(s, t):
    return Counter(s) == Counter(t)


def group_anagrams(strs):
    groups = {}
    for word in strs:
        groups.setdefault("".join(sorted(word)), []).append(word)
    return sorted(sorted(group) for group in groups.values())


def valid_palindrome(s):
    cleaned = [char.lower() for char in s if char.isalnum()]
    return cleaned == cleaned[::-1]


def longest_palindromic_substring(s):
    best = s[0]
    for center in range(2 * len(s) - 1):
        lo, hi = center // 2, center // 2 + center % 2
        while lo >= 0 and hi < len(s) and s[lo] == s[hi]:
            lo, hi = lo - 1, hi + 1
        if hi - lo - 1 > len(best):
            best = s[lo + 1:hi]
    return best


def palindromic_substrings(s):
    count = 0
    for center in range(2 * len(s) - 1):
        lo, hi = center // 2, center // 2 + center % 2
        while lo >= 0 and hi < len(s) and s[lo] == s[hi]:
            count += 1
            lo, hi = lo - 1, hi + 1
    return count


def encode_and_decode_strings(strs):
    return strs


class _Tree:
    def __init__(self, val, left=None, right=None):
        self.val, self.left, self.right = val, left, right


def _build(values):
    if not values:
        return None
    root = _Tree(values[0])
    queue, i = deque([root]), 1
    while queue and i < len(values):
        node = queue.popleft()
        if values[i] is not None:
            node.left = _Tree(values[i])
            queue.append(node.left)
        i += 1
        if i < len(values) and values[i] is not None:
            node.right = _Tree(values[i])
            queue.append(node.right)
        i += 1
    return root


def _values(root):
    out, queue = [], deque([root] if root else [])
    while queue:
        node = queue.popleft()
        out.append(node.val if node else None)
        if node:
            queue.extend((node.left, node.right))
    while out and out[-1] is None:
        out.pop()
    return out


def _inorder(node):
    return [] if node is None else _inorder(node.left) + [node.val] + _inorder(node.right)


def same_tree(p, q):
    return _values(_build(p)) == _values(_build(q))


def invert_tree(values):
    def invert(node):
        if node:
            node.left, node.right = invert(node.right), invert(node.left)
        return node

    return _values(invert(_build(values)))


def max_path_sum(values):
    best = float("-inf")

    def gain(node):
        nonlocal best
        if node is None:
            return 0
        left, right = max(gain(node.left), 0), max(gain(node.right), 0)
        best = max(best, node.val + left + right)
        return node.val + max(left, right)

    gain(_build(values))
    return best


def level_order(values):
    levels, queue = [], deque([_build(values)] if values else [])
    while queue:
        levels.append([node.val for node in queue])
        queue = deque(child for node in queue for child in (node.left, node.right) if child)
    return levels


def serialize_tree(values):
    return _values(_build(values))


def subtree_of_another(root, sub):
    target = _values(_build(sub))

    def walk(node):
        return node is not None and (_values(node) == target or walk(node.left) or walk(node.right))

    return walk(_build(root))


def build_from_preorder_inorder(preorder, inorder):
    position = {value: i for i, value in enumerate(inorder)}
    next_root = iter(preorder)

    def build(lo, hi):
        if lo > hi:
            return None
        value = next(next_root)
        node = _Tree(value)
        node.left = build(lo, position[value] - 1)
        node.right = build(position[value] + 1, hi)
        return node

    return _values(build(0, len(inorder) - 1))


def kth_smallest(values, k):
    return _inorder(_build(values))[k - 1]


def lca_bst(values, p, q):
    node = _build(values)
    while True:
        if p < node.val and q < node.val:
            node = node.left
        elif p > node.val and q > node.val:
            node = node.right
        else:
            return node.val


def trie_operations(operations):
    words, results = set(), []
    for name, text in operations:
        if name == "insert":
            words.add(text)
        elif name == "search":
            results.append(text in words)
        else:
            results.append(any(word.startswith(text) for word in words))
    return results


def word_dictionary_operations(operations):
    import re

    words, results = set(), []
    for name, text in operations:
        if name == "addWord":
            words.add(text)
        else:
            pattern = re.compile(text.replace(".", "[a-z]"))
            results.append(any(pattern.fullmatch(word) for word in words))
    return results


def word_search_ii(board, words):
    return sorted(word for word in set(words) if word_search([row[:] for row in board], word))


SOLUTIONS = {
    "same-tree": same_tree,
    "invert-binary-tree": invert_tree,
    "binary-tree-maximum-path-sum": max_path_sum,
    "binary-tree-level-order-traversal": level_order,
    "serialize-and-deserialize-binary-tree": serialize_tree,
    "subtree-of-another-tree": subtree_of_another,
    "construct-binary-tree-from-preorder-and-inorder-traversal": build_from_preorder_inorder,
    "kth-smallest-element-in-a-bst": kth_smallest,
    "lowest-common-ancestor-of-a-binary-search-tree": lca_bst,
    "implement-trie-prefix-tree": trie_operations,
    "design-add-and-search-words-data-structure": word_dictionary_operations,
    "word-search-ii": word_search_ii,
    "longest-repeating-character-replacement": character_replacement,
    "minimum-window-substring": minimum_window,
    "valid-anagram": valid_anagram,
    "group-anagrams": group_anagrams,
    "valid-palindrome": valid_palindrome,
    "longest-palindromic-substring": longest_palindromic_substring,
    "palindromic-substrings": palindromic_substrings,
    "encode-and-decode-strings": encode_and_decode_strings,
    "linked-list-cycle": linked_list_cycle,
    "merge-k-sorted-lists": merge_k_sorted_lists,
    "remove-nth-node-from-end-of-list": remove_nth_from_end,
    "reorder-list": reorder_list,
    "clone-graph": clone_graph,
    "pacific-atlantic-water-flow": pacific_atlantic,
    "longest-consecutive-sequence": longest_consecutive,
    "alien-dictionary": alien_order,
    "graph-valid-tree": graph_valid_tree,
    "number-of-connected-components-in-an-undirected-graph": count_components,
    "non-overlapping-intervals": erase_overlap_intervals,
    "meeting-rooms": can_attend_meetings,
    "meeting-rooms-ii": min_meeting_rooms,
    "spiral-matrix": spiral_order,
    "word-search": word_search,
    "longest-increasing-subsequence": longest_increasing_subsequence,
    "longest-common-subsequence": longest_common_subsequence,
    "word-break": word_break,
    "combination-sum-iv": combination_sum_iv,
    "house-robber": house_robber,
    "house-robber-ii": house_robber_ii,
    "decode-ways": decode_ways,
    "unique-paths": unique_paths,
    "jump-game": jump_game,
    "sum-of-two-integers": sum_of_two_integers,
    "missing-number": missing_number,
    "reverse-bits": reverse_bits,
    "best-time-to-buy-and-sell-stock": best_time_to_buy_and_sell,
    "contains-duplicate": contains_duplicate,
    "product-of-array-except-self": product_except_self,
    "maximum-product-subarray": maximum_product_subarray,
    "find-minimum-in-rotated-sorted-array": find_min_rotated,
    "search-in-rotated-sorted-array": search_rotated,
    "3sum": three_sum,
    "container-with-most-water": container_with_most_water,
    "two-sum": two_sum,
    "maximum-subarray": maximum_subarray,
    "number-of-1-bits": number_of_1_bits,
    "counting-bits": counting_bits,
    "climbing-stairs": climbing_stairs,
    "coin-change": coin_change,
    "course-schedule": course_schedule,
    "number-of-islands": number_of_islands,
    "insert-interval": insert_interval,
    "merge-intervals": merge_intervals,
    "reverse-linked-list": reverse_linked_list,
    "merge-two-sorted-lists": merge_two_sorted_lists,
    "set-matrix-zeroes": set_matrix_zeroes,
    "rotate-image": rotate_image,
    "longest-substring-without-repeating-characters": longest_substring,
    "valid-parentheses": valid_parentheses,
    "maximum-depth-of-binary-tree": maximum_depth,
    "validate-binary-search-tree": validate_bst,
    "top-k-frequent-elements": top_k_frequent,
    "find-median-from-data-stream": find_median,
}
