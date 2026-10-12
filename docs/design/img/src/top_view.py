import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *

L, W, T = 160.0, 103.0, 1.5
YB = 99.3/2; KO = 3.5
f, ax = fig(16, 12.4)
f.subplots_adjust(left=0.01, right=0.99, top=0.94, bottom=0.01)
f.suptitle("CHOSEN DESIGN - TOP VIEW (top wall removed), rear plate at left", fontsize=FS_T-2, fontweight="bold")

# extrusion side walls (plan) + end plates
rect(ax, 0, W/2-T, L, T, C_EXT, E_EXT, z=3); rect(ax, 0, -W/2, L, T, C_EXT, E_EXT, z=3)
rect(ax, 0, W/2-4.0, L, 2.5, C_EXT, E_EXT, z=2.5, alpha=0.55)          # tooth tips (comb) band
rect(ax, 0, -W/2+1.5, L, 2.5, C_EXT, E_EXT, z=2.5, alpha=0.55)
rect(ax, -T, -W/2, T, W, C_PLATE, E_EXT, z=3); rect(ax, L, -W/2, T, W, C_PLATE, E_EXT, z=3)
# PCB
rect(ax, 0.5, -YB, 159, 2*YB, C_PCB, E_PCB, z=1, alpha=0.30)
for s in (1, -1):   # 3.5 keepout bands
    y0 = YB - KO if s > 0 else -YB
    rect(ax, 0.5, y0, 159, KO, "none", "#555", lw=0.8, z=2.6, hatch="xx")
# rear connectors (approx sizes)
cons = [("RJ45", 29, 16, 21), ("USB-C", 18.5, 9, 7.5), ("26 VAC PP", -5.0, 21.8, 10),
        ("rotor 8-pos 5.08", -46.0, 40.6, 10)]
for name, y0, w, d in cons:
    rect(ax, 0.5, y0, d, w, C_CON, "k", z=4)
    rect(ax, -9.0, y0+0.5, 9.5, w-1, "#9C85D6", "k", z=3.6) if name not in ("RJ45", "USB-C") else None
    ax.text(0.5+d/2 if name != "rotor 8-pos 5.08" else 5.5, y0+w/2, name, rotation=90 if w < 30 else 90,
            color="white", fontsize=FS-4 if w < 12 else FS-2, ha="center", va="center", zorder=5, fontweight="bold")
rect(ax, 12, -24, 10, 16, "#8c8c8c", "k", z=4)
ax.text(17, -16, "F1\nMOV", fontsize=FS-4, ha="center", va="center", color="white", zorder=5, fontweight="bold")
# bar + pad + top-wall screws
rect(ax, 24, -25, 10, 50, C_BAR, E_BAR, lw=1.8, z=4)
rect(ax, 24.6, -24.4, 8.8, 48.8, C_PAD, "#7a1050", lw=0.8, z=4.2, alpha=0.55)
for y in (-20, 20):
    ax.add_patch(Circle((29, y), 2.85, fc=C_SCR, ec="k", lw=1.2, zorder=6))
# triacs
for i, y in enumerate((-12.7, 0, 12.7)):
    rect(ax, 34, y-5, 1.3, 10, C_TAB, "k", z=5)
    rect(ax, 35.3, y-5, 3.2, 10, C_TRI, "k", z=5)
    rect(ax, 35.3, y-2.75, 2.4, 5.5, C_SCR, "k", z=6)
    ax.text(40, y, ["CW", "CCW", "BRK"][i], fontsize=FS-3, va="center", ha="left", zorder=6, fontweight="bold")
# zones
rect(ax, 38.5, -44, 37.5, 88, C_ZONE, "#b59b00", lw=1.2, z=1.5, ls="--", alpha=0.7)
ax.text(57.25, 30, "MOC3023 x3,\nsnubbers,\nsense optos,\nK10 relay,\ninterlock", fontsize=FS-2,
        ha="center", va="center", zorder=5)
rect(ax, 78, -44, 66, 88, "#E3F0FF", "#4a78b0", lw=1.2, z=1.5, ls="--", alpha=0.7)
ax.text(111, 0, "logic: MCU, buck,\nUSB isolator,\nEthernet (opt.)", fontsize=FS, ha="center", va="center", zorder=5)
# front UI
for y in (-30, -15, 0, 15):
    rect(ax, 151, y-3.5, 8, 7, "#555", "k", z=4); rect(ax, 159, y-1.5, 3.5, 3, C_UI, "k", z=4)
for y in (28, 36):
    rect(ax, 150, y-1.5, 11.5, 3, "#cfe3f7", C_UI, z=4); ax.add_patch(Circle((150, y), 1.5, fc="#2ca02c", ec="k", zorder=5))

# ---- dims
dim(ax, (0, W/2), (L, W/2), "160.0 extrusion", off=(0, 8))
dim(ax, (L+T, -W/2), (L+T, W/2), "103.0", off=(10, 0))
dim(ax, (L+T, -YB), (L+T, YB), "PCB 99.3", off=(22, 0))
dim(ax, (0, -W/2), (24, -W/2), "24", off=(0, -8))
dim(ax, (24, -W/2), (34, -W/2), "10", off=(0, -8))
dim(ax, (34, -W/2), (36.5, -W/2), "", off=(0, -8))
ax.text(37.5, -W/2-8, "lead row 36.5 (verify)", fontsize=FS_DIM, color=C_DIM, va="center", ha="left")
dim(ax, (0, -W/2), (29, -W/2), "29 = top-wall hole x", off=(0, -17), tpos=0.5, tdx=6)
dim(ax, (24, -25), (24, 25), "50", off=(-6, 0), tpos=0.82)
dim(ax, (29, -20), (29, 20), "40 c-c", ext=False, tpos=0.5)
dim(ax, (44, 0), (44, 12.7), "", ext=False)
ax.text(45, 6.35, "12.7 pitch", fontsize=FS_DIM, color=C_DIM, va="center", ha="left",
        bbox=dict(fc="white", ec="none", pad=1, alpha=0.8), zorder=8)
dim(ax, (90, YB-KO), (90, YB), "", ext=False)
ax.text(92, YB-1.75, "3.5 edge keepout, both faces", fontsize=FS_DIM, color=C_DIM, va="center", ha="left",
        bbox=dict(fc="white", ec="none", pad=1, alpha=0.85), zorder=8)

# ---- labels
label(ax, (29, 20+2.85), "M3 x 8 button heads (x = 29, y = +-20,\n3.4 mm holes; drill template from KiCad)", (2, 66), ha="left")
label(ax, (-5, 45), "Rear plate:\nall cables", (-14, 75), ha="center")
label(ax, (162.5, 15), "Front plate: buttons\n(+ LED light pipes)", (150, 70), ha="center")
label(ax, (33, -10), "6061 bar 10 x 50 under\nTGP 3000 1.0 mm pad", (60, -70), ha="center", color=E_BAR)
label(ax, (37, -12.7), "BTA16-600SW x3 standing\non bar front face", (110, -70), ha="center")
ax.text(0, -86, "Connector widths and depths are typical catalog sizes (approx.); final order/placement TBD.",
        fontsize=FS-2, color="#444", ha="left")
ax.set_xlim(-26, 196); ax.set_ylim(-90, 80)
f.savefig(Path(__file__).resolve().parents[1] / "triac-top-view.png", dpi=100)
