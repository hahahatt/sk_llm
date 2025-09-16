#!/usr/bin/env python3
"""
시나리오 기반 다중 로그 생성기 설치 스크립트
"""

import os
import sys
import subprocess

def create_directory_structure():
    """디렉토리 구조 생성"""
    
    directories = [
        'src',
        'logs',
        'scenarios',
        'exports'
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ 디렉토리 생성: {directory}")
        else:
            print(f"📁 디렉토리 존재: {directory}")

def install_requirements():
    """필수 패키지 설치"""
    
    print("📦 필수 패키지 설치 중...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 패키지 설치 완료")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 패키지 설치 실패: {e}")
        return False