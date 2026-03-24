/**
 * sph2cart.cpp
 * Spherical-to-Cartesian Point Cloud Conversion — Vitis HLS Kernel
 *
 * Target:  Artix-7 xc7a35tcpg236-1 (Basys-3)
 * Clock:   10 ns (100 MHz)
 * Phase:   2 — ap_fixed (CORDIC trig, DSP48E1-efficient)
 *
 * Changes from Phase 1 (float):
 *   - float → ap_fixed<18,W> types sized for DSP48E1
 *   - hls::sinf/cosf → hls::sin/cos (CORDIC inference)
 *   - Explicit intermediate types to control bit growth
 *
 * Expected improvements:
 *   - DSP: 67 → ~10-15 (CORDIC uses LUTs, not DSPs)
 *   - LUT: may increase slightly (CORDIC shift-add logic)
 *   - II: should remain 1
 *   - Latency: may decrease (CORDIC is simpler than float IP)
 */

#include "sph2cart.h"

void sph2cart(
    sph_t  spherical[MAX_NUM_POINTS][SPH_DIMS],
    cart_t cartesian[MAX_NUM_POINTS][SPH_DIMS],
    int    num_points
)
{
    // ---- Interface Pragmas ----
#pragma HLS INTERFACE mode=ap_ctrl_hs port=return
#pragma HLS INTERFACE mode=ap_memory port=spherical storage_type=ram_1p
#pragma HLS INTERFACE mode=ap_memory port=cartesian storage_type=ram_1p

    // ---- Array Partitioning ----
#pragma HLS ARRAY_PARTITION variable=spherical complete dim=2
#pragma HLS ARRAY_PARTITION variable=cartesian complete dim=2

    // ---- Main Conversion Loop ----
    CONVERT_LOOP:
    for (int i = 0; i < num_points; i++) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=MAX_NUM_POINTS avg=20
#pragma HLS PIPELINE II=1

        // Read inputs with explicit type casting
        range_t range     = (range_t) spherical[i][0];
        angle_t azimuth   = (angle_t) spherical[i][1];
        angle_t elevation = (angle_t) spherical[i][2];

        // ---- CORDIC Trig ----
        // hls::sin() and hls::cos() with ap_fixed arguments
        // infer CORDIC hardware instead of floating-point IP cores.
        // CORDIC uses only shifts and adds → LUTs, not DSP slices.
        trig_t sin_az  = hls::sin(azimuth);
        trig_t cos_az  = hls::cos(azimuth);
        trig_t sin_el  = hls::sin(elevation);
        trig_t cos_el  = hls::cos(elevation);

        // ---- Cartesian Conversion ----
        // Two-stage multiply to control bit growth.
        // Stage 1: combine trig terms (trig × trig → intermediate)
        // Stage 2: scale by range (range × intermediate → output)

        // X = range * sin(azimuth) * cos(elevation)
        coord_t x = (coord_t)(range * (coord_t)(sin_az * cos_el));

        // Y = range * cos(azimuth) * cos(elevation)
        coord_t y = (coord_t)(range * (coord_t)(cos_az * cos_el));

        // Z = range * sin(elevation)
        coord_t z = (coord_t)(range * sin_el);

        // Write outputs
        cartesian[i][0] = x;
        cartesian[i][1] = y;
        cartesian[i][2] = z;
    }
}