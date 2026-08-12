# 운영 레퍼런스

<p align="center">
  <a href="operations-reference.md">English</a> · <strong>한국어</strong>
</p>

## 명령 그룹

```text
plan, replan                 방향 생성과 수정
evidence, hypothesis         주장과 불확실성 기록
view, inquiry, encounter     관점 변화 보존
probe                        학습을 만드는 개발 단계 등록
observe, watch               제한된 작업공간 신호 수집
qa, validate, health         상태와 계약 품질 검사
history, restore             revision 확인과 복원
chat                         provider 기반 cognition 실행
workspace                    저장소 등록과 선택
```

전체 옵션은 `palamedes --help` 또는 `palamedes <command> --help`로 확인합니다.

## Fingerprint와 동시성

쓰기 가능한 모든 계획에는 fingerprint가 있습니다. Client는 상태를 바꿀 때 예상
fingerprint를 제공해야 합니다. 불일치는 덮어쓰기 허가가 아니라 conflict입니다. 최신
계획을 다시 읽고 변경이 여전히 타당할 때만 retry해야 합니다.

## Restore

Restore는 복원 가능한 과거 상태에서 새 revision을 만들며 중간 역사를 삭제하지
않습니다. 복원 전에 대상을 preview하고 반환된 새 fingerprint를 보존하세요.

## 저장소

기본 state root는 선택한 작업공간의 `.palamedes/`입니다. revision, event, mission,
observation과 워크플로별 store를 포함합니다. 일관성은 `palamedes health`와
`palamedes storage`로 검사합니다.

## HTTP API

```bash
python3 palamedes_server.py --host 127.0.0.1 --port 8787
```

```text
GET  /plan /qa /health /cycle /history /validate /tools
POST /plan /evidence /replan /restore/preview /restore
POST /tools/<tool_name>
POST /tools/execute
POST /agent/act
```

현재 실행 가능한 표면은 server의 `/tools` 응답을 기준으로 합니다.

## 개발 검증

```bash
make compile
make test
make scaffold-test
make schema-check
make package-check
make check
```

## 계약 문서

- [안정성 등급](../STABILITY.md)
- [계약 버전 정책](../CONTRACT_VERSIONING.md)
- [기여 가이드](../CONTRIBUTING.md)
- [Plan schema](../schemas/plan.schema.json)
- [SDK client](../palamedes_sdk/client.py)

운영 명령은 로컬 Palamedes 상태를 변경할 수 있습니다. Host가 명시적으로 호출하지 않는
한 실행 에이전트와 외부 시스템은 Palamedes 권한 밖에 있습니다.
