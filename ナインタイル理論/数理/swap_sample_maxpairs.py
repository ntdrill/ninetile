python3 - <<'PY'
import csv
import random
from pathlib import Path
from collections import defaultdict

random.seed(42)

path = Path('/Users/numaoryuutarou/cursor/ninetile/ナインタイル理論/position_masks_by_pattern.csv')

# sample size of patterns
K = 200

# reservoir sample pattern rows
sample = []
count = 0
with path.open(newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        count += 1
        if len(sample) < K:
            sample.append(row)
        else:
            j = random.randrange(count)
            if j < K:
                sample[j] = row

print('total_patterns', count)
print('sample_size', len(sample))

# prepare masks per sampled pattern
# masks are decimal strings in columns mask1..mask9

patterns = []
for row in sample:
    masks = [int(row[f'mask{i}']) for i in range(1, 10)]
    patterns.append({
        'pattern_idx': int(row['pattern_idx']),
        'type': row['type'],
        'masks': masks,
    })

# generate all assignments (card -> position) for a pattern

def enumerate_assignments(masks):
    options = []
    for mask in masks:
        opts = [p for p in range(9) if (mask >> p) & 1]
        options.append(opts)
    order = sorted(range(9), key=lambda c: len(options[c]))
    used = [False] * 9
    pos = [-1] * 9
    out = []
    def dfs(k):
        if k == 9:
            out.append(tuple(pos))
            return
        c = order[k]
        for p in options[c]:
            if not used[p]:
                used[p] = True
                pos[c] = p
                dfs(k + 1)
                used[p] = False
                pos[c] = -1
    dfs(0)
    return out

# cache assignments
assignments = []
for pat in patterns:
    assigns = enumerate_assignments(pat['masks'])
    assignments.append(assigns)

# swap count between two assignments

def swap_count(posA, posB):
    mapping = [None] * 9
    for c in range(9):
        mapping[posA[c]] = posB[c]
    visited = [False] * 9
    cycles = 0
    for i in range(9):
        if not visited[i]:
            cycles += 1
            j = i
            while not visited[j]:
                visited[j] = True
                j = mapping[j]
    return 9 - cycles

# compute min swaps for each pair in sample
hist = defaultdict(int)
max_swaps = -1
max_pairs = []

n = len(patterns)
for i in range(n):
    assigns_i = assignments[i]
    for j in range(i + 1, n):
        assigns_j = assignments[j]
        best = None
        for posA in assigns_i:
            for posB in assigns_j:
                s = swap_count(posA, posB)
                if best is None or s < best:
                    best = s
                    if best == 0:
                        break
            if best == 0:
                break
        hist[best] += 1
        if best > max_swaps:
            max_swaps = best
            max_pairs = [(i, j, best)]
        elif best == max_swaps:
            max_pairs.append((i, j, best))

print('pair_count', n*(n-1)//2)
print('max_swaps_in_sample', max_swaps)
print('hist', dict(sorted(hist.items())))

# write sample max pairs for inspection
out_path = Path('/Users/numaoryuutarou/cursor/ninetile/ナインタイル理論/swap_sample_max_pairs.csv')
with out_path.open('w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['pattern_idx_i','pattern_idx_j','type_i','type_j','min_swaps'])
    for i, j, s in max_pairs:
        writer.writerow([patterns[i]['pattern_idx'], patterns[j]['pattern_idx'], patterns[i]['type'], patterns[j]['type'], s])

print('wrote', out_path)
PY