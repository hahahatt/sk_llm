import os
import json
from typing import List, Dict, Any, Set

class ProgressManager:
    """
    사용자별 학습 진행도를 관리하는 클래스.
    """
    def __init__(self):
        self.data_dir = 'data'
        os.makedirs(self.data_dir, exist_ok=True)

    def _get_progress_file_path(self, user_id: str) -> str:
        """사용자별 진행도 파일 경로를 반환합니다."""
        safe_user_id = "".join(c for c in user_id if c.isalnum() or c in (' ', '_')).rstrip()
        user_id = safe_user_id if safe_user_id else "default_user"
        return os.path.join(self.data_dir, f'progress_{user_id}.json')

    def load_completed_scenarios(self, user_id: str) -> Set[str]:
        """사용자가 완료한 시나리오 ID 목록을 불러옵니다."""
        file_path = self._get_progress_file_path(user_id)
        if not os.path.exists(file_path):
            return set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return set(json.loads(content)) if content else set()
        except (json.JSONDecodeError, IOError):
            return set()

    def _save_completed_scenarios(self, user_id: str, completed_ids: Set[str]):
        """완료한 시나리오 ID 목록을 파일에 저장합니다."""
        file_path = self._get_progress_file_path(user_id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(list(completed_ids), f, ensure_ascii=False, indent=4)

    def mark_scenario_completed(self, user_id: str, scenario_id: str):
        """특정 시나리오를 완료 상태로 기록합니다."""
        if not user_id or not scenario_id:
            return
        completed_ids = self.load_completed_scenarios(user_id)
        completed_ids.add(scenario_id)
        self._save_completed_scenarios(user_id, completed_ids)

    def get_dashboard_stats(self, user_id: str, all_scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """대시보드에 표시할 통계 데이터를 계산합니다."""
        completed_ids = self.load_completed_scenarios(user_id)
        
        scenarios_with_id = [s for s in all_scenarios if s.get('id')]
        total_count = len(scenarios_with_id)
        
        stats_by_difficulty = {"초급": {"total": 0, "completed": 0},
                               "중급": {"total": 0, "completed": 0},
                               "고급": {"total": 0, "completed": 0}}
        
        for scenario in scenarios_with_id:
            difficulty = scenario.get("difficulty", "중급")
            if difficulty in stats_by_difficulty:
                stats_by_difficulty[difficulty]["total"] += 1
                if scenario['id'] in completed_ids:
                    stats_by_difficulty[difficulty]["completed"] += 1

        completed_count = sum(d['completed'] for d in stats_by_difficulty.values())

        return {
            "total_count": total_count,
            "completed_count": completed_count,
            "completion_rate": (completed_count / total_count) if total_count > 0 else 0,
            "stats_by_difficulty": stats_by_difficulty,
        }

