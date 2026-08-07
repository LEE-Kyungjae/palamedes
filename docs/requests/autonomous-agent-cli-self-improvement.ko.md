# Palamedes CLI·에이전트화 자가개선 요청

- 요청일: 2026-07-30
- 현장 사례: Zaeze 장기 멀티에이전트 개발
- 목표: 사용자가 프로젝트 디렉터리에서 `palamedes`만 실행하면 Codex CLI와 연결된 자율 개발 관제 터미널이 시작되는 경험
- 기본 운영 모드: supervised autonomy

## 1. 요청 배경

현재 Palamedes에는 설치 가능한 CLI, 대화 세션, Codex/OpenAI/OpenRouter provider,
작업공간 관찰, 제한된 watch, 팀 공유 상태, 미션·handoff·outcome 원장이 있다.
그러나 Codex는 주로 격리된 추론 provider로 사용되고 있으며, 실제 저장소를 수정하고
검증하는 실행 에이전트를 Palamedes가 생성·감독·회수하는 경로는 없다.

Zaeze 장기 개발에서는 다음 문제가 관찰됐다.

- 에이전트가 골라 전달한 일부 정보만으로 Palamedes가 판단했다.
- 온라인 멀티게임이라는 제품 불변 조건과 기존 Rust 실시간 런타임을 놓친 채 로컬
  2인용 윷놀이 경로를 정밀하게 강화했다.
- 모바일, 웹 소비자, 웹 관리자, Rust realtime, 개발·운영 환경의 역할 차이가 공통
  기억에 충분히 반영되지 않았다.
- 소스 구현, 테스트, 빌드 산출물, 개발 배포, 실제 런타임 관찰이 구분되지 않았다.
- 다른 에이전트가 추가한 이미지·오디오와 변경된 역량이 후속 에이전트에 즉시 전달되지
  않아 오래된 판단이 재사용될 위험이 있었다.
- outcome이 존재하는 handoff가 열린 상태로 남고, 이미 충족된 기능이 다시 미션 후보가
  되는 등 원장과 사전감사 비용이 누적됐다.
- 자동 테스트가 게임의 재미, 관계 경험, 출시 준비를 증명하는 것처럼 과대 해석될 수
  있었다.

Palamedes의 다음 단계는 더 많은 역할을 추가하는 것이 아니라, 프로젝트를 직접 관찰하고
공통 사실을 유지하며 여러 실행 에이전트에 필요한 정보만 제공하고 결과를 회수하는 공동
두뇌가 되는 것이다.

## 2. 목표 사용자 경험

설치 후 사용자는 다음만 수행한다.

```bash
cd /path/to/project
palamedes
```

인자 없는 실행은 다음을 자동 수행해야 한다.

1. 현재 디렉터리를 workspace로 선택한다.
2. Codex CLI 설치와 인증 상태를 감지한다.
3. 프로젝트의 `.palamedes` 원장을 생성하거나 복원한다.
4. `AGENTS.md`, 제품 정렬 정보, Git 상태, 기존 역량, 활성 미션을 읽는다.
5. 관찰·준비·실행 가능한 안전한 작업을 계속 처리한다.
6. 제품 방향 변경, 운영 변경, 외부 부작용, 유료 작업 등은 승인 대기로 전환한다.
7. 사용자는 상태를 지켜보고 필요한 결정에만 응답한다.

터미널은 내부 사고 전문이 아니라 상태 변화와 의사결정만 보여준다.

```text
OBSERVE   game:yut 관련 변경 감지
PREFLIGHT 기존 Rust room runtime과 Flutter adapter 확인
READY     두 기기 재접속 검증 미션
RUN       codex-agent-01
PASS      관련 테스트 통과
EVIDENCE  실제 두 클라이언트 증거는 아직 없음
WAIT      개발 서버 배포 승인 필요
```

## 3. Palamedes와 실행 에이전트의 책임

Palamedes Core가 소유할 것:

- 제품 목적, 표면별 역할, 불변 조건
- 기존 역량과 통합 간극
- 관찰의 출처·기준 revision·최신성·무효화 조건
- 미션 선택, 비용 모드, 활성 lease
- 다른 에이전트의 작업과 계약 충돌
- 주장별 증거 요구사항
- handoff·outcome·후속 결정
- 장기 기억 압축과 에이전트별 Context Packet

Codex 실행 에이전트와 독립 스킬이 수행할 것:

- 저장소 탐색과 코드 수정
- 테스트·분석·렌더·E2E 실행
- Flutter 시각 검증
- 멀티플레이 두 기기 검증
- 미디어 생성과 품질 검수
- 구조화된 변경·증거·미검증 항목 반환

Palamedes가 모든 실행 기술을 내장하지 말고 교체 가능한 실행기와 스킬을 지휘해야 한다.

## 4. 양방향 정보 흐름

에이전트 시작 전 Palamedes는 작업별 Context Packet을 생성한다.

```yaml
packet_version: 1
mission_id: mission-...
generated_at: ...
base_revision: ...
global_direction: ...
surface:
  key: game:yut
  role: 온라인 2대2 캐릭터 조합형 보드게임
invariants: []
known_capabilities: []
relevant_decisions: []
active_conflicts: []
required_evidence: []
unknowns: []
authorized_scope: []
forbidden_scope: []
```

에이전트는 다음을 구조화해 반환한다.

```yaml
mission_id: mission-...
base_revision: ...
final_revision: ...
changes: []
claims: []
tests: []
not_verified: []
new_capabilities: []
invalidated_capabilities: []
follow_up_candidates: []
outcome:
  type: validated_improvement
```

Palamedes는 에이전트 보고를 그대로 사실로 채택하지 않고 현재 저장소·테스트·런타임
증거와 대조한다.

## 5. 직접 관찰과 공통 사실 계층

관찰 레코드는 최소한 다음을 포함한다.

```yaml
observation_id: obs-...
observer: ...
surface: ...
base_revision: ...
observed_at: ...
claim:
  type: source | integration | test | build | deployment | runtime | human
  statement: ...
evidence: []
confidence: 0
invalidated_by: []
limitations: []
```

정보는 다음 층으로 분리한다.

1. 사람이 승인한 제품 사실과 불변 조건
2. 저장소에서 직접 관찰한 역량
3. 테스트·렌더·E2E 등 검증 상태
4. 짧은 유효기간을 가진 환경·배포 상태
5. 반증 가능한 임시 가설

권위 우선순위는 사람 승인 불변 조건 → 현재 직접 관찰 → 반복 가능한 증거 → 구조화된
에이전트 보고 → 에이전트 추론 순으로 한다.

## 6. 지속 자율성

지속 자율성은 모델을 쉬지 않고 호출하는 것이 아니다.

평상시에는 다음 결정적 작업만 수행한다.

- 파일·Git 변경 감시
- capability 인덱스 무효화와 증분 갱신
- 원장 정합성 검사
- 테스트 결과 수집
- 활성 작업과 충돌 확인
- 중복 미션 제거

다음 사건에서만 추론을 깨운다.

- 의미 있는 코드·문서·제품 방향 변경
- 테스트 실패
- outcome 도착
- 관련 에이전트 충돌
- 증거 유효기간 만료
- 준비된 미션 소진

변화가 없으면 비용 없이 대기한다. 동일 신호는 반복 추론하지 않는다.

## 7. 자율성 단계와 안전 경계

- `observe`: 읽기·관찰·후보 생성만
- `prepare`: Context Packet, 증거 계약, 실행 계획 준비
- `supervised`: 안전한 프로젝트 내부 수정과 테스트 자동 수행; 외부 부작용은 승인
- `autonomous`: 사전 정책 안의 여러 미션을 연속 실행

기본값은 `supervised`로 한다.

자동 허용 후보:

- 읽기·검색·정적 분석·테스트
- 기존 역량 인덱스와 원장 갱신
- 승인된 범위의 국소 코드·테스트·문서 수정

반드시 승인할 작업:

- 제품 목적·핵심 규칙 변경
- 운영 배포와 데이터 변경
- 계정·권한·외부 메시지 변경
- 유료 API·GPU 작업
- 대량 삭제와 광범위 아키텍처 전환
- 사람 플레이테스트가 필요한 제품 주장

## 8. 비용 적응형 사이클

모든 작업에 전체 다중 역할 사이클을 사용하지 않는다.

- `lookup`: 구현 여부 확인, 0~1 모델 호출
- `micro`: 국소 결함, 1~2회
- `component`: 여러 파일과 통합 경계, 2~4회
- `product`: 목적·여정·아키텍처, 전체 역할 선택 가능
- `human-validation`: 재미·신뢰·문화·관계 경험, 사람 증거 필요

실행 전 예상 호출 수·토큰·시간·필요 증거를 표시한다.

## 9. 최소 CLI 계약

최종 사용자 기본 진입점:

```bash
palamedes
```

내부 또는 고급 명령:

```bash
palamedes agent prepare --task "..." --workspace ...
palamedes agent run <mission-id> --executor codex
palamedes agent report <mission-id> --evidence-file result.json
palamedes agent status
palamedes agent refresh <mission-id>

palamedes daemon start
palamedes daemon status
palamedes daemon logs
palamedes daemon stop
```

터미널 명령:

```text
/status /agents /mission /run /diff /evidence
/approve /reject /pause /resume /stop /history /quit
```

## 10. 구현 순서

1. 인자 없는 `palamedes`를 Codex 자동 감지 대화형 진입점으로 만든다.
2. `agent prepare/status/report`와 버전된 Context Packet·Result Packet 스키마를 만든다.
3. 제품 정렬, capability, 최신 관찰, 활성 작업을 packet에 증분 컴파일한다.
4. Codex CLI 실행 어댑터와 권한·취소·timeout·stdout/stderr 증거 수집을 구현한다.
5. `agent run`이 승인된 미션을 실행하고 결과를 검증 대기 상태로 반환하게 한다.
6. handoff/outcome 수명주기와 reconcile을 완결한다.
7. workspace·계약 단위 lease와 충돌 감지를 구현한다.
8. 이벤트 기반 supervised loop를 추가한다.
9. 재시작 복구, 중복 억제, 비용 한도, 감사 로그를 검증한다.
10. 실제 Zaeze 멀티에이전트 개발에서 전후 비교한 뒤 daemon UX를 고도화한다.

처음부터 화려한 TUI, 자체 셸, 자체 코딩 모델, 범용 도구 생태계를 만들지 않는다.
기존 Codex CLI와 현재 Palamedes 원장·watch·team 기능을 재사용한다.

## 11. 자가개선 사이클 규칙

각 사이클은 다음 순서를 따른다.

```text
현재 기능 사전감사
→ 가장 작은 미충족 수직 절편 선택
→ 실패 우선 계약
→ 구현
→ 실제 CLI에서 검증
→ 불리한 결과 포함 outcome 기록
→ 완료 handoff 종료
→ 다음 절편 선택 또는 중단
```

다음 결과 유형을 정직하게 사용한다.

```text
validated_improvement
null_finding
already_satisfied
adverse_result
insufficient_evidence
blocked_by_environment
misaligned_mission
prototype_only
```

이미 구현된 기능을 다시 만드는 사이클, 문서만 추가하는 사이클, 실제 사용 경로가 없는
추상 인프라 확장은 기각한다.

## 12. 1차 완료 기준

다음 시나리오가 깨끗한 환경에서 통과해야 한다.

1. 사용자가 프로젝트에서 `palamedes`를 실행한다.
2. Codex 설치·인증과 workspace를 자동 감지한다.
3. Palamedes가 제품 방향과 기존 역량을 포함한 Context Packet을 만든다.
4. 안전한 작은 미션을 Codex 실행 에이전트에 전달한다.
5. Codex가 저장소를 수정하고 지정 테스트를 실행한다.
6. Palamedes가 diff·테스트·미검증 사항을 Result Packet으로 회수한다.
7. 필요한 증거가 충족되면 outcome을 기록하고 handoff를 닫는다.
8. 재시작 후 동일 작업을 중복 실행하지 않는다.
9. 관련 계약을 다른 에이전트가 소유하면 충돌을 표시하고 실행하지 않는다.
10. 운영 변경을 시도하면 사용자 승인 대기로 전환한다.

측정 지표:

- 요청부터 첫 유효 작업 시작까지의 시간
- 최초 조사에 사용한 모델 호출과 토큰
- 이미 충족된 기능 재제안 비율
- 잘못된 제품 방향의 미션 비율
- 에이전트 간 충돌·재작업률
- 준비된 미션의 실제 채택률
- 사람 개입 없이 완료된 안전한 미션 비율
- 완료 outcome과 열린 handoff의 불일치 수

## 13. 이번 자가개선 요청

현재 저장소 기능을 먼저 조사하고 위 요구사항 전체를 한 번에 구현하지 않는다.

다음 질문에 답하는 가장 작은 첫 수직 절편을 선택하라.

> 사용자가 프로젝트에서 `palamedes`만 실행했을 때, 현재 Palamedes의 장기 기억과 제품
> 방향을 포함한 검증 가능한 Context Packet을 만들고 Codex 실행 에이전트에 안전하게
> 넘길 준비가 되어 있는가?

기존 기능으로 이미 충족된 부분, 최초로 실패하는 계약, 첫 구현 범위, 비목표, 필요한
증거를 명시하라. 구현 이후 실제 CLI 흐름을 실행하고 결과를 원장에 기록하라.

## 14. 최초 제출 관찰

2026-07-30에 이 요청을 현재 CLI의 Codex provider에 실제 제출했다.

- 전체 요청을 기본 `/cycle`로 제출한 세션:
  `autonomous-agent-cli-request`
- 과거 의제와 독립적인 짧은 요청을 기본 `/cycle`로 제출한 세션:
  `autonomous-agent-cli-request-v2`
- 같은 요청을 `/mission`으로 제출한 세션:
  `autonomous-agent-cli-mission`
- Vision과 자동 meta-learning을 끈 `/cycle --mode audit` 제출 세션:
  `autonomous-agent-cli-audit-cycle`

기본 cycle 두 개는 과거 Vision·meta-learning 상태와 함께 병렬로 실행되기 시작해 중복
처리 위험이 확인되었으므로 명시적으로 중단했다. 감사 모드는 다음 네 역할을 독립적으로
완료했다.

```text
Running independent roles: interpreter → inventor → adversary → selector
Audit mode: automatic Vision Genesis and meta-learning calls are disabled.
[cycle-00dbbb389a4a] interpreter → inventor → adversary → selector
```

결과:

```yaml
cycle_id: cycle-00dbbb389a4a
status: selected
selected_candidate_id: candidate-3
live_model_call_count: 4
provider_tokens: 106635
mission_id: mission-28146dc0ebc9
```

선택된 첫 미션은 구현이 아니라 다음 bounded preflight다.

> canonical request에서 빈 인자 실행 acceptance assertion을 추출하고, 실제 packaged
> `palamedes` entry point를 일회 실행해 exit code, stdout, stderr, 파일시스템 부작용,
> Context Packet 요구·생성 여부를 기록한 뒤 정확히 한 개의 최초 실패 절편을 선택한다.

이 미션을 승인하려 했으나 기존 `outcome-656f77bde982`의 production-correction gate가 열려
있어 다음 오류로 차단됐다.

```text
Mission approval blocked by unresolved outcome evidence: outcome-656f77bde982
```

새 요청의 contract는 해당 outcome ID가 입력에 제공되지 않았다고 기록했지만, approval
단계에서는 전역 열린 gate에 대한 명시적 응답을 요구했다. 따라서 자가개선 요청은 문서,
세션, cognition cycle, draft mission까지 전달됐지만 handoff는 생성되지 않았다.

이것은 다음 운영 문제의 실제 증거다.

- 새 요청 전에 전역 gate가 있으면 관련 surface가 달라도 승인 전체가 차단된다.
- selector가 받은 open gate 문맥과 생성 contract의 `outcome_response`가 불일치할 수 있다.
- 동시에 여러 cycle을 제출하면 중복 실행을 막는 단일 활성 cycle/lease가 없다.

기존 gate를 우회하거나 임의 종료하지 않는다. 해당 correction을 정상 disposition한 뒤
`mission-28146dc0ebc9`을 최신 코드로 다시 preflight하고 승인 또는 폐기해야 한다.
