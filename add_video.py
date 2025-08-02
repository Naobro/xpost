import streamlit as st
import pandas as pd
import os
import re
import requests
from requests.auth import HTTPBasicAuth
import tempfile
from config import WP_USER, WP_APP_PASSWORD, WP_API_URL, CSV_FILE

st.title("📹 アフィリエイト広告登録 & WordPress投稿（自動サムネ対応）")

# ✅ WordPressカテゴリ一覧取得
def get_wp_categories():
    url = f"{WP_API_URL}/categories?per_page=100"
    try:
        res = requests.get(url, auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD))
        if res.status_code == 200:
            return {cat["name"]: cat["id"] for cat in res.json()}
    except:
        pass
    return {"未分類": 1}

categories = get_wp_categories()

# ✅ CSV読み込み
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
else:
    df = pd.DataFrame(columns=["title", "category", "tweet_text", "script", "thumbnail_url", "tags"])

# ✅ WordPress メディアアップロード
def upload_media_to_wp_from_url(img_url):
    try:
        img_data = requests.get(img_url).content
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_img:
            tmp_img.write(img_data)
            tmp_img_path = tmp_img.name

        url = f"{WP_API_URL}/media"
        headers = {"Content-Disposition": f'attachment; filename="thumbnail.jpg"', "Content-Type": "image/jpeg"}
        auth = HTTPBasicAuth(WP_USER, WP_APP_PASSWORD)

        with open(tmp_img_path, "rb") as f:
            res = requests.post(url, headers=headers, auth=auth, files={"file": f})

        if res.status_code in [200, 201]:
            return res.json().get("id"), res.json().get("source_url")
        else:
            st.error(f"メディアアップロード失敗: {res.status_code} {res.text}")
            return None, None
    except Exception as e:
        st.error(f"サムネイル取得エラー: {e}")
        return None, None

# ✅ WordPress記事投稿
def create_wp_post(title, content, category_id, featured_image_id=None, tags=[]):
    url = f"{WP_API_URL}/posts"
    auth = HTTPBasicAuth(WP_USER, WP_APP_PASSWORD)

    post_data = {
        "title": title,
        "content": content,
        "status": "publish",
        "categories": [category_id],
    }
    if featured_image_id:
        post_data["featured_media"] = featured_image_id

    if tags:
        post_data["tags"] = tags

    res = requests.post(url, auth=auth, json=post_data)

    if res.status_code in [200, 201]:
        return True
    else:
        st.error(f"記事投稿失敗: {res.status_code} {res.text}")
        return False

# ✅ img= のURLを抽出
def extract_img_url(script_text):
    match = re.search(r'img=([^&]+)', script_text)
    return match.group(1) if match else None

# =======================
# 入力フォーム
# =======================
st.subheader("🎥 新しい広告を追加")
title = st.text_input("タイトル (title)")
category_name = st.selectbox("カテゴリ (category)", options=list(categories.keys()))
tweet_text = st.text_area("ツイート本文 (tweet_text)")
script = st.text_area("広告スクリプトタグ (script)")

default_tags = [
    "無修正", "ハメ撮り", "露出", "美乳", "ギャル",
    "巨乳", "パイパン", "パイズリ", "手コキ",
    "ベスト/オムニバス", "口内発射", "ぶっかけ", "淫語", "美脚", "美尻"
]

selected_tags = st.multiselect("📌 タグを選択（複数可）", default_tags)
custom_tag = st.text_input("✍️ 自由入力タグ（カンマ区切りで複数可）")

# =======================
# 投稿処理
# =======================
if st.button("✅ 投稿する"):
    if title and tweet_text and script:
        img_url = extract_img_url(script)
        all_tags = selected_tags + ([t.strip() for t in custom_tag.split(",")] if custom_tag else [])

        if img_url:
            with st.spinner("📤 サムネイルを取得 & 投稿中..."):
                thumb_id, thumb_url = upload_media_to_wp_from_url(img_url)

                if thumb_id:
                    content = f"<p>{tweet_text}</p>\n\n{script}"
                    category_id = categories.get(category_name, 1)

                    if create_wp_post(title, content, category_id, featured_image_id=thumb_id):
                        st.success("✅ WordPressに投稿しました！")

                        new_row = pd.DataFrame(
                            [[title, category_name, tweet_text, script, thumb_url, ", ".join(all_tags)]],
                            columns=["title", "category", "tweet_text", "script", "thumbnail_url", "tags"]
                        )
                        df = pd.concat([df, new_row], ignore_index=True)
                        df.to_csv(CSV_FILE, index=False)
                        st.success("✅ CSVに追加しました！")

                        st.markdown("[➡ 手動ツイート管理ページへ移動](manual_tweet.py)")
                    else:
                        st.error("❌ WordPress記事投稿に失敗しました")
                else:
                    st.error("❌ サムネイルアップロード失敗")
        else:
            st.error("❌ 広告スクリプトから img= URL が取得できませんでした")
    else:
        st.error("❌ すべての項目を入力してください")

st.subheader("📄 登録済み広告リスト")
st.dataframe(df)