# PROJECT_STATE — LiFePO4 Hydrothermal Dissolution Simulation

이 파일은 다음 세션이 시작될 때 가장 먼저 읽도록 설계된 **프로젝트 즉시 부팅 문서**입니다.
2026-05-05 일 작업한 LFP dissolution 시뮬레이션의 상태를 그대로 이어가기 위한 요약 + 다음 단계 가이드입니다.

---

## 1. 한 줄 요약

LiFePO4 (배터리 양극재) 가 두 hydrothermal 조건에서 얼마나 녹는지를 Reaktoro 로 평형 계산하는 프로젝트입니다.
조건 A (180 °C / 272 psi 압축액체) 에서 Li 용해율 ≈ 1.68 %, 조건 B (380 °C / 3350 psi 초임계수) 에서 ≈ 0.11 % — 초임계수가 오히려 덜 녹이는 결과 (사용자 직관과 일치, ε 저하 효과 자동 반영).

---

## 2. 파일 지도

| 경로 | 역할 |
|---|---|
| [tutorials_py/04_lifepo4_dissolution_subcrit_vs_supercrit.py](tutorials_py/04_lifepo4_dissolution_subcrit_vs_supercrit.py) | 메인 스크립트 (두 조건 비교 + JSON 자동 저장) |
| [tutorials_py/lfp_thermo.py](tutorials_py/lfp_thermo.py) | 핵심 헬퍼 모듈 — DB 빌더, 평형 풀이, JSON snapshot |
| [results/lfp_A_180C_272psi.json](results/lfp_A_180C_272psi.json) | 조건 A 평형 결과 스냅샷 |
| [results/lfp_B_380C_3350psi.json](results/lfp_B_380C_3350psi.json) | 조건 B 평형 결과 스냅샷 |
| [ref/](ref/) | 출처 PDF (Jing 2019, Loos 2015, Ong 2008, mp-19017) |
| [CLAUDE.md](CLAUDE.md) | conda 환경 활성화 규칙 등 |

---

## 3. 다음 세션 시작하기 — 5초 부팅

```bash
# 환경 활성화
source ~/miniconda3/etc/profile.d/conda.sh && conda activate reaktoro

# 기존 결과 그대로 재현
python tutorials_py/04_lifepo4_dissolution_subcrit_vs_supercrit.py
```

Python 스크립트/Jupyter 안에서 결과만 로드해서 분석/플롯하기:

```python
import sys; sys.path.insert(0, "tutorials_py")
from lfp_thermo import load_snapshot, run_case

# 1) 저장된 결과 로드
snap_A = load_snapshot("results/lfp_A_180C_272psi.json")
snap_B = load_snapshot("results/lfp_B_380C_3350psi.json")
print(snap_A["pH"], snap_A["Li_dissolved_pct"])

# 2) 새 조건 실행 — 초기 농도 sweep
result = run_case(
    T_C=180.0, P_bar=18.75,
    LFP_kg=0.020,           # 다른 양으로 바꿔보기
    H2O_kg=1.0,
    extras_mol={"H+": 0.01},  # 산성 첨가 등도 가능
    save_to="results/sweep/lfp_acid_pH2.json",
)
print(result["Li_dissolved_pct"])
```

---

## 4. 모드 선택

`run_case` / `make_db_with_lfp` 의 `mode` 인자:

- **`mode="literal"` (기본, 권장)** — Jing 2019 Table 1 의 ΔfG°(LFP) 를 그대로 사용.
  LFP가 평형(SI ≈ 0) 을 만족하면서 시스템 전체의 Gibbs minimization 이 풀린다.
  유전율 ε(T,P), HKF 활동도 보정, Fe 광물 재침전이 모두 자동 반영됨.

- `mode="supcrt_consistent"` (실험적) — Jing Reaction 7 logK(T) 와 SUPCRT 종 G°(T) 를
  화학적으로 짝맞춘 ΔfG°(LFP) 재유도. **주의**: 473 K 위 외삽이 비물리적이고 SUPCRT-HKF
  의 Fe²⁺ G°(T) 가 623 K 에서 폭주하는 한계 영역과 합쳐지면 비현실적인 결과를 줄 수 있음
  (380 °C 에서 100 % 용해 같은). sanity check 비교용으로만 사용.

---

## 5. 검증된 사실 (todo 의 "completed")

1. Loos 2015 Table 7 의 Cp(T) 다항식 계수 부호 검증 — 오리지날 Table 9 의 Cp(298)=122.1, Cp(770)=186.9 와 RMS 0.7 % 일치.
2. Reaktoro `StandardThermoModelInterpolation` 으로 LFP 커스텀 광물 추가 가능 — 임의의 (T,P) 에서 G°(LFP) 가 흡수됨.
3. Element 보존 (Li, Fe, P, O, H) 평형 후 ppm 수준에서 보존됨.
4. Charge balance |Σ z·n| < 1e-15 mol.
5. Saturation Index of LiFePO4(s) at equilibrium ≈ 0 (정확히 평형 포화).

---

## 6. 알려진 한계 (논문에 명시 필요)

- **데이터 출처 혼재**: ΔfG°(LFP) 는 Jing(FactSage 기반), 수용액 종은 SUPCRT-HKF.
  → 두 source 가 사용한 reference state 가 미묘하게 다르므로, **개별 부분반응의 logQ** 가
  Jing 의 logK(R7) 와 일치하지 않는 게 정상 (실제 약 14 차수 차이 관측됨).
  중요한 것은 LFP의 SI=0 (자기 평형) 과 시스템 전체의 Gibbs minimization.
- **Jing 데이터 범위**: 298–473 K. 380 °C (= 653 K) 는 외삽 영역.
- **SUPCRT-HKF 한계**: 약 ~600 °C, ~5 kbar 가 권장 한계. 380 °C 는 안쪽이지만 ε(T,P) 등이 빠르게 변하는 임계근접 영역.
- **부산물 광물 후보 제한**: SupcrtBL 에 vivianite (Fe3(PO4)2·8H2O), strengite (FePO4·2H2O) 가 없어, 가능한 Fe-PO4 침전 경로가 일부만 표현됨.

---

## 7. 자연스러운 다음 작업 (사용자 의도에 부합)

다음 세션에서 이어서 하기 좋은 분기:

1. **초기 농도 sweep** — `extras_mol={"H+": x}` 로 산성도 변화, 또는 LFP_kg 변화에 따른 용해율 곡선.
2. **온도/압력 grid** — 25 → 400 °C, 1 → 300 bar 격자에서 Li 용해율 contour 그리기.
3. **redox 변수 추가** — H₂O₂, NaClO 같은 산화제를 첨가해 Jing 의 leaching route I/II 모사.
4. **유전율 ε(T,P) 의 직접 영향 검증** — `waterElectroPropsJohnsonNorton` 으로 두 조건 ε 값을 뽑고, Li 용해율과 함께 보고.

---

## 8. 환경 의존성 (conda env: reaktoro)

- Python 3.12.13
- Reaktoro 2.13.0
- numpy (with reaktoro)
- poppler (PDF 텍스트 추출용 — `conda install -c conda-forge --override-channels poppler -y` 로 설치됨)

---

## 9. 핵심 식 (식별을 위한 빠른 참조)

```
Jing 2019 Table 1 (J/mol):
  ΔfG°(LiFePO4)
    298.15 K: -1480.97 kJ/mol
    363.15 K: -1490.71
    423.15 K: -1501.13
    473.15 K: -1510.79

Loos 2015 eq. 6 (300 ≤ T ≤ 773 K):
  Cp,m(T) [J/K/mol] = a0 + a1·T + a2·T² + a3·T³ + a4·T⁻²
    a0 = -41.881336    a1 =  0.78278483
    a2 = -0.0010255433 a3 =  5.0862948e-7
    a4 = +890694.39
  S°(298.15 K) = 130.95 J/K/mol

Jing SI Table S1 #7:
  LiFePO4 + 3 H+ ⇌ Li+ + Fe²+ + H3PO4(aq)
  pH = a(T) − (1/3) lg([Li+][Fe²+][H3PO4])
  ⇒ logK(T) = 3 a(T)
    298.15 K: logK = +1.84
    363.15 K: logK = -4.40
    423.15 K: logK = -8.43
    473.15 K: logK = -11.03

  → 온도가 올라갈수록 logK 가 감소, LFP가 안정화됨 (시뮬레이션 결과와 정합).
```

---

*마지막 갱신: 2026-05-05 — 메인 결과는 literal 모드 (Jing Table 1).*
