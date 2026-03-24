/**
 * tlv_sph2cart_axi.cpp
 * Fused TLV Decompression + Spherical-to-Cartesian — AXI Interface Version
 *
 * Target:  Artix-7 xc7a35tcpg236-1 (Basys-3)
 * Clock:   10 ns (100 MHz)
 *
 * Same pipeline as Phase 3, but with AXI interfaces for Vivado integration.
 * Data flows through AXI-Stream (no BRAM arrays), configuration via AXI-Lite.
 */

#include "tlv_sph2cart_axi.h"

void tlv_sph2cart_axi(
    hls::stream<axis_input_t>  &s_axis_input,
    hls::stream<axis_output_t> &m_axis_output,
    unit_t  pUnit_elev,
    unit_t  pUnit_az,
    unit_t  pUnit_dopp,
    unit_t  pUnit_rng,
    unit_t  pUnit_snr,
    int     num_points
)
{
    // ---- AXI Interface Pragmas ----
    // Streams: AXI-Stream (axis)
#pragma HLS INTERFACE mode=axis port=s_axis_input
#pragma HLS INTERFACE mode=axis port=m_axis_output

    // Scalars: AXI-Lite grouped into one control bus
#pragma HLS INTERFACE mode=s_axilite port=pUnit_elev  bundle=control
#pragma HLS INTERFACE mode=s_axilite port=pUnit_az    bundle=control
#pragma HLS INTERFACE mode=s_axilite port=pUnit_dopp  bundle=control
#pragma HLS INTERFACE mode=s_axilite port=pUnit_rng   bundle=control
#pragma HLS INTERFACE mode=s_axilite port=pUnit_snr   bundle=control
#pragma HLS INTERFACE mode=s_axilite port=num_points  bundle=control
#pragma HLS INTERFACE mode=s_axilite port=return      bundle=control

    // ---- Main Fused Pipeline ----
    DECOMPRESS_CONVERT_LOOP:
    for (int i = 0; i < num_points; i++) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=MAX_NUM_POINTS avg=20
#pragma HLS PIPELINE II=1

        // ============================================================
        // Stage 1: Read from AXI-Stream and extract fields
        // ============================================================
        axis_input_t in_word = s_axis_input.read();
        ap_uint<64> word = in_word.data;

        // Byte layout (little-endian from radar):
        //   [7:0]   = elevation  (int8,  signed)
        //   [15:8]  = azimuth    (int8,  signed)
        //   [31:16] = doppler    (int16, signed)
        //   [47:32] = range      (uint16, unsigned)
        //   [63:48] = snr        (uint16, unsigned)
        ap_int<8>   raw_elev    = (ap_int<8>)  word( 7,  0);
        ap_int<8>   raw_az      = (ap_int<8>)  word(15,  8);
        ap_int<16>  raw_doppler = (ap_int<16>) word(31, 16);
        ap_uint<16> raw_range   = (ap_uint<16>)word(47, 32);
        ap_uint<16> raw_snr     = (ap_uint<16>)word(63, 48);

        // ============================================================
        // Stage 2: Decompress
        // ============================================================
        range_t   range     = (range_t)  (raw_range   * pUnit_rng);
        angle_t   azimuth   = (angle_t)  (raw_az      * pUnit_az);
        angle_t   elevation = (angle_t)  (raw_elev    * pUnit_elev);
        doppler_t doppler   = (doppler_t)(raw_doppler * pUnit_dopp);
        snr_t     snr_val   = (snr_t)    (raw_snr     * pUnit_snr);

        // ============================================================
        // Stage 3: CORDIC trig
        // ============================================================
        trig_t sin_az  = hls::sin(azimuth);
        trig_t cos_az  = hls::cos(azimuth);
        trig_t sin_el  = hls::sin(elevation);
        trig_t cos_el  = hls::cos(elevation);

        // ============================================================
        // Stage 4: Cartesian conversion
        // ============================================================
        coord_t x = (coord_t)(range * (coord_t)(sin_az * cos_el));
        coord_t y = (coord_t)(range * (coord_t)(cos_az * cos_el));
        coord_t z = (coord_t)(range * sin_el);

        // ============================================================
        // Stage 5: Pack output and write to AXI-Stream
        // ============================================================
        // Pack 5 fields into 128-bit output word:
        //   [23:0]   = X    (coord_t, 20 bits, zero-padded to 24)
        //   [47:24]  = Y
        //   [71:48]  = Z
        //   [95:72]  = Doppler (out_t, 24 bits)
        //   [119:96] = SNR     (out_t, 24 bits)
        //   [127:120]= padding

        out_t out_x = (out_t) x;
        out_t out_y = (out_t) y;
        out_t out_z = (out_t) z;
        out_t out_d = (out_t) doppler;
        out_t out_s = (out_t) snr_val;

        ap_uint<128> out_data = 0;
        out_data( 23,   0) = out_x.range();
        out_data( 47,  24) = out_y.range();
        out_data( 71,  48) = out_z.range();
        out_data( 95,  72) = out_d.range();
        out_data(119,  96) = out_s.range();

        axis_output_t out_word;
        out_word.data = out_data;
        out_word.last = (i == num_points - 1) ? 1 : 0;  // TLAST on final point
        out_word.keep = -1;  // All bytes valid

        m_axis_output.write(out_word);
    }
}
