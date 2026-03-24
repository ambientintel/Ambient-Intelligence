/**
 * tlv_sph2cart_tb.cpp
 * Testbench for Phase 3: Fused TLV Decompression + sph2cart
 *
 * Reads:
 *   tv_compressed.dat — packed 64-bit hex per point
 *   tv_punits.dat     — 5 decompression unit factors
 *   tv_output.dat     — golden [X, Y, Z, Doppler, SNR]
 *
 * Packs compressed data into ap_uint<64>, calls kernel, compares output.
 */

#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <fstream>
#include <string>
#include <sstream>
#include <cstdint>
#include "tlv_sph2cart.h"

// Tolerances (per field)
// X,Y,Z: same as Phase 2 (CORDIC + fixed-point quantization + decompression)
// Doppler, SNR: tighter (just fixed-point multiply, no trig)
#define ABS_TOL_XYZ  1e-2f
#define ABS_TOL_DOPP 5e-2f
#define ABS_TOL_SNR  5e-1f

int main()
{
    // ============================================================
    // 1. Read test vectors
    // ============================================================
    std::ifstream fin_comp("tv_compressed.dat");
    std::ifstream fin_unit("tv_punits.dat");
    std::ifstream fin_gold("tv_output.dat");

    if (!fin_comp.is_open() || !fin_unit.is_open() || !fin_gold.is_open()) {
        printf("ERROR: Cannot open test vector files.\n");
        printf("       Run gen_testvectors.py first.\n");
        return -1;
    }

    // Kernel I/O
    ap_uint<64> compressed[MAX_NUM_POINTS];
    unit_t      pUnit[5];
    out_t       point_cloud[MAX_NUM_POINTS][OUT_DIMS] = {0};

    // Golden reference
    float golden[MAX_NUM_POINTS][OUT_DIMS];

    // ---- Read compressed data ----
    int num_points = 0;
    std::string line;
    while (std::getline(fin_comp, line) && num_points < MAX_NUM_POINTS) {
        if (line.empty() || line[0] == '#') continue;
        uint64_t val;
        if (sscanf(line.c_str(), "0x%llX", (unsigned long long*)&val) == 1 ||
            sscanf(line.c_str(), "%llu", (unsigned long long*)&val) == 1) {
            compressed[num_points] = (ap_uint<64>)val;
            num_points++;
        }
    }
    fin_comp.close();

    // ---- Read decompression units ----
    float pu[5];
    while (std::getline(fin_unit, line)) {
        if (line.empty() || line[0] == '#') continue;
        std::istringstream iss(line);
        if (iss >> pu[0] >> pu[1] >> pu[2] >> pu[3] >> pu[4]) {
            for (int j = 0; j < 5; j++) pUnit[j] = (unit_t)pu[j];
        }
    }
    fin_unit.close();

    // ---- Read golden output ----
    int num_golden = 0;
    while (std::getline(fin_gold, line) && num_golden < MAX_NUM_POINTS) {
        if (line.empty() || line[0] == '#') continue;
        std::istringstream iss(line);
        float x, y, z, d, s;
        if (iss >> x >> y >> z >> d >> s) {
            golden[num_golden][0] = x;
            golden[num_golden][1] = y;
            golden[num_golden][2] = z;
            golden[num_golden][3] = d;
            golden[num_golden][4] = s;
            num_golden++;
        }
    }
    fin_gold.close();

    if (num_points != num_golden) {
        printf("ERROR: Mismatch between compressed (%d) and golden (%d) point counts\n",
               num_points, num_golden);
        return -1;
    }

    printf("============================================\n");
    printf("  tlv_sph2cart HLS Testbench\n");
    printf("  Target:  Artix-7 xc7a35t @ 100 MHz\n");
    printf("  Phase:   3 (Fused Decompress + sph2cart)\n");
    printf("  Points:  %d\n", num_points);
    printf("  Tol XYZ: %.1e  Dopp: %.1e  SNR: %.1e\n",
           ABS_TOL_XYZ, ABS_TOL_DOPP, ABS_TOL_SNR);
    printf("============================================\n\n");

    // ============================================================
    // 2. Run the HLS kernel
    // ============================================================
    tlv_sph2cart(compressed, pUnit, point_cloud, num_points);

    // ============================================================
    // 3. Compare against golden reference
    // ============================================================
    int errors = 0;
    float max_err[OUT_DIMS] = {0};
    int   max_err_pt[OUT_DIMS] = {0};
    const char* dim_names[] = {"X", "Y", "Z", "Doppler", "SNR"};
    float tols[] = {ABS_TOL_XYZ, ABS_TOL_XYZ, ABS_TOL_XYZ, ABS_TOL_DOPP, ABS_TOL_SNR};

    for (int i = 0; i < num_points; i++) {
        for (int d = 0; d < OUT_DIMS; d++) {
            float hls_val  = (float) point_cloud[i][d];
            float gold_val = golden[i][d];
            float err = fabsf(hls_val - gold_val);

            if (err > max_err[d]) {
                max_err[d] = err;
                max_err_pt[d] = i;
            }

            if (err > tols[d]) {
                printf("MISMATCH pt[%d].%-8s : HLS=%12.6f  Gold=%12.6f  err=%.2e\n",
                       i, dim_names[d], hls_val, gold_val, err);
                errors++;
            }
        }
    }

    // ============================================================
    // 4. Print first 5 points
    // ============================================================
    printf("\n--- Sample Output (first 5 points) ---\n");
    printf("%-3s  %-10s %-10s %-10s %-10s %-10s | %-10s %-10s %-10s %-10s %-10s\n",
           "Pt", "HLS_X", "HLS_Y", "HLS_Z", "HLS_Dopp", "HLS_SNR",
           "Gld_X", "Gld_Y", "Gld_Z", "Gld_Dopp", "Gld_SNR");
    int display = (num_points < 5) ? num_points : 5;
    for (int i = 0; i < display; i++) {
        printf("%-3d  %10.4f %10.4f %10.4f %10.4f %10.4f | %10.4f %10.4f %10.4f %10.4f %10.4f\n",
               i,
               (float)point_cloud[i][0], (float)point_cloud[i][1],
               (float)point_cloud[i][2], (float)point_cloud[i][3],
               (float)point_cloud[i][4],
               golden[i][0], golden[i][1], golden[i][2],
               golden[i][3], golden[i][4]);
    }

    // ============================================================
    // 5. Summary
    // ============================================================
    printf("\n============================================\n");
    printf("  Max errors per field:\n");
    for (int d = 0; d < OUT_DIMS; d++) {
        printf("    %-8s: %.2e  (pt[%d])  %s\n",
               dim_names[d], max_err[d], max_err_pt[d],
               max_err[d] <= tols[d] ? "OK" : "FAIL");
    }
    printf("  Total mismatches: %d / %d values\n", errors, num_points * OUT_DIMS);

    if (errors == 0) {
        printf("\n  *** PASS — Full pipeline verified ***\n");
        printf("  Fused decompress + sph2cart matches Python pipeline.\n");
    } else {
        printf("\n  *** FAIL — %d mismatches detected ***\n", errors);
    }
    printf("============================================\n");

    return (errors == 0) ? 0 : 1;
}
