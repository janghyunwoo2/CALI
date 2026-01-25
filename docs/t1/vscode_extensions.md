# CALI 프로젝트 개발 - VS Code 확장 프로그램 추천

## 🎯 필수 확장 프로그램

### 1️⃣ Python 개발

#### **Python** (Microsoft)
- **ID**: `ms-python.python`
- **용도**: Python 언어 지원, IntelliSense, 디버깅, 린팅
- **필수 이유**: Consumer 애플리케이션 개발의 핵심

#### **Pylance** (Microsoft)
- **ID**: `ms-python.vscode-pylance`
- **용도**: Python 타입 체킹 및 고급 IntelliSense
- **필수 이유**: Pydantic 모델 타입 안정성 보장

#### **Python Docstring Generator**
- **ID**: `njpwerner.autodocstring`
- **용도**: 자동 docstring 생성
- **추천 설정**: Google / NumPy 스타일

---

### 2️⃣ Terraform / IaC

#### **HashiCorp Terraform** (HashiCorp)
- **ID**: `hashicorp.terraform`
- **용도**: Terraform 문법 하이라이팅, 자동완성, 검증
- **필수 이유**: 8개 Terraform 모듈 개발

#### **Terraform Autocomplete**
- **ID**: `erd0s.terraform-autocomplete`
- **용도**: Terraform 리소스 자동완성 강화

---

### 3️⃣ Kubernetes / YAML

#### **Kubernetes** (Microsoft)
- **ID**: `ms-kubernetes-tools.vscode-kubernetes-tools`
- **용도**: K8s 매니페스트 스니펫, 클러스터 관리, 디버깅
- **필수 이유**: Fluent Bit, Consumer 배포 관리

#### **YAML** (Red Hat)
- **ID**: `redhat.vscode-yaml`
- **용도**: YAML 스키마 검증, 자동완성
- **추천 설정**: Kubernetes 스키마 활성화

---

### 4️⃣ Docker

#### **Docker** (Microsoft)
- **ID**: `ms-azuretools.vscode-docker`
- **용도**: Dockerfile 린팅, 이미지 관리, 컨테이너 디버깅
- **필수 이유**: Fluent Bit, Consumer 이미지 빌드

---

### 5️⃣ AWS

#### **AWS Toolkit** (Amazon Web Services)
- **ID**: `amazonwebservices.aws-toolkit-vscode`
- **용도**: AWS 리소스 탐색, CloudFormation, S3 브라우저
- **유용한 기능**: EKS 클러스터 확인, S3 파일 업로드

---

## ⭐ 추천 확장 프로그램

### 코드 품질

#### **Ruff** (Astral Software)
- **ID**: `charliermarsh.ruff`
- **용도**: 초고속 Python 린터 및 포맷터 (Black + Flake8 + isort 통합)
- **추천 이유**: Pydantic 코드 스타일 일관성

#### **markdownlint** (David Anson)
- **ID**: `davidanson.vscode-markdownlint`
- **용도**: Markdown 문서 린팅
- **추천 이유**: 프로젝트 문서 품질 관리

---

### Git 협업

#### **GitLens** (GitKraken)
- **ID**: `eamodio.gitlens`
- **용도**: Git 히스토리, blame, 코드 변경 추적
- **유용한 기능**: 라인별 커밋 정보 표시

#### **Git Graph**
- **ID**: `mhutchie.git-graph`
- **용도**: 시각적 Git 브랜치 관리

---

### 생산성

#### **Remote - SSH** (Microsoft)
- **ID**: `ms-vscode-remote.remote-ssh`
- **용도**: 원격 서버에서 개발
- **추천 이유**: EKS 워커 노드 디버깅

#### **Path Intellisense**
- **ID**: `christian-kohler.path-intellisense`
- **용도**: 파일 경로 자동완성

#### **Todo Tree**
- **ID**: `gruntfuggly.todo-tree`
- **용도**: TODO 주석 하이라이팅 및 검색
- **추천 이유**: 프로젝트 전체 TODO 한눈에 확인

#### **Better Comments**
- **ID**: `aaron-bond.better-comments`
- **용도**: 주석 색상 구분 (TODO, FIXME, NOTE 등)

---

### 디버깅 & 테스트

#### **Python Test Explorer**
- **ID**: `littlefoxteam.vscode-python-test-adapter`
- **용도**: Pytest 테스트 시각적 실행

#### **REST Client**
- **ID**: `humao.rest-client`
- **용도**: HTTP 요청 테스트 (API 테스트용)

---

### JSON & 데이터

#### **Paste JSON as Code** (quicktype)
- **ID**: `quicktype.quicktype`
- **용도**: JSON을 Pydantic 모델로 자동 변환
- **추천 이유**: 로그 스키마 빠르게 생성

#### **JSON to TS** (MariusAlchimavicius)
- **ID**: `mariusalchimavicius.json-to-ts`
- **용도**: JSON 구조 분석

---

### 문서화

#### **Markdown All in One**
- **ID**: `yzhang.markdown-all-in-one`
- **용도**: Markdown 편집 강화 (목차 생성, 단축키)

#### **Mermaid Preview**
- **ID**: `bierner.markdown-mermaid`
- **용도**: Mermaid 다이어그램 미리보기
- **추천 이유**: 아키텍처 다이어그램 작성

---

## 🎨 테마 & UI (선택)

#### **Material Icon Theme**
- **ID**: `pkief.material-icon-theme`
- **용도**: 파일 아이콘 테마

#### **GitHub Theme**
- **ID**: `github.github-vscode-theme`
- **용도**: GitHub 스타일 컬러 테마

---

## ⚙️ 추천 VS Code 설정

프로젝트 루트에 `.vscode/settings.json` 생성:

```json
{
  // Python
  "python.defaultInterpreterPath": "${workspaceFolder}/apps/consumer/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "none",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  },

  // Terraform
  "[terraform]": {
    "editor.defaultFormatter": "hashicorp.terraform",
    "editor.formatOnSave": true
  },
  "terraform.languageServer.enable": true,

  // YAML
  "[yaml]": {
    "editor.defaultFormatter": "redhat.vscode-yaml",
    "editor.formatOnSave": true
  },
  "yaml.schemas": {
    "kubernetes": "k8s/**/*.yaml"
  },

  // Markdown
  "[markdown]": {
    "editor.wordWrap": "on",
    "editor.formatOnSave": false
  },

  // Git
  "git.autofetch": true,
  "git.confirmSync": false,

  // Files
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".terraform": true
  },

  // Editor
  "editor.rulers": [88], // PEP 8 line length
  "editor.minimap.enabled": false,
  "editor.bracketPairColorization.enabled": true
}
```

---

## 📦 확장 프로그램 일괄 설치 (선택)

`.vscode/extensions.json` 생성:

```json
{
  "recommendations": [
    // 필수
    "ms-python.python",
    "ms-python.vscode-pylance",
    "hashicorp.terraform",
    "ms-kubernetes-tools.vscode-kubernetes-tools",
    "redhat.vscode-yaml",
    "ms-azuretools.vscode-docker",
    "amazonwebservices.aws-toolkit-vscode",
    
    // 추천
    "charliermarsh.ruff",
    "davidanson.vscode-markdownlint",
    "eamodio.gitlens",
    "mhutchie.git-graph",
    "christian-kohler.path-intellisense",
    "gruntfuggly.todo-tree",
    "aaron-bond.better-comments",
    "quicktype.quicktype",
    "yzhang.markdown-all-in-one",
    "bierner.markdown-mermaid"
  ]
}
```

팀원들이 프로젝트를 열면 VS Code가 자동으로 추천 확장 설치를 제안합니다.

---

## 🚀 설치 방법

### 방법 1: VS Code UI에서 설치
1. VS Code 열기
2. 확장 프로그램 탭 (`Ctrl+Shift+X`)
3. 확장 ID로 검색 및 설치

### 방법 2: 커맨드라인 일괄 설치

```bash
# 필수 확장
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension hashicorp.terraform
code --install-extension ms-kubernetes-tools.vscode-kubernetes-tools
code --install-extension redhat.vscode-yaml
code --install-extension ms-azuretools.vscode-docker
code --install-extension amazonwebservices.aws-toolkit-vscode

# 추천 확장
code --install-extension charliermarsh.ruff
code --install-extension davidanson.vscode-markdownlint
code --install-extension eamodio.gitlens
code --install-extension gruntfuggly.todo-tree
code --install-extension aaron-bond.better-comments
code --install-extension quicktype.quicktype
code --install-extension yzhang.markdown-all-in-one
code --install-extension bierner.markdown-mermaid
```

---

## 💡 팁

1. **Python 가상환경 자동 활성화**: 
   - VS Code가 `apps/consumer/venv`를 자동 인식하도록 설정

2. **Terraform 자동 포맷**:
   - 저장 시 `terraform fmt` 자동 실행

3. **TODO 추적**:
   - Todo Tree로 프로젝트 전체 TODO 주석 확인
   - 현재 프로젝트에 많은 TODO 있음!

4. **Git 커밋 메시지**:
   - GitLens로 각 라인의 변경 이력 확인

5. **Kubernetes 디버깅**:
   - Kubernetes 확장으로 Pod 로그 실시간 확인
   - `kubectl` 명령어 자동완성

---

## 🎯 우선순위

**먼저 설치해야 할 TOP 5**:
1. ✅ Python (Microsoft)
2. ✅ HashiCorp Terraform
3. ✅ Kubernetes (Microsoft)
4. ✅ Docker (Microsoft)
5. ✅ Ruff (코드 품질)

나머지는 필요에 따라 추가하세요!
