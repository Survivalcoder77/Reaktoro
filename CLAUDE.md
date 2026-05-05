# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 이 디렉토리에 대하여 (About This Directory)

이 폴더는 **Reaktoro** 라이브러리의 HTML 튜토리얼 문서 모음입니다. Reaktoro 소스 코드 저장소가 아니며, reaktoro.org에서 렌더링된 Jupyter Book 튜토리얼 페이지들입니다.

This folder is a collection of rendered HTML tutorial pages from the [Reaktoro](https://reaktoro.org) geochemical modeling library — not the Reaktoro source code itself.

## Reaktoro란 무엇인가 (What is Reaktoro)

Reaktoro는 **화학 반응 시스템(chemically reactive systems)**을 모델링하는 C++/Python 오픈소스 프레임워크입니다. 주요 용도:

- 화학 평형(chemical equilibrium) 및 반응 속도론(kinetics) 계산
- 수계 반응(aqueous reactions), 광물 용해/침전(mineral dissolution/precipitation)
- 지구화학(geochemistry), 환경 공학, 탄소 포집 시뮬레이션

## 포함된 튜토리얼 파일들 (Tutorial Files)

각 `.html` 파일은 하나의 튜토리얼 주제를 다룹니다:

| 파일 | 내용 |
|------|------|
| `Importing Reaktoro.html` | reaktoro 패키지 임포트 방법 |
| `Defining chemical systems.html` | ChemicalSystem 정의 방법 |
| `Defining materials.html` | Material 정의 방법 |
| `Loading thermodynamic databases.html` | 열역학 데이터베이스 로드 |
| `Inspecting thermodynamic databases.html` | 데이터베이스 내용 확인 |
| `Creating chemical states.html` | ChemicalState 생성 |
| `Computing chemical properties.html` | ChemicalProps 계산 |
| `Computing aqueous properties.html` | AqueousProps 계산 |
| `Computing standard thermodynamic properties of species.html` | 종(species) 표준 열역학 특성 |
| `Computing standard thermodynamic properties of reactions.html` | 반응 표준 열역학 특성 |
| `Specifying activity models.html` | 활동도 모델(activity model) 설정 |
| `Creating thermodynamic databases.html` | 커스텀 데이터베이스 생성 |
| `Chemical equilibrium_ the basics.html` | 화학 평형 기초 |
| `Chemical equilibrium with given element and charge amounts.html` | 원소/전하 조건 평형 |
| `Chemical equilibrium with fixed pH.html` | 고정 pH 조건 평형 |
| `Chemical equilibrium with fixed pH and charge balance.html` | pH + 전하 균형 평형 |
| `Chemical equilibrium with fixed fugacity.html` | 고정 퓨가시티(fugacity) 평형 |
| `Chemical equilibrium with fixed phase amount.html` | 고정 상(phase) 양 평형 |
| `Chemical equilibrium with fixed volume and internal energy.html` | 고정 부피/내부에너지 평형 |
| `Chemical equilibrium with constraints.html` | 일반 제약 조건 평형 |
| `Chemical equilibrium with custom constraints.html` | 커스텀 제약 조건 평형 |
| `Chemical kinetics_ the basics.html` | 화학 반응 속도론 기초 |
| `Chemical kinetics for mineral reactions using Palandri-Kharaka model.html` | Palandri-Kharaka 광물 반응 모델 |

## 핵심 Reaktoro Python 패턴 (Core Reaktoro Python Patterns)

튜토리얼 코드는 아래 두 가지 임포트 방식을 사용합니다:

```python
from reaktoro import *      # 전체 임포트 (튜토리얼에서 주로 사용)
import reaktoro as rkt      # 별칭 임포트
```

### 기본 워크플로우

```python
from reaktoro import *

# 1. 데이터베이스 선택 (PhreeqcDatabase, SupcrtDatabase, NasaDatabase, ThermoFunDatabase)
db = PhreeqcDatabase("phreeqc.dat")

# 2. 상(phase) 정의
solution = AqueousPhase(speciate("H O Na Cl C"))
solution.set(ActivityModelPhreeqc(db))
mineral = MineralPhase("Calcite")

# 3. 화학 시스템 구성
system = ChemicalSystem(db, solution, mineral)

# 4. 화학 상태 초기화
state = ChemicalState(system)
state.temperature(25.0, "celsius")
state.pressure(1.0, "atm")
state.set("H2O", 1.0, "kg")

# 5. 평형 계산
solver = EquilibriumSolver(system)
result = solver.solve(state)

# 6. 결과 조회
props = ChemicalProps(state)
aprops = AqueousProps(props)
```

## Reaktoro 설치 (Installation)

```bash
# conda를 사용한 설치 (권장)
conda install -c conda-forge reaktoro

# 또는 pip
pip install reaktoro
```

## 소스 코드 및 공식 문서

- 공식 웹사이트: https://reaktoro.org
- GitHub 저장소: https://github.com/reaktoro/reaktoro
- Jupyter Book 튜토리얼: https://github.com/reaktoro/reaktoro-jupyter-book
