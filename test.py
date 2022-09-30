from re import L
from redirect_check_lib import request_head_urls


def main():
    url = "https://sps.honeywell.com/us/en/products/safety/fall-protection/harnesses-belts-and-accessories/stopfall-fall-restraint-device"
    results = request_head_urls([url])
    print(results)

if __name__ == "__main__":
    import timeit
    from datetime import timedelta

    print(str(timedelta(seconds=timeit.timeit(main, number=1))))
