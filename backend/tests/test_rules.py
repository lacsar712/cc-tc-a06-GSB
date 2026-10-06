"""判定规则：三档边界、自定义带、文案引用传入的界。"""
import pytest

from rules import LIMIT_MM, classify, judge

BAND_30_34 = [
    (0.0, "合格"),
    (3.0, "合格"),
    (-3.0, "合格"),
    (1.2, "合格"),
    (3.2, "近阈"),
    (-3.2, "近阈"),
    (3.4, "近阈"),
    (-3.4, "近阈"),
    (3.4000001, "超限"),
    (3.8, "超限"),
    (-3.8, "超限"),
    (5.6, "超限"),
]


@pytest.mark.parametrize("delta, expected", BAND_30_34)
def test_default_band_boundaries(delta, expected):
    assert classify(delta) == expected
    assert judge(delta)[0] == expected


def test_acceptance_cases():
    # 题面验收：3.2 必须近阈（不是超限），3.8 必须超限。
    assert classify(3.2) == "近阈"
    assert classify(3.8) == "超限"


def test_legacy_constant_and_seed_compat():
    assert LIMIT_MM == 3.0
    assert judge(1.2) == ("合格", "收敛 1.2 mm 在 ±3 mm 以内")
    assert judge(5.6)[0] == "超限"


def test_custom_band():
    assert classify(3.7, 3.5, 4.0) == "近阈"
    assert classify(3.5, 3.5, 4.0) == "合格"
    assert classify(4.0, 3.5, 4.0) == "近阈"


def test_reason_cites_given_bounds():
    verdict, reason = judge(3.2, 3.0, 3.4)
    assert verdict == "近阈"
    assert "±3" in reason and "±3.4" in reason and "允许进队" in reason

    _, reason_over = judge(3.8, 3.0, 3.4)
    assert "超过外缘 ±3.4 mm" in reason_over


def test_no_float_garbage_in_reason():
    _, reason = judge(3.2, 3.0, 3.4)
    assert "3.3999" not in reason
