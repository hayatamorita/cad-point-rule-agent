"""Public synthetic *example* of legacy CAD helper code, for documentation only.

This is not an OCCT geometry implementation and never should be executed as a
production point-selection rule.
"""

def find_parallel_edge_on_closed_wire(wires, reference_edge):
    """Find parallel candidate edge on a closed loop (concept only)."""
    # Historic projects typically used TopExp_Explorer, TopAbs_EDGE,
    # BRepAdaptor_Curve and gp_Dir here.
    raise NotImplementedError("illustrative example only")
