import numpy as np
import math
import pandas as pd

class Distances:
    
    def euclidean(x,y):
        if len(x) != len(y):
            print("Error! Arrays doesn't have the same length.")
            return -1
        else:
            return math.sqrt(sum([(i-j)**2 for i,j in zip(x,y)]))
        
    def DTW(x,y):
        # Size of time series
        n = len(x)
        m = len(y)
        
        # Columns and index of table
        cols = [i for i in range(m+1)]
        idx = [i for i in range(n+1)]
        
        # Cost matrix
        dtw = pd.DataFrame(index=idx[::-1], columns=cols)
        dtw.loc[0,0] = 0
        dtw.iloc[:-1, 0] = np.inf
        dtw.loc[0, 1:] = np.inf
        
        for i in range(1, n+1):
            for j in range(1, m+1):
                cost = abs(x[i-1] - y[j-1])
                dtw.loc[i, j] = cost + min(dtw.loc[i-1, j], dtw.loc[i, j-1], dtw.loc[i-1,j-1])
        
        # Warp path
        path = []
        path.append((n,m))
        i = n
        j = m
        while i > 1 or j > 1:
            if i == 1:
                j -= 1
            elif j == 1:
                i -= 1
            else:
                idxs = {dtw.loc[i-1, j]:(i-1, j), dtw.loc[i, j-1]:(i, j-1), dtw.loc[i-1,j-1]:(i-1,j-1)}
                i = idxs[min(list(idxs.keys()))][0]
                j = idxs[min(list(idxs.keys()))][1]
                path.append((i,j))

        cost = dtw.iloc[0,-1]
        return dtw.iloc[:-1, 1:], path, cost