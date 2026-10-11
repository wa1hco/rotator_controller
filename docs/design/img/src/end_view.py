import sys; sys.path.insert(0, "/workspace/rotator-design/img/src")
from common import *
import matplotlib.gridspec as gs

# ---- geometry (mm). y across width (0 = centreline), z up (0 = outside bottom)
W, HT, T = 103.0, 53.0, 1.5
Z_IT = HT - T                 # inner top face 51.5
Z_IF = Z_IT - 49.62           # inner floor 1.88
Y_SB = W/2 - T                # slot bottom 50.0
Y_TT = Y_SB - 2.5             # tooth tip 47.5
FIRST, PITCH, SLOT = 6.41, 3.5, 2.0
K = 5                         # slot used (0 = top)
def slot(n):                  # (z_bot, z_top)
    zt = Z_IT - FIRST - PITCH*n; return zt - SLOT, zt
NS = [n for n in range(20) if slot(n)[0] > Z_IF + 1.5]
PCB_T = 1.6
z_pcb_top = slot(K)[1]                    # board lifted against tooth above
z_pcb_bot = z_pcb_top - PCB_T
D_K = Z_IT - z_pcb_top                    # 23.91
H_BAR = round(D_K - 0.65, 2)
PAD = 0.65    # 1.0 mm pad compressed to 0.65
z_bar_top = z_pcb_top + H_BAR

f = plt.figure(figsize=(16, 14), dpi=100)
g = gs.GridSpec(2, 2, height_ratios=[1.5, 1], width_ratios=[1, 1.15], hspace=0.08, wspace=0.05,
                left=0.02, right=0.98, top=0.955, bottom=0.01)
ax = f.add_subplot(g[0, :]); ax.set_aspect("equal"); ax.axis("off")
f.suptitle("CHOSEN DESIGN - END VIEW (section just in front of the triacs, looking toward the rear plate)",
           fontsize=FS_T-2, fontweight="bold")

def draw_wall(ax, side):
    s = side
    # outer skin of side wall
    x0 = Y_SB if s > 0 else -W/2
    rect(ax, x0, 0, T, HT, C_EXT, E_EXT, z=3)
    # comb: solid band minus slots
    xb = Y_TT if s > 0 else -Y_SB
    zs = [Z_IF] + sum([[slot(n)[0], slot(n)[1]] for n in NS], []) + [Z_IT]
    # solid pieces between slots (teeth + bosses)
    pieces = [(Z_IF, slot(NS[-1])[0])] + [(slot(n+1)[1], slot(n)[0]) for n in NS[:-1]] + [(slot(0)[1], Z_IT)]
    for a, b in pieces:
        rect(ax, xb, a, 2.5, b - a, C_EXT, E_EXT, lw=0.6, z=3)
    # slot backs show as white
    for n in NS:
        a, b = slot(n); rect(ax, xb, a, 2.5, b - a, "white", E_EXT, lw=0.6, z=2.9)

# extrusion: top wall + both sides
rect(ax, -W/2, Z_IT, W, T, C_EXT, E_EXT, z=3)
draw_wall(ax, +1); draw_wall(ax, -1)
# belly plate
rect(ax, -Y_SB, 0.2, 2*Y_SB, Z_IF - 0.2, C_BELLY, E_EXT, z=3, hatch="//")
# PCB in slot K
rect(ax, -99.3/2, z_pcb_bot, 99.3, PCB_T, C_PCB, E_PCB, z=4)
# bar
rect(ax, -25, z_pcb_top, 50, H_BAR, C_BAR, E_BAR, lw=1.5, z=4)
# pad
rect(ax, -25, z_bar_top, 50, PAD, C_PAD, "#7a1050", lw=0.8, z=5)
# top screws (ISO 7380 M3x6) at y=+-20
for y in (-20, 20):
    ax.add_patch(Polygon([(y-2.85, HT), (y+2.85, HT), (y+2.0, HT+1.65), (y-2.0, HT+1.65)],
                 closed=True, fc=C_SCR, ec="k", lw=1, zorder=7))
    rect(ax, y-1.5, HT-8, 3.0, 8, C_SCR, "k", lw=0.8, z=6.5)
    # bottom screws M3x6 pan head from PCB underside
    rect(ax, y-2.75, z_pcb_bot-2.4, 5.5, 2.4, C_SCR, "k", lw=1, z=7)
    rect(ax, y-1.5, z_pcb_bot, 3.0, 6.0, C_SCR, "k", lw=0.8, z=6.5)
# triacs (TO-220 Ins), plastic face toward viewer, seated 3 mm up
for i, y in enumerate((-12.7, 0, 12.7)):
    zb = z_pcb_top + 3.0
    rect(ax, y-5.0, zb + 9.2, 10.0, 6.7, C_TAB, "k", lw=1, z=6)          # tab above body
    ax.add_patch(Circle((y, z_pcb_top + 16.1), 2.75, fc=C_SCR, ec="k", lw=1, zorder=7))  # M3 pan head
    rect(ax, y-5.0, zb, 10.0, 9.2, C_TRI, "k", lw=1, z=6.2)
    for dx in (-2.54, 0, 2.54):
        rect(ax, y+dx-0.4, z_pcb_top, 0.8, 3.0, "#B08D57", "k", lw=0.5, z=6)
    ax.text(y, zb + 4.6, ["CW", "CCW", "BRK"][i], color="white", fontsize=FS-2, ha="center",
            va="center", fontweight="bold", zorder=8)

# ---- dimensions
dim(ax, (-W/2, HT), (W/2, HT), "103.0 outside", off=(0, 10))
dim(ax, (-W/2, 0), (-W/2, HT), "53.0 outside", off=(-6, 0))
dim(ax, (-40, Z_IF), (-40, Z_IT), "49.62 inside", ext=False, tpos=0.27)
dim(ax, (-99.3/2, z_pcb_bot), (99.3/2, z_pcb_bot), "PCB 99.3 x 1.6", off=(0, -9), tpos=0.5)
dim(ax, (-Y_TT, 6), (Y_TT, 6), "95.0 between tooth tips", off=(0, 0), ext=False)
dim(ax, (40, z_pcb_top), (40, Z_IT), "D_k = 23.9 (verify)", ext=False, rot=90)
dim(ax, (-25, z_pcb_top), (-25, z_bar_top), "H = 23.25", off=(-6, 0), rot=90)
dim(ax, (-20, HT+1.65), (20, HT+1.65), "40 c-c", off=(0, 3.5), tpos=0.5)

# ---- labels (right side)
LX = 62
label(ax, (20+2.0, HT+1.2), "M3 x 8 ISO 7380 button head x2\n(3.4 mm holes in top wall)", (LX, 66))
label(ax, (10, Z_IT+0.75), "Top wall 1.5 (flat inside)", (LX, 58))
label(ax, (14, z_bar_top+0.25), "TGP 3000 pad 1.0 -> 0.65 clamped", (LX, 52), color="#a0106a")
label(ax, (24, z_bar_top-3), "6061 bar 10 x 50 x H\n(behind the triacs)", (LX, 43), color=E_BAR)
label(ax, (12.7+5, z_pcb_top+14), "BTA16-600SW, insulated TO-220\nM3 x 8 + Belleville into bar", (LX, 33))
label(ax, (49, slot(2)[0]+1), "Slot comb (both walls)\nsee detail below", (LX, 22.5))
label(ax, (35, z_pcb_top+0.8), "PCB in slot k, lifted\nagainst tooth above", (LX, 13))
label(ax, (20+2.75, z_pcb_bot-2.4), "M3 x 6 pan head x2 from below,\nNPTH 3.2 in PCB", (LX, 3.5))
label(ax, (-30, 1.0), "Belly plate (slides out)", (-30, -7), ha="center")
ax.text(0, (z_pcb_bot+Z_IF)/2 - 3, "Below board: ~24 mm (verify)\nfor bottom-side parts", ha="center",
        va="center", fontsize=FS-1, color="#444", zorder=8)
ax.set_xlim(-66, 126); ax.set_ylim(-10, 68)

# ---- comb detail (bottom-left)
dx = f.add_subplot(g[1, 0]); dx.set_aspect("equal"); dx.axis("off")
dx.set_title("Detail: right wall comb (approx. 4:1)", fontsize=FS+1, fontweight="bold")
rect(dx, Y_SB, Z_IT - 30, T, 30 + T, C_EXT, E_EXT, z=3)
rect(dx, Y_TT - 6, Z_IT, 6 + 2.5 + T, T, C_EXT, E_EXT, z=3)
pieces = [(slot(n+1)[1], slot(n)[0]) for n in range(0, 7)] + [(slot(0)[1], Z_IT)]
for a, b in pieces:
    rect(dx, Y_TT, max(a, Z_IT-30), 2.5, b - max(a, Z_IT-30), C_EXT, E_EXT, lw=0.8, z=3)
rect(dx, Y_TT-6, z_pcb_bot, 6 + 2.5, PCB_T, C_PCB, E_PCB, z=4)
dim(dx, (Y_SB+T, Z_IT+T), (Y_SB+T, Z_IT - FIRST), "6.41 (verify)", off=(3.2, 0), tdx=1.5, ha="left", rot=0)
z0 = slot(1)[1]
dim(dx, (Y_TT, slot(1)[1]), (Y_TT, slot(1)[0]), "slot 2.0", off=(-1.5, 0), tdx=-0.8, ha="right", rot=0)
dim(dx, (Y_TT, slot(3)[1]), (Y_TT, slot(2)[1]), "pitch 3.5", off=(-1.5, 0), tdx=-0.8, ha="right", rot=0)
dim(dx, (Y_SB, slot(3)[0]+1.0), (Y_TT, slot(3)[0]+1.0), "2.5", off=(0, 0), ext=False, tdy=-1.1)
dim(dx, (Y_SB, Z_IT-28), (Y_SB+T, Z_IT-28), "wall 1.5", off=(0, 0), ext=False, tdx=1.2, ha="left")
dim(dx, (Y_SB+T, z_pcb_top), (Y_SB+T, Z_IT), "D_k (verify)", off=(9.0, 0), tdx=1.5, ha="left", rot=0, tpos=0.5)
dx.text(Y_TT-5.0, z_pcb_top - 4.5, "slot k (example:\n6th from top)", fontsize=FS-1, ha="center", va="center")
label(dx, (Y_TT+0.4, slot(4)[0]-0.75), "tooth 1.5", (Y_TT-7, slot(4)[0]-0.75), ha="center", fs=FS-1)
dx.text(Y_SB + 6, Z_IT - 22, "Slot heights from\nHammond drawing;\nconfirm on STEP\nmodel / calipers", fontsize=FS-2,
        color="#8B0000", ha="left", va="center")
dx.set_xlim(Y_TT - 11, Y_SB + 21); dx.set_ylim(Z_IT - 30.5, Z_IT + 3)

# ---- notes / legend (bottom-right)
nx = f.add_subplot(g[1, 1]); nx.axis("off"); nx.set_xlim(0, 1); nx.set_ylim(0, 1)
items = [(C_EXT, "1455N1601 extrusion (6063 Al)"), (C_BELLY, "Belly plate"), (C_BAR, "6061 bar 10 x 50 x H"),
         (C_PAD, "TGP 3000 gap pad 1.0 mm"), (C_TRI, "Triac body (TO-220 Ins)"), (C_TAB, "Triac tab"),
         (C_PCB, "PCB 1.6"), (C_SCR, "M3 screws")]
for i, (c, t) in enumerate(items):
    yy = 0.95 - i*0.075
    nx.add_patch(Rectangle((0.03, yy-0.025), 0.07, 0.05, fc=c, ec="k", transform=nx.transAxes))
    nx.text(0.13, yy, t, fontsize=FS, va="center", transform=nx.transAxes)
nx.text(0.03, 0.33, "All dims mm.  Triacs shown 3 mm seated\nheight; tab-hole height ~16 above PCB\n(verify vs TO-220AB drawing).\n"
        "k = slot index from top. Pick k so that\nD_k is 22-29 mm; H = D_k - 0.65\n(1.0 pad compressed 0.35 = 35 %).",
        fontsize=FS-1, va="top", transform=nx.transAxes)
f.savefig("/workspace/rotator-design/img/triac-end-view.png", dpi=100)
print("D_k", D_K, "H", H_BAR, "slots", len(NS), "below", z_pcb_bot - Z_IF)
