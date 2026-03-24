# ============================================================
# run_hls.tcl
# Vitis HLS project script for sph2cart kernel
#
# Target:  Artix-7 xc7a35tcpg236-1 (Basys-3)
# Clock:   10 ns (100 MHz)
# Phase:   Float (correctness validation)
#
# Usage:
#   vitis_hls -f run_hls.tcl
#
# Or step-by-step in the Vitis HLS GUI:
#   1. Create project with these settings
#   2. Run C Simulation
#   3. Run C Synthesis
#   4. Check reports for II and resource usage
# ============================================================

# ---------- Project Setup ----------
open_project sph2cart_prj
set_top sph2cart
add_files sph2cart.cpp
add_files sph2cart.h
add_files -tb sph2cart_tb.cpp

# ---------- Solution Configuration ----------
open_solution "sol1" -flow_target vivado
set_part {xc7a35tcpg236-1}
create_clock -period 10 -name default

# ---------- C Simulation ----------
puts "=========================================="
puts "  Running C Simulation..."
puts "=========================================="
csim_design

# ---------- C Synthesis ----------
puts "=========================================="
puts "  Running C Synthesis..."
puts "=========================================="
csynth_design

# ---------- Report Summary ----------
puts "=========================================="
puts "  Synthesis complete."
puts "  Check: sph2cart_prj/sol1/syn/report/sph2cart_csynth.rpt"
puts "  Key metrics to look for:"
puts "    - CONVERT_LOOP II (target: 1)"
puts "    - Latency per point"
puts "    - DSP48E1 usage (Basys-3 has 90)"
puts "    - LUT / FF usage"
puts "=========================================="

exit
