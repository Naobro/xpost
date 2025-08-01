import streamlit as st
import pandas as pd
import os
import requests
from requests.auth import HTTPBasicAuth
from config import WP_USER, WP_APP_PASSWORD, WP_API_URL, CSV_FILE

st.title("📹 アフィリエイト動画登録 & WordPress投稿")

# ✅ WordPressカテゴリ一覧取得
def get_wp_categories():
    url = f"{WP_API_URL}/categories?per_page=100"
    try:
        res = requests.get(url, auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD))
        if res.status_code == 200:
            categories = res.json()
            return {cat["name"]: cat["id"] for cat in categories}
    except:
        pass
    return {"未分類": 1}

categories = get_wp_categories()

# ✅ CSV読み込み
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
else:
    df = pd.DataFrame(columns=["title", "category", "tweet_text", "script", "video_url"])

# 入力フォーム
st.subheader("🎥 新しい動画を追加")
title = st.text_input("タイトル (title)")
category_name = st.selectbox("カテゴリ (category)", options=list(categories.keys()))
tweet_text = st.text_area("ツイート本文 (tweet_text)")
script = st.text_area("DTIスクリプトタグ (script)")
video_file = st.file_uploader("サンプル動画 (mp4のみ)", type=["mp4"])

# ✅ 動画アップロード
def upload_video_to_wp(video_file):
    url = f"{WP_API_URL}/media"
    headers = {
        "Content-Disposition": f'attachment; filename="{video_file.name}"',
        "Content-Type": "video/mp4"  # ← これを追加！
    }
    auth = HTTPBasicAuth(WP_USER, WP_APP_PASSWORD)
    res = requests.post(url, headers=headers, auth=auth, files={"file": video_file.getbuffer()})
    
    st.write("📡 アップロード結果:", res.status_code, res.text)  # ← デバッグ用に追加

    if res.status_code in [200, 201]:
        return res.json().get("source_url")
    return None

# ✅ 記事投稿
def create_wp_post(title, content, category_id):
    url = f"{WP_API_URL}/posts"
    auth = HTTPBasicAuth(WP_USER, WP_APP_PASSWORD)
    post = {"title": title, "content": content, "status": "publish", "categories": [category_id]}
    res = requests.post(url, auth=auth, json=post)
    
    st.write("📡 投稿結果:", res.status_code, res.text)  # ← デバッグ用に追加

    return res.status_code in [200, 201]

# ✅ ボタン押下時
if st.button("✅ 動画をアップロード & 投稿"):
    if title and tweet_text and script and video_file:
        with st.spinner("📤 動画アップロード中..."):
            video_url = upload_video_to_wp(video_file)

        if video_url:
            content = f"{script}\n\n<p>サンプル動画👇</p>\n<video src='{video_url}' controls width='480'></video>"
            category_id = categories.get(category_name, 1)

            if create_wp_post(title, content, category_id):
                st.success("✅ WordPressに投稿しました！")

                new_row = pd.DataFrame([[title, category_name, tweet_text, script, video_url]],
                                       columns=["title", "category", "tweet_text", "script", "video_url"])
                df = pd.concat([df, new_row], ignore_index=True)
                df.to_csv(CSV_FILE, index=False)
                st.success("✅ CSVに追加しました！")
            else:
                st.error("❌ WordPress記事投稿に失敗しました")
        else:
            st.error("❌ 動画アップロード失敗")
    else:
        st.error("❌ すべての項目を入力してください")

st.subheader("📄 登録済み動画リスト")
st.dataframe(df)