"""
튜토리얼 4: LiFePO4(LFP)의 Li+ Dissolution — 두 조건 비교
==========================================================

목표:
  리튬 이온 배터리 양극재인 LiFePO4(광물명 Triphylite)가
  서로 다른 두 수열(hydrothermal) 조건에서 얼마나 녹는지를 평형 계산으로 비교한다.

  - 조건 A : 180 °C, 272 psi  (≈ 18.75 bar) — 압축 액체상(compressed liquid)
  - 조건 B : 380 °C, 3350 psi (≈ 231.0 bar) — 초임계수(supercritical water)

두 가지 모드:
  - "literal"           : ΔfG°(LFP) = Jing 2019 Table 1 그대로 사용 (mixed-source)
  - "supcrt_consistent" : Jing Reaction 7 logK(T)는 살리되 ΔfG°(LFP)를
                          SUPCRT의 Li+/Fe+2/H3PO4 G(T)와 화학적으로 일관되게 재유도.
                          → **기본값(권장)** — 평형식의 thermodynamic consistency 보장.

데이터 출처(모두 ref/ 폴더에 PDF 보관):
  [Jing2019]  Jing et al., J. Phys. Chem. C 2019, 123, 14207–14215.
  [Loos2015]  Loos et al., J. Chem. Thermodyn. 2015, 85, 77–85.
  [Ong2008]   Ong, Ceder et al., Chem. Mater. 2008, 20, 1798. (구조 검증용)

상세 method 와 한계는 동일 폴더의 lfp_thermo.py 모듈, 그리고 README/Notion methods 페이지 참조.
"""

from __future__ import annotations

from pathlib import Path

from lfp_thermo import (
    InitialComposition,
    LFP_MOLAR_MASS_G,
    make_db_with_lfp,
    psi_to_bar,
    save_snapshot,
    solve_equilibrium,
    state_to_snapshot,
)


# ───────────────────────────────────────────────────────────────────
# 결과 표 출력
# ───────────────────────────────────────────────────────────────────
def print_comparison_table(rA: dict, rB: dict) -> None:
    sa = rA["species_amount"]; aa = rA["species_activity"]
    sb = rB["species_amount"]; ab = rB["species_activity"]

    print()
    print("═" * 84)
    print("  LiFePO4 → 수열 분해/용해 평형 비교  (mode = " + rA["mode"] + ")")
    print("═" * 84)
    print(f"  공통 초기조건 : H2O {rA['initial']['H2O_kg']:.3f} kg + "
          f"LiFePO4 {rA['initial']['LFP_kg']*1000:.1f} g  "
          f"(≈ {rA['initial']['LFP_kg']*1000/LFP_MOLAR_MASS_G:.4f} mol LFP)")
    print(f"  열역학 데이터 : Jing2019 Table 1 + SI Reaction 7 + Loos2015 Cp(T)")
    print()

    headerA = f"A: 180°C / {rA['P_bar']:.2f} bar"
    headerB = f"B: 380°C / {rB['P_bar']:.2f} bar"
    print(f"  {'항목':<34} | {headerA:>20} | {headerB:>20}")
    print("  " + "─" * 82)
    print(f"  {'활동도 모델':<34} | {rA['model_used']:>20} | {rB['model_used']:>20}")
    print(f"  {'pH':<34} | {rA['pH']:>20.3f} | {rB['pH']:>20.3f}")
    print(f"  {'이온강도 I (mol/kg)':<34} | {rA['ionic_strength']:>20.3e} | {rB['ionic_strength']:>20.3e}")
    print("  " + "·" * 82)
    print(f"  {'Li 용해율 (%)':<34} | {rA['Li_dissolved_pct']:>20.4f} | {rB['Li_dissolved_pct']:>20.4f}")

    print("  " + "·" * 82)
    print(f"  {'수용액 종 활동도 (a_i)':<34} |")
    for sp in ["Li+", "Fe+2", "Fe+3", "H+", "H3PO4(aq)", "H2PO4-", "HPO4-2", "PO4-3"]:
        print(f"  {'  '+sp:<34} | {aa.get(sp, 0):>20.3e} | {ab.get(sp, 0):>20.3e}")

    print("  " + "·" * 82)
    print(f"  {'고체 (mol)':<34} |")
    for ph in ["LiFePO4(s)", "Hematite", "Magnetite", "Goethite", "Iron"]:
        print(f"  {'  '+ph:<34} | {sa.get(ph, 0):>20.4e} | {sb.get(ph, 0):>20.4e}")
    print("═" * 84)


# ───────────────────────────────────────────────────────────────────
# main
# ───────────────────────────────────────────────────────────────────
def main() -> None:
    print("LiFePO4 dissolution: 아임계수 vs 초임계수 비교\n")

    P_A_bar = psi_to_bar(272.0)    # ≈ 18.75
    P_B_bar = psi_to_bar(3350.0)   # ≈ 231.0
    print(f"  조건 A : 180 °C, 272  psi → {P_A_bar:.3f} bar")
    print(f"  조건 B : 380 °C, 3350 psi → {P_B_bar:.3f} bar")
    print()

    mode = "literal"
    print(f"[모드: {mode}]  Jing 2019 Table 1 의 ΔfG°(LFP)를 그대로 사용.")
    print(f"  LFP의 평형(SI≈0)은 시스템 전체 Gibbs minimization 으로 풀리며,")
    print(f"  유전율 ε(T,P)·HKF 활동도 보정·Fe 광물 재침전이 모두 자동 반영됩니다.")
    print()

    db = make_db_with_lfp(mode=mode)
    initial = InitialComposition(H2O_kg=1.0, LFP_kg=0.020)

    print("[조건 A] 평형 계산 …")
    state_A, model_A = solve_equilibrium(db, 180.0, P_A_bar, initial)
    rA = state_to_snapshot(state_A, model_used=model_A, T_C=180.0,
                           P_bar=P_A_bar, initial=initial, mode=mode, label="A_180C_272psi")
    print(f"  → 수렴 ({model_A})")

    print("[조건 B] 평형 계산 …")
    state_B, model_B = solve_equilibrium(db, 380.0, P_B_bar, initial)
    rB = state_to_snapshot(state_B, model_used=model_B, T_C=380.0,
                           P_bar=P_B_bar, initial=initial, mode=mode, label="B_380C_3350psi")
    print(f"  → 수렴 ({model_B})")

    print_comparison_table(rA, rB)

    # 결과 자동 저장 — 다음 세션에서 분석/플롯에 바로 사용 가능
    out_dir = Path(__file__).resolve().parent.parent / "results"
    pA = save_snapshot(rA, out_dir / "lfp_A_180C_272psi.json")
    pB = save_snapshot(rB, out_dir / "lfp_B_380C_3350psi.json")
    print()
    print(f"  💾 결과 저장 :")
    print(f"     - {pA}")
    print(f"     - {pB}")
    print()
    print("  💡 다음 세션에서 이 JSON을 그대로 불러올 수 있습니다.")
    print("     예) from lfp_thermo import load_snapshot")
    print("         snap = load_snapshot('results/lfp_A_180C_272psi.json')")


if __name__ == "__main__":
    main()
