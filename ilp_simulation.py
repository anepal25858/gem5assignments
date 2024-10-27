import m5
from m5.objects import *
import sys

# Force print() to flush immediately
print = lambda *args, **kwargs: __builtins__.print(*args, **kwargs, flush=True)

def create_system(use_bp=True, num_threads=1):
    system = System()

    system.clk_domain = SrcClockDomain()
    system.clk_domain.clock = "1GHz"
    system.clk_domain.voltage_domain = VoltageDomain()
    system.stats_dump_period = '1000000t'
    system.mem_mode = 'timing'
    system.mem_ranges = [AddrRange("512MB")]
    system.mem_ctrl = DDR4_2400_8x8()
    system.mem_ctrl.range = system.mem_ranges[0]

    system.cpu = X86O3CPU()
    system.cpu.numThreads = num_threads

    if use_bp:
        system.cpu.branchPred = TournamentBP()
    else:
        system.cpu.branchPred = NULL

    system.cpu.icache = L1_ICache()
    system.cpu.dcache = L1_DCache()

    system.cpu.icache.connectCPU(system.cpu)
    system.cpu.dcache.connectCPU(system.cpu)

    system.membus = SystemXBar()

    system.cpu.icache.connectBus(system.membus)
    system.cpu.dcache.connectBus(system.membus)

    system.mem_ctrl.port = system.membus.master

    system.cpu.createInterruptController()
    system.cpu.interrupts[0].pio = system.membus.master
    system.cpu.interrupts[0].int_master = system.membus.slave
    system.cpu.interrupts[0].int_slave = system.membus.master

    system.system_port = system.membus.slave

    return system


def run_simulation(system, benchmark):
    process = Process()
    process.cmd = [benchmark]
    system.cpu.workload = process
    system.cpu.createThreads()

    root = Root(full_system=False, system=system)

    m5.instantiate()

    print(f"Beginning simulation for {benchmark}!")
    exit_event = m5.simulate()
    print(f'Exiting @ tick {m5.curTick()} because {exit_event.getCause()}')

    # Explicitly dump statistics
    m5.stats.dump()
    m5.stats.reset()

def print_stats(system):
    # Your existing print_stats code here
    # ...

    # Add this line to read from stats.txt
    print("\nContents of stats.txt:")
    with open('m5out/stats.txt', 'r') as f:
        print(f.read())

def print_stats(system):
    print("\nSimulation statistics:")
    print(f"Instructions per cycle (IPC): {system.cpu.ipc}")
    print(f"Number of cycles: {system.cpu.numCycles}")
    print(f"Number of instructions: {system.cpu.numInsts}")
    if isinstance(system.cpu.branchPred, TournamentBP):
        accuracy = system.cpu.branchPred.condPredicted / (system.cpu.branchPred.condPredicted + system.cpu.branchPred.condIncorrect)
        print(f"Branch prediction accuracy: {accuracy:.2%}")
    print(f"Simulation ticks: {m5.curTick()}")

def main():
    # Enable debug flags
    m5.debug.flags['Terminal'].enable()
    m5.debug.flags['EXEC'].enable()

    benchmarks = [
        'tests/test-progs/hello/bin/x86/linux/hello',
        'tests/test-progs/matrix-multiply/bin/x86/linux/matrix-multiply',
        'tests/test-progs/quicksort/bin/x86/linux/quicksort'
    ]

    for benchmark in benchmarks:
        print(f"\n--- Running benchmark: {benchmark} ---")

        print("\nSimulation without branch prediction:")
        system = create_system(use_bp=False, num_threads=1)
        run_simulation(system, benchmark)
        print_stats(system)

        m5.reset()

        print("\nSimulation with branch prediction:")
        system = create_system(use_bp=True, num_threads=1)
        run_simulation(system, benchmark)
        print_stats(system)

        m5.reset()

if __name__ == "__main__":
    main()
