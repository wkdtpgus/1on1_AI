# Vercel 서버리스 함수용 엔트리 포인트
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.web.main import app

# Vercel이 이 변수를 찾습니다
handler = app