# CALI Knowledge Base – Fintech Infrastructure & EKS (01–50)

---

## 01. Kinesis Stream Shard Limit Exceeded
---
service: common-infra
error_message: Rate exceeded for shard in stream
---
### Incident Summary
로그 데이터 유입량 급증으로 Kinesis Stream의 처리 한도를 초과함.
### Root Cause
프로모션 트래픽 증가로 초당 쓰기 요청 수가 Shard 용량을 초과함.
### Action Items
1. Shard 수 증설(UpdateShardCount).
2. Producer 배치 전송 및 Retry 지연 조정.

---

## 02. CoreDNS DNS Resolution Timeout
---
service: network
error_message: DNS resolution failed for service
---
### Incident Summary
EKS 내부 서비스 간 통신 시 DNS 해석 실패 발생.
### Root Cause
CoreDNS 파드 부하로 인한 응답 지연.
### Action Items
1. CoreDNS Replica 증설.
2. NodeLocal DNSCache 적용 검토.

---

## 03. Pod ImagePullBackOff
---
service: deployment
error_message: ImagePullBackOff
---
### Incident Summary
파드가 컨테이너 이미지를 가져오지 못해 기동 실패.
### Root Cause
ECR 인증 토큰 만료 또는 이미지 태그 오기재.
### Action Items
1. imagePullSecret 설정 확인.
2. 이미지 태그 및 리포지토리 검증.

---

## 04. EKS API Server Throttling
---
service: eks-control-plane
error_message: ThrottlingException: Rate exceeded
---
### Incident Summary
API Server 요청 제한으로 리소스 조회 실패.
### Root Cause
컨트롤러의 과도한 API 호출.
### Action Items
1. Controller 호출 주기 조정.
2. 불필요한 watch 제거.

---

## 05. Node NotReady 상태 지속
---
service: eks-nodegroup
error_message: NodeNotReady
---
### Incident Summary
워커 노드가 Ready 상태로 복구되지 않음.
### Root Cause
노드 디스크 I/O 또는 네트워크 불안정.
### Action Items
1. 노드 재부팅 또는 교체.
2. 시스템 리소스 점검.

---

## 06. HPA Scale Out Failure
---
service: autoscaling
error_message: failed to get cpu utilization
---
### Incident Summary
트래픽 증가에도 파드가 자동 확장되지 않음.
### Root Cause
Metrics Server 비정상 동작.
### Action Items
1. Metrics Server 재배포.
2. HPA 메트릭 설정 확인.

---

## 07. Node Disk Pressure Eviction
---
service: eks-nodegroup
error_message: NodeHasDiskPressure
---
### Incident Summary
디스크 부족으로 파드가 Eviction됨.
### Root Cause
로그 파일 및 임시 파일 누적.
### Action Items
1. 로그 로테이션 설정.
2. Docker 이미지 정리.

---

## 08. Pod CrashLoopBackOff
---
service: user-api
error_message: CrashLoopBackOff
---
### Incident Summary
애플리케이션 파드가 반복 재시작됨.
### Root Cause
환경 변수 누락.
### Action Items
1. ConfigMap/Secret 점검.
2. 애플리케이션 기동 로직 검증.

---

## 09. LoadBalancer Provision Timeout
---
service: ingress
error_message: Timeout waiting for LoadBalancer
---
### Incident Summary
ALB 생성 지연으로 외부 트래픽 유입 불가.
### Root Cause
서브넷 태그 또는 IAM 권한 누락.
### Action Items
1. Subnet 태그 확인.
2. ALB Controller IAM Role 점검.

---

## 10. Security Group Rule Limit Exceeded
---
service: network
error_message: RulesPerSecurityGroupLimitExceeded
---
### Incident Summary
보안 그룹 규칙 추가 실패.
### Root Cause
Ingress 규칙 수 한도 초과.
### Action Items
1. 불필요한 규칙 제거.
2. CIDR 병합 적용.

---

## 11. Node Memory Pressure
---
service: eks-nodegroup
error_message: NodeHasMemoryPressure
---
### Incident Summary
메모리 부족으로 파드 강제 종료.
### Root Cause
메모리 제한 없는 파드 과다 실행.
### Action Items
1. requests/limits 설정.
2. 메모리 사용량 모니터링.

---

## 12. Pod Pending (Insufficient CPU)
---
service: batch-worker
error_message: Insufficient cpu
---
### Incident Summary
파드가 Pending 상태로 스케줄되지 않음.
### Root Cause
노드 CPU 리소스 부족.
### Action Items
1. 노드 스케일 아웃.
2. CPU 요청값 조정.

---

## 13. CNI IP Exhaustion
---
service: network
error_message: failed to assign an IP address
---
### Incident Summary
새 파드에 IP 할당 실패.
### Root Cause
서브넷 CIDR 부족.
### Action Items
1. 서브넷 확장.
2. Prefix Delegation 적용.

---

## 14. kube-proxy Crash
---
service: network
error_message: kube-proxy exited with error
---
### Incident Summary
노드 네트워크 라우팅 장애 발생.
### Root Cause
kube-proxy 설정 불일치.
### Action Items
1. kube-proxy 재배포.
2. CNI 설정 점검.

---

## 15. Fluent Bit Log Delivery Delay
---
service: logging
error_message: retrying chunk flush
---
### Incident Summary
로그 전송 지연 발생.
### Root Cause
로그 수집 대상 시스템 부하.
### Action Items
1. Buffer 크기 조정.
2. Flush 주기 최적화.

---

## 16. Pod Evicted (Ephemeral Storage)
---
service: logging
error_message: Evicted: ephemeral-storage
---
### Incident Summary
임시 스토리지 초과로 파드 종료.
### Root Cause
대량 로그 파일 생성.
### Action Items
1. emptyDir 제한 설정.
2. 로그 외부 전송 구조 개선.

---

## 17. EKS Cluster Autoscaler Failure
---
service: autoscaling
error_message: failed to scale node group
---
### Incident Summary
노드 자동 확장 실패.
### Root Cause
IAM 권한 부족.
### Action Items
1. IAM Role 정책 검증.
2. ASG 설정 점검.

---

## 18. Ingress 502 Bad Gateway
---
service: ingress
error_message: 502 Bad Gateway
---
### Incident Summary
외부 요청 시 502 오류 발생.
### Root Cause
백엔드 파드 헬스체크 실패.
### Action Items
1. Readiness Probe 점검.
2. 서비스 포트 확인.

---

## 19. Control Plane Upgrade Failure
---
service: eks-control-plane
error_message: Upgrade failed
---
### Incident Summary
EKS 버전 업그레이드 실패.
### Root Cause
애드온 버전 비호환.
### Action Items
1. 애드온 사전 업그레이드.
2. 호환성 매트릭스 확인.

---

## 20. Metrics Server Not Ready
---
service: monitoring
error_message: metrics not available
---
### Incident Summary
HPA 메트릭 수집 실패.
### Root Cause
Metrics Server 파드 장애.
### Action Items
1. Metrics Server 재기동.
2. 리소스 권한 점검.

---

## 21. Pod OOMKilled
---
service: payment-api
error_message: OOMKilled
---
### Incident Summary
메모리 초과로 파드 종료.
### Root Cause
메모리 사용량 급증.
### Action Items
1. 메모리 제한 상향.
2. 코드 메모리 누수 점검.

---

## 22. Readiness Probe Failed
---
service: order-api
error_message: Readiness probe failed
---
### Incident Summary
파드가 트래픽을 받지 못함.
### Root Cause
초기화 지연.
### Action Items
1. InitialDelaySeconds 조정.
2. 헬스체크 로직 검증.

---

## 23. Liveness Probe Failed
---
service: auth-api
error_message: Liveness probe failed
---
### Incident Summary
파드가 비정상으로 재시작됨.
### Root Cause
일시적 응답 지연.
### Action Items
1. TimeoutSeconds 조정.
2. 헬스체크 경량화.

---

## 24. Node CPU Throttling
---
service: eks-nodegroup
error_message: cpu throttling detected
---
### Incident Summary
CPU 제한으로 처리 지연 발생.
### Root Cause
CPU limit 과도 설정.
### Action Items
1. CPU limit 재조정.
2. 워크로드 분산.

---

## 25. Pod Scheduling Failed (Affinity)
---
service: deployment
error_message: node affinity mismatch
---
### Incident Summary
파드 스케줄링 실패.
### Root Cause
Node Affinity 조건 불일치.
### Action Items
1. Affinity 규칙 점검.
2. 노드 라벨 확인.

---

## 26. Service Endpoint Not Found
---
service: network
error_message: no endpoints available
---
### Incident Summary
서비스 엔드포인트 없음.
### Root Cause
파드 레이블 불일치.
### Action Items
1. Selector 설정 확인.
2. 파드 상태 점검.

---

## 27. EBS Volume Mount Failed
---
service: storage
error_message: Unable to attach or mount volumes
---
### Incident Summary
스토리지 마운트 실패.
### Root Cause
AZ 불일치 또는 볼륨 제한 초과.
### Action Items
1. AZ 일치 여부 확인.
2. 볼륨 상태 점검.

---

## 28. PVC Pending
---
service: storage
error_message: persistentvolumeclaim is pending
---
### Incident Summary
스토리지 프로비저닝 실패.
### Root Cause
StorageClass 설정 오류.
### Action Items
1. StorageClass 확인.
2. CSI 드라이버 상태 점검.

---

## 29. Network Policy Deny
---
service: security
error_message: connection blocked by network policy
---
### Incident Summary
파드 간 통신 차단.
### Root Cause
NetworkPolicy 과도 적용.
### Action Items
1. 정책 예외 규칙 추가.
2. 통신 경로 재설계.

---

## 30. Pod Restart Storm
---
service: batch-worker
error_message: Back-off restarting failed container
---
### Incident Summary
대량 파드 재시작 발생.
### Root Cause
공통 설정 오류.
### Action Items
1. 배포 중단.
2. 설정 롤백.

---

## 31. EKS Node Terminated Unexpectedly
---
service: eks-nodegroup
error_message: Node terminated
---
### Incident Summary
노드가 예기치 않게 종료됨.
### Root Cause
Spot 인스턴스 회수.
### Action Items
1. On-Demand 비율 조정.
2. Graceful Shutdown 설정.

---

## 32. API Latency Spike
---
service: gateway
error_message: request timeout
---
### Incident Summary
API 응답 지연 발생.
### Root Cause
백엔드 파드 부하.
### Action Items
1. HPA 확장.
2. 캐시 적용 검토.

---

## 33. ConfigMap Update Not Applied
---
service: config
error_message: config not updated
---
### Incident Summary
설정 변경이 파드에 반영되지 않음.
### Root Cause
파드 재시작 미수행.
### Action Items
1. 롤링 재시작 수행.
2. 설정 변경 프로세스 정비.

---

## 34. Secret Permission Denied
---
service: security
error_message: permission denied accessing secret
---
### Incident Summary
Secret 접근 실패.
### Root Cause
RBAC 권한 부족.
### Action Items
1. Role/RoleBinding 확인.
2. 최소 권한 재설계.

---

## 35. Pod Log Missing
---
service: logging
error_message: logs not found
---
### Incident Summary
파드 로그 확인 불가.
### Root Cause
로그 수집 에이전트 장애.
### Action Items
1. 로그 에이전트 상태 점검.
2. 로그 경로 확인.

---

## 36. Deployment Rollout Stuck
---
service: deployment
error_message: rollout status unknown
---
### Incident Summary
배포가 완료되지 않음.
### Root Cause
새 파드 헬스체크 실패.
### Action Items
1. 배포 상태 분석.
2. 이전 버전 롤백.

---

## 37. ALB Target Unhealthy
---
service: ingress
error_message: target unhealthy
---
### Incident Summary
ALB 대상 비정상 상태.
### Root Cause
헬스체크 경로 불일치.
### Action Items
1. 헬스체크 URL 확인.
2. 포트 설정 검증.

---

## 38. Node Group Scaling Delay
---
service: autoscaling
error_message: scale up timeout
---
### Incident Summary
노드 확장 지연.
### Root Cause
인스턴스 프로비저닝 지연.
### Action Items
1. ASG 설정 점검.
2. 인스턴스 타입 변경 검토.

---

## 39. DaemonSet Pod Missing
---
service: monitoring
error_message: daemonset pod not running
---
### Incident Summary
일부 노드에 DaemonSet 미배포.
### Root Cause
노드 셀렉터 불일치.
### Action Items
1. Node Selector 확인.
2. DaemonSet 재배포.

---

## 40. TLS Certificate Expired
---
service: ingress
error_message: certificate expired
---
### Incident Summary
TLS 인증서 만료로 HTTPS 오류 발생.
### Root Cause
인증서 자동 갱신 실패.
### Action Items
1. ACM 상태 확인.
2. 갱신 알림 설정.

---

## 41. API Pod Too Many Open Files
---
service: user-api
error_message: too many open files
---
### Incident Summary
파일 디스크립터 한도 초과.
### Root Cause
커넥션 미정리.
### Action Items
1. ulimit 설정 조정.
2. 커넥션 풀 점검.

---

## 42. Pod Startup Timeout
---
service: settlement-api
error_message: startup timeout
---
### Incident Summary
파드 기동 시간 초과.
### Root Cause
초기 로딩 작업 과다.
### Action Items
1. 초기화 로직 분리.
2. Startup Probe 추가.

---

## 43. Node Clock Skew Detected
---
service: eks-nodegroup
error_message: clock skew detected
---
### Incident Summary
노드 시간 불일치 감지.
### Root Cause
NTP 동기화 실패.
### Action Items
1. NTP 설정 점검.
2. 노드 재동기화.

---

## 44. Service Port Misconfiguration
---
service: network
error_message: connection refused
---
### Incident Summary
서비스 포트 오류로 연결 실패.
### Root Cause
서비스/컨테이너 포트 불일치.
### Action Items
1. 포트 설정 확인.
2. 서비스 재배포.

---

## 45. PVC Volume Full
---
service: storage
error_message: no space left on device
---
### Incident Summary
스토리지 용량 초과.
### Root Cause
데이터 정리 미흡.
### Action Items
1. 데이터 정리.
2. 볼륨 확장.

---

## 46. Job Execution Stuck
---
service: batch-worker
error_message: job not completing
---
### Incident Summary
배치 Job이 종료되지 않음.
### Root Cause
외부 의존 서비스 지연.
### Action Items
1. Timeout 설정.
2. 재시도 로직 추가.

---

## 47. Pod Network Latency High
---
service: network
error_message: high network latency
---
### Incident Summary
파드 간 통신 지연.
### Root Cause
노드 네트워크 포화.
### Action Items
1. 노드 분산.
2. 네트워크 대역폭 점검.

---

## 48. EKS Addon Health Check Failed
---
service: eks-addon
error_message: addon unhealthy
---
### Incident Summary
EKS 애드온 비정상 상태.
### Root Cause
버전 충돌.
### Action Items
1. 애드온 재설치.
2. 버전 호환성 확인.

---

## 49. Node Draining Timeout
---
service: eks-nodegroup
error_message: drain timeout
---
### Incident Summary
노드 교체 중 파드 종료 지연.
### Root Cause
Grace Period 과도 설정.
### Action Items
1. terminationGracePeriodSeconds 조정.
2. PDB 설정 확인.

---

## 50. Control Plane Endpoint Unreachable
---
service: eks-control-plane
error_message: unable to reach endpoint
---
### Incident Summary
EKS 컨트롤 플레인 접근 불가.
### Root Cause
네트워크 ACL 또는 보안 그룹 차단.
### Action Items
1. 네트워크 정책 점검.
2. 엔드포인트 접근 허용 설정.

---
## 51. Pod Init Container Failed
---
service: deployment
error_message: Init container failed
---
### Incident Summary
Init Container 단계에서 실패하여 파드가 기동되지 않음.
### Root Cause
초기 스크립트 내 외부 의존 서비스 호출 실패.
### Action Items
1. Init 로직 단순화.
2. 외부 의존성 제거 또는 재시도 추가.

---

## 52. Node Kernel Panic
---
service: eks-nodegroup
error_message: kernel panic detected
---
### Incident Summary
노드에서 커널 패닉 발생으로 인스턴스 재부팅.
### Root Cause
커널 버그 또는 드라이버 충돌.
### Action Items
1. 최신 AMI 적용.
2. 문제 노드 교체.

---

## 53. Pod Stuck in Terminating
---
service: deployment
error_message: pod stuck terminating
---
### Incident Summary
파드가 종료 상태에서 장시간 멈춤.
### Root Cause
종료 훅(preStop) 미완료.
### Action Items
1. preStop 훅 점검.
2. 강제 삭제 수행.

---

## 54. API Server Connection Refused
---
service: eks-control-plane
error_message: connection refused
---
### Incident Summary
API Server 연결 실패.
### Root Cause
보안 그룹 또는 네트워크 ACL 차단.
### Action Items
1. 보안 그룹 규칙 확인.
2. 네트워크 경로 점검.

---

## 55. Pod Volume Permission Denied
---
service: storage
error_message: permission denied
---
### Incident Summary
마운트된 볼륨 접근 실패.
### Root Cause
파일 시스템 권한 불일치.
### Action Items
1. fsGroup 설정 추가.
2. 볼륨 권한 수정.

---

## 56. DaemonSet CrashLoop
---
service: monitoring
error_message: CrashLoopBackOff
---
### Incident Summary
DaemonSet 파드 반복 재시작.
### Root Cause
공통 설정 오류.
### Action Items
1. 설정 롤백.
2. 로그 분석 후 재배포.

---

## 57. Node CPU Steal High
---
service: eks-nodegroup
error_message: cpu steal detected
---
### Incident Summary
노드 CPU steal 비율 상승으로 성능 저하.
### Root Cause
호스트 리소스 경합.
### Action Items
1. 인스턴스 타입 상향.
2. 노드 분산 배치.

---

## 58. Pod DNS Search Domain Overflow
---
service: network
error_message: DNS config exceeded limits
---
### Incident Summary
DNS 설정 길이 초과로 네임 해석 실패.
### Root Cause
과도한 Search Domain 설정.
### Action Items
1. Search Domain 축소.
2. 불필요한 네임스페이스 제거.

---

## 59. EKS Node Group Update Failed
---
service: eks-nodegroup
error_message: update failed
---
### Incident Summary
노드 그룹 업데이트 실패.
### Root Cause
롤링 업데이트 중 파드 종료 실패.
### Action Items
1. PDB 설정 점검.
2. 업데이트 전략 수정.

---

## 60. Pod Network Interface Limit Reached
---
service: network
error_message: eni limit exceeded
---
### Incident Summary
노드의 ENI 한도 초과로 파드 생성 실패.
### Root Cause
인스턴스 타입 ENI 제한.
### Action Items
1. 인스턴스 타입 변경.
2. 파드 밀도 조정.

---

## 61. Kubelet Not Responding
---
service: eks-nodegroup
error_message: kubelet stopped posting node status
---
### Incident Summary
kubelet 비응답으로 노드 상태 Unknown.
### Root Cause
노드 리소스 고갈.
### Action Items
1. 노드 재기동.
2. 리소스 사용량 점검.

---

## 62. Pod Priority Preemption
---
service: scheduler
error_message: pod preempted
---
### Incident Summary
낮은 우선순위 파드가 강제 종료됨.
### Root Cause
PriorityClass 설정 영향.
### Action Items
1. 우선순위 정책 재검토.
2. 중요 파드 보호 설정.

---

## 63. Cluster Autoscaler Scale Down Blocked
---
service: autoscaling
error_message: scale down blocked
---
### Incident Summary
노드 축소가 진행되지 않음.
### Root Cause
DaemonSet 또는 PDB 영향.
### Action Items
1. PDB 설정 조정.
2. DaemonSet 예외 설정 확인.

---

## 64. Pod Log Disk Flood
---
service: logging
error_message: disk usage high
---
### Incident Summary
로그 폭증으로 노드 디스크 급증.
### Root Cause
디버그 로그 레벨 과다.
### Action Items
1. 로그 레벨 하향.
2. 로그 샘플링 적용.

---

## 65. EKS Endpoint Private Access Failure
---
service: eks-control-plane
error_message: endpoint not reachable
---
### Incident Summary
Private Endpoint 접근 실패.
### Root Cause
VPC 라우팅 오류.
### Action Items
1. 라우트 테이블 점검.
2. 보안 그룹 확인.

---

## 66. Pod UID Collision
---
service: scheduler
error_message: uid collision detected
---
### Incident Summary
파드 UID 충돌 감지.
### Root Cause
비정상적인 재생성 로직.
### Action Items
1. 컨트롤러 재시작.
2. 파드 정리.

---

## 67. Node FS Inodes Exhausted
---
service: eks-nodegroup
error_message: no inodes left
---
### Incident Summary
inode 부족으로 파일 생성 실패.
### Root Cause
소량 파일 대량 생성.
### Action Items
1. 파일 정리.
2. 스토리지 구조 개선.

---

## 68. Pod Timezone Mismatch
---
service: common-runtime
error_message: invalid timestamp
---
### Incident Summary
타임존 불일치로 로그/데이터 오류 발생.
### Root Cause
컨테이너 타임존 설정 누락.
### Action Items
1. TZ 환경 변수 설정.
2. 공통 이미지 표준화.

---

## 69. Service Account Token Mount Failed
---
service: security
error_message: failed to mount service account token
---
### Incident Summary
ServiceAccount 토큰 마운트 실패.
### Root Cause
API Server 통신 장애.
### Action Items
1. API Server 상태 확인.
2. 파드 재기동.

---

## 70. Pod Sandbox Creation Failed
---
service: container-runtime
error_message: failed to create pod sandbox
---
### Incident Summary
컨테이너 런타임 초기화 실패.
### Root Cause
CNI 플러그인 오류.
### Action Items
1. CNI 재시작.
2. 노드 재부팅.

---

## 71. Node Network Packet Drop
---
service: network
error_message: packet drop detected
---
### Incident Summary
네트워크 패킷 드롭으로 응답 지연 발생.
### Root Cause
네트워크 대역폭 포화.
### Action Items
1. 노드 분산.
2. 트래픽 제한 적용.

---

## 72. Pod Secret Rotation Not Applied
---
service: security
error_message: secret not updated
---
### Incident Summary
Secret 변경이 파드에 반영되지 않음.
### Root Cause
자동 로테이션 미지원 구조.
### Action Items
1. 파드 재시작.
2. Secret 관리 정책 개선.

---

## 73. Node IMDS Access Blocked
---
service: eks-nodegroup
error_message: IMDS access denied
---
### Incident Summary
노드에서 AWS 메타데이터 접근 실패.
### Root Cause
IMDSv2 설정 오류.
### Action Items
1. IMDSv2 토큰 설정 확인.
2. IAM Role 점검.

---

## 74. Pod Port Exhaustion
---
service: application
error_message: cannot assign requested address
---
### Incident Summary
포트 고갈로 신규 커넥션 실패.
### Root Cause
커넥션 재사용 미흡.
### Action Items
1. 커넥션 풀 적용.
2. TIME_WAIT 튜닝.

---

## 75. EKS Addon Version Drift
---
service: eks-addon
error_message: addon version mismatch
---
### Incident Summary
애드온 버전 불일치로 오류 발생.
### Root Cause
수동 업데이트 누락.
### Action Items
1. 애드온 버전 통일.
2. 업그레이드 자동화.

---

## 76. Pod CPU Burst Throttling
---
service: application
error_message: cpu throttled
---
### Incident Summary
CPU Burst 제한으로 응답 지연.
### Root Cause
CPU limit 과소 설정.
### Action Items
1. CPU limit 조정.
2. 워크로드 분리.

---

## 77. Node Swap Usage Detected
---
service: eks-nodegroup
error_message: swap usage detected
---
### Incident Summary
스왑 사용으로 성능 저하.
### Root Cause
메모리 압박.
### Action Items
1. 메모리 증설.
2. 스왑 비활성화.

---

## 78. Pod HTTP Connection Leak
---
service: api-service
error_message: connection leak detected
---
### Incident Summary
HTTP 커넥션 누수로 리소스 고갈.
### Root Cause
커넥션 종료 누락.
### Action Items
1. 코드 수정.
2. 커넥션 타임아웃 설정.

---

## 79. Node Placement Group Imbalance
---
service: eks-nodegroup
error_message: placement imbalance
---
### Incident Summary
노드 배치 불균형으로 장애 영향 확대.
### Root Cause
AZ 편중 배치.
### Action Items
1. 멀티 AZ 분산.
2. 노드 그룹 재구성.

---

## 80. Pod Startup Probe Failed
---
service: application
error_message: startup probe failed
---
### Incident Summary
기동 검사 실패로 파드 종료.
### Root Cause
초기 로딩 시간 과소 평가.
### Action Items
1. Startup Probe 추가.
2. 지연 시간 조정.

---

## 81. EKS Node Reboot Loop
---
service: eks-nodegroup
error_message: node reboot loop
---
### Incident Summary
노드가 반복 재부팅됨.
### Root Cause
시스템 설정 오류.
### Action Items
1. 노드 교체.
2. AMI 검증.

---

## 82. Pod Config Drift Detected
---
service: config
error_message: config drift detected
---
### Incident Summary
실행 중 설정과 정의된 설정 불일치.
### Root Cause
수동 수정.
### Action Items
1. GitOps 적용.
2. 수동 변경 금지.

---

## 83. Service Load Imbalance
---
service: network
error_message: uneven traffic distribution
---
### Incident Summary
특정 파드에 트래픽 집중.
### Root Cause
세션 고정 설정.
### Action Items
1. Sticky Session 해제.
2. 로드밸런싱 정책 조정.

---

## 84. Node Security Patch Missing
---
service: eks-nodegroup
error_message: security patch missing
---
### Incident Summary
보안 패치 미적용 노드 존재.
### Root Cause
노드 업데이트 누락.
### Action Items
1. 정기 패치 스케줄링.
2. 노드 교체 자동화.

---

## 85. Pod Large Env Var Size
---
service: application
error_message: environment variable too large
---
### Incident Summary
환경 변수 크기 초과.
### Root Cause
대용량 설정 주입.
### Action Items
1. ConfigMap 분리.
2. 설정 파일 방식 전환.

---

## 86. Node Network Interface Reset
---
service: network
error_message: network interface reset
---
### Incident Summary
네트워크 인터페이스 리셋 발생.
### Root Cause
드라이버 불안정.
### Action Items
1. AMI 업데이트.
2. 노드 교체.

---

## 87. Pod Sidecar Sync Failure
---
service: service-mesh
error_message: sidecar sync failed
---
### Incident Summary
사이드카 컨테이너 동기화 실패.
### Root Cause
컨트롤 플레인 통신 오류.
### Action Items
1. 사이드카 재배포.
2. 네트워크 점검.

---

## 88. Node Disk IO Saturation
---
service: eks-nodegroup
error_message: disk io saturation
---
### Incident Summary
디스크 I/O 포화로 처리 지연.
### Root Cause
동시 쓰기 작업 증가.
### Action Items
1. IOPS 상향.
2. 워크로드 분산.

---

## 89. Pod Graceful Shutdown Failed
---
service: application
error_message: shutdown timeout
---
### Incident Summary
정상 종료 실패로 데이터 손실 위험.
### Root Cause
종료 로직 지연.
### Action Items
1. 종료 로직 최적화.
2. Grace Period 조정.

---

## 90. EKS Logging Addon Failed
---
service: logging
error_message: logging addon unhealthy
---
### Incident Summary
EKS 로깅 애드온 장애.
### Root Cause
리소스 부족.
### Action Items
1. 리소스 증설.
2. 애드온 재시작.

---

## 91. Node SELinux Denial
---
service: eks-nodegroup
error_message: selinux denial
---
### Incident Summary
SELinux 정책으로 접근 차단.
### Root Cause
보안 정책 충돌.
### Action Items
1. 정책 조정.
2. 컨테이너 권한 점검.

---

## 92. Pod File Descriptor Leak
---
service: application
error_message: fd leak detected
---
### Incident Summary
파일 디스크립터 누수.
### Root Cause
리소스 해제 누락.
### Action Items
1. 코드 수정.
2. 모니터링 추가.

---

## 93. Node Drain Data Loss
---
service: eks-nodegroup
error_message: data loss during drain
---
### Incident Summary
노드 드레인 중 데이터 손실 발생.
### Root Cause
Stateful 파드 보호 미흡.
### Action Items
1. PDB 강화.
2. StatefulSet 전략 수정.

---

## 94. Pod API Rate Limit Hit
---
service: application
error_message: rate limit exceeded
---
### Incident Summary
내부 API 호출 제한 초과.
### Root Cause
과도한 내부 호출.
### Action Items
1. 호출 빈도 제한.
2. 캐시 적용.

---

## 95. EKS Control Plane Latency High
---
service: eks-control-plane
error_message: high latency detected
---
### Incident Summary
컨트롤 플레인 응답 지연.
### Root Cause
대량 API 요청.
### Action Items
1. 요청 배치 처리.
2. 호출 패턴 개선.

---

## 96. Pod Volume Resize Failed
---
service: storage
error_message: volume resize failed
---
### Incident Summary
PVC 확장 실패.
### Root Cause
스토리지 클래스 제한.
### Action Items
1. StorageClass 수정.
2. CSI 버전 확인.

---

## 97. Node Metadata Token Expired
---
service: eks-nodegroup
error_message: metadata token expired
---
### Incident Summary
메타데이터 토큰 만료로 AWS API 호출 실패.
### Root Cause
IMDS 토큰 재발급 실패.
### Action Items
1. 토큰 재발급 로직 확인.
2. 노드 재시작.

---

## 98. Pod JVM Heap Exhausted
---
service: application
error_message: java.lang.OutOfMemoryError
---
### Incident Summary
JVM Heap 부족으로 애플리케이션 중단.
### Root Cause
Heap 사이즈 과소 설정.
### Action Items
1. JVM 옵션 조정.
2. 메모리 사용 분석.

---

## 99. Node Certificate Expired
---
service: eks-nodegroup
error_message: certificate expired
---
### Incident Summary
노드 인증서 만료로 클러스터 통신 실패.
### Root Cause
인증서 자동 갱신 실패.
### Action Items
1. 노드 재조인.
2. 인증서 갱신 점검.

---

## 100. Cluster Wide Resource Fragmentation
---
service: eks-cluster
error_message: resources fragmented
---
### Incident Summary
리소스 단편화로 신규 파드 배치 실패.
### Root Cause
비균등한 리소스 요청 설정.
### Action Items
1. 리소스 요청 표준화.
2. 노드 리밸런싱 수행.

---
