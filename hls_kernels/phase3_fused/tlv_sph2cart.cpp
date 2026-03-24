/**
 * tlv_sph2cart.cpp
 * Fused TLV Decompression + Spherical-to-Cartesian Pipeline
 *
 * Target:  Artix-7 xc7a35tcpg236-1 (Basys-3)
 * Clock:   10 ns (100 MHz)
 * Phase:   3 — Fused pipeline
 *
 * Single loop per point:
 *   1. Read 64-bit packed word
 *   2. Extract fields (bit slicing → ap_int for sign extension)
 *   3. Multiply by decompression unit factors
 *   4. CORDIC sin/cos on decompressed azimuth & elevation
 *   5. Cartesian conversion
 *   6. Write [X, Y, Z, Doppler, SNR]
 *
 * No intermediate arrays. One point per clock cycle (II=1 target).
 */

#include "tlv_sph2cart.h"

void tlv_sph2cart(
    ap_uint<64>  compressed[MAX_NUM_POINTS],
    unit_t       pUnit[5],
    out_t        point_cloud[MAX_NUM_POINTS][OUT_DIMS],
    int          num_points
)
{
    // ---- Interface Pragmas ----
#pragma HLS INTERFACE mode=ap_ctrl_hs port=return
#pragma HLS INTERFACE mode=ap_memory port=compressed  storage_type=ram_1p
#pragma HLS INTERFACE mode=ap_memory port=pUnit       storage_type=ram_1p
#pragma HLS INTERFACE mode=ap_memory port=point_cloud storage_type=ram_1p

    // ---- Array Partitioning ----
    // Partition output dim so all 5 fields write in parallel
#pragma HLS ARRAY_PARTITION variable=point_cloud complete dim=2
    // Partition pUnit completely — only 5 elements, all needed every cycle
#pragma HLS ARRAY_PARTITION variable=pUnit complete dim=1

    // ---- Cache unit factors in registers ----
    // Read once, reuse every iteration (avoids BRAM reads in the loop)
    unit_t elev_unit = pUnit[0];
    unit_t az_unit   = pUnit[1];
    unit_t dopp_unit = pUnit[2];
    unit_t rng_unit  = pUnit[3];
    unit_t snr_unit  = pUnit[4];

    // ---- Main Fused Pipeline ----
    DECOMPRESS_CONVERT_LOOP:
    for (int i = 0; i < num_points; i++) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=MAX_NUM_POINTS avg=20
#pragma HLS PIPELINE II=1

        // ============================================================
        // Stage 1: Read packed 64-bit word and extract fields
        // ============================================================
        ap_uint<64> word = compressed[i];

        // Byte layout (little-endian from radar):
        //   [7:0]   = elevation  (int8,  signed)
        //   [15:8]  = azimuth    (int8,  signed)
        //   [31:16] = doppler    (int16, signed)
        //   [47:32] = range      (uint16, unsigned)
        //   [63:48] = snr        (uint16, unsigned)
        //
        // Using ap_int for signed → automatic sign extension
        // Using ap_uint for unsigned → zero extension
        ap_int<8>   raw_elev    = (ap_int<8>)  word( 7,  0);
        ap_int<8>   raw_az      = (ap_int<8>)  word(15,  8);
        ap_int<16>  raw_doppler = (ap_int<16>) word(31, 16);
        ap_uint<16> raw_range   = (ap_uint<16>)word(47, 32);
        ap_uint<16> raw_snr     = (ap_uint<16>)word(63, 48);

        // ============================================================
        // Stage 2: Decompress — multiply raw values by unit factors
        // ============================================================
        // In Python: range = raw_range * pUnit[3], etc.
        // ap_int × ap_fixed → ap_fixed (automatic widening)
        range_t   range     = (range_t)  (raw_range   * rng_unit);
        angle_t   azimuth   = (angle_t)  (raw_az      * az_unit);
        angle_t   elevation = (angle_t)  (raw_elev    * elev_unit);
        doppler_t doppler   = (doppler_t)(raw_doppler * dopp_unit);
        snr_t     snr_val   = (snr_t)    (raw_snr     * snr_unit);

        // ============================================================
        // Stage 3: CORDIC trig on decompressed angles
        // ============================================================
        trig_t sin_az  = hls::sin(azimuth);
        trig_t cos_az  = hls::cos(azimuth);
        trig_t sin_el  = hls::sin(elevation);
        trig_t cos_el  = hls::cos(elevation);

        // ============================================================
        // Stage 4: Cartesian conversion
        // ============================================================
        // X = range * sin(azimuth) * cos(elevation)
        coord_t x = (coord_t)(range * (coord_t)(sin_az * cos_el));

        // Y = range * cos(azimuth) * cos(elevation)
        coord_t y = (coord_t)(range * (coord_t)(cos_az * cos_el));

        // Z = range * sin(elevation)
        coord_t z = (coord_t)(range * sin_el);

        // ============================================================
        // Stage 5: Write output [X, Y, Z, Doppler, SNR]
        // ============================================================
        point_cloud[i][0] = (out_t) x;
        point_cloud[i][1] = (out_t) y;
        point_cloud[i][2] = (out_t) z;
        point_cloud[i][3] = (out_t) doppler;
        point_cloud[i][4] = (out_t) snr_val;
    }
}
