from predicates import in_region


def progress_carry(w, o, *, span=0.5):
    return 1.0 + in_region(w, o.block, o.region) / span
