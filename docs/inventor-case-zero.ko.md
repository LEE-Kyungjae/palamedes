# Inventor case-zero 001

이 run은 외부 owner의 답변을 기다리지 않고 낯선 공개 오픈소스 저장소에서 실험
프로토콜과 생성 경로를 먼저 검증하는 calibration이다.

## 증거 경계

- 질문은 repository owner가 아니라 Palamedes 연구자가 공개 문서에서 작성했다.
- 실제 owner의 미결정 질문, 사용자 데이터, 운영 제약 또는 우선순위를 안다고 주장하지
  않는다.
- 생성 결과는 프로젝트에 대한 권고, issue, PR 또는 외부 Inventor 증거가 아니다.
- owner 결정 변화, 독립 인간 선호, 실제 outcome을 입증하지 않는다.
- 결과가 좋아도 `inventor_claim_demonstrated`를 통과시킬 수 없다.

## 동결 사례

- `VecterAI/reacher-x` at `d593c62e235e44d9628a5bf54ee68b5157a75219`
- `mattschaller/mcp-policy` at `18e4efec40d61dfc4bc739a52f0fc802824ad42c`
- `P-r-e-m-i-u-m/PROXY` at `e7693632cc986ed08aaedc7e26baf56ab4a187e8`

각 조건은 configured Codex model을 네 번 호출한다. Tournament는 세 독립 lens와
selector를 사용하고 Palamedes는 interpreter, inventor, adversary, selector를 사용한다.
양쪽은 동일한 frozen information packet만 받는다.
