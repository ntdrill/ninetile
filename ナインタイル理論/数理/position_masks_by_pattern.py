python3 - <<'PY'
import csv
from pathlib import Path
from itertools import combinations

# mark ids: 0..5
marks = list(range(6))

# card definitions (mark0, mark1)
cards = [
    (0, 1),  # Maru - Cookie
    (0, 2),  # Maru - Sakura
    (0, 5),  # Maru - Brocco
    (3, 4),  # Lime - Hanabana
    (3, 2),  # Lime - Sakura
    (3, 5),  # Lime - Brocco
    (1, 4),  # Cookie - Hanabana
    (1, 2),  # Cookie - Sakura
    (4, 5),  # Hanabana - Brocco
]

# output
out_path = Path('/Users/numaoryuutarou/cursor/ninetile/ナインタイル理論/position_masks_by_pattern.csv')

# generator for multiset permutations

def gen_perms(counts, prefix, total):
    if len(prefix) == total:
        yield prefix
        return
    for m in range(6):
        if counts[m] > 0:
            counts[m] -= 1
            yield from gen_perms(counts, prefix + (m,), total)
            counts[m] += 1

# iterate type X and Y signatures
# type X: (2,2,2,2,1,0) assigned to marks
# choose mark for count 1 and mark for count 0

total = 0
with out_path.open('w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['type','pattern_idx','marks','mask1','mask2','mask3','mask4','mask5','mask6','mask7','mask8','mask9'])

    pattern_idx = 0

    # type X
    for one in marks:
        for zero in marks:
            if zero == one:
                continue
            counts = [2]*6
            counts[one] = 1
            counts[zero] = 0
            for perm in gen_perms(counts, (), 9):
                # compute masks per card
                masks = []
                for a, b in cards:
                    mask = 0
                    for i, m in enumerate(perm):
                        if m == a or m == b:
                            mask |= (1 << i)
                    masks.append(mask)
                writer.writerow(['X', pattern_idx, ''.join(map(str, perm))] + masks)
                pattern_idx += 1
                total += 1

    # type Y
    for ones in combinations(marks, 3):
        counts = [2]*6
        for m in ones:
            counts[m] = 1
        for perm in gen_perms(counts, (), 9):
            masks = []
            for a, b in cards:
                mask = 0
                for i, m in enumerate(perm):
                    if m == a or m == b:
                        mask |= (1 << i)
                masks.append(mask)
            writer.writerow(['Y', pattern_idx, ''.join(map(str, perm))] + masks)
            pattern_idx += 1
            total += 1

print('wrote', out_path)
print('total_patterns', total)
PY