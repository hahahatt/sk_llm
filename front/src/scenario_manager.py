"""
시나리오 관리 모듈
사전 정의된 샘플 시나리오들을 관리하고 제공
"""

from typing import Dict, Any

class ScenarioManager:
    def __init__(self):
        """시나리오 매니저 초기화"""
        self.sample_scenarios = self._initialize_sample_scenarios()
    
    def _initialize_sample_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """샘플 시나리오들 초기화"""
        
        return {
            "web_attack": {
                "title": "🌐 웹 애플리케이션 침입 공격",
                "description": "외부 공격자가 웹 애플리케이션의 취약점을 악용하여 시스템에 침입하고 민감한 데이터를 탈취하는 시나리오",
                "attack_type": "web_attack",
                "timeline": [
                    "공격자가 대상 웹 애플리케이션 정찰 및 스캔 시작",
                    "SQL 인젝션 취약점 발견 및 초기 공격 시도",
                    "웹 애플리케이션 방화벽(WAF) 우회 기법 적용",
                    "SQL 인젝션을 통한 관리자 계정 정보 탈취",
                    "탈취된 관리자 계정으로 로그인 및 권한 확인",
                    "데이터베이스 접근 권한 획득 및 스키마 정보 수집",
                    "민감한 고객 정보 및 개인정보 대량 조회",
                    "추출된 데이터를 외부 서버로 전송",
                    "백도어 설치 및 지속적인 접근 경로 확보",
                    "로그 삭제 및 공격 흔적 제거"
                ],
                "log_types": [
                    {
                        "name": "방화벽",
                        "type": "firewall",
                        "description": "외부에서 들어오는 네트워크 트래픽 차단 및 허용 로그"
                    },
                    {
                        "name": "웹서버",
                        "type": "webserver", 
                        "description": "HTTP/HTTPS 요청 및 응답, 오류 코드 로그"
                    },
                    {
                        "name": "WAF",
                        "type": "waf",
                        "description": "웹 애플리케이션 방화벽의 공격 탐지 및 차단 로그"
                    },
                    {
                        "name": "인증시스템",
                        "type": "auth",
                        "description": "로그인 시도, 인증 성공/실패, 권한 변경 로그"
                    },
                    {
                        "name": "데이터베이스",
                        "type": "database",
                        "description": "SQL 쿼리 실행, 데이터 접근, 권한 변경 로그"
                    },
                    {
                        "name": "프록시",
                        "type": "proxy",
                        "description": "네트워크 프록시를 통한 외부 통신 로그"
                    }
                ]
            },
            
            "malware": {
                "title": "🦠 멀웨어 감염 및 확산",
                "description": "이메일을 통한 멀웨어 유입으로 시스템 감염 및 네트워크 내 확산하는 시나리오",
                "attack_type": "malware",
                "timeline": [
                    "표적형 피싱 이메일 발송 및 사용자 수신",
                    "악성 첨부파일(Office 매크로) 실행",
                    "멀웨어 다운로드 및 시스템 감염",
                    "지속성 확보를 위한 레지스트리 및 시작프로그램 수정",
                    "안티바이러스 우회 및 시스템 정보 수집",
                    "네트워크 내 다른 시스템 스캔 및 정찰",
                    "SMB/RDP를 통한 횡적 이동 시도",
                    "추가 시스템 감염 및 봇넷 구성",
                    "C&C 서버와 통신 시작 및 원격 제어",
                    "데이터 수집 및 외부 유출 준비"
                ],
                "log_types": [
                    {
                        "name": "방화벽",
                        "type": "firewall",
                        "description": "의심스러운 외부 통신 차단 및 C&C 통신 로그"
                    },
                    {
                        "name": "이메일게이트웨이",
                        "type": "email",
                        "description": "이메일 필터링, 첨부파일 검사, 스팸 탐지 로그"
                    },
                    {
                        "name": "엔드포인트",
                        "type": "endpoint",
                        "description": "악성코드 탐지, 프로세스 실행, 파일 변경 로그"
                    },
                    {
                        "name": "DNS",
                        "type": "dns",
                        "description": "악성 도메인 질의, C&C 서버 통신 로그"
                    },
                    {
                        "name": "네트워크",
                        "type": "network",
                        "description": "내부 네트워크 스캔, 횡적 이동, 비정상 트래픽 로그"
                    }
                ]
            },
            
            "insider_threat": {
                "title": "👤 내부자 위협",
                "description": "권한을 가진 내부 직원이 민감한 정보에 부적절하게 접근하여 외부로 유출하는 시나리오",
                "attack_type": "insider_threat",
                "timeline": [
                    "정상 업무시간 외 시스템 접근 시도",
                    "평소보다 높은 권한의 파일 및 디렉토리 접근",
                    "대량의 민감한 고객 정보 및 기업 기밀 조회",
                    "업무와 무관한 파일 서버 영역 탐색",
                    "USB 연결 및 대용량 파일 복사",
                    "개인 이메일 계정으로 기밀 파일 전송",
                    "클라우드 스토리지에 회사 데이터 업로드",
                    "VPN을 통한 외부에서의 추가 접근",
                    "접근 기록 삭제 및 흔적 제거 시도",
                    "퇴사 전 마지막 데이터 수집 활동"
                ],
                "log_types": [
                    {
                        "name": "인증시스템",
                        "type": "auth",
                        "description": "로그인 시간, 위치, 실패 시도, 권한 변경 로그"
                    },
                    {
                        "name": "파일서버",
                        "type": "fileserver",
                        "description": "파일 접근, 복사, 수정, 삭제 기록"
                    },
                    {
                        "name": "USB모니터링",
                        "type": "usb",
                        "description": "USB 연결, 파일 전송, 외부 저장장치 사용 로그"
                    },
                    {
                        "name": "이메일시스템",
                        "type": "email",
                        "description": "이메일 발송, 대용량 첨부파일, 외부 계정 통신 로그"
                    },
                    {
                        "name": "DLP시스템",
                        "type": "dlp",
                        "description": "데이터 유출 방지 정책 위반 탐지 로그"
                    }
                ]
            },
            
            "ddos": {
                "title": "⚡ DDoS 공격",
                "description": "대규모 분산 서비스 거부 공격으로 웹 서비스를 마비시키는 시나리오",
                "attack_type": "ddos",
                "timeline": [
                    "초기 정찰 및 대상 서버 취약점 스캔",
                    "소규모 트래픽 증가 및 서버 응답 테스트",
                    "봇넷 활성화 및 대규모 트래픽 공격 시작",
                    "HTTP Flood, SYN Flood 등 다양한 공격 기법 적용",
                    "서버 자원 고갈 및 응답 시간 급증",
                    "CDN 및 로드밸런서 과부하",
                    "서비스 완전 중단 및 접근 불가",
                    "공격 패턴 변경으로 방어 체계 우회",
                    "지속적인 대규모 트래픽 공격 유지",
                    "공격 종료 및 트래픽 정상화"
                ],
                "log_types": [
                    {
                        "name": "방화벽",
                        "type": "firewall",
                        "description": "대량 트래픽 패킷 기록 및 차단 로그"
                    },
                    {
                        "name": "라우터",
                        "type": "router",
                        "description": "네트워크 라우팅, 대역폭 사용량, 패킷 드롭 로그"
                    },
                    {
                        "name": "로드밸런서",
                        "type": "loadbalancer",
                        "description": "서버 부하 분산, 헬스체크, 응답시간 로그"
                    },
                    {
                        "name": "웹서버",
                        "type": "webserver",
                        "description": "HTTP 요청 처리, 오류 응답, 자원 사용량 로그"
                    },
                    {
                        "name": "CDN",
                        "type": "cdn",
                        "description": "콘텐츠 전송, 캐시 상태, 오리진 서버 응답 로그"
                    }
                ]
            },
            
            "apt": {
                "title": "🎯 APT 공격",
                "description": "지속적이고 은밀한 고급 지속 위협 공격으로 장기간에 걸친 정보 수집 시나리오",
                "attack_type": "apt",
                "timeline": [
                    "표적 조직 정찰 및 직원 정보 수집",
                    "스피어 피싱 이메일을 통한 초기 침입",
                    "제로데이 취약점 악용 및 시스템 감염",
                    "지속성 확보 및 은밀한 백도어 설치",
                    "내부 네트워크 정찰 및 중요 시스템 식별",
                    "권한 상승 및 도메인 관리자 계정 탈취",
                    "중요 서버 및 데이터베이스 접근",
                    "장기간에 걸친 민감 정보 수집",
                    "수집된 데이터의 은밀한 외부 전송",
                    "공격 흔적 제거 및 지속적인 접근 유지"
                ],
                "log_types": [
                    {
                        "name": "방화벽",
                        "type": "firewall",
                        "description": "장기간 지속되는 외부 통신 패턴 로그"
                    },
                    {
                        "name": "이메일게이트웨이",
                        "type": "email",
                        "description": "스피어 피싱 및 표적형 이메일 로그"
                    },
                    {
                        "name": "엔드포인트",
                        "type": "endpoint",
                        "description": "은밀한 악성코드, RAT, 백도어 탐지 로그"
                    },
                    {
                        "name": "DNS",
                        "type": "dns",
                        "description": "C&C 도메인 질의, DNS 터널링 로그"
                    },
                    {
                        "name": "네트워크",
                        "type": "network",
                        "description": "내부 네트워크 정찰, 횡적 이동 로그"
                    },
                    {
                        "name": "인증시스템",
                        "type": "auth",
                        "description": "권한 상승, 계정 탈취, 비정상 로그인 로그"
                    },
                    {
                        "name": "데이터베이스",
                        "type": "database",
                        "description": "민감 정보 접근, 대량 데이터 조회 로그"
                    }
                ]
            },
            
            "ransomware": {
                "title": "🔒 랜섬웨어 공격",
                "description": "파일 암호화를 통한 시스템 마비 및 금전적 요구를 하는 랜섬웨어 공격 시나리오",
                "attack_type": "ransomware",
                "timeline": [
                    "피싱 이메일 또는 취약점을 통한 초기 침입",
                    "랜섬웨어 페이로드 다운로드 및 실행",
                    "시스템 정보 수집 및 네트워크 환경 파악",
                    "백업 시스템 및 복구 도구 무력화",
                    "도메인 관리자 권한 획득 및 횡적 이동",
                    "중요 파일 및 데이터베이스 식별",
                    "대규모 파일 암호화 시작",
                    "시스템 부팅 및 복구 기능 차단",
                    "랜섬 노트 생성 및 금전 요구",
                    "추가 시스템 암호화 및 공격 확산"
                ],
                "log_types": [
                    {
                        "name": "엔드포인트",
                        "type": "endpoint",
                        "description": "파일 암호화, 프로세스 실행, 시스템 변경 로그"
                    },
                    {
                        "name": "파일서버",
                        "type": "fileserver",
                        "description": "대량 파일 수정, 삭제, 암호화 로그"
                    },
                    {
                        "name": "이메일시스템",
                        "type": "email",
                        "description": "초기 침입 이메일, 랜섬 요구 메시지 로그"
                    },
                    {
                        "name": "인증시스템",
                        "type": "auth",
                        "description": "관리자 계정 탈취, 권한 상승 로그"
                    },
                    {
                        "name": "네트워크",
                        "type": "network",
                        "description": "내부 네트워크 확산, 횡적 이동 로그"
                    },
                    {
                        "name": "백업시스템",
                        "type": "backup",
                        "description": "백업 파일 접근, 삭제, 무력화 로그"
                    }
                ]
            }
        }
    
    def get_sample_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """
        모든 샘플 시나리오 반환
        
        Returns:
            Dict[str, Dict[str, Any]]: 샘플 시나리오 딕셔너리
        """
        return self.sample_scenarios
    
    def get_scenario_by_key(self, key: str) -> Dict[str, Any]:
        """
        키로 특정 시나리오 반환
        
        Args:
            key (str): 시나리오 키
            
        Returns:
            Dict[str, Any]: 시나리오 정보
        """
        return self.sample_scenarios.get(key, {})
    
    def get_scenarios_by_attack_type(self, attack_type: str) -> Dict[str, Dict[str, Any]]:
        """
        공격 유형별 시나리오 반환
        
        Args:
            attack_type (str): 공격 유형
            
        Returns:
            Dict[str, Dict[str, Any]]: 해당 공격 유형의 시나리오들
        """
        return {
            key: scenario for key, scenario in self.sample_scenarios.items()
            if scenario.get('attack_type') == attack_type
        }