/**
 * tlv_sph2cart.h
 * Fused TLV Decompression + Spherical-to-Cartesian Pipeline
 *
 * Target:  Artix-7 xc7a35tcpg236-1 (Basys-3)
 * Clock:   10 ns (100 MHz)
 * Phase:   3 — Fused pipeline (decompress + convert in single pass)
 *
 * ──────────────────────────────────────────────────────────
 * Pipeline: raw compressed bytes → unpack → sign-extend →
 *           scale by unit factors → CORDIC trig → cartesian
 *
 * Eliminates intermediate spherical array from Phase 2.
 * Single streaming pass: one point in, one point out per cycle.
 * ──────────────────────────────────────────────────────────
 *
 * Compressed Point Format (from TI IWR6843 radar):
 *   Byte layout per point (8 bytes = 64 bits):
 *     [0]    elevation   int8     (signed)
 *     [1]    azimuth     int8     (signed)
 *     [2:3]  doppler     int16    (signed, little-endian)
 *     [4:5]  range       uint16   (unsigned, little-endian)
 *     [6:7]  snr         uint16   (unsigned, little-endian)
 *
 *   Decompression unit factors (5 values, from TLV header):
 *     pUnit[0] = elevation_unit   (rad per LSB)
 *     pUnit[1] = azimuth_unit     (rad per LSB)
 *     pUnit[2] = doppler_unit     (m/s per LSB)
 *     pUnit[3] = range_unit       (m per LSB)
 *     pUnit[4] = snr_unit         (dB per LSB)
 *
 *   Decompression:
 *     range     = raw_range   * pUnit[3]
 *     azimuth   = raw_azimuth * pUnit[1]
 *     elevation = raw_elev    * pUnit[0]
 *     doppler   = raw_doppler * pUnit[2]
 *     snr       = raw_snr     * pUnit[4]
 *
 *   Then spherical-to-cartesian:
 *     X = range * sin(azimuth) * cos(elevation)
 *     Y = range * cos(azimuth) * cos(elevation)
 *     Z = range * sin(elevation)
 *
 * Output per point: [X, Y, Z, Doppler, SNR]
 * ──────────────────────────────────────────────────────────
 */

#ifndef TLV_SPH2CART_H
#define TLV_SPH2CART_H

#include <ap_fixed.h>
#include <ap_int.h>
#include <hls_math.h>

// ---------- Design Parameters ----------

#define MAX_NUM_POINTS 128
#define OUT_DIMS       5     // X, Y, Z, Doppler, SNR

// ---------- Fixed-Point Type Definitions ----------

// Unit factors: small values (~0.001 to ~0.5 per LSB).
// 2 integer bits (range ±2.0), 16 fractional bits → resolution ~1.5e-5
typedef ap_fixed<18, 2>  unit_t;

// Decompressed range: up to ~16m.
// 5 integer bits (±16.0), 13 fractional bits → resolution ~0.00012m
typedef ap_fixed<18, 5>  range_t;

// Decompressed angles: up to ±π rad.
// 4 integer bits (±8.0), 14 fractional bits → resolution ~6.1e-5 rad
typedef ap_fixed<18, 4>  angle_t;

// Trig outputs: sin/cos ∈ [-1, +1].
// 2 integer bits, 16 fractional bits
typedef ap_fixed<18, 2>  trig_t;

// Cartesian output (X, Y, Z): up to ±16m.
// 5 integer bits, 15 fractional bits → resolution ~3.1e-5m
typedef ap_fixed<20, 5>  coord_t;

// Doppler output: up to ±16 m/s (typical indoor radar).
// 5 integer bits, 13 fractional bits
typedef ap_fixed<18, 6>  doppler_t;   // ±32 m/s

// SNR output: up to ~128 dB.
// 8 integer bits, 10 fractional bits
typedef ap_fixed<18, 9>  snr_t;       // ±256 dB

// Output type: must accommodate ALL output fields.
// coord_t (±16m) is fine for XYZ, but SNR can reach ~150 dB
// and Doppler can reach ±50 m/s in practice.
// ap_fixed<24,10> → range ±512, handles everything.
// Cost: 24-bit output words instead of 20-bit (4 extra bits per field).
typedef ap_fixed<24, 10> out_t;

// ---------- Top-Level Function Prototype ----------

void tlv_sph2cart(
    ap_uint<64>  compressed[MAX_NUM_POINTS],         // in:  packed raw point data
    unit_t       pUnit[5],                           // in:  decompression factors
    out_t        point_cloud[MAX_NUM_POINTS][OUT_DIMS], // out: [X, Y, Z, Doppler, SNR]
    int          num_points                          // actual point count this frame
);

#endif // TLV_SPH2CART_H