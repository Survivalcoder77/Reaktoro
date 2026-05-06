"""
LiFePO4 dissolution 시뮬레이션의 핵심 도우미 모듈.

이 모듈을 다른 스크립트에서 import 해서 두 가지 모드로 시뮬레이션을 재현할 수 있다:
  - "literal"           : ΔfG°(LFP) = Jing2019 Table 1 그대로 사용 (다른 종은 SUPCRT).
                          → 기본값(권장). LFP가 SI≈0 (평형 포화) 를 만족하면서 시스템
                          전체의 Gibbs minimization 으로 자연스럽게 평형이 풀린다.
                          유전율(ε)·이온 활동도·재침전 등 비이상성 효과가 SUPCRT-HKF
                          activity 모델로 모두 반영된다.
  - "supcrt_consistent" : Jing2019 Reaction 7 logK(T)에 짝맞춰 ΔfG°(LFP)를 SUPCRT
                          Li⁺·Fe²⁺·H₃PO₄(aq) G°(T) 로 재유도. **주의**: 473 K 위로
                          외삽이 비물리적이고, SUPCRT-HKF 의 Fe²⁺ G°가 623 K 부터
                          폭주하는 한계 영역과 결합되면 비현실적인 결과(예: 380°C
                          에서 100% 용해) 를 줄 수 있음. 비교용/sanity-check 목적으로만 사용.

자세한 식은 04_lifepo4_dissolution_subcrit_vs_supercrit.py 의 docstring 참조.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
from reaktoro import (
    AggregateState,
    ActivityModelHKF,
    ActivityModelIdealAqueous,
    AqueousPhase,
    AqueousProps,
    ChemicalProps,
    ChemicalState,
    ChemicalSystem,
    ElementalComposition,
    EquilibriumSolver,
    MineralPhase,
    Species,
    StandardThermoModelInterpolation,
    StandardThermoModelParamsInterpolation,
    SupcrtDatabase,
    speciate,
)


# ───────────────────────────────────────────────────────────────────
# 0. 상수
# ───────────────────────────────────────────────────────────────────
R_GAS = 8.314462618          # J/(mol·K)
LN10 = float(np.log(10))
LFP_MOLAR_MASS_G = 157.756   # g/mol


# ───────────────────────────────────────────────────────────────────
# 1. 단위 변환
# ───────────────────────────────────────────────────────────────────
def psi_to_bar(p_psi: float) -> float:
    """psi → bar (1 psi = 0.0689476 bar)"""
    return p_psi * 0.0689476


# ───────────────────────────────────────────────────────────────────
# 2. 문헌값 — Jing 2019 Table 1 + Loos 2015 Table 7
# ───────────────────────────────────────────────────────────────────
# Jing 2019 Table 1 — ΔfG°(LiFePO4) at four temperatures (J/mol)
JING_T_K = np.array([298.15, 363.15, 423.15, 473.15])
JING_DGF = np.array([-1480.97, -1490.71, -1501.13, -1510.79]) * 1000.0

# Jing 2019 SI Table S1 #7 — pH = a(T) − (1/3) lg([Li+][Fe2+][H3PO4])
#   ⇒ logK_R7(T) = 3 · a(T)
JING_R7_INTERCEPT = np.array([0.6137, -1.4679, -2.8112, -3.6776])
JING_R7_LOGK = 3.0 * JING_R7_INTERCEPT

# Loos 2015 Table 7 — Cp(T) [J/(K·mol)] for 300–773 K
LOOS_A0, LOOS_A1, LOOS_A2 = -41.881336, 0.78278483, -0.0010255433
LOOS_A3, LOOS_A4 = 5.0862948e-7, 890694.39
LOOS_S298 = 130.95   # J/(K·mol)


def cp_lfp(T_K) -> np.ndarray:
    """LiFePO4의 Cp(T)  [J/(K·mol)]  (Loos 2015 eq. 6)"""
    T = np.asarray(T_K, dtype=float)
    return LOOS_A0 + LOOS_A1*T + LOOS_A2*T*T + LOOS_A3*T**3 + LOOS_A4/(T*T)


# ───────────────────────────────────────────────────────────────────
# 3. ΔfG° 그리드 만들기 — 두 모드 지원
# ───────────────────────────────────────────────────────────────────
DEFAULT_T_GRID_K = np.array([298.15, 363.15, 423.15, 453.15,
                             473.15, 543.15, 623.15, 653.15])


def build_lfp_dgf_grid(
    mode: Literal["literal", "supcrt_consistent"] = "literal",
    T_grid: np.ndarray | None = None,
    db: SupcrtDatabase | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    LiFePO4의 ΔfG°(T) 그리드를 반환.

    Parameters
    ----------
    mode :
        "literal"           : Jing Table 1 의 4점 + 3차 다항식 외삽.
        "supcrt_consistent" : Jing Reaction 7 logK(T) 4점 + 2차 다항식 외삽 후
                              SUPCRT 종 G°(T) 와 결합해 ΔfG°(LFP, T) 재유도.
    T_grid :
        ΔfG°를 평가할 온도 격자(K). None 이면 DEFAULT_T_GRID_K.
    db :
        "supcrt_consistent" 모드에서 SUPCRT 종 G°를 읽기 위한 DB.
        None 이면 SupcrtDatabase("supcrtbl") 를 새로 생성.

    Returns
    -------
    (T_grid, dGf_grid_J)
    """
    if T_grid is None:
        T_grid = DEFAULT_T_GRID_K

    if mode == "literal":
        coeffs = np.polyfit(JING_T_K, JING_DGF, 3)
        return T_grid, np.polyval(coeffs, T_grid)

    if mode == "supcrt_consistent":
        if db is None:
            db = SupcrtDatabase("supcrtbl")
        # logK_R7(T) 외삽 — 2차 polyfit
        coeffs_logK = np.polyfit(JING_T_K, JING_R7_LOGK, 2)
        logK_T = np.polyval(coeffs_logK, T_grid)

        dGf_J = np.empty_like(T_grid, dtype=float)
        for i, (T_K, logK) in enumerate(zip(T_grid, logK_T)):
            G_Li = float(db.species().get("Li+").standardThermoProps(T_K, 1e5).G0)
            G_Fe = float(db.species().get("Fe+2").standardThermoProps(T_K, 1e5).G0)
            G_HP = float(db.species().get("H3PO4(aq)").standardThermoProps(T_K, 1e5).G0)
            # ΔrG° = -RT ln10 · logK
            dG_rxn = -R_GAS * T_K * LN10 * logK
            # Reaction 7 stoichiometry: ΔrG = G(Li+) + G(Fe+2) + G(H3PO4) - G(LFP) - 3·G(H+)
            #                          (G(H+) = 0)
            dGf_J[i] = G_Li + G_Fe + G_HP - dG_rxn
        return T_grid, dGf_J

    raise ValueError(f"unknown mode: {mode!r}")


# ───────────────────────────────────────────────────────────────────
# 4. SupcrtBL DB에 LiFePO4(s) species 추가
# ───────────────────────────────────────────────────────────────────
def make_db_with_lfp(mode: Literal["literal", "supcrt_consistent"] = "literal",
                     T_grid: np.ndarray | None = None) -> SupcrtDatabase:
    """SupcrtBL 데이터베이스에 LiFePO4(s) 커스텀 광물을 추가하여 반환."""
    db = SupcrtDatabase("supcrtbl")

    T_grid_used, dGf_grid = build_lfp_dgf_grid(mode=mode, T_grid=T_grid, db=db)

    elements = ElementalComposition([
        (db.element("Li"), 1.0),
        (db.element("Fe"), 1.0),
        (db.element("P"),  1.0),
        (db.element("O"),  4.0),
    ])
    params = StandardThermoModelParamsInterpolation()
    params.temperatures = T_grid_used.tolist()
    params.pressures    = [1.0e5]
    params.G0           = [[g] for g in dGf_grid.tolist()]

    sp = (Species()
          .withName("LiFePO4(s)")
          .withFormula("LiFePO4")
          .withElements(elements)
          .withAggregateState(AggregateState.Solid)
          .withStandardThermoModel(StandardThermoModelInterpolation(params)))
    db.addSpecies(sp)
    return db


# ───────────────────────────────────────────────────────────────────
# 5. ChemicalSystem 빌더
# ───────────────────────────────────────────────────────────────────
def build_system(db: SupcrtDatabase, *, ideal: bool = False) -> ChemicalSystem:
    """Li-Fe-P-H-O 화학계를 구성. ideal=True 면 IdealAqueous fallback."""
    aq = AqueousPhase(speciate("H O Li Fe P"))
    aq.set(ActivityModelIdealAqueous() if ideal else ActivityModelHKF())
    return ChemicalSystem(
        db, aq,
        MineralPhase("LiFePO4(s)"),
        MineralPhase("Hematite"),
        MineralPhase("Magnetite"),
        MineralPhase("Goethite"),
        MineralPhase("Iron"),
    )


# ───────────────────────────────────────────────────────────────────
# 6. 평형 풀이 (HKF→Ideal fallback)
# ───────────────────────────────────────────────────────────────────
@dataclass
class InitialComposition:
    """초기 조건. molality·mass 단위 자유롭게 — 다음 세션의 농도 sweep 에 사용."""
    H2O_kg: float = 1.0
    LFP_kg: float = 0.020
    extras_mol: dict[str, float] | None = None   # 예: {"H+": 0.01, "NaCl": 0.5}


def solve_equilibrium(
    db: SupcrtDatabase,
    T_C: float,
    P_bar: float,
    initial: InitialComposition | None = None,
) -> tuple[ChemicalState, str]:
    """주어진 (T,P,초기 조성) 에서 평형 계산. Returns (state, model_used)."""
    if initial is None:
        initial = InitialComposition()

    def _set_state(state: ChemicalState) -> None:
        state.temperature(T_C, "celsius")
        state.pressure(P_bar, "bar")
        state.set("H2O(aq)",   initial.H2O_kg, "kg")
        state.set("LiFePO4(s)", initial.LFP_kg, "kg")
        if initial.extras_mol:
            for name, mol in initial.extras_mol.items():
                state.set(name, mol, "mol")

    # 1차 시도 — HKF
    sys = build_system(db, ideal=False)
    state = ChemicalState(sys); _set_state(state)
    result = EquilibriumSolver(sys).solve(state)
    if result.succeeded():
        return state, "HKF"

    # 2차 — IdealAqueous fallback
    print("   [경고] HKF 수렴 실패 → IdealAqueous 로 재시도")
    sys = build_system(db, ideal=True)
    state = ChemicalState(sys); _set_state(state)
    result = EquilibriumSolver(sys).solve(state)
    if result.succeeded():
        return state, "IdealAqueous (fallback)"

    raise RuntimeError(f"수렴 실패: T={T_C}°C, P={P_bar} bar")


# ───────────────────────────────────────────────────────────────────
# 7. 결과 → dict + JSON 저장/복원
# ───────────────────────────────────────────────────────────────────
def state_to_snapshot(state: ChemicalState, *, model_used: str,
                      T_C: float, P_bar: float,
                      initial: InitialComposition,
                      mode: str,
                      label: str | None = None) -> dict:
    """평형 상태 → 직렬화 가능한 dict."""
    sys = state.system()
    aprops = AqueousProps(state)
    props  = ChemicalProps(state)

    species_amount = {sp.name(): float(state.speciesAmount(sp.name()))
                      for sp in sys.species()}
    species_activity = {sp.name(): float(props.speciesActivity(sp.name()))
                        for sp in sys.species()}
    elements_amount = {e.symbol(): float(state.elementAmounts()[i])
                       for i, e in enumerate(sys.elements())}

    n_init = (initial.LFP_kg * 1000.0) / LFP_MOLAR_MASS_G
    n_left = species_amount.get("LiFePO4(s)", 0.0)

    return {
        "schema":            "lfp_dissolution_v1",
        "label":             label or f"{T_C:g}C_{P_bar:g}bar",
        "mode":              mode,
        "model_used":        model_used,
        "T_celsius":         T_C,
        "P_bar":             P_bar,
        "initial":           {
            "H2O_kg":     initial.H2O_kg,
            "LFP_kg":     initial.LFP_kg,
            "extras_mol": initial.extras_mol or {},
        },
        "pH":                float(aprops.pH()),
        "ionic_strength":    float(aprops.ionicStrength()),
        "Li_dissolved_pct":  (1 - n_left/n_init) * 100.0,
        "elements_amount":   elements_amount,
        "species_amount":    species_amount,
        "species_activity":  species_activity,
    }


def save_snapshot(snapshot: dict, path: str | Path) -> Path:
    """JSON으로 저장. 다른 도구 (pandas, jupyter) 에서 그대로 불러올 수 있게."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    return path


def load_snapshot(path: str | Path) -> dict:
    """저장된 JSON 스냅샷을 dict로 로드."""
    with Path(path).open() as f:
        return json.load(f)


# ───────────────────────────────────────────────────────────────────
# 8. 한 줄 헬퍼 — sweep 시 가장 자주 쓸 form
# ───────────────────────────────────────────────────────────────────
def run_case(
    *, T_C: float, P_bar: float,
    LFP_kg: float = 0.020, H2O_kg: float = 1.0,
    extras_mol: dict[str, float] | None = None,
    mode: Literal["literal", "supcrt_consistent"] = "literal",
    label: str | None = None,
    save_to: str | Path | None = None,
) -> dict:
    """단일 조건 시뮬레이션을 실행하고 결과 dict 반환. 옵션으로 JSON 저장."""
    db = make_db_with_lfp(mode=mode)
    initial = InitialComposition(H2O_kg=H2O_kg, LFP_kg=LFP_kg, extras_mol=extras_mol)
    state, model = solve_equilibrium(db, T_C, P_bar, initial)
    snap = state_to_snapshot(state, model_used=model, T_C=T_C, P_bar=P_bar,
                             initial=initial, mode=mode, label=label)
    if save_to is not None:
        save_snapshot(snap, save_to)
    return snap
