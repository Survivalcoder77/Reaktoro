"""
튜토리얼 1: Reaktoro 임포트하기
================================

이 스크립트는 Reaktoro 라이브러리를 불러오는 세 가지 방식을 모두 보여주고,
각 방식이 정상적으로 작동하는지 검증합니다.

실행 방법:
    conda activate reaktoro
    python 01_importing_reaktoro.py
"""

# ═══════════════════════════════════════════════════════════════
# 방식 1: 기본 임포트 (basic import)
# ═══════════════════════════════════════════════════════════════
# reaktoro 라이브러리 전체를 reaktoro라는 이름으로 사용
import reaktoro  # 리액토로 라이브러리 불러오기

print("=" * 60)
print("  방식 1: import reaktoro")
print("=" * 60)
print(f"  Reaktoro 버전: {reaktoro.__version__}")
# ChemicalSystem 클래스(화학 시스템 객체를 만드는 설계도)에 접근하려면
# reaktoro. 접두사가 필요함
print(f"  ChemicalSystem 클래스: {reaktoro.ChemicalSystem}")

# ═══════════════════════════════════════════════════════════════
# 방식 2: 별칭 임포트 (alias import) — 가장 권장
# ═══════════════════════════════════════════════════════════════
# rkt라는 짧은 별칭으로 사용하면 코드가 깔끔해짐
import reaktoro as rkt  # rkt라는 별칭으로 임포트

print()
print("=" * 60)
print("  방식 2: import reaktoro as rkt")
print("=" * 60)
print(f"  rkt.ChemicalSystem 클래스: {rkt.ChemicalSystem}")
# 두 변수가 실제로 같은 객체인지 확인 (is 연산자)
print(f"  reaktoro와 rkt는 같은 모듈?: {reaktoro is rkt}")

# ═══════════════════════════════════════════════════════════════
# 방식 3: 전체 임포트 (wildcard import) — 튜토리얼에서 자주 사용
# ═══════════════════════════════════════════════════════════════
# 모든 클래스/함수를 직접 이름으로 사용 가능 (접두사 불필요)
from reaktoro import *  # 모든 것 가져오기

print()
print("=" * 60)
print("  방식 3: from reaktoro import *")
print("=" * 60)
# 이제 ChemicalSystem을 그냥 이름만으로 부를 수 있음
print(f"  ChemicalSystem 클래스: {ChemicalSystem}")
print(f"  PhreeqcDatabase 클래스: {PhreeqcDatabase}")
print(f"  AqueousPhase 클래스: {AqueousPhase}")
print(f"  EquilibriumSolver 클래스: {EquilibriumSolver}")

# ═══════════════════════════════════════════════════════════════
# 주요 Reaktoro 컴포넌트 둘러보기
# ═══════════════════════════════════════════════════════════════
print()
print("=" * 60)
print("  🔍 Reaktoro에서 사용 가능한 주요 컴포넌트들")
print("=" * 60)

# dir() 함수: 모듈 안의 이름들을 모두 나열해 줌
all_names = dir(rkt)
# 알파벳 순서로 정렬하고, 밑줄(_)로 시작하는 내부 이름은 제외
public_names = sorted([n for n in all_names if not n.startswith("_")])

# 카테고리별로 나눠서 보여주기 (이름 패턴으로 분류)
categories = {
    "데이터베이스 (Database)":    [n for n in public_names if "Database" in n],
    "상 (Phase)":                  [n for n in public_names if "Phase" in n and "Activity" not in n],
    "활동도 모델 (ActivityModel)": [n for n in public_names if "ActivityModel" in n][:8],
    "평형 관련 (Equilibrium)":     [n for n in public_names if "Equilibrium" in n],
    "속도론 관련 (Kinetics)":      [n for n in public_names if "Kinetic" in n],
    "특성 계산 (Props)":           [n for n in public_names if "Props" in n],
}

for category, names in categories.items():
    print(f"\n  📦 {category}: 총 {len(names)}개")
    for name in names[:6]:  # 처음 6개만 표시
        print(f"     - {name}")
    if len(names) > 6:
        print(f"     ... 외 {len(names) - 6}개 더")

print()
print("=" * 60)
print("  ✅ 튜토리얼 1 완료! 다음 튜토리얼로 진행하세요.")
print("=" * 60)
