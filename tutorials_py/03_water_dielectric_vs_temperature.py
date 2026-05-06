"""
물의 유전상수(dielectric constant, ε) vs 온도 그래프
====================================================

목적: 3350 psi 일정 압력에서 20°C ~ 500°C 범위 동안 순수한 물의
유전상수가 온도에 따라 어떻게 변하는지를 그래프로 그린다.

배경 (쉬운 말):
- 유전상수(ε)는 매질이 전기장을 얼마나 약화시키는지 나타내는 값.
- 상온의 물은 ε ≈ 78~80으로 매우 큼 → 이온을 잘 녹임 (소금이 잘 녹는 이유).
- 온도가 올라가면 분자가 격렬히 움직여 전기장 정렬이 깨져 ε이 급감함.
- 임계점(약 374°C, 22 MPa) 근처에서 변화가 가장 가파름.
- 3350 psi (≈ 23.1 MPa)는 임계압력보다 약간 높아서, 20~500°C 전 구간에서
  물이 끓지 않고 단일 유체상으로 매끄럽게 이어짐 → 깨끗한 곡선이 나옴.

사용 함수 (Reaktoro 저수준 API):
- waterThermoPropsWagnerPruss : IAPWS-95 기반 열역학 특성 (밀도 등)
- waterElectroPropsJohnsonNorton : 위 결과를 받아 유전상수(ε) 등 전기특성 계산
"""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from reaktoro import (
    waterThermoPropsWagnerPruss,
    waterElectroPropsJohnsonNorton,
    StateOfMatter,
)


# ---------------------------------------------------------------------------
# 1) 단위 변환 헬퍼 (입력은 익숙한 °C / psi, Reaktoro 내부는 K / Pa)
# ---------------------------------------------------------------------------
def celsius_to_kelvin(T_C: float) -> float:
    """섭씨 → 켈빈"""
    return T_C + 273.15


def psi_to_pascal(P_psi: float) -> float:
    """psi → Pa (1 psi = 6894.757 Pa)"""
    return P_psi * 6894.757


# 물의 임계온도 (IAPWS-95 기준, 단위: °C)
T_CRITICAL_C = 373.946

# 임계점 근처에서 Wagner-Pruss 액체 분기가 수치적으로 진동하는 구간.
# 이 구간(372~380°C)은 양 끝의 안정된 값으로 매끄럽게 보간한다.
T_BLEND_LOW_C = 372.0   # 이 아래는 Liquid 분기가 안정
T_BLEND_HIGH_C = 380.0  # 이 위는 두 분기가 합쳐짐 (Supercritical 사용)


def _epsilon_raw(T_C: float, P_psi: float, som: "StateOfMatter") -> float:
    """주어진 분기(StateOfMatter)로 ε을 계산하는 저수준 헬퍼."""
    T_K = celsius_to_kelvin(T_C)
    P_Pa = psi_to_pascal(P_psi)
    wtp = waterThermoPropsWagnerPruss(T_K, P_Pa, som)
    wep = waterElectroPropsJohnsonNorton(T_K, P_Pa, wtp)
    return wep.epsilon


# ---------------------------------------------------------------------------
# 2) 단일 (T, P)에서 물의 유전상수 계산
# ---------------------------------------------------------------------------
def water_dielectric(T_C: float, P_psi: float) -> float:
    """
    주어진 온도(°C)·압력(psi)에서 순수한 물의 유전상수 ε을 반환.

    분기 선택과 임계점 근처 보간(중요):
      Wagner-Pruss는 액체/기체 분기를 갖고, `StateOfMatter` 인자는 어느
      분기를 따라갈지의 힌트다. 임계압 위(여기서는 23.1 MPa > 22.06 MPa)에서는
      이론적으로 단일 매끄러운 곡선이 나와야 하지만, EOS 액체 분기가 임계점
      바로 근처(약 372~380°C)에서 수치적으로 진동(dip)한다. 처리 방법:

        - T ≤ 372°C            : Liquid 분기      (안정된 압축액체)
        - T ≥ 380°C            : Supercritical 분기 (안정, 두 분기 합쳐짐)
        - 372°C < T < 380°C    : 양 끝점을 직선 보간 (진동 우회)
    """
    if T_C <= T_BLEND_LOW_C:
        return _epsilon_raw(T_C, P_psi, StateOfMatter.Liquid)
    if T_C >= T_BLEND_HIGH_C:
        return _epsilon_raw(T_C, P_psi, StateOfMatter.Supercritical)

    # 보간 구간: 양 끝점의 안정된 값을 직선으로 잇는다.
    eps_low = _epsilon_raw(T_BLEND_LOW_C, P_psi, StateOfMatter.Liquid)
    eps_high = _epsilon_raw(T_BLEND_HIGH_C, P_psi, StateOfMatter.Supercritical)
    w = (T_C - T_BLEND_LOW_C) / (T_BLEND_HIGH_C - T_BLEND_LOW_C)
    return (1.0 - w) * eps_low + w * eps_high


# ---------------------------------------------------------------------------
# 3) 메인 — 곡선 계산 + 그래프 그리기 + PNG 저장
# ---------------------------------------------------------------------------
def main() -> None:
    # 조건 확인용 출력
    P_psi = 3350.0
    P_MPa = psi_to_pascal(P_psi) / 1e6
    print(f"압력: {P_psi:.0f} psi ≈ {P_MPa:.3f} MPa "
          f"(임계압 22.06 MPa보다 약간 높음 → 단일 유체상)")

    # 온도 그리드 (20 ~ 500 °C, 200점)
    T_C = np.linspace(20.0, 500.0, 200)

    # 각 온도에서 ε 계산
    epsilons = np.array([water_dielectric(T, P_psi) for T in T_C])

    # 빠른 검증 출력 (계획서의 sanity-check 값과 비교)
    for T_check in (25.0, 100.0, 200.0, 374.0, 500.0):
        eps_check = water_dielectric(T_check, P_psi)
        print(f"  T = {T_check:6.1f} °C  →  ε = {eps_check:7.3f}")

    # ---- 그래프 그리기 ----
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(T_C, epsilons, color="#1f4e79", linewidth=2.0,
            label=f"Water  (P = {P_psi:.0f} psi ≈ {P_MPa:.1f} MPa)")

    # 임계온도(374°C) 점선 표시
    ax.axvline(T_CRITICAL_C, color="crimson", linestyle="--", linewidth=1.2,
               label=f"Critical point ({T_CRITICAL_C:.1f} °C)")

    ax.set_xlabel("Temperature  (°C)")
    ax.set_ylabel("Dielectric constant  ε  (dimensionless)")
    ax.set_title("Dielectric constant of water vs. temperature")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right")
    fig.tight_layout()

    # ---- PNG 저장 ----
    out_dir = Path(__file__).resolve().parent.parent / "plots"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "water_dielectric_3350psi.png"
    fig.savefig(out_path, dpi=150)
    print(f"\nPNG 저장됨: {out_path}")

    # ---- 화면 표시 ----
    plt.show()


if __name__ == "__main__":
    main()
