def search(x, seq):
    for index in range(len(seq) - 1):
        if x <= index:
            return 0
        if seq[index] <= x <= seq[index + 1]:
            return index + 1
        if x >= seq[-1]:
            return len(seq)
    return len(seq)