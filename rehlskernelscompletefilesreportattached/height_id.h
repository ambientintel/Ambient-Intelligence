/**
 * height_id.h
 * Biometric Height Identification HLS Kernel
 *
 * Target:  Artix-7 xc7a35tcpg236-1 (Basys-3)
 * Clock:   15 ns (67 MHz)
 *
 * Assigns persistent resident IDs based on average head height.
 * Solves the problem of stochastic TID assignment from the radar
 * tracker — if the same person leaves and re-enters the scene,
 * they get the same resident ID based on their height biometric.
 *
 * Algorithm:
 *   1. For each active track, compute avg_height = (maxZ + minZ) / 2
 *   2. Compare against stored resident profiles (height ± tolerance)
 *   3. If match found: assign that resident ID, update running average
 *   4. If no match: create new resident profile
 *   5. Age out profiles that haven't been seen for N frames
 *
 * Profile table persists across calls via static BRAM.
 * Called once per radar frame (~18 Hz), after fall_detect.
 */

#ifndef HEIGHT_ID_H
#define HEIGHT_ID_H

#include <ap_fixed.h>
#include <ap_int.h>

// ---------- Design Parameters ----------

#define MAX_TRACKS       30    // Max radar tracks per frame
#define MAX_RESIDENTS    10    // Max known residents in profile table
#define HEIGHT_TOL_CM    15    // Match tolerance: ±15 cm (0.15 m)
#define MIN_FRAMES_STABLE 5   // Frames before a track's height is considered stable
#define PROFILE_TIMEOUT  1800  // Frames before unused profile expires (~100 sec at 18 Hz)
#define ALPHA_SHIFT      4     // Running average: new = old + (sample - old) >> 4 (~6% weight)

// Special values
#define RESIDENT_UNKNOWN 255   // No resident match yet
#define RESIDENT_EMPTY   255   // Empty profile slot

// ---------- Fixed-Point Types ----------

// Heights: person height 0–3 m, sensor offset up to 3 m
typedef ap_fixed<18, 4> height_t;    // ±8.0 m, resolution ~0.06 mm

// Height tolerance for comparison
typedef ap_fixed<18, 4> tol_t;

// Frame counters
typedef ap_uint<16> frame_ctr_t;     // Up to 65535 frames (~1 hour at 18 Hz)

// Resident ID
typedef ap_uint<8> resident_id_t;    // 0–9 = valid, 255 = unknown

// Per-frame confidence counter
typedef ap_uint<8> confidence_t;

// ---------- Input Struct ----------
// Matches parseTrackHeightTLV output: [tid, maxZ, minZ]
typedef struct {
    ap_uint<5>  tid;       // Track ID (0–29)
    height_t    maxZ;      // Top of person (head)
    height_t    minZ;      // Bottom of person (feet)
} height_input_t;

// ---------- Top-Level Function Prototype ----------

void height_id(
    height_input_t   heights[MAX_TRACKS],        // in:  current frame height data
    int              num_heights,                  // in:  number of active heights
    resident_id_t    resident_map[MAX_TRACKS],    // out: resident ID per track (255=unknown)
    int              num_residents_out             // out: current number of known residents
);

#endif // HEIGHT_ID_H