#!/bin/bash

is_asap7nm=true

# Benchmarks
bench_suite=(
    "usb_funct"
)

# Logic Synthesis
synth_scenarios=(
    "lazyman"
)
max_fanout=16

# Floorplanning
utilization=0.5

# Placement
placers=(
    "Capo"
)
target_density=0.8

# Timer
timers=(
    "UITimer"
    "iTimerC2.0"
)

# Gate Sizing
run_gs=false
sizers=(
    "USizer2013"
)

# Global Routing
global_routers=(
    "NCTUgr"
)
tile_size=30
num_layer=6
adjustment=10
safety=90

