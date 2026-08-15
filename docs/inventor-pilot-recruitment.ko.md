# Inventor Pilot 외부 프로젝트 모집

## 제안 문안

안녕하세요. 저는 오픈소스 Goal Discovery·Goal Synthesis 시스템 Palamedes를 개발하고
있습니다. 이미 정해진 기능을 구현하는 도구가 아니라, 프로젝트가 다음에 추구할 가치가
있는 기회를 발견하는 능력을 검증하려 합니다.

귀하의 프로젝트를 판매·홍보하거나 무단으로 변경하려는 제안이 아닙니다. 다음 조건의
작은 블라인드 실험 참여를 요청드립니다.

- owner가 아직 결정하지 못한 실제 제품 질문 하나와 공개 가능한 자료를 제공
- 같은 모델·같은 정보·각 네 번의 호출로 일반 tournament와 Palamedes를 생성
- 출처를 숨긴 두 결과를 독립 리뷰어가 비교
- owner는 더 유용한 결과를 선택하거나 둘 다 거부
- 선택한 제안에서 1–7일 안에 가능한 작은 probe 하나만 실행
- 사전 합의한 metric과 실패 기준에 따라 결과 기록

코드 변경, 배포, credential 제공은 필수가 아닙니다. 프로젝트명이나 결과 공개 범위도
owner가 사전에 정할 수 있습니다. 실험 실패와 Palamedes 패배도 그대로 보존됩니다.

참여 의사가 있다면 `experiments/inventor-proof-intake.example.json`의 질문에 답하거나
다음 네 항목만 회신해 주십시오.

1. 지금 실제로 미결정인 제품 질문
2. 그 결정에 필요한 공개 가능한 자료
3. 1–7일 안에 측정할 수 있는 가장 작은 변화
4. 공개 가능한 범위와 익명화 요구

## 초기 연락 후보

이 목록은 참여 확정 사례가 아니라 공개적으로 feedback을 요청한 후보군이다. 연락과
참여 동의 전에는 Inventor proof case로 계산하지 않는다.

1. **ReacherX** — 작은 초기 오픈소스 제품이며 README에서 product direction과 agent
   behavior 논의를 위해 maintainer에게 먼저 연락하라고 명시한다. 모집 조건과 가장 잘
   맞고 실제 사용자 연구·outreach loop를 짧게 측정할 수 있다.
2. **ML Patron** — working prototype 단계이며 어느 부분이 자기 workflow 밖에서도
   일반화되는지 모르겠다고 밝히고 feedback과 시험 사용자를 공개 요청했다. 연구자 후원,
   실행 수요 또는 반복 사용 중 어느 loop를 우선할지 실제 질문으로 전환할 수 있다.
3. **mcp-policy** — v0.1 단계에서 policy schema와 GitHub Action 형태가 실제 팀에
   유용한지 feedback을 요청했다. security team의 adoption 경로 또는 local MCP 통제
   범위를 작은 문서·workflow probe로 검증할 수 있다.

보류 후보: AT Protocol commerce lexicon은 좋은 발명 문제지만 owner와 실행 주체가
분리될 가능성이 높다. LangGraph, Strapi, PhotoPrism은 첫 pilot에 비해 조직 규모와
의사결정 주기가 크므로 후속 검증 후보로 둔다.

## 연락 전 운영 규칙

- 세 owner는 Palamedes 개발과 무관해야 한다.
- owner에게 원하는 해답이나 Palamedes 후보를 먼저 보여주지 않는다.
- 공개 자료만으로 부족하면 owner가 정보 packet을 승인한 뒤 동결한다.
- 참여 동의 전 repository clone, 분석 결과 공개, 이슈 작성 또는 PR 제출을 하지 않는다.
- 이메일·GitHub issue·Discord 메시지는 사람의 명시적 승인 뒤 발송한다.
