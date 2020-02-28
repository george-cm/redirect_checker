def outer(n):
    def inner(gen):
        while True:
            results = []
            for i in range(n):
                try:
                    el = next(gen)
                except StopIteration:
                    if results:
                        yield results
                        return
                    else:
                        return
                results.append(el)
            yield results
    return inner

lst = ['a', 'b', 'c', 'd', 'e', 'f']
gen = (x for x in lst)

mygen = outer(1)

for i in mygen(gen):
    print(i)