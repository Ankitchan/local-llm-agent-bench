def merge_intervals(intervals):
    result = []
    for start, end in sorted(intervals, key=lambda x: x[0]):
        if result and start <= result[-1][1]:
            result[-1][1] = max(result[-1][1], end)
        else:
            result.append([start, end])
    return result
