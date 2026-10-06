"""收敛判定三档：|δ|≤内缘 合格；内缘<|δ|≤外缘 近阈（琥珀区）；|δ|>外缘 才算超限。"""
DEFAULT_INNER_MM = 3.0  # 合格带内缘（±3.0 mm）
DEFAULT_OUTER_MM = 3.4  # 琥珀近阈区外缘（±3.4 mm）


def judge(
    delta_mm: float,
    inner_mm: float = DEFAULT_INNER_MM,
    outer_mm: float = DEFAULT_OUTER_MM,
) -> tuple[str, str]:
    a = abs(delta_mm)
    if a <= inner_mm:
        return "合格", f"收敛 {delta_mm} mm 在合格带 ±{inner_mm} mm 以内"
    if a <= outer_mm:
        return (
            "近阈",
            f"收敛 {delta_mm} mm 越内缘 ±{inner_mm} mm、未出外缘 ±{outer_mm} mm，落入琥珀区标近阈",
        )
    return "超限", f"收敛 {delta_mm} mm 超出外缘 ±{outer_mm} mm"
