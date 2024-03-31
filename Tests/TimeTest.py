import time
import subprocess
avg_exec_count = 3

def get_execution_time(path):
    start_time = time.time()
    subprocess.call(['python', path])
    end_time = time.time()
    return (end_time - start_time)

if __name__ == "__main__":
    one_sngl_time = get_execution_time('tst.py')
    two_sngl_time = get_execution_time('GhostSpot.py')
    print(f"\nScript 1 execution time: {one_sngl_time} seconds")
    print(f"\nScript 2 execution time: {two_sngl_time} seconds")
    one_avg_time = sum([get_execution_time('tst.py') for _ in range(avg_exec_count)]) / avg_exec_count
    two_avg_time = sum([get_execution_time('GhostSpot.py') for _ in range(avg_exec_count)]) / avg_exec_count
    print(f"\nScript 1 single execution time: {one_sngl_time} seconds")
    print(f"\nScript 2 single execution time: {two_sngl_time} seconds")
    print(f"\nScript 1 average execution time: {one_avg_time} seconds")
    print(f"\nScript 2 average execution time: {two_avg_time} seconds")