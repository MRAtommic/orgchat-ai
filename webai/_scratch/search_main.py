with open('templates/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

output = []
for i, line in enumerate(lines):
    if 'LINE_CHANNEL_ACCESS_TOKEN' in line:
        output.append(f"Line {i+1}: {line.strip()}")
        # print 20 lines around it
        start = max(0, i - 10)
        end = min(len(lines), i + 20)
        for j in range(start, end):
            output.append(f"  {j+1}: {lines[j].rstrip()}")

with open('_scratch/scratch_search_results.txt', 'w', encoding='utf-8') as out:
    out.write('\n'.join(output))
print("Done!")
