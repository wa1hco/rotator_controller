import sys; sys.path.insert(0, "/workspace/rotator-design/img/src")
from common import *
import matplotlib.gridspec as gs

L, HT, T = 160.0, 53.0, 1.5
Z_IT = HT - T; Z_IF = Z_IT - 49.62
zp = 27.59 - 1.6; zt = 27.59          # PCB bottom/top (slot k, lifted)
H = 23.25; PAD = 0.65; zb = zt + H      # bar top
XB0, XB1 = 24.0, 34.0                  # bar
XS = 29.0                              # bar screws x
TAB = 1.3; BODY = 4.5; SEAT = 3.0; HOLE = 16.1; TABTOP = 18.9; BODYTOP = 12.2
XL = XB1 + 2.5                         # lead row

def hidden_screw(ax, x, top=True):
    if top:
        ax.add_patch(Polygon([(x-2.85, HT), (x+2.85, HT), (x+2.0, HT+1.65), (x-2.0, HT+1.65)], closed=True,
                     fc=C_SCR, ec="k", lw=1, zorder=7))
        rect(ax, x-1.5, HT-8, 3, 8, "none", C_SCR, lw=1.6, z=7, ls="--")
    else:
        rect(ax, x-2.75, zp-2.4, 5.5, 2.4, C_SCR, "k", lw=1, z=7)
        rect(ax, x-1.5, zp, 3, 6, "none", C_SCR, lw=1.6, z=7, ls="--")

def draw_core(ax, detail=False):
    # extrusion top wall (section) and belly plate
    rect(ax, 0, Z_IT, L, T, C_EXT, E_EXT, z=3)
    rect(ax, 0, 0.2, L, Z_IF-0.2, C_BELLY, E_EXT, z=3, hatch="//")
    # far side wall comb seen beyond the section: tooth bands (light)
    if False:
        for n in range(12):
            ztop = Z_IT - 6.41 - 3.5*n
            if ztop - 2 < Z_IF + 1.5: break
            ax.plot([0, L], [ztop, ztop], color="#B8C2CC", lw=0.7, zorder=1)
            ax.plot([0, L], [ztop-2, ztop-2], color="#B8C2CC", lw=0.7, zorder=1)
    # end plates
    rect(ax, -T, 0, T, HT, C_PLATE, E_EXT, z=3)
    rect(ax, L, 0, T, HT, C_PLATE, E_EXT, z=3)
    # PCB
    rect(ax, 0.5, zp, 159.0, 1.6, C_PCB, E_PCB, z=4)
    # bar + pad
    rect(ax, XB0, zt, XB1-XB0, H, C_BAR, E_BAR, lw=1.5, z=4)
    rect(ax, XB0, zb, XB1-XB0, PAD, C_PAD, "#7a1050", lw=0.8, z=5)
    hidden_screw(ax, XS, True); hidden_screw(ax, XS, False)
    # triac: tab (metal) + body (plastic) + leads
    rect(ax, XB1, zt+SEAT, TAB, TABTOP-SEAT, C_TAB, "k", lw=1, z=6)
    rect(ax, XB1+TAB, zt+SEAT, BODY-TAB, BODYTOP-SEAT, C_TRI, "k", lw=1, z=6)
    rect(ax, XL-0.4, zp-1.5, 0.8, SEAT+1.6+1.5, "#B08D57", "k", lw=0.6, z=6)
    # triac screw M3x8 pan head + Belleville, horizontal into the bar
    rect(ax, XB1+TAB, zt+HOLE-2.75, 2.4, 5.5, C_SCR, "k", lw=1, z=7)
    rect(ax, XB1+TAB-8, zt+HOLE-1.5, 8, 3, C_SCR, "k", lw=0.8, z=6.5)

# =========================================================
f = plt.figure(figsize=(16, 13), dpi=100)
g = gs.GridSpec(2, 1, height_ratios=[0.85, 1.1], hspace=0.04, left=0.01, right=0.99, top=0.955, bottom=0.01)
ax = f.add_subplot(g[0]); ax.set_aspect("equal"); ax.axis("off")
f.suptitle("CHOSEN DESIGN - SIDE VIEW (section on the board centreline, looking across the width)",
           fontsize=FS_T-2, fontweight="bold")
draw_core(ax)
# rear connectors (rotor pluggable shown; RJ45 etc. dashed behind)
rect(ax, 0.5, zt, 13.0, 12.0, C_CON, "k", z=5)                 # header
rect(ax, -9.0, zt+1.5, 13.0, 13.5, "#9C85D6", "k", z=5.5)      # plug through plate cut-out
rect(ax, 0.5, zt, 18.0, 13.5, "none", C_CON, lw=1.4, z=5, ls="--")   # RJ45 outline behind
# F1 / MOV
rect(ax, 18.5, zt, 4.5, 9.0, "#8c8c8c", "k", z=5)
# MOC / snubber / relay zone
rect(ax, 40, zt, 7.6, 4.5, "#444", "k", z=5)                  # MOC3023 DIP6
rect(ax, 50, zt, 7.0, 12.0, "#E6C229", "k", z=5)              # X2 film cap
rect(ax, 60, zt, 15.7, 15.7, "#3B6FB6", "k", z=5)             # G5LE relay K10
# logic: MCU etc
rect(ax, 95, zt, 12, 1.6, "#333", "k", z=5)
rect(ax, 80, zt, 9, 6, "#777", "k", z=5)                     # buck inductor
# front: right-angle tact switch + light pipe
rect(ax, 150.5, zt, 8.0, 6.5, "#555", "k", z=5)
rect(ax, 158.5, zt+1.8, 4.6, 3.0, C_UI, "k", z=5.5)           # actuator through front plate
rect(ax, 154, zt+8.5, 9.1, 3.0, "none", C_UI, lw=1.6, z=5.5, ls="--")  # light pipe (other y)
rect(ax, 152.5, zt, 1.6, 9.0, "none", C_UI, lw=1.2, z=5.5, ls="--")   # LED under pipe

# dims
dim(ax, (0, HT+1.7), (L, HT+1.7), "160.0 extrusion (x = 0 at rear inner face; end-plate stack verify)", off=(0, 5))
dim(ax, (0, zp), (XB0, zp), "24", off=(0, -6), tdy=0)
dim(ax, (XB0, zp), (XB1, zp), "10", off=(0, -6))
dim(ax, (L+T, 0), (L+T, HT), "53.0", off=(6, 0))
dim(ax, (125, zt), (125, Z_IT), "D_k 23.9\n(verify)", ext=False, rot=0, tdx=1.5, ha="left")
dim(ax, (125, Z_IF), (125, zp), "~24 below\nboard (verify)", ext=False, rot=0, tdx=1.5, ha="left")
dim(ax, (0.5, 12), (18.5, 12), "0..18 connectors", ext=False, tdy=-3.0)
dim(ax, (38, 12), (75.7, 12), "38..76 drivers / snubbers / K10", ext=False, tdy=-3.0)

# labels
label(ax, (-0.75, 4), "Rear plate (all cables):\nrotor plug, RJ45, USB-C,\n13.8 V, 26 VAC", (2, -9), ha="left", va="top")
label(ax, (160.75, 4), "Front plate:\nbuttons + LEDs\n(light pipes)", (158, -9), ha="right", va="top")
label(ax, (68, zt+14), "K10 relay", (68, 50), ha="center")
label(ax, (37, zt+8), "triacs", (88, 47), ha="left")
label(ax, (31, zt+11), "bar", (100, 40), ha="left", color=E_BAR)
ax.set_xlim(-14, 178); ax.set_ylim(-24, 66)

# =========================================================
dx = f.add_subplot(g[1]); dx.set_aspect("equal"); dx.axis("off")
dx.set_title("Detail: bar, triac and fasteners (about 2.5:1).  Dashed screws are at y = +-20, behind the section.",
             fontsize=FS, fontweight="bold")
draw_core(dx, detail=True)
dim(dx, (XB0, zp-3), (XB1, zp-3), "10.0", off=(0, -4))
dim(dx, (XB1, zp-3), (XL, zp-3), "2.5", off=(0, -4), tdx=3.5, bg=True, ha="left")
dim(dx, (XB0, zt), (XB0, zb), "H 23.25", off=(-4, 0))
dim(dx, (XB0-4, zt), (XB0-4, Z_IT), "D_k 23.9 (verify)", off=(-6, 0))
dim(dx, (42, zt), (42, zt+SEAT), "", ext=False)
dx.text(42.8, zt+1.5, "3 seat (verify)", fontsize=FS_DIM, color=C_DIM, va="center")
dim(dx, (46, zt), (46, zt+HOLE), "", ext=False)
dx.plot([XB1+TAB+2.4, 46.5], [zt+HOLE]*2, color=C_DIM, lw=0.8)
dx.text(46.8, zt+HOLE-1.2, "16.1 hole (verify)", fontsize=FS_DIM, color=C_DIM, va="center")
dim(dx, (50, zt), (50, zt+TABTOP), "", ext=False)
dx.plot([XB1+TAB, 50.5], [zt+TABTOP]*2, color=C_DIM, lw=0.8)
dx.text(50.8, zt+TABTOP+0.9, "18.9 tab top (verify)", fontsize=FS_DIM, color=C_DIM, va="center")
LX = 78
label(dx, (XS+2.3, HT+1.2), "M3 x 8 ISO 7380 button head, 3.4 hole", (LX, 57))
label(dx, (36, Z_IT+0.75), "Top wall 1.5", (LX, 54))
label(dx, (33, zb+0.25), "TGP 3000 1.0 pad (0.65 clamped)", (LX, 51), color="#a0106a")
label(dx, (XB1+TAB+2.4, zt+HOLE+1.5), "M3 x 8 pan + Belleville, ~0.55 N m", (LX, 39.5))
label(dx, (XB1+0.65, zt+TABTOP-4.5), "Insulated tab, greased to bar", (LX, 35.5))
label(dx, (XB1+3, zt+7), "BTA16-600SW body", (LX, 31.5))
label(dx, (31, zt+3), "6061 bar 10 thick", (LX, 27.5), color=E_BAR)
label(dx, (44, zp+0.8), "PCB 1.6 in slot k", (LX, 23.5))
label(dx, (XL+0.4, zp-1), "Leads 2.5 from bar face (verify)", (LX, 19.5))
label(dx, (XS+2.75, zp-1.6), "M3 x 6 pan from below, NPTH 3.2", (LX, 15.5))
dx.set_xlim(8, 132); dx.set_ylim(13, 59)
f.savefig("/workspace/rotator-design/img/triac-side-view.png", dpi=100)
