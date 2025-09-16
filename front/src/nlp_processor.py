"""
자연어 처리 모듈
OpenAI GPT를 사용하여 사용자 입력을 분석하고 시나리오를 구체화
"""

import openai
import json
import re
from typing import Dict, List, Any

class NLPProcessor:
    def __init__(self, api_key: str):
        """
        NLP 프로세서 초기화
        
        Args:
            api_key (str): OpenAI API 키
        """
        self.client = openai.OpenAI(api_key=api_key)
        
    def process_scenario(self, user_input: str) -> Dict[str, Any]:
        """
        사용자 입력을 분석하여 구체적인 시나리오 생성
        
        Args:
            user_input (str): 사용자가 입력한 자연어 시나리오
            
        Returns:
            Dict[str, Any]: 구체화된 시나리오 정보
        """
        
        # 시스템 프롬프트 정의
        system_prompt = """
당신은 사이버 보안 전문가입니다. 사용자가 입력한 자연어 시나리오를 분석하여 구체적인 보안 시나리오를 생성해주세요.

다음 JSON 형태로 응답해주세요:

{
    "title": "시나리오 제목",
    "description": "시나리오 상세 설명",
    "attack_type": "공격 유형 (web_attack, malware, insider_threat, ddos, apt, ransomware 중 하나)",
    "timeline": [
        "공격 단계 1",
        "공격 단계 2",
        "공격 단계 3",
        "..."
    ],
    "log_types": [
        {
            "name": "로그 시스템 이름",
            "type": "로그 타입 (영문, 소문자, 언더스코어)",
            "description": "해당 로그에서 기록될 내용 설명"
        }
    ]
}

시나리오 유형별 대표적인 로그 타입들:
- web_attack: firewall, webserver, waf, auth, database, proxy
- malware: firewall, email, endpoint, dns, network  
- insider_threat: auth, fileserver, usb, email, dlp
- ddos: firewall, router, loadbalancer, webserver, cdn
- apt: firewall, email, endpoint, dns, network, auth, database
- ransomware: endpoint, fileserver, email, auth, network, backup

사용자 입력을 분석하여 가장 적절한 공격 유형을 선택하고, 해당 유형에 맞는 로그 타입들을 포함시켜 주세요.
타임라인은 실제 공격 흐름에 맞게 6-10단계로 구성해주세요.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"다음 시나리오를 분석하고 구체화해주세요:\n\n{user_input}"}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # JSON 응답 파싱
            content = response.choices[0].message.content
            
            # JSON 추출 (마크다운 코드 블록 제거)
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 코드 블록이 없는 경우 전체 내용에서 JSON 찾기
                json_str = content
            
            scenario = json.loads(json_str)
            
            # 필수 필드 검증 및 기본값 설정
            scenario = self._validate_and_enhance_scenario(scenario)
            
            return scenario
            
        except json.JSONDecodeError as e:
            raise Exception(f"JSON 파싱 오류: {str(e)}")
        except Exception as e:
            raise Exception(f"시나리오 분석 실패: {str(e)}")
    
    def _validate_and_enhance_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        시나리오 검증 및 보완
        
        Args:
            scenario (Dict[str, Any]): 원본 시나리오
            
        Returns:
            Dict[str, Any]: 검증되고 보완된 시나리오
        """
        
        # 필수 필드 기본값 설정
        defaults = {
            "title": "사용자 정의 시나리오",
            "description": "사용자가 입력한 보안 시나리오",
            "attack_type": "web_attack",
            "timeline": [
                "공격 준비 단계",
                "초기 침입 시도",
                "권한 획득",
                "내부 탐색",
                "목표 달성",
                "흔적 제거"
            ],
            "log_types": []
        }
        
        # 기본값으로 누락된 필드 채우기
        for key, default_value in defaults.items():
            if key not in scenario:
                scenario[key] = default_value
        
        # 로그 타입이 비어있으면 attack_type에 따라 기본 로그 타입 설정
        if not scenario["log_types"]:
            scenario["log_types"] = self._get_default_log_types(scenario["attack_type"])
        
        # 로그 타입 필드 검증
        for log_type in scenario["log_types"]:
            if "name" not in log_type:
                log_type["name"] = "Unknown System"
            if "type" not in log_type:
                log_type["type"] = "unknown"
            if "description" not in log_type:
                log_type["description"] = "시스템 로그"
        
        return scenario
    
    def _get_default_log_types(self, attack_type: str) -> List[Dict[str, str]]:
        """
        공격 유형별 기본 로그 타입 반환
        
        Args:
            attack_type (str): 공격 유형
            
        Returns:
            List[Dict[str, str]]: 기본 로그 타입 목록
        """
        
        default_logs = {
            "web_attack": [
                {"name": "방화벽", "type": "firewall", "description": "네트워크 트래픽 차단 및 허용 로그"},
                {"name": "웹서버", "type": "webserver", "description": "HTTP 요청 및 응답 로그"},
                {"name": "WAF", "type": "waf", "description": "웹 애플리케이션 방화벽 탐지 로그"},
                {"name": "인증시스템", "type": "auth", "description": "로그인 시도 및 권한 변경 로그"},
                {"name": "데이터베이스", "type": "database", "description": "쿼리 실행 및 데이터 접근 로그"},
                {"name": "프록시", "type": "proxy", "description": "네트워크 프록시 트래픽 로그"}
            ],
            "malware": [
                {"name": "방화벽", "type": "firewall", "description": "의심스러운 외부 통신 차단 로그"},
                {"name": "이메일게이트웨이", "type": "email", "description": "이메일 필터링 및 첨부파일 검사 로그"},
                {"name": "엔드포인트", "type": "endpoint", "description": "악성코드 탐지 및 실행 로그"},
                {"name": "DNS", "type": "dns", "description": "악성 도메인 질의 로그"},
                {"name": "네트워크", "type": "network", "description": "내부 네트워크 스캔 및 전파 로그"}
            ],
            "insider_threat": [
                {"name": "인증시스템", "type": "auth", "description": "로그인 시간 및 위치 기록"},
                {"name": "파일서버", "type": "fileserver", "description": "파일 접근 및 복사 기록"},
                {"name": "USB모니터링", "type": "usb", "description": "USB 연결 및 파일 전송 로그"},
                {"name": "이메일시스템", "type": "email", "description": "이메일 발송 및 첨부파일 로그"},
                {"name": "DLP시스템", "type": "dlp", "description": "데이터 유출 방지 탐지 로그"}
            ],
            "ddos": [
                {"name": "방화벽", "type": "firewall", "description": "대량 트래픽 패킷 기록"},
                {"name": "라우터", "type": "router", "description": "네트워크 라우팅 및 대역폭 로그"},
                {"name": "로드밸런서", "type": "loadbalancer", "description": "서버 부하 분산 상태 로그"},
                {"name": "웹서버", "type": "webserver", "description": "HTTP 요청 처리 상태 로그"},
                {"name": "CDN", "type": "cdn", "description": "콘텐츠 전송 네트워크 상태 로그"}
            ],
            "apt": [
                {"name": "방화벽", "type": "firewall", "description": "지속적인 외부 통신 로그"},
                {"name": "이메일게이트웨이", "type": "email", "description": "스피어 피싱 이메일 로그"},
                {"name": "엔드포인트", "type": "endpoint", "description": "악성코드 및 RAT 탐지 로그"},
                {"name": "DNS", "type": "dns", "description": "C&C 도메인 질의 로그"},
                {"name": "네트워크", "type": "network", "description": "내부 네트워크 정찰 로그"},
                {"name": "인증시스템", "type": "auth", "description": "권한 상승 시도 로그"},
                {"name": "데이터베이스", "type": "database", "description": "민감 정보 접근 로그"}
            ],
            "ransomware": [
                {"name": "엔드포인트", "type": "endpoint", "description": "파일 암호화 및 프로세스 로그"},
                {"name": "파일서버", "type": "fileserver", "description": "대량 파일 수정 및 삭제 로그"},
                {"name": "이메일시스템", "type": "email", "description": "랜섬 요구 이메일 로그"},
                {"name": "인증시스템", "type": "auth", "description": "관리자 계정 탈취 시도 로그"},
                {"name": "네트워크", "type": "network", "description": "내부 네트워크 확산 로그"},
                {"name": "백업시스템", "type": "backup", "description": "백업 파일 접근 및 삭제 로그"}
            ]
        }
        
        return default_logs.get(attack_type, default_logs["web_attack"])
    
    def enhance_scenario_details(self, scenario: Dict[str, Any], user_feedback: str) -> Dict[str, Any]:
        """
        사용자 피드백을 바탕으로 시나리오 세부사항 보완
        
        Args:
            scenario (Dict[str, Any]): 기존 시나리오
            user_feedback (str): 사용자 피드백
            
        Returns:
            Dict[str, Any]: 보완된 시나리오
        """
        
        system_prompt = """
기존 시나리오를 사용자 피드백에 따라 수정하고 보완해주세요.
동일한 JSON 형태로 응답하되, 사용자가 요청한 변경사항을 반영해주세요.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"기존 시나리오:\n{json.dumps(scenario, ensure_ascii=False, indent=2)}\n\n사용자 피드백:\n{user_feedback}"}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            
            # JSON 추출
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = content
            
            enhanced_scenario = json.loads(json_str)
            
            return self._validate_and_enhance_scenario(enhanced_scenario)
            
        except Exception as e:
            raise Exception(f"시나리오 보완 실패: {str(e)}")