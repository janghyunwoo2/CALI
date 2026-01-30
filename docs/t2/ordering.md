# rag 실험
## 파일 복사
- kubectl cp apps/consumer/tests/manual_test_rag.py consumer-7d74c96775-7wlg6:/app/tests/
## 스크립트 실행
- kubectl exec -it consumer-7d74c96775-7wlg6 -- python tests/manual_test_rag.py

