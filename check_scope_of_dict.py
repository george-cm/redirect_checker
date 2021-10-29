from random import randint

def main():
    cached_results = dict()
    for i in range(10000):
        x = randint(1, 10)
        f = closure(x, cached_results)
        r = f()
        print(i, r)

def closure(x, cached_results):
    def func():
        if x in cached_results:
            print('Returning cached result')
            return cached_results[x]
        print('Returning computed result')
        cached_results[x] = randint(1, 100)
        return cached_results[x]
    return func

if __name__ == "__main__":
    import timeit
    from datetime import timedelta
    print(str(timedelta(seconds=timeit.timeit(main, number=1))))