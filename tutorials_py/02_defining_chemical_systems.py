"""
튜토리얼 2: 화학 시스템 정의하기 (Defining Chemical Systems)
============================================================

목표: 화학 반응 계산의 기초가 되는 ChemicalSystem 객체 만들기.
      여러 데이터베이스(PHREEQC, SUPCRTBL, ThermoFun, NASA-CEA)를 활용해
      다양한 시나리오의 화학 시스템을 구성하는 방법을 익힌다.

실행:
    conda activate reaktoro
    python tutorials_py/02_defining_chemical_systems.py
"""

from reaktoro import *  # 튜토리얼 스타일 — 모든 컴포넌트를 직접 이름으로 사용


# ═══════════════════════════════════════════════════════════════
# 시나리오 1: 가장 단순한 시스템 — 물 + Halite(암염, NaCl 광물)
# ═══════════════════════════════════════════════════════════════
def scenario_1_halite_solubility():
    """
    Halite(암염) 용해도 모델링용 시스템:
    - 수용액 상(aqueous phase): H2O, H+, OH-, Na+, Cl-
    - 광물 상(mineral phase): Halite (NaCl 결정)
    """
    print("\n" + "=" * 70)
    print("  시나리오 1: Halite(암염) 용해도 시스템")
    print("=" * 70)

    # PHREEQC 데이터베이스 로드 (지구화학 분야 표준 DB 중 하나)
    db = PhreeqcDatabase("phreeqc.dat")

    # 수용액 상 정의 — 종(species)을 명시적으로 나열
    solution = AqueousPhase("H2O H+ OH- Na+ Cl-")

    # 광물 상 정의 — Halite(암염)만 고려
    halite = MineralPhase("Halite")

    # 화학 시스템 객체 생성 — 데이터베이스 + 모든 상을 묶음
    system = ChemicalSystem(db, solution, halite)

    # ── 시스템 들여다보기: 상별로 어떤 종이 들어있나?
    print("\n[상(phase)별 종(species) 구성]")
    for phase in system.phases():
        print(f"  📦 {phase.name()}")
        for species in phase.species():
            print(f"     :: {species.name()}")

    # ── 시스템 전체 종 목록 (Reaktoro 내부 순서대로)
    print("\n[전체 종 순서 — system.species()]")
    for species in system.species():
        print(f"  - {species.name()}")

    # ── 시스템에 등장하는 화학 원소들
    print("\n[시스템 원소 목록 — system.elements()]")
    for element in system.elements():
        print(f"  - {element.symbol()}")

    # ── Formula Matrix(화학식 행렬): 각 종의 원소 구성을 행렬로 표현
    # 행: 원소(+ 마지막 행은 전하), 열: 종
    print("\n[Formula Matrix — 행=원소(마지막은 전하), 열=종]")
    print(system.formulaMatrix())

    return system


# ═══════════════════════════════════════════════════════════════
# 시나리오 2: speciate()로 자동 종 선택 — CO2 용해도 모델링
# ═══════════════════════════════════════════════════════════════
def scenario_2_co2_solubility_auto():
    """
    speciate("H O Na Cl Ca C") = 이 원소들로 만들 수 있는 모든 종을 자동 수집.
    유기 종까지 포함되어 결과가 매우 많아짐 → 다음 시나리오에서 거른다.
    """
    print("\n" + "=" * 70)
    print("  시나리오 2: SUPCRTBL DB로 자동 종 선택 (유기물 포함)")
    print("=" * 70)

    # SUPCRTBL 데이터베이스 — 유기 종까지 포함한 확장판
    db = SupcrtDatabase("supcrtbl-organics")

    # 원소만 지정하면 reaktoro가 알아서 종을 모음(speciate)
    solution = AqueousPhase(speciate("H O Na Cl Ca C"))

    # 빈 GaseousPhase() = 위 원소로 만들 수 있는 모든 기체 자동 선택
    gas = GaseousPhase()

    system = ChemicalSystem(db, solution, gas)

    # 너무 많으니 처음 10개만 출력
    print("\n[자동 수집된 종 — 너무 많아서 상위 10개만]")
    print(f"{'Name':<25}{'Formula':<25}{'Molar Mass (kg/mol)':<20}")
    for i, species in enumerate(system.species()):
        if i >= 10:
            break
        print(f"{species.name():<25}{species.formula().str():<25}{species.molarMass():<20.6f}")
    total = system.species().size()
    print(f"  ... 총 {total}개 종 (유기 종이 매우 많음)")


# ═══════════════════════════════════════════════════════════════
# 시나리오 3: exclude("organic")로 유기 종 거르기
# ═══════════════════════════════════════════════════════════════
def scenario_3_co2_solubility_filtered():
    """
    같은 SUPCRTBL DB지만 유기 종을 빼고, 기체는 CO2(g)만 명시.
    """
    print("\n" + "=" * 70)
    print("  시나리오 3: 유기 종 제외 + 명시적 기체 지정")
    print("=" * 70)

    db = SupcrtDatabase("supcrtbl-organics")

    # exclude("organic") = 'organic' 태그가 붙은 종 모두 제외
    solution = AqueousPhase(speciate("H O Na Cl Ca C"), exclude("organic"))

    # 기체는 CO2(g) 하나로 한정
    gas = GaseousPhase("CO2(g)")

    system = ChemicalSystem(db, solution, gas)

    print(f"\n[필터링 후 종 목록 — 총 {system.species().size()}개]")
    for species in system.species():
        print(f"  - {species.name()}")


# ═══════════════════════════════════════════════════════════════
# 시나리오 4: 종을 직접 리스트로 지정 — 가장 정밀한 제어
# ═══════════════════════════════════════════════════════════════
def scenario_4_explicit_species_list():
    """
    원하는 종을 정확히 알고 있을 때, Python 리스트로 직접 넘긴다.
    필요한 종만 들어가므로 계산이 빠르고 결과 해석이 쉬움.
    """
    print("\n" + "=" * 70)
    print("  시나리오 4: 명시적인 종 리스트로 정의")
    print("=" * 70)

    db = SupcrtDatabase("supcrtbl-organics")

    # 정확히 원하는 종만 지정한 리스트
    aqueous_species = [
        "H2O(aq)", "CaOH+", "CO2(aq)", "CO3-2", "Ca(HCO3)+",
        "Ca+2", "CaCl+", "Cl-", "H+", "HCO3-",
        "HO2-", "Na+", "OH-",
    ]
    solution = AqueousPhase(aqueous_species)
    gas = GaseousPhase("CO2(g)")
    system = ChemicalSystem(db, solution, gas)

    print(f"\n[지정한 종만 들어간 시스템 — 총 {system.species().size()}개]")
    for species in system.species():
        print(f"  - {species.name()}")


# ═══════════════════════════════════════════════════════════════
# 시나리오 5: 시멘트 화학 — 매우 복잡한 다상(multi-phase) 시스템
# ═══════════════════════════════════════════════════════════════
def scenario_5_cement_chemistry():
    """
    ThermoFun cemdata18 데이터베이스로 시멘트 화학 시스템 구성.
    여러 광물 상이 자동으로 추가되며, 고용체(solid solution) 광물도 포함.
    """
    print("\n" + "=" * 70)
    print("  시나리오 5: 시멘트 화학(ThermoFun cemdata18) — 다상 시스템")
    print("=" * 70)

    db = ThermoFunDatabase("cemdata18")

    solution = AqueousPhase(speciate("H O Na Cl Ca Mg C Si Fe Al K S"))
    gas = GaseousPhase()
    # MineralPhases (복수형) = 가능한 모든 광물 상을 자동 추가
    pureminerals = MineralPhases()
    # 고용체(solid solution) = 두 광물이 서로 섞여 있는 단일 상
    solidsolution = MineralPhase("ettringite Fe-ettringite")

    system = ChemicalSystem(db, solution, gas, pureminerals, solidsolution)

    n_phases = system.phases().size()
    n_species = system.species().size()
    print(f"\n  📊 총 상(phase) 개수: {n_phases}")
    print(f"  📊 총 종(species) 개수: {n_species}")
    print(f"\n[처음 5개 상의 이름]")
    for i, phase in enumerate(system.phases()):
        if i >= 5:
            print(f"  ... 외 {n_phases - 5}개 상")
            break
        print(f"  📦 {phase.name()} (종 {phase.species().size()}개)")


# ═══════════════════════════════════════════════════════════════
# 시나리오 6: 빈 AqueousPhase() — 광물에서 원소 추론
# ═══════════════════════════════════════════════════════════════
def scenario_6_inferred_from_minerals():
    """
    수용액 상에 종이나 원소를 명시하지 않으면,
    Reaktoro가 같이 정의된 광물의 구성 원소로부터 자동으로 종을 수집한다.
    """
    print("\n" + "=" * 70)
    print("  시나리오 6: 광물 → 수용액 종 자동 추론")
    print("=" * 70)

    db = PhreeqcDatabase("phreeqc.dat")

    # 빈 AqueousPhase() — 어떤 종도 명시하지 않음
    solution = AqueousPhase()

    # Albite(NaAlSi3O8), Kaolinite(Al2Si2O5(OH)4) 광물 상
    albite = MineralPhase("Albite")
    kaolinite = MineralPhase("Kaolinite")

    system = ChemicalSystem(db, albite, kaolinite, solution)

    # 자동으로 어떤 수용액 종이 선택되었는지 확인
    aqueousphase = system.phases().get("AqueousPhase")
    print(f"\n[광물 원소(Na, Al, Si, O, H)로부터 자동 수집된 수용액 종 "
          f"— 총 {aqueousphase.species().size()}개]")
    for species in aqueousphase.species():
        print(f"  - {species.name()}")


# ═══════════════════════════════════════════════════════════════
# 시나리오 7: 흑색화약 연소 — NASA-CEA DB의 응축상(condensed phase)
# ═══════════════════════════════════════════════════════════════
def scenario_7_black_powder_combustion():
    """
    흑색화약(K, N, O, C, Ca, H, S) 연소 모델링.
    고온에서 일어나므로 NASA-CEA(항공우주 추진제용) DB 사용.
    """
    print("\n" + "=" * 70)
    print("  시나리오 7: 흑색화약 연소(NASA-CEA) — 기체 + 응축상")
    print("=" * 70)

    db = NasaDatabase("nasa-cea")

    # 응축상(고체/액체) — 연소 후 생성될 수 있는 모든 응축 물질
    condensed = CondensedPhases(speciate("K N O C Ca H S"))
    # 위 원소로 만들 수 있는 모든 기체 자동 수집
    gases = GaseousPhase()

    system = ChemicalSystem(db, gases, condensed)

    # 기체와 응축상 종을 분리해서 출력 (aggregateState로 구분)
    print("\n[기체 종 — 처음 10개만]")
    gas_count = 0
    for species in system.species():
        if species.aggregateState() == AggregateState.Gas:
            if gas_count < 10:
                print(f"  :: {species.name()}")
            gas_count += 1
    print(f"  ... 총 기체 종 {gas_count}개")

    print("\n[응축상 종]")
    cd_count = 0
    for species in system.species():
        if species.aggregateState() == AggregateState.CondensedPhase:
            print(f"  :: {species.name()}")
            cd_count += 1

    print(f"\n  📊 시스템 내 총 종(species) 개수: {system.species().size()}")
    print(f"  📊 시스템 내 총 상(phase)   개수: {system.phases().size()}")


# ═══════════════════════════════════════════════════════════════
# 메인 — 모든 시나리오를 순서대로 실행
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    scenario_1_halite_solubility()
    scenario_2_co2_solubility_auto()
    scenario_3_co2_solubility_filtered()
    scenario_4_explicit_species_list()
    scenario_5_cement_chemistry()
    scenario_6_inferred_from_minerals()
    scenario_7_black_powder_combustion()

    print("\n" + "=" * 70)
    print("  ✅ 튜토리얼 2 완료!")
    print("=" * 70)
