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

## 이 시스템의 Reaktoro 설치 상태 (Local Setup)

이 머신에는 Reaktoro가 다음과 같이 설치되어 있습니다:

- **Miniconda 위치**: `~/miniconda3/`
- **conda 환경 이름**: `reaktoro` (전용 환경)
- **Python 버전**: 3.12.13
- **Reaktoro 버전**: 2.13.0
- **conda 채널 설정**: `conda-forge` 전용 (`channel_priority: strict`, `~/.condarc`)
- **튜토리얼 실습 코드 폴더**: `tutorials_py/` (예: `tutorials_py/01_importing_reaktoro.py`)

## 환경 활성화 — 모든 Python/Reaktoro 명령은 이 환경에서 실행해야 함

### 사용자 인터랙티브 셸에서

```bash
conda activate reaktoro     # 활성화 — 프롬프트가 (reaktoro)로 바뀜
# ... 작업 ...
conda deactivate            # 사용 종료
```

### Claude Code(또는 비대화형 셸)에서 실행할 때

Claude는 매번 새 Bash 세션에서 명령을 실행하므로 셸 상태가 유지되지 않습니다.
따라서 **Reaktoro와 관련된 모든 Bash 명령에는 환경을 활성화하는 한 줄을 항상 앞에 붙여야 합니다**:

```bash
source ~/miniconda3/etc/profile.d/conda.sh && conda activate reaktoro && <실행할 명령>
```

예시 — 튜토리얼 스크립트 실행:

```bash
source ~/miniconda3/etc/profile.d/conda.sh && conda activate reaktoro && python tutorials_py/01_importing_reaktoro.py
```

예시 — Reaktoro 한 줄 테스트:

```bash
source ~/miniconda3/etc/profile.d/conda.sh && conda activate reaktoro && python -c "import reaktoro; print(reaktoro.__version__)"
```

> ⚠️ `conda activate reaktoro`만 단독으로 쓰면 비대화형 셸에서는 `conda: command not found` 오류가 나므로,
> 반드시 `source ~/miniconda3/etc/profile.d/conda.sh`를 먼저 실행해야 합니다.

## Reaktoro 재설치 / 다른 머신에 설치 (Installation Reference)

이미 설치된 머신에서는 불필요하지만, 참고용으로 남겨둡니다:

```bash
# 1) Miniconda 설치 (Apple Silicon)
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh
bash Miniconda3-latest-MacOSX-arm64.sh -b -p ~/miniconda3
~/miniconda3/bin/conda init zsh

# 2) conda-forge 전용 채널 설정
conda config --add channels conda-forge
conda config --set channel_priority strict

# 3) Reaktoro 환경 생성
conda create -n reaktoro -c conda-forge --override-channels reaktoro python=3.12 -y
```

## 소스 코드 및 공식 문서

- 공식 웹사이트: https://reaktoro.org
- GitHub 저장소: https://github.com/reaktoro/reaktoro
- Jupyter Book 튜토리얼: https://github.com/reaktoro/reaktoro-jupyter-book
