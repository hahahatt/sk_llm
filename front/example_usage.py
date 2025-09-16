#!/usr/bin/env python3
"""
시나리오 기반 다중 로그 생성기 사용 예시
CLI 버전으로 기본 기능 테스트
"""

import os
import sys
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.nlp_processor import NLPProcessor
from src.scenario_manager import ScenarioManager
from src.log_generator import LogGenerator
from src.download_manager import DownloadManager

def example_natural_language_processing():
    """자연어 처리 예시"""
    
    print("🤖 자연어 처리 예시")
    print("=" * 50)
    
    # API 키 확인
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("💡 .env 파일에서 API 키를 설정하거나 다음과 같이 실행하세요:")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        return None
    
    # NLP 프로세서 초기화
    nlp = NLPProcessor(api_key)
    
    # 사용자 입력 시뮬레이션
    user_inputs = [
        "웹서버에 SQL 인젝션 공격을 통해 고객 데이터를 탈취하는 시나리오를 만들어주세요",
        "이메일을 통한 랜섬웨어 공격으로 회사 시스템을 암호화하는 상황",
        "내부 직원이 USB를 이용해서 회사 기밀을 유출하는 시나리오"
    ]
    
    for i, user_input in enumerate(user_inputs, 1):
        print(f"\n📝 예시 {i}: {user_input}")
        
        try:
            processed_scenario = nlp.process_scenario(user_input)
            
            print(f"✅ 분석된 시나리오: {processed_scenario['title']}")
            print(f"🎯 공격 유형: {processed_scenario['attack_type']}")
            print(f"📊 로그 타입 수: {len(processed_scenario['log_types'])}")
            
            # 첫 번째 예시만 자세히 출력
            if i == 1:
                print(f"\n📋 타임라인:")
                for j, step in enumerate(processed_scenario['timeline'], 1):
                    print(f"   {j}. {step}")
                
                print(f"\n📊 생성될 로그 타입:")
                for log_type in processed_scenario['log_types']:
                    print(f"   • {log_type['name']}: {log_type['description']}")
                
                return processed_scenario
        
        except Exception as e:
            print(f"❌ 분석 실패: {str(e)}")
    
    return None

def example_sample_scenarios():
    """샘플 시나리오 예시"""
    
    print("\n📋 샘플 시나리오 예시")
    print("=" * 50)
    
    scenario_manager = ScenarioManager()
    samples = scenario_manager.get_sample_scenarios()
    
    for key, scenario in samples.items():
        print(f"\n🔸 {scenario['title']}")
        print(f"   유형: {scenario['attack_type']}")
        print(f"   로그 타입: {len(scenario['log_types'])}개")
        
        # 로그 타입 나열
        log_names = [log['name'] for log in scenario['log_types']]
        print(f"   시스템: {', '.join(log_names)}")
    
    # 첫 번째 샘플 반환
    return list(samples.values())[0]

def example_log_generation(scenario, log_count=100):
    """로그 생성 예시"""
    
    print(f"\n🚀 로그 생성 예시 (시나리오: {scenario['title']})")
    print("=" * 50)
    
    log_generator = LogGenerator()
    generated_logs = {}
    
    print(f"📊 {len(scenario['log_types'])}개 시스템의 로그를 각각 {log_count}개씩 생성 중...")
    
    for i, log_type in enumerate(scenario['log_types'], 1):
        print(f"   {i}. {log_type['name']} 로그 생성 중...")
        
        log_content = log_generator.generate_log_content(
            log_type, log_count, scenario
        )
        
        generated_logs[log_type['type']] = {
            'name': log_type['name'],
            'content': log_content,
            'filename': f"{log_type['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        }
        
        # 첫 3줄 미리보기
        lines = log_content.split('\n')[:3]
        print(f"      미리보기:")
        for line in lines:
            print(f"        {line}")
        print(f"      총 {len(log_content.split('\\n'))} 라인 생성")
    
    print("✅ 모든 로그 생성 완료!")
    return generated_logs

def example_download_management(generated_logs, scenario):
    """다운로드 관리 예시"""
    
    print(f"\n📦 다운로드 관리 예시")
    print("=" * 50)
    
    download_manager = DownloadManager()
    
    # 통계 정보 생성
    stats = download_manager.get_file_statistics(generated_logs)
    
    print(f"📈 생성 통계:")
    print(f"   총 파일 수: {stats['total_files']}개")
    print(f"   총 라인 수: {stats['total_lines']:,}개")
    print(f"   총 크기: {stats['total_size_formatted']}")
    
    # 파일별 상세 정보
    print(f"\n📋 파일별 정보:")
    for detail in stats['file_details']:
        print(f"   • {detail['name']}: {detail['lines']:,} 라인, {detail['size_formatted']}")
    
    # ZIP 아카이브 생성
    print(f"\n📦 ZIP 아카이브 생성...")
    zip_data = download_manager.create_zip_archive(generated_logs)
    
    # 출력 디렉토리 생성
    output_dir = 'exports'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # ZIP 파일 저장
    zip_filename = f"logs_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_path = os.path.join(output_dir, zip_filename)
    
    with open(zip_path, 'wb') as f:
        f.write(zip_data)
    
    print(f"✅ ZIP 파일 저장: {zip_path}")
    print(f"📏 ZIP 크기: {download_manager._format_file_size(len(zip_data))}")
    
    # 개별 파일도 저장
    logs_dir = 'logs'
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    print(f"\n📄 개별 로그 파일 저장:")
    for log_type, log_data in generated_logs.items():
        log_path = os.path.join(logs_dir, log_data['filename'])
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(log_data['content'])
        print(f"   • {log_data['filename']}")
    
    # 요약 보고서 생성
    summary = download_manager.create_log_summary(generated_logs, scenario)
    summary_path = os.path.join(output_dir, f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print(f"📊 요약 보고서 저장: {summary_path}")

def main():
    """메인 예시 실행 함수"""
    
    print("🚀 시나리오 기반 다중 로그 생성기 - 사용 예시")
    print("=" * 70)
    
    # .env 파일 로드 시도
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ .env 파일 로드됨")
    except ImportError:
        print("⚠️  python-dotenv가 설치되지 않음 (선택사항)")
    except Exception as e:
        print(f"⚠️  .env 파일 로드 실패: {e}")
    
    # 1. 자연어 처리 예시 (API 키 필요)
    nlp_scenario = example_natural_language_processing()
    
    # 2. 샘플 시나리오 예시
    sample_scenario = example_sample_scenarios()
    
    # 3. 로그 생성 예시 (샘플 시나리오 사용)
    scenario_to_use = nlp_scenario if nlp_scenario else sample_scenario
    generated_logs = example_log_generation(scenario_to_use, log_count=50)  # 예시용으로 50개만
    
    # 4. 다운로드 관리 예시
    example_download_management(generated_logs, scenario_to_use)
    
    print("\n" + "=" * 70)
    print("✅ 모든 예시 실행 완료!")
    print("\n📁 생성된 파일:")
    print("   • ./logs/ - 개별 로그 파일들")
    print("   • ./exports/ - ZIP 아카이브 및 요약 보고서")
    print("\n🚀 Streamlit 웹 인터페이스를 사용하려면:")
    print("   streamlit run main.py")

if __name__ == "__main__":
    main()