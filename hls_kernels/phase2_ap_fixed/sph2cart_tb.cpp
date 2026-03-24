/**
 * sph2cart_tb.cpp
 * Testbench for Phase 2 (ap_fixed) Spherical-to-Cartesian HLS Kernel
 *
 * Same golden vectors as Phase 1, but:
 *   - Casts float inputs → ap_fixed for kernel call
 *   - Casts ap_fixed outputs → float for comparison
 *   - Relaxed tolerance to account for fixed-point quantization
 *     and CORDIC approximation error
 */

#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <fstream>
#include <string>
#include <sstream>
#include "sph2cart.h"

// Tolerance: relaxed from 1e-4 (float phase) to 5e-3 (ap_fixed phase)
// CORDIC with 18-bit fixed-point has ~14-bit precision → ~6e-5 per trig call
// Two multiplies compound the error, so 5e-3 gives comfortable margin.
// If this passes, we know the fixed-point format has enough precision for radar.
#define ABS_TOL 5e-3f

int main()
{
    // ============================================================
    // 1. Read input test vectors (same files as Phase 1)
    // ============================================================
    std::ifstream fin_sph("tv_spherical.dat");
    std::ifstream fin_cart("tv_cartesian.dat");

    if (!fin_sph.is_open()) {
        printf("ERROR: Cannot open tv_spherical.dat\n");
        printf("       Run gen_testvectors.py first to generate test vectors.\n");
        return -1;
    }
    if (!fin_cart.is_open()) {
        printf("ERROR: Cannot open tv_cartesian.dat\n");
        printf("       Run gen_testvectors.py first to generate test vectors.\n");
        return -1;
    }

    // Kernel I/O arrays (ap_fixed types)
    sph_t  spherical[MAX_NUM_POINTS][SPH_DIMS];
    cart_t cartesian[MAX_NUM_POINTS][SPH_DIMS] = {0};

    // Golden reference (float)
    float golden[MAX_NUM_POINTS][SPH_DIMS];

    int num_points = 0;
    std::string line;

    // Read spherical inputs → cast to ap_fixed
    while (std::getline(fin_sph, line) && num_points < MAX_NUM_POINTS) {
        if (line.empty() || line[0] == '#') continue;
        std::istringstream iss(line);
        float r, az, el;
        if (iss >> r >> az >> el) {
            spherical[num_points][0] = (sph_t) r;
            spherical[num_points][1] = (sph_t) az;
            spherical[num_points][2] = (sph_t) el;
            num_points++;
        }
    }
    fin_sph.close();

    // Read golden cartesian outputs (keep as float)
    int num_golden = 0;
    while (std::getline(fin_cart, line) && num_golden < MAX_NUM_POINTS) {
        if (line.empty() || line[0] == '#') continue;
        std::istringstream iss(line);
        float x, y, z;
        if (iss >> x >> y >> z) {
            golden[num_golden][0] = x;
            golden[num_golden][1] = y;
            golden[num_golden][2] = z;
            num_golden++;
        }
    }
    fin_cart.close();

    if (num_points != num_golden) {
        printf("ERROR: Mismatch between input (%d) and golden (%d) point counts\n",
               num_points, num_golden);
        return -1;
    }

    printf("============================================\n");
    printf("  sph2cart HLS Testbench\n");
    printf("  Target:  Artix-7 xc7a35t @ 100 MHz\n");
    printf("  Phase:   2 (ap_fixed / CORDIC)\n");
    printf("  Points:  %d\n", num_points);
    printf("  Tolerance: %.1e\n", ABS_TOL);
    printf("============================================\n\n");

    // ============================================================
    // 2. Run the HLS kernel
    // ============================================================
    sph2cart(spherical, cartesian, num_points);

    // ============================================================
    // 3. Compare against golden reference
    // ============================================================
    int errors = 0;
    float max_err = 0.0f;
    int max_err_pt = 0;
    int max_err_dim = 0;

    for (int i = 0; i < num_points; i++) {
        for (int d = 0; d < SPH_DIMS; d++) {
            // Cast ap_fixed result back to float for comparison
            float hls_val = (float) cartesian[i][d];
            float gold_val = golden[i][d];
            float err = fabsf(hls_val - gold_val);

            if (err > max_err) {
                max_err = err;
                max_err_pt = i;
                max_err_dim = d;
            }

            if (err > ABS_TOL) {
                const char* dim_name[] = {"X", "Y", "Z"};
                printf("MISMATCH pt[%d].%s : HLS=%.8f  Golden=%.8f  err=%.2e\n",
                       i, dim_name[d], hls_val, gold_val, err);
                errors++;
            }
        }
    }

    // ============================================================
    // 4. Print first 5 points for quick visual check
    // ============================================================
    printf("\n--- Sample Output (first 5 points) ---\n");
    printf("%-4s  %-12s %-12s %-12s | %-12s %-12s %-12s\n",
           "Pt", "HLS_X", "HLS_Y", "HLS_Z", "Gold_X", "Gold_Y", "Gold_Z");
    int display = (num_points < 5) ? num_points : 5;
    for (int i = 0; i < display; i++) {
        printf("%-4d  %12.6f %12.6f %12.6f | %12.6f %12.6f %12.6f\n",
               i,
               (float)cartesian[i][0], (float)cartesian[i][1], (float)cartesian[i][2],
               golden[i][0],           golden[i][1],           golden[i][2]);
    }

    // ============================================================
    // 5. Summary
    // ============================================================
    const char* dim_names[] = {"X", "Y", "Z"};
    printf("\n============================================\n");
    printf("  Max absolute error: %.2e (pt[%d].%s)\n",
           max_err, max_err_pt, dim_names[max_err_dim]);
    printf("  Total mismatches:   %d / %d values\n", errors, num_points * SPH_DIMS);
    printf("  Tolerance used:     %.1e\n", ABS_TOL);

    if (errors == 0) {
        printf("\n  *** PASS — All %d points match golden reference ***\n", num_points);
        printf("  Fixed-point precision is sufficient for radar data.\n");
    } else {
        printf("\n  *** FAIL — %d mismatches detected ***\n", errors);
        printf("  Consider widening fractional bits or relaxing tolerance.\n");
    }
    printf("============================================\n");

    return (errors == 0) ? 0 : 1;
}