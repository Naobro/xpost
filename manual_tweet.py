import streamlit as st
import pandas as pd
import os
import tweepy
from config import API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET

CSV_FILE = "affiliate_videos.csv"

st.title("🐦 手動ツイート管理ツール")

# ✅ CSVを読み込む
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
else:
    st.error("CSVファイルが見つかりません。まず add_video.py で登録してください。")
    st.stop()

if "posted" not in df.columns:
    df["posted"] = False

# ✅ 未投稿と投稿済みを分けて表示
tab1, tab2 = st.tabs(["未投稿リスト", "投稿済みリスト"])
with tab1:
    st.subheader("⏳ 未投稿リスト")
    st.dataframe(df[df["posted"] == False])

with tab2:
    st.subheader("✅ 投稿済みリスト")
    st.dataframe(df[df["posted"] == True])

# ✅ ツイート対象の選択
video_titles = df[df["posted"] == False]["title"].tolist()
if video_titles:
    selected_title = st.selectbox("ツイートする動画を選択", video_titles)
    tweet_button = st.button("🐦 ツイートする")
else:
    st.info("未投稿の動画がありません。")
    selected_title = None
    tweet_button = False

# ✅ Twitter API 認証
def get_twitter_api():
    auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    return tweepy.API(auth)

# ✅ ツイート送信
def post_tweet(api, text, video_url):
    try:
        tweet_text = f"{text}\n\n動画はこちら👇\n{video_url}"
        api.update_status(tweet_text)
        return True
    except Exception as e:
        st.error(f"❌ ツイート失敗: {e}")
        return False

# ✅ ボタンが押されたらツイート
if tweet_button and selected_title:
    api = get_twitter_api()
    row = df[df["title"] == selected_title].iloc[0]
    success = post_tweet(api, row["tweet_text"], row["video_url"])

    if success:
        st.success(f"✅ ツイートしました: {selected_title}")
        df.loc[df["title"] == selected_title, "posted"] = True
        df.to_csv(CSV_FILE, index=False)
        st.experimental_rerun()