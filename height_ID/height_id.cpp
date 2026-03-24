/**
 * height_id.cpp
 * Biometric Height Identification HLS Kernel — Restructured
 *
 * Target:  Artix-7 xc7a35tcpg236-1 (Basys-3)
 * Clock:   15 ns (67 MHz)
 *
 * RESTRUCTURED to avoid combinational explosion in the pipelined loop.
 * Original version tried to do height stabilization + profile matching +
 * profile creation all inside one PIPELINE'd loop, which created 65 ns
 * mux chains from variable-indexed profile array accesses.
 *
 * New architecture — 4 simple sequential phases:
 *   Phase 1: Age out stale profiles (unrolled, 1 cycle)
 *   Phase 2: Update per-track height accumulators (pipelined II=1, simple)
 *   Phase 3: Match stabilized tracks to profiles (sequential, per-track)
 *   Phase 4: Output results (pipelined II=1)
 *
 * Phase 3 is NOT pipelined — it runs sequentially for each active track.
 * At most 30 tracks × ~10 cycles per match = 300 cycles = 4.5 µs.
 * The radar frame period is 55,000 µs. This is fine.
 */

#include "height_id.h"

void height_id(
    height_input_t   heights[MAX_TRACKS],
    int              num_heights,
    resident_id_t    resident_map[MAX_TRACKS],
    int              num_residents_out
)
{
#pragma HLS INTERFACE mode=s_axilite port=heights          bundle=control
#pragma HLS INTERFACE mode=s_axilite port=num_heights      bundle=control
#pragma HLS INTERFACE mode=s_axilite port=resident_map     bundle=control
#pragma HLS INTERFACE mode=s_axilite port=num_residents_out bundle=control
#pragma HLS INTERFACE mode=s_axilite port=return           bundle=control

    // ============================================================
    // Persistent State
    // ============================================================

    // Resident profile table (10 slots, fully in registers)
    static height_t    profile_height[MAX_RESIDENTS];
    static frame_ctr_t profile_last_seen[MAX_RESIDENTS];
    static bool        profile_valid[MAX_RESIDENTS];
#pragma HLS ARRAY_PARTITION variable=profile_height complete
#pragma HLS ARRAY_PARTITION variable=profile_last_seen complete
#pragma HLS ARRAY_PARTITION variable=profile_valid complete

    // Per-track state (30 tracks, fully in registers)
    static height_t      track_height_accum[MAX_TRACKS];
    static confidence_t  track_frame_count[MAX_TRACKS];
    static resident_id_t track_resident[MAX_TRACKS];
#pragma HLS ARRAY_PARTITION variable=track_height_accum complete
#pragma HLS ARRAY_PARTITION variable=track_frame_count complete
#pragma HLS ARRAY_PARTITION variable=track_resident complete

    static frame_ctr_t global_frame = 0;
    static ap_uint<MAX_TRACKS> prev_active_mask = 0;
    static bool initialized = false;

    if (!initialized) {
        for (int r = 0; r < MAX_RESIDENTS; r++) {
#pragma HLS UNROLL
            profile_height[r] = 0;
            profile_last_seen[r] = 0;
            profile_valid[r] = false;
        }
        for (int t = 0; t < MAX_TRACKS; t++) {
#pragma HLS UNROLL
            track_height_accum[t] = 0;
            track_frame_count[t] = 0;
            track_resident[t] = RESIDENT_UNKNOWN;
        }
        initialized = true;
    }

    global_frame++;

    // ============================================================
    // Phase 1: Age out stale profiles (single cycle, unrolled)
    // ============================================================
    int num_residents = 0;

    AGE_PROFILES:
    for (int r = 0; r < MAX_RESIDENTS; r++) {
#pragma HLS UNROLL
        if (profile_valid[r]) {
            frame_ctr_t age = global_frame - profile_last_seen[r];
            if (age > PROFILE_TIMEOUT) {
                profile_valid[r] = false;
                profile_height[r] = 0;
            } else {
                num_residents++;
            }
        }
    }

    // ============================================================
    // Phase 2: Update height accumulators (pipelined, simple math only)
    // Store results in local arrays for Phase 3
    // ============================================================
    ap_uint<MAX_TRACKS> curr_active_mask = 0;

    // Local arrays to pass data from Phase 2 to Phase 3
    ap_uint<5>  active_tid_list[MAX_TRACKS];
    height_t    active_avg_height[MAX_TRACKS];
    bool        active_stable[MAX_TRACKS];
    int num_active = 0;

    UPDATE_HEIGHTS:
    for (int i = 0; i < num_heights; i++) {
#pragma HLS LOOP_TRIPCOUNT min=0 max=MAX_TRACKS avg=5
#pragma HLS PIPELINE II=1

        ap_uint<5> tid = heights[i].tid;
        height_t maxZ = heights[i].maxZ;
        height_t minZ = heights[i].minZ;

        curr_active_mask[tid] = 1;

        // Average height
        height_t avg_h = (height_t)((maxZ + minZ) >> 1);

        // Update running average
        if (track_frame_count[tid] == 0) {
            track_height_accum[tid] = avg_h;
            track_frame_count[tid] = 1;
        } else {
            height_t diff = avg_h - track_height_accum[tid];
            track_height_accum[tid] = track_height_accum[tid] + (height_t)(diff >> ALPHA_SHIFT);
            if (track_frame_count[tid] < 255) {
                track_frame_count[tid] = track_frame_count[tid] + 1;
            }
        }

        // Store for Phase 3
        active_tid_list[i] = tid;
        active_avg_height[i] = track_height_accum[tid];
        active_stable[i] = (track_frame_count[tid] >= MIN_FRAMES_STABLE);
    }
    num_active = num_heights;

    // ============================================================
    // Phase 3: Profile matching (sequential, NOT pipelined)
    // This runs once per active track — at most 30 iterations.
    // Each iteration does a linear scan of 10 profiles.
    // Total: ~300 cycles = 4.5 µs. Negligible vs 55 ms frame.
    // ============================================================
    MATCH_TRACKS:
    for (int i = 0; i < num_active; i++) {
#pragma HLS LOOP_TRIPCOUNT min=0 max=MAX_TRACKS avg=5
        // NO PIPELINE pragma here — let the tool schedule freely

        ap_uint<5> tid = active_tid_list[i];

        // Skip if not stable yet
        if (!active_stable[i]) {
            track_resident[tid] = RESIDENT_UNKNOWN;
            continue;
        }

        // Skip if already assigned
        if (track_resident[tid] != RESIDENT_UNKNOWN) {
            // Just update the existing profile
            int rid = (int)track_resident[tid];
            if (rid < MAX_RESIDENTS && profile_valid[rid]) {
                height_t pdiff = active_avg_height[i] - profile_height[rid];
                profile_height[rid] = profile_height[rid] + (height_t)(pdiff >> ALPHA_SHIFT);
                profile_last_seen[rid] = global_frame;
            }
            continue;
        }

        // Find best matching profile
        height_t best_dist = (height_t)99.0;
        int best_match = -1;
        const height_t tolerance = (height_t)0.15;

        SCAN_PROFILES:
        for (int r = 0; r < MAX_RESIDENTS; r++) {
#pragma HLS UNROLL
            if (profile_valid[r]) {
                height_t diff_p = active_avg_height[i] - profile_height[r];
                height_t abs_diff = (diff_p < (height_t)0) ? (height_t)(-diff_p) : diff_p;

                if (abs_diff < tolerance && abs_diff < best_dist) {
                    best_dist = abs_diff;
                    best_match = r;
                }
            }
        }

        if (best_match >= 0) {
            // Matched existing resident
            track_resident[tid] = (resident_id_t)best_match;
            profile_last_seen[best_match] = global_frame;
            height_t pdiff = active_avg_height[i] - profile_height[best_match];
            profile_height[best_match] = profile_height[best_match] + (height_t)(pdiff >> ALPHA_SHIFT);
        } else {
            // Create new profile
            for (int r = 0; r < MAX_RESIDENTS; r++) {
                if (!profile_valid[r]) {
                    profile_valid[r] = true;
                    profile_height[r] = active_avg_height[i];
                    profile_last_seen[r] = global_frame;
                    track_resident[tid] = (resident_id_t)r;
                    num_residents++;
                    break;
                }
            }
        }
    }

    // ============================================================
    // Phase 4: Reset disappeared tracks (unrolled, single cycle)
    // ============================================================
    ap_uint<MAX_TRACKS> tracks_to_reset = prev_active_mask & ~curr_active_mask;

    RESET_TRACKS:
    for (int t = 0; t < MAX_TRACKS; t++) {
#pragma HLS UNROLL
        if (tracks_to_reset[t] == 1) {
            track_height_accum[t] = 0;
            track_frame_count[t] = 0;
            track_resident[t] = RESIDENT_UNKNOWN;
        }
    }

    prev_active_mask = curr_active_mask;

    // ============================================================
    // Phase 5: Output (pipelined)
    // ============================================================
    OUTPUT_MAP:
    for (int t = 0; t < MAX_TRACKS; t++) {
#pragma HLS PIPELINE II=1
        resident_map[t] = track_resident[t];
    }

    num_residents_out = num_residents;
}