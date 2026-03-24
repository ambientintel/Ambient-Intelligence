/**
 * fall_detect_axi_tb.cpp
 * Testbench for AXI-Lite Fall Detection Kernel
 * Same 5 scenarios as original, simplified interface (no active_tids).
 */

#include <cstdio>
#include <cmath>
#include "fall_detect_axi.h"

void run_frame(int tid, float height, result_t fall_results[MAX_TRACKS]) {
    height_input_t heights[MAX_HEIGHTS];
    heights[0].tid = tid;
    heights[0].height = (height_t)height;
    fall_detect_axi(heights, 1, fall_results);
}

void run_empty_frame(result_t fall_results[MAX_TRACKS]) {
    height_input_t heights[MAX_HEIGHTS];
    fall_detect_axi(heights, 0, fall_results);
}

int main() {
    result_t fall_results[MAX_TRACKS];
    int errors = 0;

    printf("============================================\n");
    printf("  Fall Detection AXI Testbench\n");
    printf("  Target:  Artix-7 xc7a35t @ 100 MHz\n");
    printf("  Tracks:  %d max, History: %d frames\n", MAX_TRACKS, HISTORY_LEN);
    printf("============================================\n\n");

    // Scenario 1: Standing
    printf("--- Scenario 1: Standing person (100 frames @ 1.7m) ---\n");
    for (int f = 0; f < 100; f++) {
        run_frame(0, 1.7f, fall_results);
        if (fall_results[0] > 0) {
            printf("  FAIL: False fall at frame %d\n", f);
            errors++;
        }
    }
    if (errors == 0) printf("  PASS: No false falls detected\n");

    // Scenario 2: Falling
    printf("\n--- Scenario 2: Person falls (1.7m -> 0.3m) ---\n");
    int fall_detected_frame = -1;
    for (int f = 0; f < 20; f++) {
        float h = (f < 10) ? (1.7f - 1.2f * f / 10.0f) : 0.3f;
        run_frame(0, h, fall_results);
        if (fall_results[0] > 0 && fall_detected_frame < 0) {
            fall_detected_frame = f;
            printf("  Fall detected at frame %d (height=%.2f, result=%d)\n",
                   f, h, (int)fall_results[0]);
        }
    }
    if (fall_detected_frame >= 0) printf("  PASS: Fall correctly detected\n");
    else { printf("  FAIL: No fall detected\n"); errors++; }

    // Scenario 3: Cooldown
    printf("\n--- Scenario 3: Cooldown period ---\n");
    bool re_triggered = false;
    result_t prev_result = fall_results[0];
    for (int f = 0; f < 50; f++) {
        run_frame(0, 0.3f, fall_results);
        if (fall_results[0] > prev_result && f > 0) {
            printf("  FAIL: Re-triggered at frame %d\n", f);
            re_triggered = true;
            errors++;
            break;
        }
        prev_result = fall_results[0];
    }
    if (!re_triggered) printf("  PASS: No re-trigger during cooldown\n");

    // Scenario 4: Track disappears
    printf("\n--- Scenario 4: Track disappears and reappears ---\n");
    for (int f = 0; f < 5; f++) run_empty_frame(fall_results);
    bool false_fall = false;
    result_t prev_s4 = 127;
    for (int f = 0; f < 30; f++) {
        run_frame(0, 1.7f, fall_results);
        if (fall_results[0] > prev_s4) {
            printf("  FAIL: New fall triggered at frame %d\n", f);
            false_fall = true;
            errors++;
            break;
        }
        prev_s4 = fall_results[0];
    }
    if (!false_fall) printf("  PASS: No new fall trigger after track reset\n");

    // Scenario 5: Two tracks
    printf("\n--- Scenario 5: Two tracks, only one falls ---\n");
    height_input_t mh[MAX_HEIGHTS];
    for (int f = 0; f < 90; f++) {
        mh[0].tid = 1; mh[0].height = (height_t)1.8f;
        mh[1].tid = 2; mh[1].height = (height_t)1.6f;
        fall_detect_axi(mh, 2, fall_results);
    }
    bool t1_fell = false, t2_false = false;
    for (int f = 0; f < 20; f++) {
        float h1 = (f < 10) ? (1.8f - 1.4f * f / 10.0f) : 0.3f;
        mh[0].tid = 1; mh[0].height = (height_t)h1;
        mh[1].tid = 2; mh[1].height = (height_t)1.6f;
        fall_detect_axi(mh, 2, fall_results);
        if (fall_results[1] > 0 && !t1_fell) {
            printf("  Track 1 fall detected at frame %d (h=%.2f)\n", f, h1);
            t1_fell = true;
        }
        if (fall_results[2] > 0) {
            printf("  FAIL: Track 2 false fall at frame %d\n", f);
            t2_false = true; errors++;
        }
    }
    if (t1_fell) printf("  PASS: Track 1 fall correctly detected\n");
    else { printf("  FAIL: Track 1 fall not detected\n"); errors++; }
    if (!t2_false) printf("  PASS: Track 2 no false fall\n");

    // Summary
    printf("\n============================================\n");
    if (errors == 0) printf("  *** PASS — All AXI scenarios verified ***\n");
    else printf("  *** FAIL — %d errors ***\n", errors);
    printf("============================================\n");
    return (errors == 0) ? 0 : 1;
}
