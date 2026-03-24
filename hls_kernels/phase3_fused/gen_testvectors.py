#!/usr/bin/env python3
"""
gen_testvectors.py
Generate test vectors for sph2cart HLS kernel validation.

Uses the ORIGINAL sphericalToCartesianPointCloud() from gui_common.py
as the golden reference so the HLS output is verified against the
exact same math the radar pipeline currently runs.

Generates two files:
    tv_spherical.dat  — input  (range  azimuth  elevation) per line
    tv_cartesian.dat  — golden (x      y        z)         per line

Test vector composition:
    - Edge cases: zero range, zero angles, π/2 boundaries, negative angles
    - Typical radar data: ranges 0.5–8m, azimuth ±70°, elevation ±70°
      (matches the fovCfg in Final_config_6m.cfg: 70° azimuth, 70° elevation)
    - Random spread for coverage

Usage:
    python3 gen_testvectors.py
    → Produces tv_spherical.dat and tv_cartesian.dat in current directory.
    → Copy these into the Vitis HLS project directory before running C Sim.
"""

import numpy as np
import os
import sys

# ---------- Import the original function ----------
# Add the parent directory (where gui_common.py lives) to the path
# Adjust this path if your repo structure differs.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Try to import from the repo; fall back to a local copy of the function
try:
    sys.path.insert(0, os.path.join(SCRIPT_DIR, '..'))
    from gui_common import sphericalToCartesianPointCloud
    print("Imported sphericalToCartesianPointCloud from gui_common.py")
except ImportError:
    print("gui_common.py not found on path — using inline copy of function")
    def sphericalToCartesianPointCloud(sphericalPointCloud):
        """Exact copy from gui_common.py for standalone use."""
        shape = sphericalPointCloud.shape
        cartesianPointCloud = sphericalPointCloud.copy()
        if shape[1] < 3:
            return sphericalPointCloud
        # X = Range * sin(azimuth) * cos(elevation)
        cartesianPointCloud[:, 0] = (sphericalPointCloud[:, 0]
                                     * np.sin(sphericalPointCloud[:, 1])
                                     * np.cos(sphericalPointCloud[:, 2]))
        # Y = Range * cos(azimuth) * cos(elevation)
        cartesianPointCloud[:, 1] = (sphericalPointCloud[:, 0]
                                     * np.cos(sphericalPointCloud[:, 1])
                                     * np.cos(sphericalPointCloud[:, 2]))
        # Z = Range * sin(elevation)
        cartesianPointCloud[:, 2] = (sphericalPointCloud[:, 0]
                                     * np.sin(sphericalPointCloud[:, 2]))
        return cartesianPointCloud


# ---------- Test Vector Generation ----------

def generate_edge_cases():
    """Boundary and degenerate inputs."""
    cases = [
        # [range, azimuth, elevation]
        [0.0,    0.0,    0.0],      # Zero everything → (0, 0, 0)
        [1.0,    0.0,    0.0],      # Unit range, zero angles → (0, 1, 0)
        [1.0,    np.pi/2, 0.0],     # 90° azimuth → (1, 0, 0)
        [1.0,    0.0,    np.pi/2],  # 90° elevation → (0, 0, 1)
        [1.0,   -np.pi/2, 0.0],    # -90° azimuth → (-1, 0, 0)
        [1.0,    0.0,   -np.pi/2], # -90° elevation → (0, 0, -1)
        [1.0,    np.pi/4, np.pi/4], # 45° both
        [5.0,    0.0,    0.0],      # Larger range
        [0.001,  0.1,    0.1],      # Very small range (near-zero)
        [8.0,    1.2217, 1.2217],   # Max FOV (~70°) both axes
    ]
    return np.array(cases, dtype=np.float64)


def generate_typical_radar_data(n=40):
    """
    Simulate realistic point cloud data from the xWR6843.
    Ranges from cfg: boundaryBox -4 4 0 8 0 3 → range ~0.5 to 8m
    FOV from cfg:    fovCfg -1 70.0 70.0       → ±70° = ±1.2217 rad
    """
    rng = np.random.seed(42)
    ranges     = np.random.uniform(0.5, 8.0, n)
    azimuths   = np.random.uniform(-1.2217, 1.2217, n)    # ±70° in radians
    elevations = np.random.uniform(-1.2217, 1.2217, n)    # ±70° in radians
    return np.column_stack([ranges, azimuths, elevations])


def generate_stress_test(n=20):
    """Wider range of angles for robustness."""
    np.random.seed(99)
    ranges     = np.random.uniform(0.01, 10.0, n)
    azimuths   = np.random.uniform(-np.pi, np.pi, n)
    elevations = np.random.uniform(-np.pi/2, np.pi/2, n)
    return np.column_stack([ranges, azimuths, elevations])


def main():
    # Combine all test vectors
    edge    = generate_edge_cases()
    typical = generate_typical_radar_data(40)
    stress  = generate_stress_test(20)

    spherical = np.vstack([edge, typical, stress])  # 70 points total
    num_points = spherical.shape[0]

    print(f"Generated {num_points} test points "
          f"({len(edge)} edge + {len(typical)} typical + {len(stress)} stress)")

    # Run through the golden reference function
    # The function expects at least 3 columns; we have exactly 3
    cartesian = sphericalToCartesianPointCloud(spherical)

    # Write output files
    with open('tv_spherical.dat', 'w') as f:
        f.write(f"# Spherical test vectors: range  azimuth(rad)  elevation(rad)\n")
        f.write(f"# {num_points} points total\n")
        for i in range(num_points):
            f.write(f"{spherical[i,0]:.10f}  {spherical[i,1]:.10f}  {spherical[i,2]:.10f}\n")

    with open('tv_cartesian.dat', 'w') as f:
        f.write(f"# Golden cartesian reference: x  y  z\n")
        f.write(f"# {num_points} points total\n")
        for i in range(num_points):
            f.write(f"{cartesian[i,0]:.10f}  {cartesian[i,1]:.10f}  {cartesian[i,2]:.10f}\n")

    print(f"Wrote tv_spherical.dat ({num_points} points)")
    print(f"Wrote tv_cartesian.dat ({num_points} points)")

    # Quick sanity print
    print(f"\n--- First 5 points ---")
    print(f"{'Pt':>3s}  {'Range':>10s} {'Azimuth':>10s} {'Elev':>10s}  →  {'X':>10s} {'Y':>10s} {'Z':>10s}")
    for i in range(min(5, num_points)):
        print(f"{i:3d}  {spherical[i,0]:10.4f} {spherical[i,1]:10.4f} {spherical[i,2]:10.4f}"
              f"  →  {cartesian[i,0]:10.4f} {cartesian[i,1]:10.4f} {cartesian[i,2]:10.4f}")


if __name__ == '__main__':
    main()
