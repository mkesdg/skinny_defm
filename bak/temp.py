import itertools

def sum_to_num(a,n):
    """Check for combinations of elements from an array that sum to a number"""
    res = []
    #a.sort(reverse = True)
    for c in xrange(len(a) + 1):
        for combo in itertools.combinations(a, c):
            #print combo
            if sum(combo) == n:
                res.append(combo)
    return [res]
    
153,190,675,545,426,519
