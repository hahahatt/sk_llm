import os
import json
import uuid
from typing import List, Dict, Any

class CaseLibraryManager:
    def __init__(self, user_id: str):
        """
        케이스 라이브러리 매니저 초기화. 사용자별로 데이터를 관리합니다.
        
        Args:
            user_id (str): 사용자 식별자
        """
        # 사용자 이름으로 사용할 수 없는 문자를 제거하여 안전한 파일명 생성
        safe_user_id = "".join(c for c in user_id if c.isalnum() or c in (' ', '_')).rstrip()
        if not safe_user_id:
            # 기본 사용자 이름 설정 (오류 방지)
            safe_user_id = "default_user"
        
        self.user_id = safe_user_id
        self.data_dir = 'data'
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 사용자별 고유 파일 경로 생성
        self.file_path = os.path.join(self.data_dir, f'case_library_{self.user_id}.json')

    def _save_cases(self, cases: List[Dict[str, Any]]):
        """케이스 데이터를 사용자의 JSON 파일에 저장"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(cases, f, ensure_ascii=False, indent=4)

    def load_cases(self) -> List[Dict[str, Any]]:
        """사용자별 케이스 라이브러리 파일 로드 및 자동 복구"""
        if not os.path.exists(self.file_path):
            return []
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content:
                    return []
                cases = json.loads(content)
            
            needs_update = False
            for case in cases:
                if 'id' not in case or not case.get('id'):
                    case['id'] = str(uuid.uuid4())
                    needs_update = True
            
            if needs_update:
                self._save_cases(cases)

            return cases
        except (json.JSONDecodeError, IOError):
            return []

    def add_case(self, scenario_data: Dict[str, Any]) -> bool:
        """새로운 케이스를 사용자의 라이브러리에 추가"""
        cases = self.load_cases()
        
        if 'id' not in scenario_data or not scenario_data.get('id'):
            scenario_data['id'] = str(uuid.uuid4())
        
        if any(c.get('id') == scenario_data['id'] for c in cases):
            return False

        if any(c.get('title') == scenario_data.get('title') for c in cases):
            return False

        cases.append(scenario_data)
        self._save_cases(cases)
        return True