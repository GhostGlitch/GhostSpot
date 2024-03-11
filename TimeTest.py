import time
import subprocess

# Script 1
def Script_1():
    start_time = time.time()
    subprocess.call(['python', 'tst.py'])
    end_time = time.time()
    return (end_time - start_time)


# Script 2
def Script_2():
    start_time = time.time()
    subprocess.call(['python', 'GhostSpot.py'])
    end_time = time.time()
    execution_time = end_time - start_time
    return (end_time - start_time)
    print(f"Script 2 execution time: {execution_time} seconds")

if __name__ == "__main__":
    one_time = Script_1()
    two_time = Script_2()
    print(f"\nScript 1 execution time: {one_time} seconds")
    print(f"\nScript 2 execution time: {two_time} seconds")
    one_ten_times = sum([Script_1() for _ in range(10)]) / 10
    two_ten_times = sum([Script_2() for _ in range(10)]) / 10
    print(f"\nScript 1 single execution time: {one_time} seconds")
    print(f"\nScript 2 single execution time: {two_time} seconds")
    print(f"\nScript 1 average execution time: {one_ten_times} seconds")
    print(f"\nScript 2 average execution time: {two_ten_times} seconds")