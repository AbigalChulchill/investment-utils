
def crossover(a,b):
    return len(a)>=2 and len(b)>=2 and a[-2] < b[-2] and a[-1] > b[-1]

def crossunder(a,b):
    return len(a)>=2 and len(b)>=2 and a[-2] > b[-2] and a[-1] < b[-1]

def crossup(a,y):
    return len(a)>=2 and a[-2] < y and a[-1] > y

def crossdown(a,y):
    return len(a)>=2 and a[-2] > y and a[-1] < y

def hlc3(h, l, c):
    return (h + l + c)/3
