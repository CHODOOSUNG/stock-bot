import pandas as pd
import requests
import io
import time
import os
from datetime import datetime

TOKEN = os.environ.get('TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# 종목 리스트 (원하는 만큼 추가하세요!)
target_stocks = [
    ('005930', '삼성전자'), ('000660', 'SK하이닉스'), ('005380', '현대차'), 
    ('035420', 'NAVER'), ('068270', '셀트리온'), ('005490', 'POSCO홀딩스'),
    ('035720', '카카오'), ('000270', '기아'), ('066570', 'LG전자'),
    ('096530', '씨젠'), ('006400', '삼성SDI'), ('051910', 'LG화학'),
    ('005935', '삼성전자우'), ('034020', '두산에너빌리티'), ('010130', '고려아연')
]

def get_stock_data(code):
    url = f"https://finance.naver.com/item/frgn.naver?code={code}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers)
        tables = pd.read_html(io.StringIO(res.text))
        for table in tables:
            if '외국인' in str(table.columns):
                table.columns = ['날짜', '종가', '전일비', '등락률', '거래량', '기관', '외국인', '보유주수', '보유율']
                table = table.iloc[1:]
                # 숫자형 변환
                for col in ['거래량', '기관', '외국인']:
                    table[col] = pd.to_numeric(table[col], errors='coerce')
                table['등락률_num'] = table['등락률'].replace({'%': '', '\+': ''}, regex=True).astype(float)
                return table
    except: return None
    return None

def generate_report():
    report_msg = f"📊 [{datetime.now().strftime('%Y-%m-%d')} 수급&거래량 분석]\n\n"
    found_list = ""
    
    for code, name in target_stocks:
        df = get_stock_data(code)
        if df is not None:
            # 1. 수급 조건: 5일 합계가 20일 평균의 4배 이상
            recent_5d_flow = df[['기관', '외국인']].head(5).sum().sum()
            avg_20d_flow = df[['기관', '외국인']].head(20).mean().sum()
            is_strong_flow = recent_5d_flow > (avg_20d_flow * 4)
            
            # 2. [추가] 거래량 조건: 당일 거래량이 20일 평균의 3배 이상
            today_vol = df['거래량'].iloc[0]
            avg_20d_vol = df['거래량'].head(20).mean()
            is_volume_spike = today_vol > (avg_20d_vol * 3)
            
            if is_strong_flow and is_volume_spike:
                found_list += f"🚀 {name} (수급+거래량 급증!)\n"
        time.sleep(0.5)
    
    if found_list:
        send_telegram_message(report_msg + "🚨 [핵심 포착 종목]\n" + found_list)
    else:
        send_telegram_message(report_msg + "금일 조건 만족 종목 없음.")

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
    requests.get(url)

if __name__ == "__main__":
    generate_report()
