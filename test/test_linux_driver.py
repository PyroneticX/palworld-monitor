import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.process_manager import LinuxProcessManager
import time

# Test LinuxProcessManager. This test its main methods are working properly. 
# This test is meant to be run on a Linux machine.
def main():
    driver = LinuxProcessManager()
    
    test_exe = 'python'
    test_args = 'test_sleep.py'
    
    print('>>> Testing LinuxProcessManager...')
    print('>>> 1. Launching test process...')
    driver.launch_process(test_exe, test_args)
    
    print('>>> 2. Checking if launched process is running...')
    time.sleep(1)
    is_running = driver.is_process_running()
    print(f'>>>    Launched process running: {is_running}')
    
    if is_running:
        print('>>> 3. Terminating launched process...')
        driver.terminate_process()
        time.sleep(1)
        
        is_still_running = driver.is_process_running()
        print(f'>>>    Launched process still running: {is_still_running}')
        
        if not is_still_running:
            print('>>> ✅ Test passed: Launched process was successfully terminated')
        else:
            print('>>> ❌ Test failed: Launched process is still running after termination')
    else:
        print('>>> ❌ Test failed: Launched process was not detected as running')

if __name__ == '__main__':
    main()