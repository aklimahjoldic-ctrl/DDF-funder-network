import itertools, math
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D

OUT = "DDF_funder_network.png"
DDF = "Doris Duke Foundation"

# (program, DDF area, total pool $M or None if unpublished, partner funders)
P = [
 ("Humanity AI", "Cross-cutting", 500, ["Ford", "Lumina", "Kapor", "MacArthur", "Mellon", "Mozilla", "Omidyar Network", "Packard", "Siegel Family Endowment"]),
 ("Tribal Nations Conservation Pledge", "Environment", 102.5, ["Alaska Conservation Fdn", "Christensen Fund", "Decolonizing Wealth Project", "Moore", "Grousemont", "J.M. Kaplan Fund", "Packard", "Resources Legacy Fund", "Re:wild", "Walton Family", "Water Foundation", "Wilburforce", "Hewlett", "Wyss"]),
 ("National Dance Project", "Arts", 38.5, ["Mellon", "Aliad Fund"]),
 ("Opt-in for Families", "Child Well-being", 33, ["Duke Endowment", "Aviv Foundation"]),
 ("Artist Relief", "Arts", 25, ["Mellon", "Rauschenberg", "Knight", "Open Society"]),
 ("Fund to Retain Clinical Scientists", "Medical Research", 12.1, ["American Heart Assn", "Burroughs Wellcome", "Templeton", "Rita Allen", "Walder"]),
 ("Artists Make Technology", "Arts", 11, ["Mozilla", "Hewlett", "Ford", "MacArthur", "Omidyar Network"]),
 ("Institutional Challenge Grants", "Child Well-being", 7.8, ["W.T. Grant", "Spencer", "Bezos Family", "Annie E. Casey"]),
 ("Tech Infrastructure Grants", "Arts", 4, ["Ford"]),
 ("Performing Artist Recovery Fund", "Arts", 3, ["NY Community Trust"]),
 ("Land and Climate Program", "Environment", 1.2, ["J.M. Kaplan Fund", "Jane's Trust", "Merck Family Fdn", "Oregon Community Fdn", "Volgenau", "William Penn"]),
 ("Mosaic Network and Fund", "Arts", None, ["Mellon", "Ford", "Bloomberg", "Rockefeller Brothers", "Surdna", "Stavros Niarchos", "Jerome", "Mertz Gilmore", "Altman", "Howard Gilman", "NY Community Trust"]),
 ("Collective for Health Research", "Medical Research", None, ["American Cancer Society", "American Heart Assn", "Burroughs Wellcome", "Dana Foundation", "Donaghue", "Prebys", "Robertson", "Susan G. Komen"]),
]

AREA_COLOR = {
    "Arts": "#257de0",
    "Child Well-being": "#f47230",
    "Medical Research": "#00b894",
    "Cross-cutting": "#f2a600",
    "Environment": "#008a17",
    "Multiple areas": "#8c8c8c",
}
INK, INK2, FAINT = "#1a1a1a", "#6b6b6b", "#d9d9d9"
CO = "#b8b8b8"
UNPUB = 0.5  # stand-in weight ($M) for programs with no published pool

# DDF spokes: total pool of shared programs; partner-partner: co-funding ties (layout + faint lines)
spoke = {}
areas = {}
nprog = {}
known = {}
pair = {}
pair_known = {}
pair_lay = {}
for name, area, pool, funders in P:
    w = pool if pool is not None else UNPUB
    for f in funders:
        spoke[f] = spoke.get(f, 0) + w
        areas.setdefault(f, set()).add(area)
        nprog[f] = nprog.get(f, 0) + 1
        known[f] = known.get(f, False) or pool is not None
    for a, b in itertools.combinations(sorted(set(funders)), 2):
        pair[(a, b)] = pair.get((a, b), 0) + w
        pair_known[(a, b)] = pair_known.get((a, b), False) or pool is not None
        pair_lay[(a, b)] = pair_lay.get((a, b), 0) + 3.0 / (len(funders) - 1)

G = nx.Graph()
G.add_node(DDF)
for f, w in spoke.items():
    G.add_edge(DDF, f, w=w, kind="spoke")
for (a, b), w in pair.items():
    G.add_edge(a, b, w=w, kind="co", lay=pair_lay[(a, b)])

# Layout: spring, edge attraction grows with log of funding
for u, v, d in G.edges(data=True):
    d["lw"] = 0.3 * (math.log10(d["w"] + 1) + 0.3) if d["kind"] == "spoke" else d["lay"]
pos = nx.spring_layout(G, weight="lw", k=1.2, iterations=1000, seed=7)

fig, ax = plt.subplots(figsize=(19, 12), dpi=200)
fig.patch.set_facecolor("white")
ax.set_facecolor("white")
ax.axis("off")

# DDF spokes: width ~ log total pool
def width(w):
    return 0.6 + 2.4 * math.log10(w + 1)

# co-funding ties between partners: same width scale, lighter ink
for (a, b), w in pair.items():
    style = "solid" if pair_known[(a, b)] else (0, (2, 2))
    nx.draw_networkx_edges(G, pos, edgelist=[(a, b)], width=width(w) * 0.6,
                           edge_color=CO, alpha=0.45, style=style, ax=ax)

# program name at the center of each cluster
import statistics
for name, area, pool, funders in P:
    xs = [pos[f][0] for f in funders]; ys = [pos[f][1] for f in funders]
    if len(funders) < 2:
        continue
    cx, cy = statistics.mean(xs), statistics.mean(ys)
    dx, dy = cx - pos[DDF][0], cy - pos[DDF][1]
    r = math.hypot(dx, dy) or 1
    mx = max(math.hypot(pos[f][0]-pos[DDF][0], pos[f][1]-pos[DDF][1]) for f in funders)
    ax.text(pos[DDF][0] + dx / r * (mx + 0.08), pos[DDF][1] + dy / r * (mx + 0.08), name, fontsize=9, color=INK2, style="italic", fontweight="bold",
            ha="center", va="center", zorder=6,
            path_effects=[pe.withStroke(linewidth=3, foreground="white")])
for f in spoke:
    style = "solid" if known[f] else (0, (2, 2))
    nx.draw_networkx_edges(G, pos, edgelist=[(DDF, f)], width=width(spoke[f]),
                           edge_color="#5a5a5a", alpha=0.55, style=style, ax=ax)

# nodes
for f in spoke:
    a = areas[f]
    c = AREA_COLOR[next(iter(a))] if len(a) == 1 else AREA_COLOR["Multiple areas"]
    nx.draw_networkx_nodes(G, pos, nodelist=[f], node_size=90 + 110 * nprog[f],
                           node_color=c, edgecolors="white", linewidths=1.5, ax=ax)
nx.draw_networkx_nodes(G, pos, nodelist=[DDF], node_size=2600, node_color=INK,
                       edgecolors="white", linewidths=2, ax=ax)

# labels
for n, (x, y) in pos.items():
    if n == DDF:
        ax.text(x, y, "Doris Duke\nFoundation", color="white", fontsize=8, fontweight="bold",
                ha="center", va="center", zorder=5)
    else:
        ax.text(x, y - 0.035, n, color=INK, fontsize=7.5, ha="center", va="top", zorder=5, path_effects=[pe.withStroke(linewidth=2.5, foreground="white")])

ax.set_title("Who the Doris Duke Foundation pools funds with", loc="left", fontsize=18,
             color=INK, fontweight="bold", pad=28)
ax.text(0, 1.012, "Funders that co-funded at least one of 13 pooled or co-funded programs with DDF. Data from DDF and partner press releases, 2018–2026.",
        transform=ax.transAxes, fontsize=10, color=INK2)

legend = [Line2D([0], [0], marker="o", color="w", markerfacecolor=c, markersize=9, label=a)
          for a, c in AREA_COLOR.items()]
legend += [Line2D([0], [0], color="#5a5a5a", lw=width(5), alpha=0.55, label="$5M pool"),
           Line2D([0], [0], color="#5a5a5a", lw=width(100), alpha=0.55, label="$100M pool"),
           Line2D([0], [0], color="#5a5a5a", lw=width(500), alpha=0.55, label="$500M pool"),
           Line2D([0], [0], color="#5a5a5a", lw=1.2, ls=(0, (2, 2)), label="Pool size unpublished"),
           Line2D([0], [0], color=CO, lw=2, alpha=0.6, label="Partners co-funding the same program")]
leg = ax.legend(handles=legend, loc="lower left", frameon=False, fontsize=8.5, title="DDF program area  ·  edge width",
                title_fontsize=9, labelcolor=INK, ncol=1, bbox_to_anchor=(1.0, 0.0))
leg.get_title().set_color(INK2)

fig.text(0.012, 0.012,
         "Node size = number of programs shared with DDF. Edge width = total pool of shared programs (log scale); dark edges link to DDF, light edges link partners in the same program; DDF's own share is rarely published. "
         "Layout: spring (force-directed). Mosaic Fund shows 11 of its 27 donors.",
         fontsize=8, color=INK2)
plt.tight_layout(rect=(0.02, 0.03, 0.88, 1))
plt.savefig(OUT, facecolor="white")
print("saved", OUT, G.number_of_nodes(), "nodes")
