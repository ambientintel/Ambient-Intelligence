/**
 * fall_detect.h
 * Fall Detection HLS Kernel
 *
 * Target:  Artix-7 xc7a35tcpg236-1 (Basys-3)
 * Clock:   10 ns (100 MHz)
 *
 * Port of new_fall_detection.py FallDetection.step()
 *
 * ──────────────────────────────────────────────────────────
 * Key HLS design decisions vs Python original:
 *
 * 1. TID matching: Python uses nested O(n²) loop to match
 *    heights to tracks by TID. Hardware uses TID as direct
 *    BRAM address → O(1) lookup.
 *
 * 2. Deques → circular buffers: Python's deque(maxlen=82)
 *    becomes a BRAM-backed circular buffer with a write pointer.
 *    Only 3 values accessed per frame: newest, previous, oldest.
 *
 * 3. time.time() → frame counter: Cooldown of 10 seconds =
 *    182 frames at 55ms/frame. Tracked with a decrement counter.
 *
 * 4. Speed buffer eliminated: Speed only depends on the two
 *    most recent heights. No history needed.
 *
 * 5. State persists across calls via 'static' arrays → BRAM.
 * ──────────────────────────────────────────────────────────
 *
 * Memory layout (BRAM usage):
 *   height_buffer: 30 tracks × 82 entries × 18 bits ≈ 2.5 BRAM18K
 *   Per-track state: 30 tracks × ~64 bits ≈ negligible
 *   Total: ~3 BRAM18K of 50 available (6%)
 * ──────────────────────────────────────────────────────────
 */

#ifndef FALL_DETECT_H
#define FALL_DETECT_H

#include <ap_fixed.h>
#include <ap_int.h>

// ---------- Design Parameters ----------

// Max tracks the radar tracker can report (from trackingCfg)
#define MAX_TRACKS          30

// Height history length: round(1.5 seconds * 55ms frame time) = 82
#define HISTORY_LEN         82

// Max heights per frame (same as max tracks)
#define MAX_HEIGHTS         MAX_TRACKS

// Fall detection parameters (from Python defaults)
#define FALL_THRESHOLD_PROP 0.6f    // Current height < 60% of oldest → falling
#define MIN_HEIGHT_THRESH   0.3f    // Person must be at least 0.3m initially
#define MAX_FALL_SPEED     -0.6f    // Speed threshold (m/s, negative = downward)
#define REQUIRED_CONSISTENT 3       // Consecutive frames to confirm fall
#define DISPLAY_FRAMES      100     // Frames to display fall alert
#define COOLDOWN_FRAMES     182     // 10 seconds / 55ms ≈ 182 frames
#define FRAME_TIME_S        0.055f  // 55ms per frame

// Sentinel value for empty/invalid height
#define HEIGHT_SENTINEL    -5.0f

// ---------- Fixed-Point Types ----------

// Heights: person height 0–3m, sensor height offset up to 3m
// 4 integer bits (±8.0), 14 fractional bits
typedef ap_fixed<18, 4> height_t;

// Speed: height change per second, typically ±5 m/s max
// 4 integer bits (±8.0), 14 fractional bits
typedef ap_fixed<18, 4> speed_t;

// Threshold/proportion: 0.0 to 1.0
// 2 integer bits, 16 fractional bits
typedef ap_fixed<18, 2> thresh_t;

// Counters: small integers (0–200 range)
typedef ap_uint<8> counter_t;

// Frame counter: up to 182 for cooldown
typedef ap_uint<8> cooldown_t;

// Fall result: 0 or display count (0–100)
typedef ap_uint<7> result_t;

// ---------- Input Struct ----------
// Matches heightData from parseTrackHeightTLV: [tid, maxZ, minZ]
// We only use tid and maxZ (height)

typedef struct {
    ap_uint<5>  tid;     // Track ID (0–29)
    height_t    height;  // maxZ in meters
} height_input_t;

// ---------- Top-Level Function Prototype ----------

void fall_detect(
    height_input_t  heights[MAX_HEIGHTS],      // in:  current frame's height data
    int             num_heights,                // in:  number of active heights
    ap_uint<5>      active_tids[MAX_HEIGHTS],   // in:  list of active track TIDs
    int             num_active_tracks,          // in:  number of active tracks
    result_t        fall_results[MAX_TRACKS]    // out: fall display counter per track
);

#endif // FALL_DETECT_H
