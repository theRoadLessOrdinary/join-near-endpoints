#!/usr/bin/env python3
"""
Join Near Endpoints

Select one or more paths, then run this. Inside each selected path, every
pair of open subpath ends that sit closer together than the tolerance is
joined into one node, so the pieces become one continuous subpath. The
joined node goes halfway between the two old ends, and the Bezier handles
on each side move with it, so curve shapes are kept.

Each end is joined at most once, nearest pairs first. A piece whose ends
lead back around to its own start becomes a closed subpath. Pieces are
reversed where needed so the joined subpath runs one way. Closed subpaths
and ends with no partner in range are left as they are.

Only subpaths inside the same path are joined. The tolerance is measured
on the canvas in millimeters, after any transforms on the path and its
groups.
"""
import math

import inkex
from inkex import EffectExtension, PathElement
from inkex.paths import Curve, Line, Move, Path, ZoneClose

EPS = 1e-9
NODETYPES = "sodipodi:nodetypes"

HOW_TO = "Select one or more paths, then run this again."


def shift(p, d):
    return [p[0] + d[0], p[1] + d[1]]


def reverse_sub(sub):
    """CubicSuperPath subpath with its direction flipped."""
    return [[n[2], n[1], n[0]] for n in reversed(sub)]


def merge_nodes(a, b):
    """Join node a (end of one piece) and node b (start of the next) at their
    midpoint. a keeps its incoming handle, b keeps its outgoing handle."""
    mid = [(a[1][0] + b[1][0]) / 2, (a[1][1] + b[1][1]) / 2]
    da = (mid[0] - a[1][0], mid[1] - a[1][1])
    db = (mid[0] - b[1][0], mid[1] - b[1][1])
    return [shift(a[0], da), mid, shift(b[2], db)]


def same(a, b):
    return abs(a[0] - b[0]) < EPS and abs(a[1] - b[1]) < EPS


def is_closed(sub):
    return len(sub) > 2 and same(sub[0][1], sub[-1][1])


def to_path(subs):
    """subs: list of (nodes, closed). Straight segments are written as lines."""
    out = Path()
    for nodes, closed in subs:
        out.append(Move(*nodes[0][1]))
        for prev, cur in zip(nodes, nodes[1:]):
            if same(prev[2], prev[1]) and same(cur[0], cur[1]):
                out.append(Line(*cur[1]))
            else:
                out.append(Curve(*prev[2], *cur[0], *cur[1]))
        if closed:
            out.append(ZoneClose())
    return out


class JoinNearEndpoints(EffectExtension):
    def add_arguments(self, pars):
        pars.add_argument("--tolerance", type=float, default=0.3)

    def effect(self):
        paths = [el for el in self.svg.selection.values() if isinstance(el, PathElement)]
        if not paths:
            raise inkex.AbortExtension(HOW_TO)
        tol = self.svg.viewport_to_unit(f"{self.options.tolerance}mm")
        total = 0
        for el in paths:
            total += self.join(el, tol)
        if total == 0:
            inkex.errormsg(
                f"No subpath ends were closer than {self.options.tolerance} mm. Nothing changed."
            )

    def join(self, el, tol):
        csp = el.path.to_absolute().to_superpath()
        subs = [list(s) for s in csp if len(s) > 0]
        transform = el.composed_transform()

        def canvas(p):
            return transform.apply_to_point(p)

        open_ids = [i for i, s in enumerate(subs) if len(s) > 1 and not is_closed(s)]

        # Ends are (subpath index, 0 = start / 1 = end).
        ends = []
        for i in open_ids:
            ends.append((i, 0, canvas(subs[i][0][1])))
            ends.append((i, 1, canvas(subs[i][-1][1])))

        pairs = []
        for a in range(len(ends)):
            for b in range(a + 1, len(ends)):
                ea, eb = ends[a], ends[b]
                if ea[0] == eb[0] and len(subs[ea[0]]) < 3:
                    continue  # a single segment can't close on itself
                d = math.hypot(ea[2].x - eb[2].x, ea[2].y - eb[2].y)
                if d < tol:
                    pairs.append((d, ea[:2], eb[:2]))
        pairs.sort(key=lambda p: p[0])

        partner = {}
        for _d, a, b in pairs:
            if a in partner or b in partner:
                continue
            partner[a] = b
            partner[b] = a
        if not partner:
            return 0

        # Walk each chain of pieces. Start from pieces with a free end first,
        # then whatever is left is a loop.
        used = set()
        result = {}  # first subpath index of the chain -> (nodes, closed)

        def walk(start, start_end):
            """Follow the chain from piece `start`, entering at `start_end`."""
            nodes = None
            first = start
            idx, entry = start, start_end
            while True:
                used.add(idx)
                piece = subs[idx] if entry == 0 else reverse_sub(subs[idx])
                if nodes is None:
                    nodes = list(piece)
                else:
                    nodes = nodes[:-1] + [merge_nodes(nodes[-1], piece[0])] + piece[1:]
                exit_end = 1 - entry
                nxt = partner.get((idx, exit_end))
                if nxt is None:
                    return first, nodes, False
                if nxt[0] in used:
                    # Back at the start: close the loop.
                    m = merge_nodes(nodes[-1], nodes[0])
                    nodes[0] = [m[1], m[1], m[2]]
                    nodes[-1] = [m[0], m[1], m[1]]
                    return first, nodes, True
                idx, entry = nxt

        for i in open_ids:
            if i in used:
                continue
            if (i, 0) not in partner:
                first, nodes, closed = walk(i, 0)
            elif (i, 1) not in partner:
                first, nodes, closed = walk(i, 1)
            else:
                continue
            result[first] = (nodes, closed)
        for i in open_ids:
            if i not in used and (i, 0) in partner:
                first, nodes, closed = walk(i, 0)
                result[first] = (nodes, closed)

        out = []
        for i, s in enumerate(subs):
            if i in result:
                out.append(result[i])
            elif i not in used:
                out.append((s, is_closed(s)))
        el.path = to_path(out)
        if el.get(NODETYPES) is not None:
            el.set(NODETYPES, None)
        return len(partner) // 2


if __name__ == "__main__":
    JoinNearEndpoints().run()
