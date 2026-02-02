# CALI Simulated Log Cases – Infra / EKS (01–100)
# "우리 서비스 로그 한 줄 + 대응 가이드" 형태로 바로 임베딩 가능한 더미데이터

---

## 01. Kinesis Shard Limit Exceeded
---
service: common-infra
error_message: Rate exceeded for shard in stream
---
### Incident Summary
[ERROR] 2024-03-15T09:00:00.123Z common-infra/v1.8.0 [kin-001]: Kinesis Error - Rate exceeded for shard in stream. | Context: {Stream="cali-log-stream", PutRecords="6500/s", ShardCount="4", Limit="1000/s/shard"}

### Root Cause
프로모션/배치 등으로 로그 유입량이 급증해 shard 처리 한도를 초과. 재시도 폭주로 백프레셔가 더 악화될 수 있음.

### Action Items
1. (즉시) PutRecords 실패율/재시도율 확인 후, Fluent Bit/Producer retry backoff+jitter 적용.
2. (즉시) shard 확장(UpdateShardCount) 또는 On-Demand 모드 전환 검토.
3. (확인) 트래픽 급증 원인(배포/프로모션/오류 루프 로그 폭증) 식별.
4. (재발방지) 스트림 autoscaling/알람(put throttle) + 로그 샘플링/레이트리밋 정책.

---

## 02. CoreDNS Resolution Timeout
---
service: network
error_message: DNS resolution failed for service
---
### Incident Summary
[ERROR] 2024-03-15T09:02:00.456Z network/v2.3.1 [dns-002]: DNS Error - DNS resolution failed for service. | Context: {Query="db-cache.svc.cluster.local", Timeout="2s", Pod="order-api-7f9c", CoreDNSCPU="95%"}

### Root Cause
CoreDNS 파드 과부하/리소스 부족 또는 DNS QPS 급증. NodeLocal DNSCache 미적용 시 노드 전체 영향 가능.

### Action Items
1. (즉시) CoreDNS replica 증설 + 리소스 요청/제한 상향.
2. (즉시) 문제 파드에서 nslookup/dig 재현으로 DNS vs 네트워크 분리.
3. (확인) DNS QPS 상위 네임/클라이언트 파드 파악(폭주 원인).
4. (재발방지) NodeLocal DNSCache 도입 + CoreDNS 캐시/튜닝 + 알람 설정.

---

## 03. EKS API Server Throttling
---
service: eks-control-plane
error_message: Throttling request to kube-apiserver
---
### Incident Summary
[WARN] 2024-03-15T09:04:10.111Z eks-control-plane/v1.28 [api-003]: ControlPlane - Throttling request to kube-apiserver. | Context: {Client="kube-controller-manager", QPS="150", Burst="300", HTTP="429"}

### Root Cause
컨트롤러/오퍼레이터가 과도한 watch/list 호출. 장애 시 재시도 폭주로 429 증가.

### Action Items
1. (즉시) 429 발생 주체(컨트롤러/외부 오퍼레이터) 식별.
2. (확인) 최근 배포된 오퍼레이터/컨트롤러 설정 변경 여부 점검.
3. (완화) 해당 컴포넌트 QPS/Burst 설정 조정 또는 일시 중지.
4. (재발방지) 컨트롤러 리소스 튜닝 가이드 + API 서버 사용량 알람.

---

## 04. etcd Request Latency High
---
service: eks-control-plane
error_message: etcd request latency too high
---
### Incident Summary
[CRITICAL] 2024-03-15T09:06:00.000Z eks-control-plane/v1.28 [etcd-004]: ControlPlane - etcd request latency too high. | Context: {P99="1200ms", Threshold="250ms", Writes="high"}

### Root Cause
리소스 churn(대량 Pod create/delete) 또는 watch 폭주로 etcd 부하 증가. 컨트롤 플레인 전반 지연 유발.

### Action Items
1. (즉시) 대량 롤링/스케일 이벤트 중단(배포/잡) 및 안정화.
2. (확인) 이벤트 폭주 원인(크래시루프/오토스케일/잡 스파이크) 파악.
3. (완화) 불필요한 컨트롤러/오퍼레이터 일시 중지.
4. (재발방지) 대량 배포 시 rate-limit/배치화 + 리소스 쿼터 + 이벤트 알람.

---

## 05. ImagePullBackOff (ECR 403)
---
service: eks-cluster
error_message: ImagePullBackOff - 403 Forbidden
---
### Incident Summary
[ERROR] 2024-03-15T09:08:30.222Z eks-cluster/v1.28 [img-005]: Deploy Error - ImagePullBackOff - 403 Forbidden. | Context: {Pod="payment-api-6d7f", Image="123456789.dkr.ecr.ap-northeast-2.amazonaws.com/payment:v2.5.1", NodeRole="eks-node-role"}

### Root Cause
노드 IAM Role에 ECR read 권한 누락, 또는 cross-account/pull secret 설정 문제.

### Action Items
1. (즉시) 이미지 태그 존재 여부 확인(오타/미푸시).
2. (즉시) 노드 IAM Role/ECR 정책(ecr:GetAuthorizationToken, BatchGetImage 등) 점검.
3. (확인) IRSA 사용 시 serviceAccount에 imagePull 권한/secret 연결 여부 확인.
4. (재발방지) CI 배포 전 프리플라이트(이미지 존재+권한 체크) 추가.

---

## 06. CrashLoopBackOff (App Exit 1)
---
service: eks-cluster
error_message: CrashLoopBackOff
---
### Incident Summary
[ERROR] 2024-03-15T09:10:00.333Z eks-cluster/v1.28 [crash-006]: Pod Error - CrashLoopBackOff. | Context: {Pod="order-api-7f9c", ExitCode="1", Restarts="12", Node="ip-10-0-1-21"}

### Root Cause
환경변수/시크릿 누락, DB 연결 실패, 잘못된 설정으로 프로세스 즉시 종료. 반복 재시작으로 노드/로그/CPU 소모.

### Action Items
1. (즉시) pod logs(이전 로그 포함)에서 최초 에러 확인.
2. (즉시) 최근 배포/환경변수 변경 여부 확인 후 롤백 고려.
3. (확인) readiness/liveness 설정이 과도하게 공격적인지 점검.
4. (재발방지) startupProbe 도입 + config validation + 배포 전 smoke test.

---

## 07. OOMKilled
---
service: eks-cluster
error_message: Container killed due to OOM
---
### Incident Summary
[ERROR] 2024-03-15T09:12:10.444Z eks-cluster/v1.28 [oom-007]: Pod Error - Container killed due to OOM. | Context: {Pod="analytics-worker-5c8b", MemLimit="512Mi", Peak="780Mi", Node="ip-10-0-2-11"}

### Root Cause
메모리 리밋 대비 워킹셋 증가(데이터 급증/누수/버퍼링). 재시작 반복 시 처리 지연 누적.

### Action Items
1. (즉시) 임시로 mem limit 상향 또는 HPA 스케일아웃으로 분산.
2. (확인) 최근 데이터량/배포 변경 여부 확인.
3. (확인) heap/profile로 누수/대용량 객체 원인 파악.
4. (재발방지) 스트리밍/페이징 처리 + 메모리 알람/부하테스트.

---

## 08. Node NotReady
---
service: eks-cluster
error_message: NodeNotReady
---
### Incident Summary
[CRITICAL] 2024-03-15T09:14:00.000Z eks-cluster/v1.28 [node-008]: Node Alert - NodeNotReady. | Context: {Node="ip-10-0-3-7", Reason="KubeletStoppedPosting", AZ="apne2-a"}

### Root Cause
노드 장애(네트워크/디스크/커널), kubelet 다운, 또는 인스턴스 성능 문제.

### Action Items
1. (즉시) 해당 노드 cordon+drain(가능하면)으로 서비스 영향 최소화.
2. (확인) 노드 시스템 로그/kubelet 로그 확인(디스크, 네트워크, OOM).
3. (완화) ASG에서 문제 노드 교체(terminate) 검토.
4. (재발방지) 노드 헬스체크/오토리커버리 + 중요한 워크로드 PDB 설정.

---

## 09. Node Disk Pressure (Eviction)
---
service: eks-cluster
error_message: NodeHasDiskPressure
---
### Incident Summary
[ERROR] 2024-03-15T09:16:00.555Z eks-cluster/v1.28 [disk-009]: Node Alert - NodeHasDiskPressure. | Context: {Node="ip-10-0-1-33", EphemeralUsed="92%", Threshold="85%", EvictedPods="6"}

### Root Cause
컨테이너 로그/이미지/임시파일(/tmp) 누적으로 ephemeral storage 부족 → kubelet이 파드를 Evict.

### Action Items
1. (즉시) 영향 노드에서 불필요 이미지/컨테이너 정리, 로그 로테이션 확인.
2. (즉시) Evicted 파드 재스케줄 상황 확인 및 서비스 영향 완화.
3. (확인) 특정 파드가 ephemeral 과다 사용(대용량 로그/파일)하는지 확인.
4. (재발방지) logrotate/Fluent Bit 설정 + ephemeral requests/limits + 정리 작업 자동화.

---

## 10. Node Memory Pressure
---
service: eks-cluster
error_message: NodeHasMemoryPressure
---
### Incident Summary
[WARN] 2024-03-15T09:18:00.000Z eks-cluster/v1.28 [mem-010]: Node Alert - NodeHasMemoryPressure. | Context: {Node="ip-10-0-2-19", MemAvailable="3%", Evictions="starting"}

### Root Cause
노드 과밀 배치/리소스 요청 과소 설정으로 압박. 캐시/버퍼 증가도 원인.

### Action Items
1. (즉시) 해당 노드 신규 스케줄 차단(cordon) 후 워크로드 분산.
2. (확인) top nodes/pods로 메모리 상위 파드 식별.
3. (완화) HPA/Cluster Autoscaler로 노드 증설.
4. (재발방지) requests/limits 재조정 + VPA 검토 + 과밀 방지.

---

## 11. Node PID Pressure
---
service: eks-cluster
error_message: NodeHasPIDPressure
---
### Incident Summary
[ERROR] 2024-03-15T09:20:00.000Z eks-cluster/v1.28 [pid-011]: Node Alert - NodeHasPIDPressure. | Context: {Node="ip-10-0-4-2", PidsUsed="32700", Limit="32768", TopPod="log-collector"}

### Root Cause
프로세스 폭주(포크 폭탄/버그)로 PID 고갈 → 새 프로세스 생성 불가.

### Action Items
1. (즉시) TopPod 격리/재시작 또는 노드 드레인 후 교체.
2. (확인) 해당 파드의 프로세스 수 증가 원인(버그/재시도 루프) 파악.
3. (재발방지) pid limit 설정 + 프로세스 폭주 감지 알람.

---

## 12. Pending Pods (Insufficient CPU)
---
service: scheduler
error_message: FailedScheduling - Insufficient cpu
---
### Incident Summary
[WARN] 2024-03-15T09:22:00.000Z scheduler/v1.28 [sch-012]: Scheduling - FailedScheduling - Insufficient cpu. | Context: {Deployment="payment-api", PendingPods="12", RequestsCPU="1500m", NodesAvailable="0"}

### Root Cause
요청 CPU 대비 클러스터 여유 부족(트래픽 급증/노드 축소/요청 과대).

### Action Items
1. (즉시) Cluster Autoscaler 상태 확인 후 노드 증설.
2. (확인) requests 과대 설정 여부 점검(실사용 대비).
3. (완화) 임시로 HPA/replica 조정 또는 우선순위 낮은 잡 중지.
4. (재발방지) 리소스 용량 계획 + 우선순위/쿼터 구성.

---

## 13. Pending Pods (Insufficient Memory)
---
service: scheduler
error_message: FailedScheduling - Insufficient memory
---
### Incident Summary
[WARN] 2024-03-15T09:23:00.000Z scheduler/v1.28 [sch-013]: Scheduling - FailedScheduling - Insufficient memory. | Context: {Deployment="auth-security-svc", PendingPods="8", RequestsMem="2Gi"}

### Root Cause
노드 메모리 여유 부족 또는 requests 과대.

### Action Items
1. (즉시) 노드 증설/큰 인스턴스로 스케일업.
2. (확인) requests/limits 재조정 및 VPA 검토.
3. (재발방지) 메모리 상위 파드 최적화 + capacity planning.

---

## 14. Pod Evicted (Ephemeral Storage)
---
service: eks-cluster
error_message: Pod ephemeral storage exceeded
---
### Incident Summary
[ERROR] 2024-03-15T09:24:00.000Z eks-cluster/v1.28 [eph-014]: Pod Evicted - ephemeral storage exceeded. | Context: {Pod="fluentbit-xyz", Used="5.2Gi", Limit="4Gi", Node="ip-10-0-1-33"}

### Root Cause
임시 파일/버퍼/로그가 과도하게 쌓여 ephemeral limit 초과.

### Action Items
1. (즉시) 해당 파드 로그/버퍼 설정 확인(파일 기반 버퍼 크기 제한).
2. (완화) ephemeral limit 상향(임시) + 원인 제거.
3. (재발방지) ephemeral requests/limits 설정 표준화 및 모니터링.

---

## 15. HPA Metrics Unavailable
---
service: autoscaling
error_message: failed to get cpu utilization
---
### Incident Summary
[ERROR] 2024-03-15T09:25:00.000Z autoscaling/v2 [hpa-015]: HPA Error - failed to get cpu utilization. | Context: {Target="deployment/order-api", Reason="metrics API unavailable"}

### Root Cause
metrics-server 장애/권한 문제/네트워크 문제로 메트릭 수집 불가 → 오토스케일 중단.

### Action Items
1. (즉시) metrics-server 상태/로그 확인 및 재시작.
2. (완화) 수동으로 replica 조정하여 트래픽 대응.
3. (재발방지) metrics-server HA 구성 + 알람 + 리소스 튜닝.

---

## 16. Metrics Server CrashLoop
---
service: monitoring
error_message: metrics-server CrashLoopBackOff
---
### Incident Summary
[CRITICAL] 2024-03-15T09:26:00.000Z monitoring/v0.6.4 [met-016]: metrics-server CrashLoopBackOff. | Context: {Pod="metrics-server-6f9c", ExitCode="1", Error="x509: certificate signed by unknown authority"}

### Root Cause
kubelet 인증서/메트릭 서버 TLS 설정 불일치.

### Action Items
1. (즉시) metrics-server args(--kubelet-insecure-tls 등) 설정 확인(보안 고려).
2. (확인) 노드 kubelet 인증서/CA 설정 점검.
3. (재발방지) 클러스터 업그레이드 시 metrics 구성 검증 체크리스트.

---

## 17. Cluster Autoscaler Not Scaling
---
service: autoscaling
error_message: cluster autoscaler not triggering scale up
---
### Incident Summary
[ERROR] 2024-03-15T09:27:00.000Z autoscaling/v1.27 [ca-017]: Autoscaler - not triggering scale up. | Context: {Reason="max node group size reached", NodeGroup="ng-app", PendingPods="20"}

### Root Cause
ASG 최대치 도달 또는 스케일업 조건 불일치(taint/selector).

### Action Items
1. (즉시) node group max size 상향 또는 추가 노드그룹 생성.
2. (확인) Pending 파드의 nodeSelector/taint toleration 확인.
3. (재발방지) 용량 한도 알람 + 다중 노드그룹 전략.

---

## 18. Pod Topology Spread Skew
---
service: scheduler
error_message: topology spread constraints unsatisfied
---
### Incident Summary
[WARN] 2024-03-15T09:28:00.000Z scheduler/v1.28 [top-018]: Scheduling - topology spread constraints unsatisfied. | Context: {Deployment="wallet-service", AZs="3", Skew="2", MaxSkew="1"}

### Root Cause
AZ 분산 제약으로 스케줄 실패. 특정 AZ 용량 부족.

### Action Items
1. (즉시) 특정 AZ 용량 증설 또는 MaxSkew 완화(임시).
2. (확인) 노드 라벨/가용영역 분포 확인.
3. (재발방지) AZ별 최소 용량 확보 + 분산 정책 설계.

---

## 19. Pod Disruption Budget Blocking
---
service: eks-cluster
error_message: eviction blocked by PDB
---
### Incident Summary
[WARN] 2024-03-15T09:29:00.000Z eks-cluster/v1.28 [pdb-019]: Maintenance - eviction blocked by PDB. | Context: {PDB="payment-api-pdb", AllowedDisruptions="0", Node="ip-10-0-3-7"}

### Root Cause
PDB가 너무 엄격해서 드레인/업그레이드가 멈춤.

### Action Items
1. (즉시) 서비스 트래픽/레플리카 확인 후 PDB 완화(임시).
2. (재발방지) PDB는 운영/배포 전략과 함께 설계(최소 가용성 보장).

---

## 20. Liveness Probe Failed
---
service: eks-cluster
error_message: Liveness probe failed
---
### Incident Summary
[WARN] 2024-03-15T09:30:00.000Z eks-cluster/v1.28 [live-020]: Pod Unhealthy - Liveness probe failed. | Context: {Pod="payment-api-6d7f", FailCount="3", LastStatus="500", Timeout="1s"}

### Root Cause
헬스체크 엔드포인트가 DB/외부 의존을 포함하거나, 앱이 과부하로 응답 지연. 과도한 probe 설정으로 재시작 루프 유발.

### Action Items
1. (즉시) probe timeout/threshold 완화로 불필요 재시작 방지(임시).
2. (확인) 헬스체크가 외부 의존을 호출하는지 점검(가벼운 체크로 변경).
3. (재발방지) startupProbe 도입 + readiness/liveness 분리 + 서킷브레이커.

---

## 21. Readiness Probe Failed
---
service: eks-cluster
error_message: Readiness probe failed
---
### Incident Summary
[WARN] 2024-03-15T09:31:00.000Z eks-cluster/v1.28 [ready-021]: Pod NotReady - Readiness probe failed. | Context: {Pod="order-api-7f9c", Reason="timeout", Timeout="1s"}

### Root Cause
앱 웜업/캐시 로딩/DB 커넥션 풀 초기화가 완료되지 않음.

### Action Items
1. (즉시) readiness timeout/initialDelay 재조정.
2. (확인) 스타트업 단계에서 어떤 작업이 오래 걸리는지 로그로 확인.
3. (재발방지) 준비 완료 후 트래픽 받도록 설계(워밍업/프리로드 최소화).

---

## 22. Startup Probe Failed
---
service: eks-cluster
error_message: Startup probe failed
---
### Incident Summary
[ERROR] 2024-03-15T09:32:00.000Z eks-cluster/v1.28 [start-022]: Pod Startup - Startup probe failed. | Context: {Pod="analytics-worker-5c8b", FailCount="30", Period="10s"}

### Root Cause
기동 시간이 길어 startupProbe 임계치를 초과. 또는 실제로 기동 실패(시크릿/마이그레이션).

### Action Items
1. (즉시) 기동 로그 확인 후 DB 마이그레이션/시크릿 누락 점검.
2. (완화) startupProbe threshold 조정(정상적으로 오래 걸리면).
3. (재발방지) 기동 경로 최적화 + 배포 전 기동 테스트.

---

## 23. Service Endpoint Empty (No Ready Pods)
---
service: network
error_message: no endpoints available for service
---
### Incident Summary
[ERROR] 2024-03-15T09:33:00.000Z network/v2.3.1 [ep-023]: Service Error - no endpoints available for service. | Context: {Service="db-cache", Namespace="prod", CallerPod="order-api-7f9c"}

### Root Cause
대상 서비스 파드가 NotReady/크래시/스케일 0. 또는 label selector 불일치.

### Action Items
1. (즉시) 대상 deployment/pod readiness 상태 확인.
2. (확인) service selector와 pod label 매칭 확인.
3. (재발방지) 배포 시 selector/label 계약 테스트 + 최소 레플리카 유지.

---

## 24. NetworkPolicy Blocking Traffic
---
service: network
error_message: connection refused by network policy
---
### Incident Summary
[ERROR] 2024-03-15T09:34:00.000Z network/v2.3.1 [np-024]: NetworkPolicy - connection blocked. | Context: {From="order-api", To="db-cache:6379", Policy="deny-all-prod"}

### Root Cause
네트워크폴리시 변경으로 트래픽 차단(의도/실수).

### Action Items
1. (즉시) 최근 NetworkPolicy 변경 이력 확인 후 롤백/수정.
2. (확인) 필요한 ingress/egress 룰을 최소권한으로 추가.
3. (재발방지) 정책 변경은 PR 리뷰+시뮬레이션(테스트) 절차.

---

## 25. CNI IP Exhaustion
---
service: network
error_message: failed to assign an IP address to pod
---
### Incident Summary
[CRITICAL] 2024-03-15T09:35:00.000Z network/v2.3.1 [cni-025]: CNI Error - failed to assign an IP address to pod. | Context: {Node="ip-10-0-1-21", AvailableIPs="0", ENIs="maxed"}

### Root Cause
서브넷 IP 부족 또는 노드 ENI/IP 할당 한계 도달. 스케일아웃이 오히려 실패.

### Action Items
1. (즉시) 문제 서브넷 가용 IP 확인, 추가 서브넷/확장.
2. (완화) 노드 타입 변경(ENI 더 큰 인스턴스) 또는 max-pods 조정.
3. (재발방지) IP capacity planning + CNI prefix delegation 검토.

---

## 26. CNI Plugin Crash
---
service: network
error_message: aws-node CrashLoopBackOff
---
### Incident Summary
[ERROR] 2024-03-15T09:36:00.000Z network/v2.3.1 [cni-026]: CNI - aws-node CrashLoopBackOff. | Context: {DaemonSet="aws-node", Node="ip-10-0-2-11", Exit="1"}

### Root Cause
CNI 버전/권한 문제 또는 노드 네트워크 설정 불일치.

### Action Items
1. (즉시) aws-node 로그 확인(권한, IPAM 오류).
2. (확인) 최근 EKS 업그레이드/CNI 업데이트 여부 확인.
3. (재발방지) CNI 업그레이드는 점진 롤아웃 + 사전 호환성 체크.

---

## 27. kube-proxy iptables Sync Failed
---
service: network
error_message: kube-proxy iptables sync failed
---
### Incident Summary
[WARN] 2024-03-15T09:37:00.000Z network/v2.3.1 [kpxy-027]: kube-proxy - iptables sync failed. | Context: {Node="ip-10-0-3-9", Error="too many rules"}

### Root Cause
서비스/엔드포인트가 너무 많아 iptables 규칙 폭증. 노드 네트워크 성능 저하.

### Action Items
1. (즉시) 서비스/엔드포인트 수 급증 원인(배포/잡) 확인.
2. (완화) IPVS 모드 검토 또는 노드 분산.
3. (재발방지) 서비스 설계 최적화, 과도한 headless/service 생성 제한.

---

## 28. Ingress 502 Bad Gateway
---
service: ingress-nginx
error_message: 502 Bad Gateway
---
### Incident Summary
[ERROR] 2024-03-15T09:38:00.000Z ingress-nginx/v1.9.0 [ing-028]: Ingress - 502 Bad Gateway. | Context: {Host="api.cali.local", Upstream="order-api:8080", Latency="3ms"}

### Root Cause
업스트림 파드 다운/NotReady, 또는 서비스 엔드포인트 문제, 혹은 타임아웃/프로브 설정 부적절.

### Action Items
1. (즉시) 업스트림 파드 readiness/로그 확인.
2. (확인) 서비스 엔드포인트가 비어있는지 확인.
3. (완화) nginx timeouts 조정(임시) + 업스트림 스케일아웃.
4. (재발방지) readiness 설계 개선 + 배포 시 단계적 롤아웃.

---

## 29. Ingress 504 Gateway Timeout
---
service: ingress-nginx
error_message: 504 Gateway Timeout
---
### Incident Summary
[ERROR] 2024-03-15T09:39:00.000Z ingress-nginx/v1.9.0 [ing-029]: Ingress - 504 Gateway Timeout. | Context: {Host="api.cali.local", Path="/v1/payments", UpstreamTimeout="60s"}

### Root Cause
업스트림 응답 지연(슬로우쿼리/외부 PG 호출/스레드 고갈). 타임아웃이 너무 짧거나 트래픽 급증.

### Action Items
1. (즉시) 업스트림 p95/p99 지연 원인(외부 호출/DB) 분해.
2. (완화) HPA 스케일아웃 + 서킷브레이커(외부 의존) 적용.
3. (재발방지) 타임아웃/재시도 정책 표준화 + 슬로우 경로 최적화.

---

## 30. Ingress TLS Handshake Error
---
service: ingress-nginx
error_message: TLS handshake error
---
### Incident Summary
[WARN] 2024-03-15T09:40:00.000Z ingress-nginx/v1.9.0 [ing-030]: Ingress TLS - handshake error. | Context: {SNI="api.cali.local", Reason="unknown certificate", ClientIP="203.0.113.99"}

### Root Cause
인증서 체인 문제/만료 또는 클라이언트 구버전 TLS.

### Action Items
1. (즉시) 인증서 만료/체인(fullchain) 확인.
2. (확인) TLS 정책(1.2+) 및 SNI 매칭 확인.
3. (재발방지) cert-manager 자동 갱신 + 만료 알람.

---

## 31. cert-manager Failed to Issue Certificate
---
service: cert-manager
error_message: failed to issue certificate
---
### Incident Summary
[ERROR] 2024-03-15T09:41:00.000Z cert-manager/v1.13.0 [cm-031]: Cert Error - failed to issue certificate. | Context: {Issuer="letsencrypt-prod", Challenge="http-01", Reason="timeout"}

### Root Cause
DNS/HTTP 챌린지 라우팅 문제 또는 ACME 제공사 응답 지연.

### Action Items
1. (즉시) challenge 리소스 상태 확인 및 인그레스 라우팅 확인.
2. (확인) DNS 레코드/전파 상태 확인( dns-01 사용 시).
3. (재발방지) 발급/갱신 모니터링 + 장애 시 수동 발급 런북.

---

## 32. Prometheus Scrape Failed
---
service: monitoring
error_message: prometheus scrape failed
---
### Incident Summary
[WARN] 2024-03-15T09:42:00.000Z monitoring/v2.48.0 [mon-032]: Monitoring - prometheus scrape failed. | Context: {Target="order-api:metrics", Error="connection refused", FailRate="30%"}

### Root Cause
타겟 파드 재시작/네트워크 정책/metrics 포트 미노출.

### Action Items
1. (즉시) 타겟 파드 상태 및 metrics 포트/서비스 확인.
2. (확인) ServiceMonitor/PodMonitor selector 매칭 확인.
3. (재발방지) 메트릭 엔드포인트 표준화 + 모니터링 구성 테스트.

---

## 33. Fluent Bit Buffer Overflow
---
service: logging
error_message: buffer overflow
---
### Incident Summary
[ERROR] 2024-03-15T09:43:00.000Z logging/v2.2.0 [log-033]: FluentBit - buffer overflow. | Context: {Input="tail", Buffer="mem", Dropped="12000", Reason="output blocked"}

### Root Cause
출력(예: Kinesis/ES) 장애로 백프레셔 → 버퍼 포화 → 로그 드랍.

### Action Items
1. (즉시) 출력 대상 상태 확인(Throttle/Down) 및 복구.
2. (완화) 파일 기반 버퍼로 전환/버퍼 상향(임시) + 샘플링 적용.
3. (재발방지) 로그 파이프라인 이중화 + 백프레셔 설계 + 알람.

---

## 34. Log Volume Spike (Noisy Neighbor)
---
service: logging
error_message: log volume spike detected
---
### Incident Summary
[WARN] 2024-03-15T09:44:00.000Z logging/v2.2.0 [log-034]: Logging - log volume spike detected. | Context: {Namespace="prod", TopPod="order-api", Lines="2M/min", Cause="error loop"}

### Root Cause
애플리케이션 에러 루프가 과도한 로그 생성 → 디스크/파이프라인 비용 폭증.

### Action Items
1. (즉시) TopPod 로그 레벨 하향 또는 rate-limit(로그 샘플링) 적용.
2. (확인) 에러 루프 원인(외부 의존/코드 버그) 분석.
3. (재발방지) 로그 쿼터/샘플링 정책 + 에러 폭주 알림.

---

## 35. Kubelet Node Registration Failed
---
service: eks-cluster
error_message: failed to register node
---
### Incident Summary
[ERROR] 2024-03-15T09:45:00.000Z eks-cluster/v1.28 [kbl-035]: Node Error - failed to register node. | Context: {Node="ip-10-0-5-5", Error="Unauthorized", Bootstrap="true"}

### Root Cause
부트스트랩 토큰/인증서 문제 또는 IAM 인증 설정 오류.

### Action Items
1. (즉시) aws-auth ConfigMap/노드 IAM role 매핑 확인.
2. (확인) 노드 부트스트랩 로그 및 인증서 생성 과정 확인.
3. (재발방지) 노드 프로비저닝 표준화(IaC) + 변경 감지.

---

## 36. EBS CSI Attach Timeout
---
service: storage
error_message: AttachVolume.Attach timed out
---
### Incident Summary
[ERROR] 2024-03-15T09:46:00.000Z storage/v1.29.0 [ebs-036]: CSI - AttachVolume.Attach timed out. | Context: {PVC="pg-data", PV="pvc-123", Node="ip-10-0-3-9", Timeout="6m"}

### Root Cause
EBS API 지연/노드 장애/볼륨 상태 이상. Stateful 워크로드 기동 지연.

### Action Items
1. (즉시) PV/PVC 이벤트 확인 및 볼륨 상태(available/in-use) 점검.
2. (확인) 노드 NotReady 여부 확인, 필요 시 노드 교체.
3. (재발방지) 스토리지 클래스/재시도 정책 점검 + EBS CSI 모니터링.

---

## 37. EBS CSI Provisioning Failed
---
service: storage
error_message: failed to provision volume
---
### Incident Summary
[ERROR] 2024-03-15T09:47:00.000Z storage/v1.29.0 [ebs-037]: CSI - failed to provision volume. | Context: {StorageClass="gp3", Error="insufficient capacity", AZ="apne2-b"}

### Root Cause
특정 AZ의 EBS 용량 부족 또는 제한.

### Action Items
1. (즉시) 다른 AZ/스토리지 타입으로 재시도(가능하면).
2. (확인) 계정/리전 한도 및 AWS 상태 확인.
3. (재발방지) 멀티 AZ 분산 및 스토리지 사전 용량 계획.

---

## 38. EFS Mount Failed
---
service: storage
error_message: mount failed
---
### Incident Summary
[ERROR] 2024-03-15T09:48:00.000Z storage/v1.29.0 [efs-038]: EFS - mount failed. | Context: {Pod="reporting-0", EFS="fs-abc", Error="access denied"}

### Root Cause
보안그룹/NFS 포트 차단 또는 EFS access point/권한 설정 문제.

### Action Items
1. (즉시) SG에서 NFS(2049) 허용 여부 및 EFS mount target 확인.
2. (확인) access point/posix 권한 설정 점검.
3. (재발방지) 스토리지 네트워크 정책 템플릿화.

---

## 39. IRSA WebIdentity Error
---
service: common-infra
error_message: WebIdentityErr: failed to retrieve credentials
---
### Incident Summary
[ERROR] 2024-03-15T09:49:00.000Z common-infra/v1.8.0 [irsa-039]: IRSA - WebIdentityErr: failed to retrieve credentials. | Context: {ServiceAccount="payment-api", Namespace="prod", Error="invalid identity token"}

### Root Cause
서비스어카운트 어노테이션/STS 설정 오류 또는 OIDC provider 문제.

### Action Items
1. (즉시) SA annotation(role-arn) 및 OIDC provider 설정 확인.
2. (확인) 토큰 파일 마운트/만료 여부 확인.
3. (재발방지) IRSA 설정을 IaC로 관리 + 배포 전 검증.

---

## 40. STS AssumeRole Throttling
---
service: common-infra
error_message: Throttling: Rate exceeded
---
### Incident Summary
[WARN] 2024-03-15T09:50:00.000Z common-infra/v1.8.0 [sts-040]: STS - Throttling: Rate exceeded. | Context: {Action="AssumeRoleWithWebIdentity", Calls="500/s", Role="payment-role"}

### Root Cause
짧은 수명의 자격증명을 너무 자주 갱신(캐시 미사용)하거나 파드 급증으로 STS 호출 폭주.

### Action Items
1. (즉시) SDK 자격증명 캐시 사용 여부 확인 및 TTL 조정.
2. (완화) 파드 스케일 급증 시 단계적 롤아웃/스케일링.
3. (재발방지) STS 호출량 알람 + 캐시 전략 표준화.

---

## 41. Karpenter Provisioning Failed
---
service: autoscaling
error_message: karpenter failed to provision nodes
---
### Incident Summary
[ERROR] 2024-03-15T09:51:00.000Z autoscaling/v0.35.0 [karp-041]: Karpenter - failed to provision nodes. | Context: {Reason="subnet not found", PendingPods="15"}

### Root Cause
서브넷/보안그룹 태그 누락 또는 프로비저닝 권한 문제.

### Action Items
1. (즉시) Karpenter 설정(Subnet/SG selector) 및 태그 확인.
2. (확인) IAM 권한(EC2/SSM) 및 인스턴스 프로파일 확인.
3. (재발방지) 태그 표준화 + 프로비저닝 프리플라이트 체크.

---

## 42. Node Drain Stuck (Terminating Pods)
---
service: eks-cluster
error_message: drain stuck - pods terminating
---
### Incident Summary
[WARN] 2024-03-15T09:52:00.000Z eks-cluster/v1.28 [drain-042]: Maintenance - drain stuck. | Context: {Node="ip-10-0-3-7", TerminatingPods="9", Reason="finalizers"}

### Root Cause
finalizer 또는 PDB/볼륨 detach 지연으로 드레인이 멈춤.

### Action Items
1. (즉시) Terminating 파드의 finalizer/owner 확인 후 정리.
2. (확인) 스토리지 detach 지연 여부 확인(EBS).
3. (재발방지) finalizer 관리, PDB/Stateful drain 런북 강화.

---

## 43. Pod Terminating Stuck (Finalizers)
---
service: eks-cluster
error_message: pod stuck terminating
---
### Incident Summary
[ERROR] 2024-03-15T09:53:00.000Z eks-cluster/v1.28 [term-043]: Pod - stuck terminating. | Context: {Pod="db-migrator-0", Age="30m", Finalizers="kubernetes.io/pvc-protection"}

### Root Cause
PVC 보호 finalizer 또는 컨트롤러 정지.

### Action Items
1. (즉시) PV/PVC 상태 확인 후 안전하면 finalizer 제거(주의).
2. (확인) 컨트롤러(스토리지) 상태 확인.
3. (재발방지) 종료 훅/파이널라이저 운영 가이드 문서화.

---

## 44. ConfigMap Update Not Reflected
---
service: eks-cluster
error_message: config change not applied
---
### Incident Summary
[WARN] 2024-03-15T09:54:00.000Z eks-cluster/v1.28 [cfg-044]: Config - config change not applied. | Context: {Deployment="order-api", ConfigMap="order-config", PodsOld="10", PodsNew="0"}

### Root Cause
ConfigMap 변경은 파드 재시작 없이는 반영되지 않거나, 롤아웃 트리거(annot) 미적용.

### Action Items
1. (즉시) rollout restart 또는 checksum annotation 반영.
2. (재발방지) helm/kustomize에서 checksum 기반 자동 롤아웃 적용.

---

## 45. Secret Mount Failed
---
service: eks-cluster
error_message: secret not found
---
### Incident Summary
[ERROR] 2024-03-15T09:55:00.000Z eks-cluster/v1.28 [sec-045]: Pod Error - secret not found. | Context: {Pod="payment-api-6d7f", Secret="pg-api-key", Namespace="prod"}

### Root Cause
시크릿 누락/이름 오타/배포 순서 문제.

### Action Items
1. (즉시) Secret 존재/네임스페이스 확인 후 생성/수정.
2. (확인) GitOps/helm values에서 이름 일치 여부 점검.
3. (재발방지) 배포 전 시크릿 프리플라이트 검증 + .env 대신 SecretManager/IaC 관리.

---

## 46. AWS Load Balancer Controller Error
---
service: ingress
error_message: failed to reconcile target group
---
### Incident Summary
[ERROR] 2024-03-15T09:56:00.000Z ingress/v2.7.0 [alb-046]: ALB Controller - failed to reconcile target group. | Context: {Ingress="api-ing", Error="AccessDenied", Role="alb-controller"}

### Root Cause
ALB 컨트롤러 IAM 권한 부족 또는 리소스 태그/쿼터 문제.

### Action Items
1. (즉시) IRSA 역할 정책 확인(ELB, EC2, WAF).
2. (확인) 타겟그룹/리스너 한도 확인.
3. (재발방지) 컨트롤러 권한을 최소권한 템플릿으로 관리.

---

## 47. Target Group Health Check Failing
---
service: ingress
error_message: target group unhealthy
---
### Incident Summary
[WARN] 2024-03-15T09:57:00.000Z ingress/v2.7.0 [alb-047]: ALB - target group unhealthy. | Context: {Target="order-api", HCPath="/health", Status="500", Unhealthy="70%"}

### Root Cause
헬스체크 경로 오류/앱 장애/보안그룹 차단.

### Action Items
1. (즉시) HCPath 응답 확인(파드 직접 호출).
2. (확인) SG/NACL에서 ALB→노드/파드 트래픽 허용 여부 확인.
3. (재발방지) 헬스체크 경로 표준화 + readiness와 분리.

---

## 48. ServiceAccount Token Projection Failure
---
service: eks-cluster
error_message: failed to mount projected service account token
---
### Incident Summary
[ERROR] 2024-03-15T09:58:00.000Z eks-cluster/v1.28 [sa-048]: Pod Error - failed to mount projected service account token. | Context: {Pod="wallet-service", Error="permission denied"}

### Root Cause
노드/파일시스템 권한 문제 또는 kubelet 이슈.

### Action Items
1. (즉시) 노드 상태/디스크 상태 확인.
2. (확인) 해당 파드의 securityContext/fsGroup 설정 점검.
3. (재발방지) 노드 이미지/권한 정책 표준화.

---

## 49. Containerd Image GC Failing
---
service: eks-cluster
error_message: image garbage collection failed
---
### Incident Summary
[WARN] 2024-03-15T09:59:00.000Z eks-cluster/v1.28 [gc-049]: Node - image garbage collection failed. | Context: {Node="ip-10-0-1-33", DiskUsed="91%", Error="no space left"}

### Root Cause
디스크 부족으로 GC 실패. 이미지/로그 누적.

### Action Items
1. (즉시) 노드 디스크 정리(이미지 prune) 후 재확인.
2. (재발방지) 이미지 풀 정책/디스크 모니터링/노드 교체 자동화.

---

## 50. System Pod Pending (DaemonSet)
---
service: eks-cluster
error_message: daemonset pods pending
---
### Incident Summary
[WARN] 2024-03-15T10:00:00.000Z eks-cluster/v1.28 [ds-050]: System - daemonset pods pending. | Context: {DaemonSet="aws-node", Pending="3", Reason="insufficient cpu"}

### Root Cause
노드 용량 부족 또는 시스템 파드 requests 과대.

### Action Items
1. (즉시) 노드 증설/빈 노드 확인.
2. (확인) 시스템 파드 requests 최적화.
3. (재발방지) 시스템 파드 우선순위(priorityClass) 적용.

---

## 51. Pod Security Policy / Admission Denied
---
service: policy
error_message: admission webhook denied the request
---
### Incident Summary
[ERROR] 2024-03-15T10:01:00.000Z policy/v1.0.0 [adm-051]: Admission - denied the request. | Context: {Webhook="pod-security", Reason="privileged not allowed", Pod="debug-shell"}

### Root Cause
Pod Security(PSA) 정책 위반(권한 상승/privileged 컨테이너).

### Action Items
1. (즉시) 필요한 권한만으로 securityContext 수정(cap drop, runAsNonRoot).
2. (확인) 네임스페이스 PSA 레벨(baseline/restricted) 확인.
3. (재발방지) 배포 템플릿에 보안 컨텍스트 표준화 + 정책 테스트.

---

## 52. Mutating Webhook Timeout
---
service: policy
error_message: mutating webhook timeout
---
### Incident Summary
[ERROR] 2024-03-15T10:02:00.000Z policy/v1.0.0 [wh-052]: Webhook - mutating webhook timeout. | Context: {Webhook="istio-sidecar-injector", Timeout="10s", AffectedCreates="120"}

### Root Cause
웹훅 파드 과부하/다운으로 파드 생성이 지연/실패.

### Action Items
1. (즉시) 웹훅 서비스/파드 상태 확인 및 스케일아웃.
2. (완화) 장애 시 fail-open 정책 검토(보안/기능 영향 고려).
3. (재발방지) 웹훅 HA + SLO/알람.

---

## 53. Validating Webhook Certificate Expired
---
service: policy
error_message: x509: certificate has expired
---
### Incident Summary
[CRITICAL] 2024-03-15T10:03:00.000Z policy/v1.0.0 [wh-053]: Webhook TLS - certificate has expired. | Context: {Webhook="policy-validator", ExpiredAt="2024-03-14"}

### Root Cause
웹훅 TLS 인증서 갱신 누락 → API 서버가 호출 실패.

### Action Items
1. (즉시) 인증서 재발급/재배포(가능하면 자동화 도입).
2. (확인) cert-manager 연동/갱신 크론 점검.
3. (재발방지) 만료 알람 + 자동 갱신 파이프라인.

---

## 54. Kubernetes Events Flood
---
service: eks-control-plane
error_message: event rate too high
---
### Incident Summary
[WARN] 2024-03-15T10:04:00.000Z eks-control-plane/v1.28 [evt-054]: ControlPlane - event rate too high. | Context: {Events="5000/min", TopReason="BackOff", TopNamespace="prod"}

### Root Cause
CrashLoopBackOff 등 반복 이벤트가 컨트롤플레인/etcd 부하를 증폭.

### Action Items
1. (즉시) BackOff 상위 파드 원인 해결(근본 에러).
2. (완화) 불필요한 재시도/리스타트 줄이기(probe/백오프).
3. (재발방지) 이벤트 폭주 알람 + 자동 격리(runbook).

---

## 55. Node Clock Skew Detected
---
service: common-infra
error_message: node clock skew detected
---
### Incident Summary
[WARN] 2024-03-15T10:05:00.000Z common-infra/v1.8.0 [clk-055]: Node Alert - node clock skew detected. | Context: {Node="ip-10-0-2-11", Skew="180s", NTP="unsynced"}

### Root Cause
NTP 동기화 실패로 토큰/인증/TLS 등 다양한 장애를 유발 가능.

### Action Items
1. (즉시) 해당 노드 NTP 재동기화 또는 노드 교체.
2. (확인) 시간 드리프트가 확산되는지(여러 노드) 확인.
3. (재발방지) 시간 동기화 상태 모니터링/알람.

---

## 56. Container Time Drift Impact (JWT)
---
service: common-infra
error_message: time drift impacting auth
---
### Incident Summary
[ERROR] 2024-03-15T10:06:00.000Z common-infra/v1.8.0 [clk-056]: Infra - time drift impacting auth. | Context: {Service="auth-security-svc", Symptom="nbf/exp errors", Skew=">60s"}

### Root Cause
노드/컨테이너 시간 불일치로 nbf/exp 검증 실패가 증가.

### Action Items
1. (즉시) clock skew 노드 격리/교체.
2. (재발방지) 시간 드리프트 알람 + 허용 오차(leeway) 정책 정의(보안 고려).

---

## 57. EKS Upgrade Compatibility Issue
---
service: eks-cluster
error_message: api version deprecated
---
### Incident Summary
[ERROR] 2024-03-15T10:07:00.000Z eks-cluster/v1.28 [upg-057]: Upgrade - api version deprecated. | Context: {Resource="Ingress", ApiVersion="extensions/v1beta1", ClusterVersion="1.28"}

### Root Cause
클러스터 업그레이드로 deprecated API 제거 → 매니페스트 적용 실패.

### Action Items
1. (즉시) 해당 리소스 API 버전 최신으로 수정(networking.k8s.io/v1 등).
2. (확인) kube-no-trouble/scan으로 전체 deprecated API 점검.
3. (재발방지) 업그레이드 전 사전 호환성 스캔을 CI에 포함.

---

## 58. Pod Priority Preemption
---
service: scheduler
error_message: preempted by higher priority pod
---
### Incident Summary
[WARN] 2024-03-15T10:08:00.000Z scheduler/v1.28 [pre-058]: Scheduling - preempted by higher priority pod. | Context: {VictimPod="batch-job-1", Preemptor="system-critical", Node="ip-10-0-1-21"}

### Root Cause
우선순위 클래스에 의해 저우선 파드가 축출. 용량 부족 상태.

### Action Items
1. (즉시) 서비스 중요 파드에 priorityClass 설정 확인.
2. (확인) 용량 부족 원인(트래픽/노드) 해결.
3. (재발방지) 우선순위/쿼터 설계 및 배치 스케줄링 정책.

---

## 59. Kubelet Eviction (Memory)
---
service: eks-cluster
error_message: eviction due to memory pressure
---
### Incident Summary
[ERROR] 2024-03-15T10:09:00.000Z eks-cluster/v1.28 [ev-059]: Eviction - eviction due to memory pressure. | Context: {Node="ip-10-0-2-19", Evicted="order-api-7f9c", MemAvail="2%"}

### Root Cause
노드 메모리 부족으로 kubelet이 eviction 수행.

### Action Items
1. (즉시) 노드 증설/워크로드 분산.
2. (확인) 메모리 상위 파드 및 누수/폭주 원인 확인.
3. (재발방지) requests/limits 조정 + VPA/HPA 조합.

---

## 60. Kubelet Eviction (Disk)
---
service: eks-cluster
error_message: eviction due to disk pressure
---
### Incident Summary
[ERROR] 2024-03-15T10:10:00.000Z eks-cluster/v1.28 [ev-060]: Eviction - eviction due to disk pressure. | Context: {Node="ip-10-0-1-33", DiskAvail="4%", EvictedPods="5"}

### Root Cause
디스크 부족으로 eviction.

### Action Items
1. (즉시) 디스크 정리 및 로그 로테이션 확인.
2. (재발방지) 디스크 모니터링/알람, 노드 교체 자동화.

---

## 61. Container CPU Throttling High
---
service: monitoring
error_message: cpu throttling high
---
### Incident Summary
[WARN] 2024-03-15T10:11:00.000Z monitoring/v2.48.0 [cpu-061]: Perf - cpu throttling high. | Context: {Pod="payment-api-6d7f", Throttle="65%", CPUlimit="500m"}

### Root Cause
CPU limit이 낮아 throttling 발생 → 지연 증가.

### Action Items
1. (즉시) CPU limit 상향 또는 replica 증가.
2. (확인) 실제 CPU 사용량 프로파일링.
3. (재발방지) 리소스 튜닝 표준화 + SLO 기반 자동 조정.

---

## 62. Network Latency Spike (Node)
---
service: network
error_message: node network latency spike
---
### Incident Summary
[WARN] 2024-03-15T10:12:00.000Z network/v2.3.1 [net-062]: Network - node latency spike. | Context: {Node="ip-10-0-3-9", P99="120ms", Baseline="5ms"}

### Root Cause
노드/ENI 문제, AZ 네트워크 이슈, 혹은 noisy neighbor.

### Action Items
1. (즉시) 동일 AZ/노드에서 동시 발생 여부 확인.
2. (완화) 영향 노드 드레인 후 교체.
3. (재발방지) 네트워크 지표 알람 + 노드 분산 전략.

---

## 63. Pod-to-Pod Connection Reset
---
service: network
error_message: connection reset by peer
---
### Incident Summary
[ERROR] 2024-03-15T10:13:00.000Z network/v2.3.1 [net-063]: Network - connection reset by peer. | Context: {FromPod="order-api", ToPod="db-cache", Count="1200/5m"}

### Root Cause
대상 파드 재시작/리소스 부족/커넥션 제한. 또는 네트워크 정책/프록시 영향.

### Action Items
1. (즉시) 대상 파드 재시작/크래시 여부 확인.
2. (확인) 커넥션 풀/백로그 설정 및 리소스 사용량 확인.
3. (재발방지) 재시도 정책(백오프) + HPA + 커넥션 튜닝.

---

## 64. NLB Target Deregistration Delay
---
service: ingress
error_message: target deregistration delay
---
### Incident Summary
[WARN] 2024-03-15T10:14:00.000Z ingress/v2.7.0 [nlb-064]: NLB - target deregistration delay. | Context: {Service="order-api", Delay="300s", RequestsDropped="true"}

### Root Cause
드레인 타임/커넥션 유지 설정 불일치로 롤링 시 연결 드랍.

### Action Items
1. (즉시) terminationGracePeriod와 deregistration delay 정렬.
2. (확인) keep-alive 커넥션 처리(서버/클라) 점검.
3. (재발방지) 그레이스풀 셧다운 핸들러 + 롤링 전략 표준화.

---

## 65. Node Group Spot Interruption
---
service: eks-cluster
error_message: spot interruption notice
---
### Incident Summary
[WARN] 2024-03-15T10:15:00.000Z eks-cluster/v1.28 [spot-065]: Node - spot interruption notice. | Context: {Node="ip-10-0-6-2", TimeToTerminate="2m", Workloads="batch"}

### Root Cause
스팟 인스턴스 회수.

### Action Items
1. (즉시) 노드 cordon/drain로 워크로드 이동.
2. (재발방지) 중요한 서비스는 온디맨드/다중 노드그룹, 스팟은 배치 위주로.

---

## 66. Service Mesh Sidecar Injection Failure
---
service: policy
error_message: sidecar injection failed
---
### Incident Summary
[ERROR] 2024-03-15T10:16:00.000Z policy/v1.0.0 [mesh-066]: Mesh - sidecar injection failed. | Context: {Namespace="prod", Pod="wallet-service", Reason="webhook timeout"}

### Root Cause
injector 웹훅 장애/타임아웃.

### Action Items
1. (즉시) injector 스케일아웃/재시작.
2. (완화) 필요 시 해당 네임스페이스 injection 임시 비활성.
3. (재발방지) injector HA + 알람.

---

## 67. Istio Envoy 503 UF
---
service: service-mesh
error_message: upstream connect error or disconnect/reset
---
### Incident Summary
[ERROR] 2024-03-15T10:17:00.000Z service-mesh/v1.20.0 [ist-067]: Envoy - upstream connect error or disconnect/reset. | Context: {From="order-api", To="payment-api", Code="503 UF"}

### Root Cause
업스트림 파드 미가용/연결 실패(DNS, 엔드포인트 없음, 네트워크 정책).

### Action Items
1. (즉시) payment-api endpoints/ready 확인.
2. (확인) mTLS/정책 변경 여부 확인.
3. (재발방지) 서비스 디스커버리/정책 변경 시 점진 적용.

---

## 68. Egress Blocked (NAT/Firewall)
---
service: network
error_message: egress blocked
---
### Incident Summary
[CRITICAL] 2024-03-15T10:18:00.000Z network/v2.3.1 [egr-068]: Network - egress blocked. | Context: {From="payment-api", To="pg.example.com:443", Error="timeout", NAT="suspected"}

### Root Cause
NAT GW 장애/라우팅/NACL/SG로 외부 통신 불가.

### Action Items
1. (즉시) NAT GW 상태/라우팅 테이블 확인.
2. (확인) 특정 AZ만 영향인지 확인(AZ 장애 가능성).
3. (재발방지) NAT 다중 AZ + egress 모니터링 + 페일오버.

---

## 69. Security Group Misconfiguration (Port Closed)
---
service: network
error_message: connection timed out - port closed
---
### Incident Summary
[ERROR] 2024-03-15T10:19:00.000Z network/v2.3.1 [sg-069]: Network - connection timed out. | Context: {From="order-api", To="db-cache:5432", SG="sg-abc", Change="recent"}

### Root Cause
SG 변경으로 포트가 닫힘.

### Action Items
1. (즉시) 최근 SG 변경 롤백.
2. (재발방지) SG 변경은 IaC+승인+자동 테스트.

---

## 70. Route53 Resolver / DNS Upstream Failure
---
service: network
error_message: upstream dns failure
---
### Incident Summary
[ERROR] 2024-03-15T10:20:00.000Z network/v2.3.1 [dns-070]: DNS - upstream dns failure. | Context: {Upstream="VPCResolver", FailRate="40%", Query="pg.example.com"}

### Root Cause
VPC resolver 문제 또는 네트워크 이슈.

### Action Items
1. (즉시) NodeLocal DNSCache로 완화(가능 시).
2. (확인) AWS 상태/Resolver 지표 확인.
3. (재발방지) 외부 도메인 캐시/리졸버 모니터링.

---

## 71. Pod Sandbox Changed (Container Runtime)
---
service: eks-cluster
error_message: Pod sandbox changed
---
### Incident Summary
[WARN] 2024-03-15T10:21:00.000Z eks-cluster/v1.28 [rt-071]: Runtime - Pod sandbox changed. | Context: {Pod="order-api-7f9c", Runtime="containerd", Count="30/10m"}

### Root Cause
노드 런타임 불안정/네트워크 플러그인 재시작으로 sandbox 재생성.

### Action Items
1. (즉시) 해당 노드 이벤트/로그 확인.
2. (완화) 영향 노드 교체.
3. (재발방지) 런타임/노드 AMI 업데이트 및 안정성 모니터링.

---

## 72. Container Runtime Disk Full
---
service: eks-cluster
error_message: container runtime disk full
---
### Incident Summary
[ERROR] 2024-03-15T10:22:00.000Z eks-cluster/v1.28 [rt-072]: Runtime - disk full. | Context: {Node="ip-10-0-1-33", Path="/var/lib/containerd", Used="97%"}

### Root Cause
컨테이너 이미지/레이어 누적으로 runtime 디스크 포화.

### Action Items
1. (즉시) 이미지 prune + 로그 정리.
2. (재발방지) 노드 디스크 사이징/정리 자동화.

---

## 73. kubelet PLEG Not Healthy
---
service: eks-cluster
error_message: PLEG is not healthy
---
### Incident Summary
[CRITICAL] 2024-03-15T10:23:00.000Z eks-cluster/v1.28 [pleg-073]: Node - PLEG is not healthy. | Context: {Node="ip-10-0-4-2", Symptom="pods not updating"}

### Root Cause
kubelet이 컨테이너 상태를 못 따라감(디스크/CPU 포화, 런타임 문제).

### Action Items
1. (즉시) 노드 격리/드레인 후 교체.
2. (확인) 노드 자원/런타임 로그 확인.
3. (재발방지) 노드 자원 여유 확보 및 알람.

---

## 74. kubelet Too Many Open Files
---
service: eks-cluster
error_message: too many open files
---
### Incident Summary
[ERROR] 2024-03-15T10:24:00.000Z eks-cluster/v1.28 [fd-074]: Node - too many open files. | Context: {Node="ip-10-0-3-9", Limit="1024", Used="1024", TopProcess="kubelet"}

### Root Cause
파일 디스크립터 한도 낮음 또는 로그/연결 폭주.

### Action Items
1. (즉시) 노드 교체(긴급), ulimit 상향 계획 수립.
2. (확인) 누수가 있는 프로세스/로그 폭주 확인.
3. (재발방지) OS 튜닝 템플릿 + 연결/로그 제한.

---

## 75. Pod DNS Search Path Too Long
---
service: network
error_message: DNS config form too long
---
### Incident Summary
[WARN] 2024-03-15T10:25:00.000Z network/v2.3.1 [dns-075]: DNS - DNS config form too long. | Context: {Pod="legacy-app", SearchDomains="12", Limit="6"}

### Root Cause
dnsConfig/search path 과다로 kubelet이 설정을 잘라 DNS 해석 실패 가능.

### Action Items
1. (즉시) Pod dnsConfig 정리.
2. (재발방지) 네임스페이스/클러스터 DNS 정책 표준화.

---

## 76. Pod Scheduling Failed (Taints)
---
service: scheduler
error_message: node(s) had taint that the pod didn't tolerate
---
### Incident Summary
[WARN] 2024-03-15T10:26:00.000Z scheduler/v1.28 [sch-076]: Scheduling - taint not tolerated. | Context: {Pod="payment-api", Taint="dedicated=system:NoSchedule"}

### Root Cause
노드 taint에 대한 toleration 누락.

### Action Items
1. (즉시) 파드에 올바른 toleration 추가 또는 노드 라벨/taint 조정.
2. (재발방지) 워크로드 배치 정책 문서화 및 템플릿화.

---

## 77. Pod Scheduling Failed (NodeSelector)
---
service: scheduler
error_message: node(s) didn't match node selector
---
### Incident Summary
[WARN] 2024-03-15T10:27:00.000Z scheduler/v1.28 [sch-077]: Scheduling - node selector mismatch. | Context: {Pod="wallet-service", Selector="workload=secure", NodesMatched="0"}

### Root Cause
노드 라벨 누락 또는 selector 오타.

### Action Items
1. (즉시) 노드 라벨 확인 및 수정.
2. (재발방지) 라벨 표준/검증 자동화.

---

## 78. Pod Scheduling Failed (Affinity)
---
service: scheduler
error_message: pod affinity/anti-affinity rules not satisfied
---
### Incident Summary
[WARN] 2024-03-15T10:28:00.000Z scheduler/v1.28 [sch-078]: Scheduling - affinity rules not satisfied. | Context: {Pod="db-cache", Rule="anti-affinity", Pending="6"}

### Root Cause
anti-affinity로 인해 배치 불가(노드 부족).

### Action Items
1. (즉시) 노드 증설 또는 rule 완화(임시).
2. (재발방지) affinity 설계 시 용량 고려.

---

## 79. Node Scale-In Caused Pod Churn
---
service: autoscaling
error_message: scale-in caused pod churn
---
### Incident Summary
[WARN] 2024-03-15T10:29:00.000Z autoscaling/v1.27 [scin-079]: Autoscaling - scale-in caused pod churn. | Context: {NodeGroup="ng-app", Removed="3", EvictedPods="120"}

### Root Cause
스케일인 정책이 공격적이어서 파드 이동/재시작 증가.

### Action Items
1. (즉시) scale-in cool down 증가 및 PDB/priority 확인.
2. (재발방지) 스케일인 정책 튜닝 및 안정성 테스트.

---

## 80. Node Scale-Up Slow (Capacity)
---
service: autoscaling
error_message: scale-up slow
---
### Incident Summary
[WARN] 2024-03-15T10:30:00.000Z autoscaling/v1.27 [scup-080]: Autoscaling - scale-up slow. | Context: {PendingPods="40", LaunchTime="8m", Expected="2m", Reason="EC2 capacity"}

### Root Cause
EC2 용량 부족/스팟/서브넷 문제.

### Action Items
1. (즉시) 인스턴스 타입 다양화, 다른 AZ/서브넷 사용.
2. (재발방지) 다중 노드그룹/타입 전략.

---

## 81. KMS Decrypt Failure for Secrets
---
service: security
error_message: kms decrypt failed
---
### Incident Summary
[ERROR] 2024-03-15T10:31:00.000Z security/v1.0.0 [kms-081]: KMS - decrypt failed. | Context: {KeyId="kms-1234", Service="external-secrets", Error="AccessDenied"}

### Root Cause
KMS 키 정책/역할 권한 변경으로 시크릿 복호화 실패.

### Action Items
1. (즉시) KMS key policy 및 IRSA role 권한 점검/복구.
2. (확인) 영향 시크릿/서비스 목록 확인.
3. (재발방지) KMS 변경 승인 워크플로우 + 알람.

---

## 82. External Secrets Sync Failed
---
service: security
error_message: external secrets sync failed
---
### Incident Summary
[ERROR] 2024-03-15T10:32:00.000Z security/v1.0.0 [sec-082]: Secrets - sync failed. | Context: {Secret="prod/pg-api-key", Controller="external-secrets", Error="throttling"}

### Root Cause
Secrets Manager/API throttling 또는 권한/네트워크 문제.

### Action Items
1. (즉시) 재시도 백오프 강화, 동기화 주기 조정.
2. (확인) STS/Secrets API 호출량 확인.
3. (재발방지) 캐시/배치 동기화, 쿼터/알람.

---

## 83. EKS Control Plane Endpoint Private Only
---
service: eks-control-plane
error_message: endpoint not reachable
---
### Incident Summary
[ERROR] 2024-03-15T10:33:00.000Z eks-control-plane/v1.28 [cp-083]: ControlPlane - endpoint not reachable. | Context: {Endpoint="private", From="bastion", Error="timeout"}

### Root Cause
엔드포인트 접근 경로/VPN/보안그룹 문제.

### Action Items
1. (즉시) 접근 네트워크(VPN/라우팅/SG) 확인.
2. (재발방지) 접근 경로 문서화 + 점검 자동화.

---

## 84. AWS API Rate Limit (EC2)
---
service: common-infra
error_message: EC2 API rate exceeded
---
### Incident Summary
[WARN] 2024-03-15T10:34:00.000Z common-infra/v1.8.0 [aws-084]: AWS API - EC2 API rate exceeded. | Context: {API="DescribeInstances", Calls="800/s", Source="autoscaler"}

### Root Cause
오토스케일러/툴의 과도한 폴링으로 EC2 API 한도 초과.

### Action Items
1. (즉시) 폴링 주기/캐시 적용으로 호출량 감소.
2. (재발방지) API 사용량 모니터링 + 백오프 표준화.

---

## 85. IAM Authenticator Error
---
service: eks-control-plane
error_message: aws-iam-authenticator error
---
### Incident Summary
[ERROR] 2024-03-15T10:35:00.000Z eks-control-plane/v1.28 [iam-085]: Auth - aws-iam-authenticator error. | Context: {User="arn:aws:iam::123:user/dev", Error="AccessDenied"}

### Root Cause
RBAC 매핑(a ws-auth) 누락 또는 IAM 권한 변경.

### Action Items
1. (즉시) aws-auth ConfigMap에서 role/user 매핑 확인.
2. (재발방지) RBAC 변경은 GitOps로 관리.

---

## 86. kubeconfig Expired Token
---
service: common-infra
error_message: expired token in kubeconfig
---
### Incident Summary
[ERROR] 2024-03-15T10:36:00.000Z common-infra/v1.8.0 [kcfg-086]: kubectl - expired token in kubeconfig. | Context: {User="devops", Tool="kubectl", Error="Unauthorized"}

### Root Cause
임시 토큰 만료 또는 SSO 세션 만료.

### Action Items
1. (즉시) 재로그인/토큰 갱신.
2. (재발방지) 접근 절차 문서화 및 SSO 세션 모니터링.

---

## 87. ArgoCD Sync Failed
---
service: cicd
error_message: argocd sync failed
---
### Incident Summary
[ERROR] 2024-03-15T10:37:00.000Z cicd/v2.10.0 [argo-087]: GitOps - argocd sync failed. | Context: {App="prod-order-api", Reason="InvalidManifest", Commit="abc123"}

### Root Cause
매니페스트 문법 오류/리소스 누락/권한 문제로 동기화 실패.

### Action Items
1. (즉시) 실패 리소스/이벤트 확인 후 롤백 또는 수정 커밋.
2. (재발방지) PR 단계에서 매니페스트 lint/validate(kubeval) 필수화.

---

## 88. Helm Release Failed (Atomic Rollback)
---
service: cicd
error_message: helm upgrade failed
---
### Incident Summary
[ERROR] 2024-03-15T10:38:00.000Z cicd/v1.0.0 [helm-088]: Deploy - helm upgrade failed. | Context: {Release="payment-api", Error="timed out waiting for condition", Atomic="true"}

### Root Cause
롤아웃이 readiness 조건을 만족하지 못함(앱 장애/리소스 부족/프로브 과도).

### Action Items
1. (즉시) rollout status 및 이벤트 확인(이미지풀/프로브/리소스).
2. (완화) 원인 해결 후 재배포.
3. (재발방지) 배포 전 smoke test + 점진 배포(카나리) 도입.

---

## 89. Namespace ResourceQuota Exceeded
---
service: policy
error_message: exceeded quota
---
### Incident Summary
[WARN] 2024-03-15T10:39:00.000Z policy/v1.0.0 [rq-089]: Quota - exceeded quota. | Context: {Namespace="prod", Resource="pods", Used="200", Hard="200"}

### Root Cause
리소스쿼터 한도 도달로 새 파드 생성 불가.

### Action Items
1. (즉시) 불필요 파드/잡 정리 또는 쿼터 상향(임시).
2. (재발방지) 쿼터/용량 계획 및 배치 정책.

---

## 90. LimitRange Violated
---
service: policy
error_message: limitrange violated
---
### Incident Summary
[ERROR] 2024-03-15T10:40:00.000Z policy/v1.0.0 [lr-090]: Policy - limitrange violated. | Context: {Namespace="prod", Reason="cpu limit required", Pod="new-api"}

### Root Cause
LimitRange 정책상 리소스 limit 미설정.

### Action Items
1. (즉시) deployment에 requests/limits 추가.
2. (재발방지) 템플릿에 기본 리소스 포함.

---

## 91. Pod PriorityClass Missing
---
service: policy
error_message: priorityclass missing
---
### Incident Summary
[WARN] 2024-03-15T10:41:00.000Z policy/v1.0.0 [pc-091]: Policy - priorityclass missing. | Context: {Workload="payment-api", Risk="preemption"}

### Root Cause
중요 서비스가 기본 우선순위로 동작해 용량 부족 시 축출 위험.

### Action Items
1. (즉시) 중요 서비스에 priorityClass 적용.
2. (재발방지) 워크로드 분류 기준/템플릿화.

---

## 92. Horizontal Pod Autoscaler Flapping
---
service: autoscaling
error_message: hpa flapping detected
---
### Incident Summary
[WARN] 2024-03-15T10:42:00.000Z autoscaling/v2 [hpa-092]: HPA - flapping detected. | Context: {Target="order-api", ScaleEvents="20/10m", Metric="cpu"}

### Root Cause
메트릭 변동/스파이크, 안정화 윈도우 미설정.

### Action Items
1. (즉시) stabilizationWindowSeconds 설정 및 targetUtilization 조정.
2. (재발방지) SLO 기반 오토스케일 설계.

---

## 93. KEDA Scaling Misconfigured
---
service: autoscaling
error_message: keda scaler error
---
### Incident Summary
[ERROR] 2024-03-15T10:43:00.000Z autoscaling/v2.12.0 [keda-093]: KEDA - scaler error. | Context: {Scaler="kinesis", Error="auth failed", Target="log-worker"}

### Root Cause
스케일러 인증/권한 문제 또는 메트릭 소스 장애.

### Action Items
1. (즉시) IRSA/시크릿 설정 확인.
2. (재발방지) 스케일러 헬스체크/알람.

---

## 94. NodeLocal DNSCache Not Running
---
service: network
error_message: nodelocaldnscache not running
---
### Incident Summary
[WARN] 2024-03-15T10:44:00.000Z network/v2.3.1 [dns-094]: DNS - NodeLocal DNSCache not running. | Context: {NodesAffected="30%", DaemonSet="node-local-dns"}

### Root Cause
DaemonSet 스케줄 실패/리소스 부족.

### Action Items
1. (즉시) DS 상태 확인 및 노드 라벨/taint에 의한 미스케줄 점검.
2. (재발방지) 시스템 DS 우선순위 설정 및 리소스 예약.

---

## 95. KubeDNS/Service CIDR Conflict
---
service: network
error_message: service cidr conflict
---
### Incident Summary
[CRITICAL] 2024-03-15T10:45:00.000Z network/v2.3.1 [cidr-095]: Network - service CIDR conflict. | Context: {ServiceCIDR="10.0.0.0/16", VPC="10.0.0.0/16"}

### Root Cause
CIDR 중복으로 라우팅 충돌.

### Action Items
1. (즉시) 신규 클러스터/서브넷 설계 수정(운영 중이면 마이그레이션 필요).
2. (재발방지) 네트워크 설계 표준/검증 프로세스.

---

## 96. ELB 503 (No Targets)
---
service: ingress
error_message: 503 Service Unavailable - no targets
---
### Incident Summary
[ERROR] 2024-03-15T10:46:00.000Z ingress/v2.7.0 [elb-096]: LB - 503 no targets. | Context: {Service="wallet-service", TargetsHealthy="0", Zone="apne2-a"}

### Root Cause
타겟 파드 모두 unhealthy 또는 등록 실패.

### Action Items
1. (즉시) 타겟그룹 헬스체크/파드 readiness 확인.
2. (확인) 보안그룹/포트/경로 설정 점검.
3. (재발방지) 배포 시 헬스체크 계약 테스트.

---

## 97. ALB Listener Rule Limit Reached
---
service: ingress
error_message: listener rule limit reached
---
### Incident Summary
[WARN] 2024-03-15T10:47:00.000Z ingress/v2.7.0 [alb-097]: ALB - listener rule limit reached. | Context: {ALB="prod-alb", Rules="100", Limit="100"}

### Root Cause
라우팅 룰 과다 생성(마이크로서비스/경로 폭증).

### Action Items
1. (즉시) 불필요 룰 정리 또는 ALB 분리.
2. (재발방지) 라우팅 설계 단순화(경로 통합) 및 한도 모니터링.

---

## 98. Fluent Bit Delivery Failed (Kinesis)
---
service: logging
error_message: failed to deliver logs to kinesis
---
### Incident Summary
[ERROR] 2024-03-15T10:48:00.000Z logging/v2.2.0 [log-098]: Logging - failed to deliver logs to kinesis. | Context: {Stream="cali-log-stream", Error="ProvisionedThroughputExceededException", Retries="50"}

### Root Cause
Kinesis 처리량 초과 또는 권한/네트워크 문제. 재시도 폭주로 로그 드랍 위험.

### Action Items
1. (즉시) Kinesis shard 증설/On-Demand 전환 검토.
2. (완화) Fluent Bit retry backoff/jitter, buffer 조정.
3. (재발방지) 로그 볼륨 제어 + 파이프라인 용량 계획.

---

## 99. Cluster-Wide Outage Suspected (Multiple System Pods Down)
---
service: eks-cluster
error_message: multiple system pods unavailable
---
### Incident Summary
[CRITICAL] 2024-03-15T10:49:00.000Z eks-cluster/v1.28 [out-099]: Cluster - multiple system pods unavailable. | Context: {CoreDNS="down", MetricsServer="down", AWSNode="degraded", NodesNotReady="12%"}

### Root Cause
노드/네트워크/컨트롤플레인 연쇄 장애 또는 최근 변경(업그레이드/정책)이 시스템 파드에 영향을 줌.

### Action Items
1. (즉시) 영향 범위(노드/AZ/네임스페이스) 파악 후 장애 격리.
2. (즉시) 시스템 파드 우선 복구(CoreDNS, CNI, metrics).
3. (확인) 직전 변경(업그레이드/정책/배포) 롤백 여부 판단.
4. (재발방지) 변경 관리(카나리/점진) + 핵심 시스템 파드 SLO/알람.

---

## 100. Critical Infra Incident – Control Plane Degraded
---
service: eks-control-plane
error_message: control plane degraded
---
### Incident Summary
[CRITICAL] 2024-03-15T10:50:00.000Z eks-control-plane/v1.28 [cp-100]: ControlPlane - control plane degraded. | Context: {APIServer="high latency", ETCD="p99 1200ms", Symptom="kubectl timeouts", Region="ap-northeast-2"}

### Root Cause
컨트롤플레인 지연(etcd/요청 폭주)으로 클러스터 전반 장애(스케줄링/롤아웃/서비스 디스커버리)가 연쇄적으로 발생.

### Action Items
1. (즉시) 대량 배포/잡/오퍼레이터 변경을 중단해 churn을 줄이고 안정화.
2. (즉시) API 서버 429/타임아웃 원인 컴포넌트(오퍼레이터/컨트롤러) 식별 후 rate-limit/중지.
3. (확인) 이벤트 폭주(CrashLoopBackOff) 상위 워크로드를 먼저 정상화.
4. (재발방지) 업그레이드/대량 배포는 카나리+속도 제한, 컨트롤플레인 지표 알람 강화.

---
