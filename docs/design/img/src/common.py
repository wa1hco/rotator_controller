import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle, FancyBboxPatch

# palette
C_EXT = "#9AA6B4"; E_EXT = "#3E4A59"     # extrusion
C_BELLY = "#C9D1DA"                      # belly plate
C_PLATE = "#B7C3CF"                      # end plates
C_BAR = "#F2A33A"; E_BAR = "#8A5300"     # 6061 bar
C_PAD = "#E040A0"                        # gap pad
C_TRI = "#262626"; C_TAB = "#C9C9C9"     # triac body / tab
C_PCB = "#1E8C45"; E_PCB = "#0B4D22"     # PCB
C_SCR = "#D62728"                        # screws
C_CON = "#6A4FB3"                        # connectors
C_UI = "#1F77B4"                         # buttons / LEDs
C_DIM = "#0A2A6B"                        # dimensions
C_ZONE = "#FFF3B0"

FS = 17      # label font (pt) at 100 dpi -> >=14 pt requirement
FS_DIM = 16
FS_T = 24

def fig(w_in, h_in):
    f, ax = plt.subplots(figsize=(w_in, h_in), dpi=100)
    ax.set_aspect("equal"); ax.axis("off")
    return f, ax

def rect(ax, x, y, w, h, fc, ec="k", lw=1.2, z=2, **kw):
    r = Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, linewidth=lw, zorder=z, **kw)
    ax.add_patch(r); return r

def dim(ax, p1, p2, text, off=(0, 0), tpos=0.5, ext=True, color=C_DIM, fs=FS_DIM,
        rot=None, tdx=0, tdy=0, ha="center", va="center", bg=True):
    """Dimension between p1 and p2, drawn displaced by 'off', with extension lines."""
    (x1, y1), (x2, y2) = p1, p2
    a = (x1 + off[0], y1 + off[1]); b = (x2 + off[0], y2 + off[1])
    if ext and (off[0] or off[1]):
        ax.plot([x1, a[0]], [y1, a[1]], color=color, lw=0.8, zorder=6)
        ax.plot([x2, b[0]], [y2, b[1]], color=color, lw=0.8, zorder=6)
    ax.annotate("", xy=a, xytext=b, zorder=7,
                arrowprops=dict(arrowstyle="<|-|>", color=color, lw=1.3,
                                shrinkA=0, shrinkB=0, mutation_scale=16))
    tx = a[0] + (b[0] - a[0]) * tpos + tdx; ty = a[1] + (b[1] - a[1]) * tpos + tdy
    if rot is None:
        rot = 90 if abs(x1 - x2) < 1e-9 else 0
    ax.text(tx, ty, text, color=color, fontsize=fs, rotation=rot, ha=ha, va=va, zorder=8,
            bbox=dict(fc="white", ec="none", pad=1.5, alpha=0.9) if bg else None)

def label(ax, xy, txt, xytext, fs=FS, color="k", ha="left", va="center", ac=None):
    ax.annotate(txt, xy=xy, xytext=xytext, fontsize=fs, color=color, ha=ha, va=va, zorder=9,
                arrowprops=dict(arrowstyle="-|>", color=ac or color, lw=1.2, mutation_scale=14,
                                shrinkA=2, shrinkB=0),
                bbox=dict(fc="white", ec="none", pad=1.0, alpha=0.85))

def button_head(ax, x, ytop, up=True, horizontal=False, length=6.0, z=6):
    """ISO 7380 M3 button head: head d=5.7, k=1.65; shank 3.0."""
    s = 1 if up else -1
    if not horizontal:
        # head sits above ytop (outside), shank goes down 'length'
        ax.add_patch(Polygon([(x-2.85, ytop), (x+2.85, ytop), (x+2.0, ytop+s*1.65), (x-2.0, ytop+s*1.65)],
                             closed=True, fc=C_SCR, ec="k", lw=1, zorder=z))
        rect(ax, x-1.5, ytop - s*length if up else ytop, 3.0, length, C_SCR, z=z-0.5, lw=0.8)
