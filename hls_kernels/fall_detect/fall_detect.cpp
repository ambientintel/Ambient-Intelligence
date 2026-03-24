/**
 * fall_detect.cpp
 * Fall Detection HLS Kernel
 *
 * Target:  Artix-7 xc7a35tcpg236-1 (Basys-3)
 * Clock:   10 ns (100 MHz)
 *
 * Called once per radar frame (~18 Hz). Processes up to 30 tracks.
 * State persists across calls via static arrays → BRAM.
 *
 * Architecture: 3 sequential phases per frame call
 *   Phase 1: Decrement fall display counters (all 30 tracks)
 *   Phase 2: Process each active height (compute speed, check fall criteria)
 *   Phase 3: Reset state for tracks that disappeared
 *
 * II=1 fix: Previous height stored in a separate register array
 * so the main BRAM only needs 1 read (oldest) + 1 write (new) per cycle.
 * Dual-port BRAM handles that in 1 cycle → II=1.
 *
 * Python equivalent: new_fall_detection.py FallDetection.step()
 */

#include "fall_detect.h"

void fall_detect(
    height_input_t  heights[MAX_HEIGHTS],
    int             num_heights,
    ap_uint<5>      active_tids[MAX_HEIGHTS],
    int             num_active_tracks,
    result_t        fall_results[MAX_TRACKS]
)
{
#pragma HLS INTERFACE mode=ap_ctrl_hs port=return
#pragma HLS INTERFACE mode=ap_memory port=heights       storage_type=ram_1p
#pragma HLS INTERFACE mode=ap_memory port=active_tids   storage_type=ram_1p
#pragma HLS INTERFACE mode=ap_memory port=fall_results  storage_type=ram_1p

    // ============================================================
    // Persistent state (static → BRAM/registers, survives across calls)
    // ============================================================

    // Circular buffer for height history — BRAM, dual-port
    // Only 2 accesses per cycle now: 1 read (oldest) + 1 write (new)
    static height_t height_buffer[MAX_TRACKS][HISTORY_LEN];
    #pragma HLS BIND_STORAGE variable=height_buffer type=ram_2p impl=bram

    // Previous height per track — REGISTER array (30 elements, tiny)
    // This eliminates the second BRAM read that caused II=2.
    static height_t prev_height[MAX_TRACKS];
    #pragma HLS ARRAY_PARTITION variable=prev_height complete

    // Write pointer per track (circular index into height_buffer)
    static ap_uint<7> write_ptr[MAX_TRACKS];
    #pragma HLS ARRAY_PARTITION variable=write_ptr complete

    // Fall display countdown per track
    static result_t fall_display[MAX_TRACKS];
    #pragma HLS ARRAY_PARTITION variable=fall_display complete

    // Cooldown counter: frames remaining until fall detection re-enabled
    static cooldown_t cooldown_ctr[MAX_TRACKS];
    #pragma HLS ARRAY_PARTITION variable=cooldown_ctr complete

    // Consecutive frames where fall criteria are met
    static counter_t consistent_frames[MAX_TRACKS];
    #pragma HLS ARRAY_PARTITION variable=consistent_frames complete

    // Track active in previous frame (bitmask)
    static ap_uint<MAX_TRACKS> prev_active_mask = 0;

    // Initialization flag
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
    // Phase 1: Decrement fall display and cooldown counters
    // ============================================================
    DECREMENT_DISPLAY:
    for (int t = 0; t < MAX_TRACKS; t++) {
#pragma HLS UNROLL
        if (fall_display[t] > 0) {
            fall_display[t] = fall_display[t] - 1;
        }
        if (cooldown_ctr[t] > 0) {
            cooldown_ctr[t] = cooldown_ctr[t] - 1;
        }
    }

    // ============================================================
    // Phase 2: Process each height in the current frame
    // ============================================================
    ap_uint<MAX_TRACKS> curr_active_mask = 0;

    PROCESS_HEIGHTS:
    for (int i = 0; i < num_heights; i++) {
#pragma HLS LOOP_TRIPCOUNT min=0 max=MAX_HEIGHTS avg=5
#pragma HLS PIPELINE II=1

        // Read input
        ap_uint<5> tid   = heights[i].tid;
        height_t   h_new = heights[i].height;

        // Mark this track as active
        curr_active_mask[tid] = 1;

        // ---- Circular buffer: 1 read + 1 write (fits in dual-port BRAM) ----
        ap_uint<7> wp = write_ptr[tid];

        // Read oldest from BRAM (1 read port)
        ap_uint<7> oldest_idx = (wp < HISTORY_LEN - 1) ? (ap_uint<7>)(wp + 1) : (ap_uint<7>)0;
        height_t h_oldest = height_buffer[tid][oldest_idx];

        // Read previous from REGISTER (no BRAM access needed!)
        height_t h_prev = prev_height[tid];

        // Write new height to BRAM (1 write port)
        height_buffer[tid][wp] = h_new;

        // Update previous height register for next frame
        prev_height[tid] = h_new;

        // Advance write pointer
        write_ptr[tid] = (wp < HISTORY_LEN - 1) ? (ap_uint<7>)(wp + 1) : (ap_uint<7>)0;

        // ---- Speed calculation ----
        speed_t speed = 0;
        if (h_prev != (height_t)HEIGHT_SENTINEL && h_new != (height_t)HEIGHT_SENTINEL) {
            speed = (speed_t)((h_new - h_prev) * (ap_fixed<18, 6>)18.182);
        }

        // ---- Fall detection criteria ----
        if (cooldown_ctr[tid] > 0) {
            continue;
        }

        bool height_criterion     = (h_new < (height_t)((thresh_t)FALL_THRESHOLD_PROP * h_oldest));
        bool min_height_criterion = (h_oldest > (height_t)MIN_HEIGHT_THRESH);
        bool speed_criterion      = (speed < (speed_t)MAX_FALL_SPEED);

        // ---- Evaluate ----
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
    // Phase 3: Reset state for tracks that disappeared
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

    // Update previous-frame mask for next call
    prev_active_mask = curr_active_mask;

    // ============================================================
    // Output: copy fall display results
    // ============================================================
    OUTPUT_RESULTS:
    for (int t = 0; t < MAX_TRACKS; t++) {
#pragma HLS PIPELINE II=1
        fall_results[t] = fall_display[t];
    }
}