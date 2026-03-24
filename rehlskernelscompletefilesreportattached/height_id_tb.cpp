/**
 * height_id_tb.cpp
 * Testbench for Biometric Height Identification Kernel
 *
 * Scenarios:
 *   1. Single person enters — assigned Resident 0
 *   2. Person leaves and re-enters — re-matched to Resident 0
 *   3. Second person with different height — assigned Resident 1
 *   4. Two people present simultaneously — independent IDs
 *   5. Person with very different height — new resident, not confused
 */

#include <cstdio>
#include "height_id.h"

// Helper: run one frame with one track
void run_frame_1(int tid, float maxZ, float minZ,
                 resident_id_t resident_map[MAX_TRACKS], int &num_res) {
    height_input_t heights[MAX_TRACKS];
    heights[0].tid = tid;
    heights[0].maxZ = (height_t)maxZ;
    heights[0].minZ = (height_t)minZ;
    height_id(heights, 1, resident_map, num_res);
}

// Helper: run one frame with two tracks
void run_frame_2(int tid1, float maxZ1, float minZ1,
                 int tid2, float maxZ2, float minZ2,
                 resident_id_t resident_map[MAX_TRACKS], int &num_res) {
    height_input_t heights[MAX_TRACKS];
    heights[0].tid = tid1;
    heights[0].maxZ = (height_t)maxZ1;
    heights[0].minZ = (height_t)minZ1;
    heights[1].tid = tid2;
    heights[1].maxZ = (height_t)maxZ2;
    heights[1].minZ = (height_t)minZ2;
    height_id(heights, 2, resident_map, num_res);
}

// Helper: run empty frame
void run_empty(resident_id_t resident_map[MAX_TRACKS], int &num_res) {
    height_input_t heights[MAX_TRACKS];
    height_id(heights, 0, resident_map, num_res);
}

int main() {
    resident_id_t resident_map[MAX_TRACKS];
    int num_res = 0;
    int errors = 0;

    printf("============================================\n");
    printf("  Biometric Height ID Testbench\n");
    printf("  Max Residents: %d, Tolerance: %d cm\n", MAX_RESIDENTS, HEIGHT_TOL_CM);
    printf("  Stabilization: %d frames\n", MIN_FRAMES_STABLE);
    printf("============================================\n\n");

    // ============================================================
    // Scenario 1: Single person (1.72m tall) enters on TID 3
    // Expected: After stabilization, assigned Resident 0
    // Height: maxZ=1.82, minZ=1.62 → avg=1.72
    // ============================================================
    printf("--- Scenario 1: Single person enters (1.72m) ---\n");

    for (int f = 0; f < 20; f++) {
        // Slight noise in height measurements
        float noise = (f % 3 == 0) ? 0.01f : ((f % 3 == 1) ? -0.01f : 0.0f);
        run_frame_1(3, 1.82f + noise, 1.62f + noise, resident_map, num_res);
    }

    if (resident_map[3] == 0) {
        printf("  PASS: TID 3 assigned Resident %d\n", (int)resident_map[3]);
    } else if (resident_map[3] == RESIDENT_UNKNOWN) {
        printf("  FAIL: TID 3 still unknown after 20 frames\n");
        errors++;
    } else {
        printf("  INFO: TID 3 assigned Resident %d (expected 0)\n", (int)resident_map[3]);
    }

    resident_id_t person1_id = resident_map[3];

    // ============================================================
    // Scenario 2: Person leaves (5 empty frames) then re-enters on TID 7
    // Expected: After stabilization, matched back to same Resident ID
    // Same height (1.72m) but different TID from radar
    // ============================================================
    printf("\n--- Scenario 2: Same person leaves and re-enters on new TID ---\n");

    // Leave
    for (int f = 0; f < 5; f++) {
        run_empty(resident_map, num_res);
    }

    // Re-enter on different TID with same height
    for (int f = 0; f < 20; f++) {
        float noise = (f % 3 == 0) ? 0.01f : ((f % 3 == 1) ? -0.01f : 0.0f);
        run_frame_1(7, 1.83f + noise, 1.61f + noise, resident_map, num_res);
    }

    if (resident_map[7] == person1_id) {
        printf("  PASS: TID 7 re-matched to Resident %d (same person)\n", (int)resident_map[7]);
    } else if (resident_map[7] == RESIDENT_UNKNOWN) {
        printf("  FAIL: TID 7 still unknown after 20 frames\n");
        errors++;
    } else {
        printf("  FAIL: TID 7 assigned Resident %d, expected %d\n",
               (int)resident_map[7], (int)person1_id);
        errors++;
    }

    // ============================================================
    // Scenario 3: Second person (1.45m tall) enters on TID 5
    // Expected: Assigned a DIFFERENT Resident ID (not person1_id)
    // ============================================================
    printf("\n--- Scenario 3: Shorter person enters (1.45m) ---\n");

    for (int f = 0; f < 20; f++) {
        float noise = (f % 3 == 0) ? 0.01f : ((f % 3 == 1) ? -0.01f : 0.0f);
        // Also keep person 1 present
        run_frame_2(7, 1.82f, 1.62f,
                    5, 1.55f + noise, 1.35f + noise,
                    resident_map, num_res);
    }

    if (resident_map[5] != RESIDENT_UNKNOWN && resident_map[5] != person1_id) {
        printf("  PASS: TID 5 assigned Resident %d (different from person 1)\n",
               (int)resident_map[5]);
    } else if (resident_map[5] == person1_id) {
        printf("  FAIL: TID 5 incorrectly matched to person 1's ID\n");
        errors++;
    } else {
        printf("  FAIL: TID 5 still unknown after 20 frames\n");
        errors++;
    }

    resident_id_t person2_id = resident_map[5];

    // ============================================================
    // Scenario 4: Both people present — verify independent IDs maintained
    // ============================================================
    printf("\n--- Scenario 4: Both people present simultaneously ---\n");

    for (int f = 0; f < 10; f++) {
        run_frame_2(7, 1.82f, 1.62f,
                    5, 1.55f, 1.35f,
                    resident_map, num_res);
    }

    bool s4_pass = true;
    if (resident_map[7] != person1_id) {
        printf("  FAIL: Person 1 (TID 7) changed ID from %d to %d\n",
               (int)person1_id, (int)resident_map[7]);
        s4_pass = false;
        errors++;
    }
    if (resident_map[5] != person2_id) {
        printf("  FAIL: Person 2 (TID 5) changed ID from %d to %d\n",
               (int)person2_id, (int)resident_map[5]);
        s4_pass = false;
        errors++;
    }
    if (s4_pass) printf("  PASS: Both residents maintain stable IDs\n");

    // ============================================================
    // Scenario 5: Third person (2.01m, very tall) enters
    // Expected: Gets a new unique ID, not confused with existing
    // ============================================================
    printf("\n--- Scenario 5: Third person enters (2.01m, tall) ---\n");

    // Clear previous tracks
    for (int f = 0; f < 5; f++) run_empty(resident_map, num_res);

    for (int f = 0; f < 20; f++) {
        float noise = (f % 3 == 0) ? 0.01f : ((f % 3 == 1) ? -0.01f : 0.0f);
        run_frame_1(10, 2.11f + noise, 1.91f + noise, resident_map, num_res);
    }

    if (resident_map[10] != RESIDENT_UNKNOWN &&
        resident_map[10] != person1_id &&
        resident_map[10] != person2_id) {
        printf("  PASS: TID 10 assigned Resident %d (unique, new person)\n",
               (int)resident_map[10]);
    } else if (resident_map[10] == person1_id || resident_map[10] == person2_id) {
        printf("  FAIL: Tall person incorrectly matched to existing resident\n");
        errors++;
    } else {
        printf("  FAIL: TID 10 still unknown after 20 frames\n");
        errors++;
    }

    // ============================================================
    // Summary
    // ============================================================
    printf("\n============================================\n");
    printf("  Known residents: %d\n", num_res);
    if (errors == 0) {
        printf("  *** PASS \u2014 All biometric scenarios verified ***\n");
    } else {
        printf("  *** FAIL \u2014 %d errors detected ***\n", errors);
    }
    printf("============================================\n");

    return (errors == 0) ? 0 : 1;
}