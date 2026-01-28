"""
=====================================================
Milvus Vector DB 클라이언트
=====================================================
설명: Milvus를 사용한 과거 장애 사례 벡터 검색
역할: 현재 로그와 유사한 과거 사례 검색 (RAG용)
=====================================================
"""

from typing import Any, Dict, List

from config.settings import settings
from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)
from utils.logger import setup_logger

logger = setup_logger(__name__)


class MilvusClient:
    """Milvus 벡터 DB 클라이언트"""

    def __init__(self):
        """초기화 및 연결"""
        self.collection_name = settings.MILVUS_COLLECTION_NAME
        self.dim = settings.VECTOR_DIMENSION
        self.collection = None

        try:
            self._connect()
            self._init_collection()
        except Exception as e:
            logger.error(f"Milvus 초기화 실패: {e}")
            raise

    def _connect(self):
        """Milvus 서버 연결"""
        try:
            connections.connect(
                alias="default", host=settings.MILVUS_HOST, port=settings.MILVUS_PORT
            )
            logger.info(f"Milvus 연결 성공: {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
        except Exception as e:
            if settings.MILVUS_HOST in ["localhost", "127.0.0.1"]:
                logger.error(
                    "❌ 로컬에서 EKS Milvus에 접속하려면 포트 포워딩이 필요합니다.\n"
                    "   새 터미널에서 아래 명령어를 실행하세요:\n"
                    "   kubectl port-forward svc/milvus -n milvus 19530:19530"
                )
            raise e

    def _init_collection(self):
        """컬렉션 초기화 (없으면 생성, 있으면 로드)"""
        if utility.has_collection(self.collection_name):
            self.collection = Collection(self.collection_name)
            self.collection.load()
            logger.info(f"기존 컬렉션 로드: {self.collection_name}")
        else:
            self._create_collection()

    def _create_collection(self):
        """새 컬렉션 스키마 정의 및 생성"""
        fields = [
            FieldSchema(
                name="id",
                dtype=DataType.INT64,
                is_primary=True,
                auto_id=True,
                description="Primary Key",
            ),
            FieldSchema(
                name="vector",
                dtype=DataType.FLOAT_VECTOR,
                dim=self.dim,
                description="Log Embedding Vector",
            ),
            FieldSchema(
                name="service",
                dtype=DataType.VARCHAR,
                max_length=64,
                description="Service Name",
            ),
            FieldSchema(
                name="error_message",
                dtype=DataType.VARCHAR,
                max_length=1024,
                description="Error Summary",
            ),
            FieldSchema(
                name="cause",
                dtype=DataType.VARCHAR,
                max_length=2048,
                description="Root Cause",
            ),
            FieldSchema(
                name="action",
                dtype=DataType.VARCHAR,
                max_length=2048,
                description="Resolution Action",
            ),
        ]

        schema = CollectionSchema(fields, description="Log Analysis Knowledge Base")
        self.collection = Collection(name=self.collection_name, schema=schema)

        # 인덱스 생성 (IVF_FLAT or HNSW)
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128},
        }
        self.collection.create_index(field_name="vector", index_params=index_params)
        self.collection.load()
        logger.info(f"새 컬렉션 생성 및 로드 완료: {self.collection_name}")

    def search_similar_logs(
        self, query_vector: List[float], top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        벡터 유사도 검색

        Args:
            query_vector (List[float]): 검색할 벡터
            top_k (int): 반환할 상위 결과 수

        Returns:
            List[Dict]: 유사한 과거 사례 리스트 (cause, action 등 포함 for RAG)
        """
        if not self.collection:
            logger.warning("컬렉션이 로드되지 않아 검색 불가")
            return []

        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}

        try:
            results = self.collection.search(
                data=[query_vector],
                anns_field="vector",
                param=search_params,
                limit=top_k,
                output_fields=["service", "error_message", "cause", "action"],
            )

            similar_cases = []
            for hits in results:
                for hit in hits:
                    similar_cases.append(
                        {
                            "id": hit.id,
                            "score": hit.distance,  # L2 거리 (작을수록 유사)
                            "service": hit.entity.get("service"),
                            "error": hit.entity.get("error_message"),
                            "cause": hit.entity.get("cause"),
                            "action": hit.entity.get("action"),
                        }
                    )
            
            logger.info(f"유사 사례 {len(similar_cases)}건 발견")
            return similar_cases

        except Exception as e:
            logger.error(f"벡터 검색 중 오류 발생: {e}")
            return []

    def insert_log_case(self, log_data: Dict[str, Any], vector: List[float]):
        """
        새로운 장애 사례 지식화 (벡터 DB 저장)

        Args:
            log_data (Dict): {service, error_message, cause, action} 포함
            vector (List[float]): 임베딩 벡터
        """
        if not self.collection:
            return

        try:
            # 데이터 준비 (스키마 순서와 무관하게 kwargs로 들어가는게 아니라 리스트로 넣어야 함 usually)
            # Pymilvus insert takes list of columns (old) or list of dicts (new in recent versions)
            # Using list of dicts for clearer code if supported, else list of lists.
            # Milvus 2.x insert accepts: [ [id1, id2], [vec1, vec2], ... ] OR [{...}, {...}] rows
            
            # 행 단위 데이터 구성
            row = {
                "vector": vector,
                "service": log_data.get("service", "unknown")[:64],
                "error_message": log_data.get("message", "")[:1024],
                "cause": log_data.get("cause", "")[:2048],
                "action": log_data.get("action", "")[:2048],
            }

            self.collection.insert([row])
            self.collection.flush()  # 바로 반영
            logger.info(f"신규 사례 저장 완료: {row['service']} - {row['error_message'][:30]}...")

        except Exception as e:
            logger.error(f"데이터 삽입 실패: {e}")
