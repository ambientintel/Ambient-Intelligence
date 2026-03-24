/**
 * fall_detect_axi.h
 * Fall Detection HLS Kernel — AXI Interface Version
 *
 * Target:  Artix-7 xc7a35tcpg236-1 (Basys-3)
 * Clock:   10 ns (100 MHz)
 *
 * Interfaces:
 *   - AXI-Lite (s_axilite) for everything:
 *     heights input, fall results output, control
 *
 * Fall detection processes ≤30 heights per 55ms frame.
 * Data volume is tiny → AXI-Lite is sufficient, no need for AXI-Stream.
 * The processor writes heights into AXI-Lite registers, triggers the kernel,
 * then reads back the 30 fall result registers.
 */

#ifndef FALL_DETECT_AXI_H
#define FALL_DETECT_AXI_H

#include <ap_fixed.h>
#include <ap_int.h>

// ---------- Design Parameters ----------
#define MAX_TRACKS          30
#define HISTORY_LEN         82
#define MAX_HEIGHTS         MAX_TRACKS

// Fall detection parameters
#define FALL_THRESHOLD_PROP 0.6f
#define MIN_HEIGHT_THRESH   0.3f
#define MAX_FALL_SPEED     -0.6f
#define REQUIRED_CONSISTENT 3
#define DISPLAY_FRAMES      100
#define COOLDOWN_FRAMES     182
#define FRAME_TIME_S        0.055f
#define HEIGHT_SENTINEL    -5.0f

// ---------- Fixed-Point Types ----------
typedef ap_fixed<18, 4>  height_t;
typedef ap_fixed<18, 4>  speed_t;
typedef ap_fixed<18, 2>  thresh_t;
typedef ap_uint<8>       counter_t;
typedef ap_uint<8>       cooldown_t;
typedef ap_uint<7>       result_t;

// ---------- Input Struct ----------
typedef struct {
    ap_uint<5>  tid;
    height_t    height;
} height_input_t;

// ---------- Top-Level Function Prototype ----------

void fall_detect_axi(
    height_input_t  heights[MAX_HEIGHTS],
    int             num_heights,
    result_t        fall_results[MAX_TRACKS]
);

#endif // FALL_DETECT_AXI_H
