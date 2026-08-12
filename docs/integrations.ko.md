# 통합

<p align="center">
  <a href="integrations.md">English</a> · <strong>한국어</strong>
</p>

Palamedes는 실행 에이전트보다 upstream에 위치합니다. Host가 process lifecycle,
credential, side effect, 승인과 delivery 권한을 유지합니다.

## 통합 표면

| 표면 | 용도 |
| --- | --- |
| CLI | 로컬 사람·에이전트 워크플로 |
| HTTP API | 언어 중립 plan-state 접근 |
| Python client | 편의 메서드와 retry 동작 |
| Agent wrapper | 제한된 mission drafting과 handoff |
| Reference adapter | 실험적 host 패턴 |

## HTTP server

```bash
python3 palamedes_server.py --host 127.0.0.1 --port 8787
```

읽기 endpoint에는 `/plan`, `/qa`, `/health`, `/cycle`, `/history`, `/validate`,
`/tools`가 있습니다. 쓰기에는 `/plan`, `/evidence`, `/replan`, restore와 generic tool
실행이 있습니다. 안전한 쓰기는 현재 fingerprint를 사용해 오래된 상태를 거부합니다.

## Python client

```python
from palamedes_sdk import PalamedesClient

client = PalamedesClient("http://127.0.0.1:8787")
cycle = client.get_cycle(history_limit=5)
updated = client.update_plan({"goal": "검증된 agent layer 출시"})
```

Client는 stale-write 처리, refresh-and-retry, 쓰기 후 cycle snapshot, restore,
idempotency key와 선택적 health gate를 지원합니다.

## Host 책임

1. 출처와 경계가 명확한 context를 제공합니다.
2. 계획 identity와 실행 identity를 분리합니다.
3. delivery 전에 명시적 승인을 요구합니다.
4. 귀속을 성급히 단정하지 않고 관찰 가능한 outcome을 반환합니다.
5. fingerprint conflict와 restore 계보를 존중합니다.

## 상세 가이드

- [AgentScope 통합](integration-agentscope.md)
- [Agent team 통합](integration-agent-teams.md)
- [Agents bootstrap](palamedes-agents-bootstrap.md)
- [Agent skills](palamedes-agents-skills.md)
- [Pre-planner contract](palamedes-pre-planner-contract.md)
- [Reference agent pattern](reference-agent-patterns.md)
- [Python SDK](../palamedes_sdk/client.py)
- [TypeScript consumer](../palamedes_reference_consumer.ts)
- [Kernel adapter 예제](../examples/palamedes_kernel_adapter.py)
- [Planner host 예제](../examples/palamedes_planner_host.py)

[STABILITY.md](../STABILITY.md)에 별도 표시가 없으면 reference 표면은 실험적입니다.
