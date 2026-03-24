/**
 * tlv_sph2cart_axi.h
 * Fused TLV Decompression + Spherical-to-Cartesian — AXI Interface Version
 *
 * Target:  Artix-7 xc7a35tcpg236-1 (Basys-3)
 * Clock:   10 ns (100 MHz)
 *
 * Interfaces:
 *   - AXI-Stream (axis) for compressed input and cartesian output
 *   - AXI-Lite (s_axilite) for control, unit factors, and num_points
 *
 * This version is Vivado block-design ready. Connect:
 *   - s_axis_input  ← DMA or custom UART-to-AXI bridge
 *   - m_axis_output → DMA or downstream processing
 *   - s_axi_control ← processor (PS or MicroBlaze)
 */

#ifndef TLV_SPH2CART_AXI_H
#define TLV_SPH2CART_AXI_H

#include <ap_fixed.h>
#include <ap_int.h>
#include <hls_math.h>
#include <hls_stream.h>
#include <ap_axi_sdata.h>

// ---------- Design Parameters ----------

#define MAX_NUM_POINTS 128
#define OUT_DIMS       5     // X, Y, Z, Doppler, SNR

// ---------- Fixed-Point Types (same as Phase 3) ----------

typedef ap_fixed<18, 2>  unit_t;
typedef ap_fixed<18, 5>  range_t;
typedef ap_fixed<18, 4>  angle_t;
typedef ap_fixed<18, 2>  trig_t;
typedef ap_fixed<20, 5>  coord_t;
typedef ap_fixed<18, 6>  doppler_t;
typedef ap_fixed<18, 9>  snr_t;
typedef ap_fixed<24, 10> out_t;

// ---------- AXI-Stream Data Types ----------

// Input stream: 64-bit packed compressed point data
// TDATA=64 bits, no TKEEP/TSTRB/TUSER for simplicity
typedef ap_axiu<64, 0, 0, 0> axis_input_t;

// Output stream: 5 fields × 24 bits = 120 bits → round up to 128 bits
// Pack [X(24) | Y(24) | Z(24) | Doppler(24) | SNR(24) | pad(8)] = 128 bits
typedef ap_axiu<128, 0, 0, 0> axis_output_t;

// ---------- Top-Level Function Prototype ----------

void tlv_sph2cart_axi(
    hls::stream<axis_input_t>  &s_axis_input,    // AXI-Stream in: compressed points
    hls::stream<axis_output_t> &m_axis_output,    // AXI-Stream out: [X,Y,Z,Dopp,SNR]
    unit_t  pUnit_elev,                           // AXI-Lite: elevation unit factor
    unit_t  pUnit_az,                             // AXI-Lite: azimuth unit factor
    unit_t  pUnit_dopp,                           // AXI-Lite: doppler unit factor
    unit_t  pUnit_rng,                            // AXI-Lite: range unit factor
    unit_t  pUnit_snr,                            // AXI-Lite: snr unit factor
    int     num_points                            // AXI-Lite: point count this frame
);

#endif // TLV_SPH2CART_AXI_H
