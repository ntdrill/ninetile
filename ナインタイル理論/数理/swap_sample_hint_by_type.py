python3 - <<'PY'
import csv
import random
from pathlib import Path
from collections import defaultdict

random.seed(42)

path = Path('/Users/numaoryuutarou/cursor/ninetile/ナインタイル理論/position_masks_by_pattern.csv')

K = 200

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

patterns = []
for row in sample:
    masks = [int(row[f'mask{i}']) for i in range(1, 10)]
    patterns.append({
        'pattern_idx': int(row['pattern_idx']),
        'type': row['type'],
        'masks': masks,
    })


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

assignments = [enumerate_assignments(p['masks']) for p in patterns]


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

pair_hist = {
    'X-X': defaultdict(int),
    'X-Y': defaultdict(int),
    'Y-Y': defaultdict(int),
}
max_by_type = {
    'X-X': -1,
    'X-Y': -1,
    'Y-Y': -1,
}

n = len(patterns)
for i in range(n):
    assigns_i = assignments[i]
    ti = patterns[i]['type']
    for j in range(i + 1, n):
        assigns_j = assignments[j]
        tj = patterns[j]['type']
        key = f"{ti}-{tj}" if ti <= tj else f"{tj}-{ti}"
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
        pair_hist[key][best] += 1
        if best > max_by_type[key]:
            max_by_type[key] = best

out_path = Path('/Users/numaoryuutarou/cursor/ninetile/ナインタイル理論/swap_sample_hist_by_type.csv')
with out_path.open('w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['pair_type','min_swaps','count'])
    for key in ['X-X','X-Y','Y-Y']:
        for k in sorted(pair_hist[key]):
            writer.writerow([key, k, pair_hist[key][k]])

print('sample_size', n)
print('max_by_type', max_by_type)
print('wrote', out_path)
PY