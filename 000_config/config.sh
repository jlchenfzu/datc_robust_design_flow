#!/bin/bash

# Benchmarks
bench_suite=(
    "ac97_ctrl"
)

# Logic Synthesis
synth_scenarios=(
    "timing"
)
max_fanout=16

# Floorplanning
utilization=0.6

# Placement
placers=(
    "EhPlacer"
)
target_density=0.8

# Gate Sizing
run_gs=false
sizers=(
    "USizer2013"
)

# Global Routing
global_routers=("NCTUgr")
tile_size=50
num_layer=4
adjustment=10
safety=90

# Detailed Routing
detail_routers=(
    "NCTUdr"
)

