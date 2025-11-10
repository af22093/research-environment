import pandas as pd
import random
import csv
import os
import json
from datetime import datetime
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import re
import gspread

# --- Base Directory Setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Google Sheets Setup ---
from google.oauth2.service_account import Credentials

try:
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # 環境変数からの読み込みを優先、なければローカルファイルから
    if os.getenv('GOOGLE_CREDENTIALS'):
        creds_dict = json.loads(os.getenv('GOOGLE_CREDENTIALS'))
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        print("Google認証: 環境変数から読み込み成功")
    else:
        creds_path = os.path.join(BASE_DIR, "credentials.json")
        if os.path.exists(creds_path):
            creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
            print("Google認証: ローカルファイルから読み込み成功")
        else:
            creds = None
            print("警告: credentials.jsonが見つかりません")
    
    if creds:
        client = gspread.authorize(creds)
        SPREADSHEET_NAME = "Twitter Stress Results"
        sheet = client.open(SPREADSHEET_NAME).sheet1
        print("Googleスプレッドシートへの接続に成功しました。")
    else:
        sheet = None

except gspread.exceptions.SpreadsheetNotFound:
    print(f"エラー: スプレッドシート '{SPREADSHEET_NAME}' が見つかりません。")
    print("1. スプレッドシート名が正しいか確認してください。")
    print(f"2. サービスアカウントのメールアドレスにスプレッドシートが共有されているか確認してください。")
    sheet = None
except Exception as e:
    print(f"Googleスプレッドシートへの接続中に予期せぬエラーが発生しました: {e}")
    print("続行しますが、データはCSVにのみ保存されます。")
    sheet = None

# --- Flask App Setup ---
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'))
CORS(app)

# --- Helper Function ---
def clean_text_line(text):
    """Removes potential prefixes like usernames or list markers from a string."""
    if not isinstance(text, str):
        return ""
    cleaned = re.sub(r'^\s*([A-Za-z0-9_]+:|@\w+\s*:|\s*[-\*\d\.]+\s*)', '', text)
    return cleaned.strip().strip('「」')

# --- Main Simulator Class ---
class TwitterSimulator:
    def __init__(self, low_stress_file, mid_stress_file, high_stress_file):
        """
        Initializes the simulator by loading tweet data from CSV files.
        """
        self.P_LOW = 0.0
        self.P_MID = 0.44
        self.P_HIGH = 0.74

        try:
            self.df_low = pd.read_csv(low_stress_file, on_bad_lines='skip', engine='python')
            self.low_tweets = self.df_low['text'].dropna().tolist()
            print(f"Successfully loaded {len(self.low_tweets)} low-stress tweets from {low_stress_file}")

            self.df_mid = pd.read_csv(mid_stress_file, on_bad_lines='skip', engine='python')
            self.mid_tweets = self.df_mid['text'].dropna().tolist()
            print(f"Successfully loaded {len(self.mid_tweets)} mid-stress tweets from {mid_stress_file}")

            self.df_high = pd.read_csv(high_stress_file, on_bad_lines='skip', engine='python')
            self.high_tweets = self.df_high['text'].dropna().tolist()
            print(f"Successfully loaded {len(self.high_tweets)} high-stress tweets from {high_stress_file}")

        except FileNotFoundError as e:
            print(f"FATAL ERROR: Data file not found: {e}. Make sure all CSV files are in the same directory as app.py.")
            exit()
        except KeyError as e:
            print(f"FATAL ERROR: A required column is missing from a CSV file: {e}")
            exit()

    def _calculate_counts(self, p, n):
        """
        Calculates the number of tweets to draw from each category to achieve the target probability 'p'.
        """
        if p <= 0:
            return n, 0, 0
        
        if p >= 1:
            return 0, 0, n
        
        if p <= self.P_MID:
            if self.P_MID > 0:
                ratio = p / self.P_MID
                n_mid = round(n * ratio)
                n_low = n - n_mid
                n_high = 0
            else:
                n_low = n
                n_mid = 0
                n_high = 0
        else:
            if self.P_HIGH > self.P_MID:
                ratio = (p - self.P_MID) / (self.P_HIGH - self.P_MID)
                n_high = round(n * ratio)
                n_mid = n - n_high
                n_low = 0
            else:
                n_high = n
                n_mid = 0
                n_low = 0

        n_low = max(0, n_low)
        n_mid = max(0, n_mid)
        n_high = max(0, n_high)
        
        return int(n_low), int(n_mid), int(n_high)

    def create_timeline(self, target_probability, total_tweets=100):
        """
        Generates a timeline of tweets with a specific stress density.
        """
        n_low, n_mid, n_high = self._calculate_counts(target_probability, total_tweets)
        
        low_samples = random.choices(self.low_tweets, k=n_low) if n_low > 0 else []
        mid_samples = random.choices(self.mid_tweets, k=n_mid) if n_mid > 0 else []
        high_samples = random.choices(self.high_tweets, k=n_high) if n_high > 0 else []

        timeline = []
        timeline.extend([{'text': clean_text_line(t), 'source': 'Low Stress', 'stress': self.P_LOW} for t in low_samples])
        timeline.extend([{'text': clean_text_line(t), 'source': 'Mid Stress', 'stress': self.P_MID} for t in mid_samples])
        timeline.extend([{'text': clean_text_line(t), 'source': 'High Stress', 'stress': self.P_HIGH} for t in high_samples])

        random.shuffle(timeline)

        actual_stress_points = sum(t['stress'] for t in timeline)
        actual_prob = actual_stress_points / len(timeline) if timeline else 0
        
        return timeline, actual_prob

# --- Flask App Routes ---
# CSVファイルの絶対パスを指定
simulator = TwitterSimulator(
    low_stress_file=os.path.join(BASE_DIR, 'wrime-ver1_converted.csv'),
    mid_stress_file=os.path.join(BASE_DIR, 'all_merged.csv'),
    high_stress_file=os.path.join(BASE_DIR, 'output.csv')
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/timeline', methods=['GET'])
def get_timeline():
    try:
        probability_percent = float(request.args.get('probability', '25'))
        target_probability = probability_percent / 100.0
        timeline, actual_prob = simulator.create_timeline(target_probability=target_probability, total_tweets=100)
        
        return jsonify({
            'success': True, 
            'timeline': timeline, 
            'target_probability': target_probability, 
            'actual_probability': actual_prob
        })
    except Exception as e:
        print(f"APIエラー: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/save_survey', methods=['POST'])
def save_survey():
    data = request.get_json()
    try:
        row_data_gsheet = [
            data.get('sessionId'), 
            data.get('userName'),
            data.get('targetProbability'), 
            data.get('actualProbability'), 
            data.get('interval'), 
            data.get('stressLevel'), 
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ]

        # --- 1. CSVファイルへの保存 ---
        filename = os.path.join(BASE_DIR, "survey_results.csv")
        file_exists = os.path.isfile(filename)
        
        with open(filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['session_id', 'user_name', 'target_probability', 'actual_probability', 'survey_interval_min', 'stress_level_vas', 'timestamp'])
            
            writer.writerow(row_data_gsheet)
        
        print(f"アンケート結果をCSVに保存しました: {data}")

        # --- 2. Googleスプレッドシートへの保存 ---
        if sheet:
            try:
                sheet.append_row(row_data_gsheet, value_input_option='USER_ENTERED')
                print(f"アンケート結果をGoogleスプレッドシートに保存しました。")
            except Exception as e:
                print(f"Googleスプレッドシートへの書き込みエラー: {e}")

        return jsonify({'success': True, 'message': 'Result saved.'})
    except Exception as e:
        print(f"アンケート保存エラー: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)