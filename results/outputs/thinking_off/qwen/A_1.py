def merge_intervals(intervals):
    if not intervals:
        return []
    
    # Sort by start time without mutating the original input
    sorted_intervals = sorted(intervals, key=lambda x: x[0])
    
    result = []
    for start, end in sorted_intervals:
        if result and start <= result[-1][1]:
            result[-1][1] = max(result[-1][1], end)
        else:
            result.append([start, end])
    return result
