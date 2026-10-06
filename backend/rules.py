"""收敛判定：合格 / 近阈（琥珀带）/ 超限 三档。

|Δ| ≤ 内缘          合格
内缘 < |Δ| ≤ 外缘  近阈（琥珀带，仍可进队）
|Δ| > 外缘          超限

内缘、外缘可由监理在琥珀专页调整，默认 3.0 / 3.4 mm。
每行单据在提交时快照当时的内缘/外缘，认领时按快照判定（见 claimer.py）。
"""
import math

DEFAULT_INNER_MM = 3.0
DEFAULT_OUTER_MM = 3.4
# 兼容旧引用：3.0 仍是合格带的界（近阈带内缘）。
LIMIT_MM = DEFAULT_INNER_MM

OK = "合格"
NEAR = "近阈"
OVER = "超限"


def _mm(value) -> str:
    """最多两位小数、去尾零：3.0 -> '3'，3.40 -> '3.4'，3.25 -> '3.25'。"""
    return f"{float(value):.2f}".rstrip("0").rstrip(".")


def classify(delta_mm, inner_mm: float = DEFAULT_INNER_MM, outer_mm: float = DEFAULT_OUTER_MM) -> str:
    """按给定内缘/外缘返回 合格 / 近阈 / 超限。"""
    absolute = abs(float(delta_mm))
    if absolute <= float(inner_mm):
        return OK
    if absolute <= float(outer_mm):
        return NEAR
    return OVER


def judge(delta_mm, inner_mm: float = DEFAULT_INNER_MM, outer_mm: float = DEFAULT_OUTER_MM) -> tuple[str, str]:
    """按给定内缘/外缘判定，返回 (结论, 说明文案)。文案引用传入的界（通常是行快照）。"""
    verdict = classify(delta_mm, inner_mm, outer_mm)
    delta = _mm(delta_mm)
    inner = _mm(inner_mm)
    outer = _mm(outer_mm)
    if verdict == OK:
        reason = f"收敛 {delta} mm 在 ±{inner} mm 以内"
    elif verdict == NEAR:
        reason = f"收敛 {delta} mm 位于近阈带（±{inner}～±{outer} mm），允许进队"
    else:
        reason = f"收敛 {delta} mm 超过外缘 ±{outer} mm"
    return verdict, reason


def valid_bounds(inner_mm, outer_mm) -> tuple[bool, str]:
    """改带入参校验：有限、非负、内缘 < 外缘。"""
    try:
        inner = float(inner_mm)
        outer = float(outer_mm)
    except (TypeError, ValueError):
        return False, "内缘/外缘必须是数字"
    if not (math.isfinite(inner) and math.isfinite(outer)):
        return False, "内缘/外缘必须是有限数值"
    if inner < 0 or outer < 0:
        return False, "内缘/外缘不能为负"
    if not (inner < outer):
        return False, "要求 0 ≤ 内缘 < 外缘"
    return True, ""
