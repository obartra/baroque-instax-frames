# SPDX-License-Identifier: MIT
"""Actual-mesh views for the eight floral Rococo print projects."""
import sys
import json
import os
from pathlib import Path
import numpy as np
from shapely import wkt
from matplotlib.patches import Polygon as Patch

from render_utils import *
from render_floral_utils import render
from functools import partial
render = partial(render, relief_shadows=True)
from build_catalog import read_project_mesh
from paths import ROOT, P

DS = json.loads(Path(os.environ.get("BAROQUE_DESIGNS_FILE", ROOT / "source/designs-current.json")).read_text())
GOLD = np.array([.82, .57, .22])
CHARCOAL = np.array([.22, .23, .24])


def load(d):
    q = P / d["id"]
    report = json.loads((q / "validation.json").read_text())
    project = P / (d["id"] + "-Instax-Mini-3-Magnets.3mf")
    white, black, back = [read_project_mesh(project, n) for n in (1, 2, 4)]
    front = [(white, WHITE), (black, CHARCOAL)]
    pic = picture(d["orientation"] == "portrait")
    magnets = [(cylinder(3, 3, [x, y, 1.5]), METAL) for x, y in report["magnet_centers_mm"]]
    rear = [(back, WHITE)] + magnets
    assembly = shifted(front, 3.6) + pic + rear
    gilt = shifted([(white, WHITE), (black, GOLD)], 3.6) + pic + rear
    return report, front, pic, rear, assembly, gilt


def fit(ax, d):
    q = P / d["id"]
    outer = wkt.loads((q / "outer.wkt").read_text())
    aperture = wkt.loads((q / "aperture.wkt").read_text())
    report = json.loads((q / "validation.json").read_text())
    def patch(poly, color, alpha=1, edge=None, lw=1):
        ax.add_patch(Patch(np.asarray(poly.exterior.coords), closed=True,
                           facecolor=color, edgecolor=edge or color, alpha=alpha, lw=lw))
    patch(outer, "#302e2b", .2)
    portrait = d["orientation"] == "portrait"
    film = np.array([[-27, -47], [27, -47], [27, 39], [-27, 39], [-27, -47]]) if portrait else np.array([[-47, -27], [39, -27], [39, 27], [-47, 27], [-47, -27]])
    image = np.array([[-23, -31], [23, -31], [23, 31], [-23, 31], [-23, -31]]) if portrait else np.array([[-31, -23], [31, -23], [31, 23], [-31, 23], [-31, -23]])
    patch(aperture.buffer(6.5, join_style=2 if d["shape"] in ("rectangle", "octagon") else 1), "#faf8f2")
    patch(aperture, "#82adc0", .85, "#48738b")
    if d.get("petal_overlap_regions_mm"):
        from build_floral_rococo import drawing, petal_overlap
        rgb,gold,solid,pix,cx,cy,factor=drawing(d)
        inner=aperture.buffer(6.5,join_style=2 if d["shape"] in ("rectangle","octagon") else 1)
        petals=petal_overlap(d,gold,cx,cy,report["drawing_mm_per_pixel"],inner,aperture)
        for petal in petals.geoms if hasattr(petals,"geoms") else [petals]:
            if not petal.is_empty:patch(petal,"#302e2b")
    ax.plot(*film.T, color="#c45e2b", lw=1.8, ls="--")
    ax.plot(*image.T, color="#48738b", lw=1, ls=":")
    for x, y in report["magnet_centers_mm"]:
        ax.add_patch(plt.Circle((x, y), 3, color="#a58749", alpha=.8))
    bounds = np.asarray(outer.bounds).reshape(2, 2)
    ax.set_xlim(bounds[0, 0] - 5, bounds[1, 0] + 5)
    ax.set_ylim(bounds[0, 1] - 5, bounds[1, 1] + 5)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(f"Uncut film hidden · {report['image_area_visible_percent']:.1f}% image visible\nDashed orange = full film; gold = magnets", fontsize=10)


def individual(d):
    report, front, pic, rear, assembly, gilt = load(d)
    fig, axes = plt.subplots(2, 3, figsize=(18, 12), dpi=150)
    views = [(axes[0, 0], assembly, 90, -90, "Actual mesh · front"),
             (axes[0, 1], assembly, 36, -66, "Assembled · layered relief"),
             (axes[0, 2], gilt, 36, -66, "Same mesh · gold study material"),
             (axes[1, 0], rear, -90, 90, "White back · three flush magnets"),
             (axes[1, 1], assembly, 7, -80, "Low angle · actual depth")]
    for ax, items, elev, azim, title in views:
        render(ax, items, elev, azim, width=900)
        ax.set_title(title, fontsize=11, weight="bold")
    fit(axes[1, 2], d)
    dims = report["front_dimensions_mm"]
    mat_note = "6.5 mm mat offset, locally overlapped by petals; 0.36 mm layer" if d.get("petal_overlap_regions_mm") else "6.5 mm even mat, 0.36 mm high"
    fig.suptitle(d["name"].upper() + " · PRINTABLE FLORAL ROCOCO STUDY", fontsize=21, weight="bold", y=.975)
    fig.text(.5, .035,
        f"{dims[0]:.1f} × {dims[1]:.1f} mm · Front height {report['front_bounds_mm'][1][2]:.1f} mm · "
        + mat_note + " · 3 magnets · Matching rounded-root PLA forks",
        ha="center", fontsize=10)
    fig.text(.5, .015, "Drawing-guided bas-relief and exact CAD mechanics · Synthetic photo illustration · Physical fit and durability untested", ha="center", fontsize=9)
    fig.subplots_adjust(top=.91, bottom=.075, left=.025, right=.975, wspace=.12, hspace=.20)
    fig.savefig(O / (d["id"] + "-actual-multiview.png"), facecolor=fig.get_facecolor())
    plt.close(fig)
    # Detailed oblique of real geometry, for reviewer inspection of petals.
    fig, axes = plt.subplots(1, 2, figsize=(14, 8), dpi=160)
    for ax, items, title in [(axes[0], assembly, d.get("front_material_label", "Black / white print materials")), (axes[1], gilt, "Same geometry · relief inspection")]:
        render(ax, items, 48, -72, width=1300)
        ax.set_title(title, fontsize=12)
    fig.suptitle(d["name"] + " · ACTUAL MESH", fontsize=20, weight="bold")
    fig.subplots_adjust(top=.90, bottom=.04, left=.025, right=.975, wspace=.08)
    fig.savefig(O / (d["id"] + "-actual-detail.png"), facecolor=fig.get_facecolor())
    plt.close(fig)
    print("RENDERED", d["id"], flush=True)


def overview():
    reports = [json.loads((P / d["id"] / "validation.json").read_text()) for d in DS]
    lo = np.min([r["front_bounds_mm"][0][:2] for r in reports], axis=0) - 3
    hi = np.max([r["front_bounds_mm"][1][:2] for r in reports], axis=0) + 3
    fig, axes = plt.subplots(2, 4, figsize=(21, 13), dpi=160)
    for ax, d in zip(axes.flat, DS):
        report, _, _, _, assembly, _ = load(d)
        render(ax, assembly, 90, -90, limits=(lo, hi), width=950)
        ax.set_title(f"{d['name']}\n{report['image_area_visible_percent']:.1f}% image visible", fontsize=12, weight="bold")
    fig.suptitle("EIGHT FLORAL ROCOCO INSTAX FRAMES · ACTUAL MESHES", fontsize=23, weight="bold", y=.97)
    fig.text(.5, .025, "Common scale · Full uncut Instax Mini sheets concealed · Even inner mats · Three concealed magnets · Modern Louis XV–inspired designs", ha="center", fontsize=11)
    fig.subplots_adjust(top=.90, bottom=.07, left=.02, right=.98, wspace=.09, hspace=.12)
    fig.savefig(O / "Eight-Floral-Rococo-Actual-Fronts.png", facecolor=fig.get_facecolor())
    plt.close(fig)
    print("OVERVIEW COMPLETE", flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "overview":
        overview()
    else:
        for d in DS:
            if len(sys.argv) == 1 or d["id"] in sys.argv[1:]:
                individual(d)
