/**
 * fall_detect_axi.cpp
 * Fall Detection HLS Kernel — AXI Interface Version
 *
 * Same logic as fall_detect.cpp (II=1 version with prev_height registers),
 * but with AXI-Lite interfaces for Vivado block design integration.
 *
 * Simplified interface: removed active_tids (redundant — derived from heights).
 * The processor writes height data into AXI-Lite registers, starts the kernel,
 * and reads back fall_results from AXI-Lite registers.
 */

#include "fall_detect_axi.h"

void fall_detect_axi(
    height_input_t  heights[MAX_HEIGHTS],
    int             num_heights,
    result_t        fall_results[MAX_TRACKS]
)
{
    // ---- AXI-Lite Interface Pragmas ----
    // All ports on one AXI-Lite bus for simple processor access
#pragma HLS INTERFACE mode=s_axilite port=heights      bundle=control
#pragma HLS INTERFACE mode=s_axilite port=num_heights  bundle=control
#pragma HLS INTERFACE mode=s_axilite port=fall_results bundle=control
#pragma HLS INTERFACE mode=s_axilite port=return       bundle=control

    // ============================================================
    // Persistent state (static → BRAM/registers)
    // ============================================================
    static height_t height_buffer[MAX_TRACKS][HISTORY_LEN];
    #pragma HLS BIND_STORAGE variable=height_buffer type=ram_2p impl=bram

    static height_t prev_height[MAX_TRACKS];
    #pragma HLS ARRAY_PARTITION variable=prev_height complete

    static ap_uint<7> write_ptr[MAX_TRACKS];
    #pragma HLS ARRAY_PARTITION variable=write_ptr complete

    static result_t fall_display[MAX_TRACKS];
    #pragma HLS ARRAY_PARTITION variable=fall_display complete

    static cooldown_t cooldown_ctr[MAX_TRACKS];
    #pragma HLS ARRAY_PARTITION variable=cooldown_ctr complete

    static counter_t consistent_frames[MAX_TRACKS];
    #pragma HLS ARRAY_PARTITION variable=consistent_frames complete

    static ap_uint<MAX_TRACKS> prev_active_mask = 0;
    static bool initialized = false;

    // ---- First-call initialization ----
    if (!initialized) {
        INIT_TRACKS:
        for (int t = 0; t < MAX_TRACKS; t++) {
            write_ptr[t] = 0;
            fall_display[t] = 0;
            cooldown_ctr[t] = 0;
            consistent_frames[t] = 0;
            prev_height[t] = (height_t)HEIGHT_SENTINEL;

            INIT_HISTORY:
            for (int h = 0; h < HISTORY_LEN; h++) {
#pragma HLS PIPELINE II=1
                height_buffer[t][h] = (height_t)HEIGHT_SENTINEL;
            }
        }
        initialized = true;
    }

    // ============================================================
    // Phase 1: Decrement display and cooldown counters
    // ============================================================
    DECREMENT_DISPLAY:
    for (int t = 0; t < MAX_TRACKS; t++) {
#pragma HLS UNROLL
        if (fall_display[t] > 0)
            fall_display[t] = fall_display[t] - 1;
        if (cooldown_ctr[t] > 0)
            cooldown_ctr[t] = cooldown_ctr[t] - 1;
    }

    // ============================================================
    // Phase 2: Process each height
    // ============================================================
    ap_uint<MAX_TRACKS> curr_active_mask = 0;

    PROCESS_HEIGHTS:
    for (int i = 0; i < num_heights; i++) {
#pragma HLS LOOP_TRIPCOUNT min=0 max=MAX_HEIGHTS avg=5
#pragma HLS PIPELINE II=1

        ap_uint<5> tid   = heights[i].tid;
        height_t   h_new = heights[i].height;

        curr_active_mask[tid] = 1;

        // Circular buffer: 1 BRAM read (oldest) + 1 BRAM write (new)
        ap_uint<7> wp = write_ptr[tid];
        ap_uint<7> oldest_idx = (wp < HISTORY_LEN - 1) ? (ap_uint<7>)(wp + 1) : (ap_uint<7>)0;
        height_t h_oldest = height_buffer[tid][oldest_idx];

        // Previous from register (no BRAM access)
        height_t h_prev = prev_height[tid];

        height_buffer[tid][wp] = h_new;
        prev_height[tid] = h_new;
        write_ptr[tid] = (wp < HISTORY_LEN - 1) ? (ap_uint<7>)(wp + 1) : (ap_uint<7>)0;

        // Speed calculation
        speed_t speed = 0;
        if (h_prev != (height_t)HEIGHT_SENTINEL && h_new != (height_t)HEIGHT_SENTINEL) {
            speed = (speed_t)((h_new - h_prev) * (ap_fixed<18, 6>)18.182);
        }

        // Fall criteria
        if (cooldown_ctr[tid] > 0) continue;

        bool height_criterion     = (h_new < (height_t)((thresh_t)FALL_THRESHOLD_PROP * h_oldest));
        bool min_height_criterion = (h_oldest > (height_t)MIN_HEIGHT_THRESH);
        bool speed_criterion      = (speed < (speed_t)MAX_FALL_SPEED);

        if (height_criterion && min_height_criterion && speed_criterion) {
            consistent_frames[tid] = consistent_frames[tid] + 1;
            if (consistent_frames[tid] >= REQUIRED_CONSISTENT) {
                fall_display[tid] = DISPLAY_FRAMES;
                cooldown_ctr[tid] = COOLDOWN_FRAMES;
                consistent_frames[tid] = 0;
            }
        } else {
            consistent_frames[tid] = 0;
        }
    }

    // ============================================================
    // Phase 3: Reset disappeared tracks
    // ============================================================
    ap_uint<MAX_TRACKS> tracks_to_reset = prev_active_mask & ~curr_active_mask;

    RESET_TRACKS:
    for (int t = 0; t < MAX_TRACKS; t++) {
#pragma HLS LOOP_TRIPCOUNT min=0 max=MAX_TRACKS avg=2
        if (tracks_to_reset[t] == 1) {
            RESET_BUFFER:
            for (int h = 0; h < HISTORY_LEN; h++) {
#pragma HLS PIPELINE II=1
                height_buffer[t][h] = (height_t)HEIGHT_SENTINEL;
            }
            write_ptr[t] = 0;
            consistent_frames[t] = 0;
            prev_height[t] = (height_t)HEIGHT_SENTINEL;
        }
    }

    prev_active_mask = curr_active_mask;

    // ============================================================
    // Output
    // ============================================================
    OUTPUT_RESULTS:
    for (int t = 0; t < MAX_TRACKS; t++) {
#pragma HLS PIPELINE II=1
        fall_results[t] = fall_display[t];
    }
}
