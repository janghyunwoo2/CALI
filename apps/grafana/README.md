# Grafana Dashboards

이 폴더는 Grafana 대시보드 JSON 파일을 관리합니다.

## 구조
```
dashboards/
├── log-overview.json       # 로그 전체 개요
├── error-analysis.json     # 에러 분석
└── performance.json        # 성능 모니터링
```

## 사용 방법
1. Grafana UI에서 대시보드 생성
2. JSON 내보내기
3. 이 폴더에 저장
4. Git으로 버전 관리

## 배포
- Grafana Provisioning으로 자동 배포
- 또는 Terraform/Helm에서 참조
