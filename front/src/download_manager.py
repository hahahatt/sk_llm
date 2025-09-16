"""
다운로드 관리 모듈
생성된 로그 파일들의 다운로드 및 압축 기능 제공
"""

import zipfile
import io
from typing import Dict, Any
from datetime import datetime

class DownloadManager:
    def __init__(self):
        """다운로드 매니저 초기화"""
        pass
    
    def create_zip_archive(self, generated_logs: Dict[str, Dict[str, Any]]) -> bytes:
        """
        생성된 로그들을 ZIP 아카이브로 생성
        
        Args:
            generated_logs (Dict[str, Dict[str, Any]]): 생성된 로그 데이터
            
        Returns:
            bytes: ZIP 파일 바이트 데이터
        """
        
        # 메모리 내에서 ZIP 파일 생성
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # 각 로그 파일을 ZIP에 추가
            for log_type, log_data in generated_logs.items():
                file_name = log_data['filename']
                file_content = log_data['content']
                
                # ZIP 파일에 로그 추가
                zip_file.writestr(file_name, file_content.encode('utf-8'))
            
            # README 파일 추가
            readme_content = self._generate_readme(generated_logs)
            zip_file.writestr('README.txt', readme_content.encode('utf-8'))
        
        zip_buffer.seek(0)
        return zip_buffer.read()
    
    def _generate_readme(self, generated_logs: Dict[str, Dict[str, Any]]) -> str:
        """
        README 파일 내용 생성
        
        Args:
            generated_logs (Dict[str, Dict[str, Any]]): 생성된 로그 데이터
            
        Returns:
            str: README 파일 내용
        """
        
        readme_content = f"""
시나리오 기반 다중 로그 생성기
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

이 아카이브에는 시나리오 기반으로 생성된 {len(generated_logs)}개의 로그 파일이 포함되어 있습니다.

생성된 로그 파일 목록:
{'='*50}
"""
        
        for log_type, log_data in generated_logs.items():
            lines_count = len(log_data['content'].split('\n'))
            file_size = len(log_data['content'].encode('utf-8'))
            
            readme_content += f"""
📄 {log_data['filename']}
   - 시스템: {log_data['name']}
   - 로그 라인 수: {lines_count:,}개
   - 파일 크기: {self._format_file_size(file_size)}
"""
        
        readme_content += f"""

사용 방법:
{'='*50}
1. 각 .log 파일을 원하는 로그 분석 도구에 로드하세요.
2. 시간순으로 정렬하여 공격 시나리오의 흐름을 확인하세요.
3. 여러 시스템의 로그를 상관 분석하여 종합적인 보안 이벤트를 파악하세요.

주의사항:
{'='*50}
- 이 로그들은 시뮬레이션 목적으로 생성된 것입니다.
- 실제 보안 사고가 아닌 교육/테스트 용도로만 사용하세요.
- 로그 분석 연습 및 SIEM 도구 테스트에 활용하세요.

생성기 정보:
{'='*50}
- 개발: 시나리오 기반 다중 로그 생성기
- 버전: 1.0
- 생성 엔진: AI 기반 자연어 처리
"""
        
        return readme_content
    
    def _format_file_size(self, size_bytes: int) -> str:
        """
        파일 크기를 읽기 쉬운 형태로 포맷
        
        Args:
            size_bytes (int): 바이트 크기
            
        Returns:
            str: 포맷된 크기 문자열
        """
        
        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    def get_file_statistics(self, generated_logs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        생성된 로그 파일들의 통계 정보 생성
        
        Args:
            generated_logs (Dict[str, Dict[str, Any]]): 생성된 로그 데이터
            
        Returns:
            Dict[str, Any]: 통계 정보
        """
        
        total_files = len(generated_logs)
        total_lines = 0
        total_size = 0
        
        file_details = []
        
        for log_type, log_data in generated_logs.items():
            lines = len(log_data['content'].split('\n'))
            size = len(log_data['content'].encode('utf-8'))
            
            total_lines += lines
            total_size += size
            
            file_details.append({
                'name': log_data['name'],
                'filename': log_data['filename'],
                'lines': lines,
                'size': size,
                'size_formatted': self._format_file_size(size)
            })
        
        return {
            'total_files': total_files,
            'total_lines': total_lines,
            'total_size': total_size,
            'total_size_formatted': self._format_file_size(total_size),
            'file_details': file_details,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def create_log_summary(self, generated_logs: Dict[str, Dict[str, Any]], 
                          scenario: Dict[str, Any]) -> str:
        """
        로그 생성 요약 정보 생성
        
        Args:
            generated_logs (Dict[str, Dict[str, Any]]): 생성된 로그 데이터
            scenario (Dict[str, Any]): 시나리오 정보
            
        Returns:
            str: 요약 정보
        """
        
        stats = self.get_file_statistics(generated_logs)
        
        summary = f"""
📊 로그 생성 요약 보고서
{'='*60}

🎯 시나리오 정보:
   제목: {scenario.get('title', 'Unknown')}
   공격 유형: {scenario.get('attack_type', 'Unknown')}
   설명: {scenario.get('description', 'No description')}

📈 생성 통계:
   총 로그 파일 수: {stats['total_files']}개
   총 로그 라인 수: {stats['total_lines']:,}개
   총 파일 크기: {stats['total_size_formatted']}
   생성 시간: {stats['generated_at']}

📋 파일 상세 정보:
"""
        
        for detail in stats['file_details']:
            summary += f"""   • {detail['name']} ({detail['filename']})
     라인 수: {detail['lines']:,}개, 크기: {detail['size_formatted']}
"""
        
        summary += f"""
🔄 공격 타임라인:
"""
        
        for i, step in enumerate(scenario.get('timeline', []), 1):
            summary += f"   {i}. {step}\n"
        
        return summary