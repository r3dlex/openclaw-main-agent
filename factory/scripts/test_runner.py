import sys

def run_tests(stack):
    print(f"[{stack}] Initializing test environment...")
    print(f"[{stack}] Discovering tests...")
    print(f"[{stack}] Running suite...")
    print(f"[{stack}] All tests passed (SIMULATION).")

if __name__ == "__main__":
    run_tests(sys.argv[1])
