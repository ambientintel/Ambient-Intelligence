/**
 * sph2cart.h
 * Spherical-to-Cartesian Point Cloud Conversion — Vitis HLS Kernel
 *
 * Target:  Artix-7 xc7a35tcpg236-1 (Basys-3)
 * Clock:   10 ns (100 MHz)
 * Phase:   2 — ap_fixed (CORDIC trig, DSP48E1-efficient)
 *
 * ──────────────────────────────────────────────────────────
 * Fixed-Point Format Rationale
 * ──────────────────────────────────────────────────────────
 *
 * DSP48E1 on Artix-7 has 18×25 multipliers.
 * Using ap_fixed<18,W> ensures each multiply maps to 1 DSP slice.
 *
 * Type         Format           Range           Resolution    Usage
 * ─────────────────────────────────────────────────────────────────
 * range_t      ap_fixed<18,5>   [-16, +15.99]   ~0.000122     Range (0.5–8m)
 * angle_t      ap_fixed<18,4>   [-8, +7.99]     ~0.000061     Azimuth/Elevation (±π)
 * trig_t       ap_fixed<18,2>   [-2, +1.99]     ~0.000015     sin/cos outputs (±1)
 * coord_t      ap_fixed<20,5>   [-16, +15.99]   ~0.000031     Cartesian XYZ output
 *
 * coord_t is 20 bits (not 18) to hold the product of range × trig × trig
 * without losing precision in the final result. The extra 2 fractional bits
 * capture precision from the trig multiplication chain.
 *
 * Bit growth analysis:
 *   range(18,5) × trig(18,2) = intermediate(36,7) → truncate to (20,5)
 *   intermediate(20,5) × trig(18,2) = result(38,7) → truncate to (20,5)
 *
 * ──────────────────────────────────────────────────────────
 */

#ifndef SPH2CART_H
#define SPH2CART_H

#include <ap_fixed.h>
#include <hls_math.h>

// ---------- Design Parameters ----------

#define MAX_NUM_POINTS 128
#define SPH_DIMS 3

// ---------- Fixed-Point Type Definitions ----------

// Range: radar reports 0.5–8.0m. 5 integer bits → ±16.0 headroom.
// 13 fractional bits → resolution ~0.000122m (~0.1mm)
typedef ap_fixed<18, 5> range_t;

// Angles: azimuth/elevation in radians. 4 integer bits → ±8.0 covers ±π.
// 14 fractional bits → resolution ~0.000061 rad (~0.0035°)
typedef ap_fixed<18, 4> angle_t;

// Trig outputs: sin/cos ∈ [-1, +1]. 2 integer bits (sign + 1).
// 16 fractional bits → resolution ~0.000015
typedef ap_fixed<18, 2> trig_t;

// Cartesian output: X,Y,Z up to ±8.0m. 5 integer bits for headroom.
// 15 fractional bits → resolution ~0.000031m
typedef ap_fixed<20, 5> coord_t;

// Input/output array element type (matches interface)
// Using range_t for input (spherical) and coord_t for output (cartesian)
typedef range_t  sph_t;
typedef coord_t  cart_t;

// ---------- Top-Level Function Prototype ----------

void sph2cart(
    sph_t  spherical[MAX_NUM_POINTS][SPH_DIMS],  // in:  [range, azimuth, elevation]
    cart_t cartesian[MAX_NUM_POINTS][SPH_DIMS],   // out: [x, y, z]
    int    num_points                              // actual point count this frame
);

#endif // SPH2CART_H