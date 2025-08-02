import pandas as pd
import tweepy
import time
from datetime import datetime
from config import API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET, CSV_FILE

def tweet_video():
    df = pd.read_csv(CSV_FILE)
    if df.empty:
        print("⚠️ CSVが空です。ツイート対象なし。")
        return

    row = df[df["posted"] == False].iloc[0]
    text = f"{row['tweet_text']}\n\n{row.get('tags', '')}\n\n{row['thumbnail_url']}"

    auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

    try:
        api.update_status(status=text)
        print(f"✅ ツイート成功: {row['title']}")

        df.loc[df.index[0], "posted"] = True
        df.to_csv(CSV_FILE, index=False)
        print("✅ CSVを更新しました（posted=True）")
    except Exception as e:
        print(f"❌ ツイート失敗: {e}")

# =========================
# 23時になるまで待機 → ツイート実行
# =========================
while True:
    now = datetime.now().strftime("%H:%M")
    if now == "23:00":
        tweet_video()
        time.sleep(60)  # 1分待って次ループ
    else:
        time.sleep(30)