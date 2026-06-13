"""CasADi compatibility shim for GP-MPC dynamics (SSI-MPC + CasADi >= 3.6).

GP-augmented dynamics keep gp_x / trigger as free symbols when building x_dot.
Newer CasADi rejects that unless allow_free is set on Function creation.
"""


def apply_casadi_gp_compat() -> None:
    import casadi as cs

    if getattr(cs.Function, "_paper_repro_gp_patched", False):
        return

    original = cs.Function

    def function_with_allow_free(*args, **kwargs):
        try:
            return original(*args, **kwargs)
        except RuntimeError as exc:
            if "free" not in str(exc):
                raise
            return original(*args, {"allow_free": True})

    function_with_allow_free._paper_repro_gp_patched = True  # type: ignore[attr-defined]
    cs.Function = function_with_allow_free
