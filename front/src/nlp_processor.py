"""
자연어 처리 모듈
OpenAI GPT를 사용하여 사용자 입력을 분석하고 시나리오를 구체화
"""

import openai
import json
import re
import uuid  # id 생성을 위해 추가
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
        
        # 시스템 프롬프트에 difficulty 필드 추가
        system_prompt = """
당신은 사이버 보안 전문가입니다. 사용자가 입력한 자연어 시나리오를 분석하여 구체적인 보안 시나리오를 생성해주세요.

다음 JSON 형태로 응답해주세요:

{
    "title": "시나리오 제목",
    "description": "시나리오 상세 설명",
    "attack_type": "공격 유형 (web_attack, malware, insider_threat, ddos, apt, ransomware 중 하나)",
    "difficulty": "난이도 (초급, 중급, 고급 중 하나)",
    "timeline": [
        "공격 단계 1", "공격 단계 2", "..."
    ],
    "log_types": [
        { "name": "로그 시스템 이름", "type": "로그 타입", "description": "로그 내용 설명" }
    ]
}

시나리오의 복잡성과 전문성에 따라 난이도를 '초급', '중급', '고급'으로 분류해주세요.
타임라인은 실제 공격 흐름에 맞게 6-10단계로 구성해주세요.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"다음 시나리오를 분석하고 구체화해주세요:\n\n{user_input}"}
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            scenario = json.loads(content)
            
            # 생성된 시나리오에 고유 ID 부여
            scenario['id'] = str(uuid.uuid4())
            scenario = self._validate_and_enhance_scenario(scenario)
            
            return scenario
            
        except Exception as e:
            raise Exception(f"시나리오 분석 실패: {str(e)}")
    
    def _validate_and_enhance_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """시나리오 검증 및 보완 (difficulty 기본값 추가)"""
        
        defaults = {
            "title": "사용자 정의 시나리오", "description": "사용자가 입력한 보안 시나리오",
            "attack_type": "web_attack", "difficulty": "중급",
            "timeline": ["공격 준비", "초기 침입", "내부 활동", "목표 달성", "흔적 제거"],
            "log_types": []
        }
        
        for key, default_value in defaults.items():
            scenario.setdefault(key, default_value)
        
        if not scenario["log_types"]:
            scenario["log_types"] = self._get_default_log_types(scenario["attack_type"])
        
        return scenario
    
    def _get_default_log_types(self, attack_type: str) -> List[Dict[str, str]]:
        """공격 유형별 기본 로그 타입 반환"""
        # (기존 코드와 동일)
        default_logs = {
            "web_attack": [{"name": "웹서버", "type": "webserver", "description": "HTTP 요청 로그"}],
            "malware": [{"name": "엔드포인트", "type": "endpoint", "description": "프로세스 실행 로그"}],
            "insider_threat": [{"name": "파일서버", "type": "fileserver", "description": "파일 접근 로그"}],
            "ddos": [{"name": "방화벽", "type": "firewall", "description": "대량 트래픽 로그"}],
            "apt": [{"name": "네트워크", "type": "network", "description": "내부 통신 로그"}],
            "ransomware": [{"name": "엔드포인트", "type": "endpoint", "description": "파일 암호화 로그"}]
        }
        return default_logs.get(attack_type, default_logs["web_attack"])
    
    def enhance_scenario_details(self, scenario: Dict[str, Any], user_feedback: str) -> Dict[str, Any]:
        """사용자 피드백을 바탕으로 시나리오 세부사항 보완"""
        # (기존 코드와 동일)
        system_prompt = "기존 시나리오를 사용자 피드백에 따라 수정하고 보완해주세요. 동일한 JSON 형태로 응답하되, 사용자가 요청한 변경사항을 반영해주세요."
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"기존 시나리오:\n{json.dumps(scenario, ensure_ascii=False, indent=2)}\n\n사용자 피드백:\n{user_feedback}"}
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            enhanced_scenario = json.loads(content)
            return self._validate_and_enhance_scenario(enhanced_scenario)
        except Exception as e:
            raise Exception(f"시나리오 보완 실패: {str(e)}")

