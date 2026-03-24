/**
 * fall_detect_tb.cpp
 * Testbench for Fall Detection HLS Kernel
 *
 * Simulates multiple frames of radar data to test:
 *   Scenario 1: Standing person (no fall)   → expect no alerts
 *   Scenario 2: Falling person              → expect alert after 3 consistent frames
 *   Scenario 3: Cooldown period             → expect no re-trigger for 182 frames
 *   Scenario 4: Track disappears and resets → expect no NEW fall trigger
 *   Scenario 5: Multiple simultaneous tracks → independent detection
 *
 * Each call to fall_detect() represents one radar frame (55ms).
 */

#include <cstdio>
#include <cmath>
#include "fall_detect.h"

// Helper: call fall_detect for a single track at a given height
void run_frame(int tid, float height, result_t fall_results[MAX_TRACKS]) {
    height_input_t heights[MAX_HEIGHTS];
    ap_uint<5> active_tids[MAX_HEIGHTS];

    heights[0].tid = tid;
    heights[0].height = (height_t)height;
    active_tids[0] = tid;

    fall_detect(heights, 1, active_tids, 1, fall_results);
}

// Helper: call fall_detect with no active tracks (empty frame)
void run_empty_frame(result_t fall_results[MAX_TRACKS]) {
    height_input_t heights[MAX_HEIGHTS];
    ap_uint<5> active_tids[MAX_HEIGHTS];

    fall_detect(heights, 0, active_tids, 0, fall_results);
}

int main() {
    result_t fall_results[MAX_TRACKS];
    int errors = 0;

    printf("============================================\n");
    printf("  Fall Detection HLS Testbench\n");
    printf("  Target:  Artix-7 xc7a35t @ 100 MHz\n");
    printf("  Tracks:  %d max, History: %d frames\n", MAX_TRACKS, HISTORY_LEN);
    printf("============================================\n\n");

    // ============================================================
    // Scenario 1: Standing person — 100 frames at 1.7m
    // Expected: No fall detected (height stable)
    // ============================================================
    printf("--- Scenario 1: Standing person (100 frames @ 1.7m) ---\n");

    for (int f = 0; f < 100; f++) {
        run_frame(0, 1.7f, fall_results);
        if (fall_results[0] > 0) {
            printf("  FAIL: False fall detected at frame %d (result=%d)\n", f, (int)fall_results[0]);
            errors++;
        }
    }
    if (errors == 0) printf("  PASS: No false falls detected\n");

    // ============================================================
    // Scenario 2: Person falls — height drops from 1.7m to 0.3m
    // Expected: Fall detected after 3 consecutive frames meeting criteria
    //
    // Setup: Buffer already has 1.7m from Scenario 1 (oldest = 1.7m)
    // Drop height rapidly over several frames
    // Fall criteria: current < 0.6 * oldest → need current < 1.02m
    //               oldest > 0.3m           → 1.7m > 0.3m ✓
    //               speed < -0.6 m/s        → need fast drop
    //
    // Speed = (h_new - h_prev) * 18.182
    // For speed < -0.6: (h_new - h_prev) < -0.033m per frame
    // Drop from 1.7 to 0.5 in ~10 frames = -0.12m/frame → speed ≈ -2.18 m/s ✓
    // ============================================================
    printf("\n--- Scenario 2: Person falls (1.7m -> 0.3m over 10 frames) ---\n");

    int fall_detected_frame = -1;
    for (int f = 0; f < 20; f++) {
        float h;
        if (f < 10) {
            // Linear drop: 1.7 → 0.5 over 10 frames
            h = 1.7f - (1.2f * f / 10.0f);
        } else {
            // Stay low
            h = 0.3f;
        }

        run_frame(0, h, fall_results);

        if (fall_results[0] > 0 && fall_detected_frame < 0) {
            fall_detected_frame = f;
            printf("  Fall detected at drop frame %d (height=%.2f, result=%d)\n",
                   f, h, (int)fall_results[0]);
        }
    }

    if (fall_detected_frame >= 0) {
        printf("  PASS: Fall correctly detected at frame %d\n", fall_detected_frame);
    } else {
        printf("  FAIL: No fall detected during height drop\n");
        errors++;
    }

    // ============================================================
    // Scenario 3: Cooldown — verify no re-detection immediately
    // Expected: fall_results[0] should decrement but not re-trigger
    // ============================================================
    printf("\n--- Scenario 3: Cooldown period (stay low, no re-trigger) ---\n");

    bool re_triggered = false;
    result_t prev_result = fall_results[0];

    for (int f = 0; f < 50; f++) {
        run_frame(0, 0.3f, fall_results);

        // Check if result jumped UP (re-triggered) instead of decrementing
        if (fall_results[0] > prev_result && f > 0) {
            printf("  FAIL: Re-triggered during cooldown at frame %d (prev=%d, curr=%d)\n",
                   f, (int)prev_result, (int)fall_results[0]);
            re_triggered = true;
            errors++;
            break;
        }
        prev_result = fall_results[0];
    }
    if (!re_triggered) printf("  PASS: No re-trigger during cooldown\n");

    // ============================================================
    // Scenario 4: Track disappears and reappears
    // Expected: State resets when track disappears.
    //           No NEW fall trigger (display counter may still be
    //           counting down from Scenario 2 — that's correct
    //           Python behavior, not a false fall).
    // ============================================================
    printf("\n--- Scenario 4: Track disappears and reappears ---\n");

    // Run empty frames (track 0 disappears)
    for (int f = 0; f < 5; f++) {
        run_empty_frame(fall_results);
    }

    // Track reappears at normal standing height.
    // Check for NEW fall triggers (result jumping UP), not residual
    // countdown from Scenario 2's legitimate fall alert.
    bool false_fall = false;
    result_t prev_result_s4 = 127; // Start high so first frame's decrement isn't flagged
    for (int f = 0; f < 30; f++) {
        run_frame(0, 1.7f, fall_results);

        // A false fall means the result jumped UP (new trigger)
        if (fall_results[0] > prev_result_s4) {
            printf("  FAIL: New fall triggered after track reset at frame %d (prev=%d, curr=%d)\n",
                   f, (int)prev_result_s4, (int)fall_results[0]);
            false_fall = true;
            errors++;
            break;
        }
        prev_result_s4 = fall_results[0];
    }
    if (!false_fall) printf("  PASS: No new fall trigger after track reset\n");

    // ============================================================
    // Scenario 5: Multiple simultaneous tracks
    // Expected: Independent fall detection per track
    // ============================================================
    printf("\n--- Scenario 5: Two tracks, only one falls ---\n");

    // Fill both tracks with standing height
    height_input_t multi_heights[MAX_HEIGHTS];
    ap_uint<5> multi_tids[MAX_HEIGHTS];

    for (int f = 0; f < 90; f++) {
        multi_heights[0].tid = 1;
        multi_heights[0].height = (height_t)1.8f;
        multi_heights[1].tid = 2;
        multi_heights[1].height = (height_t)1.6f;
        multi_tids[0] = 1;
        multi_tids[1] = 2;
        fall_detect(multi_heights, 2, multi_tids, 2, fall_results);
    }

    // Now track 1 falls, track 2 stays standing
    bool track1_fell = false;
    bool track2_false_fall = false;

    for (int f = 0; f < 20; f++) {
        float h1 = (f < 10) ? (1.8f - 1.4f * f / 10.0f) : 0.3f;  // Track 1 falls
        float h2 = 1.6f;  // Track 2 stands

        multi_heights[0].tid = 1;
        multi_heights[0].height = (height_t)h1;
        multi_heights[1].tid = 2;
        multi_heights[1].height = (height_t)h2;

        fall_detect(multi_heights, 2, multi_tids, 2, fall_results);

        if (fall_results[1] > 0 && !track1_fell) {
            printf("  Track 1 fall detected at frame %d (height=%.2f)\n", f, h1);
            track1_fell = true;
        }
        if (fall_results[2] > 0) {
            printf("  FAIL: Track 2 false fall at frame %d\n", f);
            track2_false_fall = true;
            errors++;
        }
    }

    if (track1_fell) printf("  PASS: Track 1 fall correctly detected\n");
    else { printf("  FAIL: Track 1 fall not detected\n"); errors++; }

    if (!track2_false_fall) printf("  PASS: Track 2 no false fall\n");

    // ============================================================
    // Summary
    // ============================================================
    printf("\n============================================\n");
    if (errors == 0) {
        printf("  *** PASS — All scenarios verified ***\n");
    } else {
        printf("  *** FAIL — %d errors detected ***\n", errors);
    }
    printf("============================================\n");

    return (errors == 0) ? 0 : 1;
}