import streamlit as st
import pandas as pd
import os
import requests
from requests.auth import HTTPBasicAuth
from PIL import Image
from io import BytesIO
import tempfile
from config import WP_USER, WP_APP_PASSWORD, WP_API_URL, CSV_FILE

st.title("📹 アフィリエイト広告登録 & WordPress投稿（動画アップなし）")

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
    df = pd.DataFrame(columns=["title", "category", "tweet_text", "script", "thumbnail_url"])

# ✅ WordPress メディアアップロード関数
def upload_media_to_wp(file_path, file_name, mime_type):
    url = f"{WP_API_URL}/media"
    headers = {
        "Content-Disposition": f'attachment; filename="{file_name}"',
        "Content-Type": mime_type
    }
    auth = HTTPBasicAuth(WP_USER, WP_APP_PASSWORD)

    with open(file_path, "rb") as f:
        res = requests.post(url, headers=headers, auth=auth, files={"file": f})

    if res.status_code in [200, 201]:
        return res.json().get("id"), res.json().get("source_url")
    else:
        st.error(f"メディアアップロード失敗: {res.status_code} {res.text}")
        return None, None

# ✅ WordPress 投稿作成関数
def create_wp_post(title, content, category_id, featured_image_id=None):
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

    res = requests.post(url, auth=auth, json=post_data)

    if res.status_code in [200, 201]:
        return True
    else:
        st.error(f"記事投稿失敗: {res.status_code} {res.text}")
        return False

# ✅ スクリプトタグから img=URL を抽出
def extract_img_url(script_text):
    import re
    match = re.search(r"img=(https?://[^\s&\"]+)", script_text)
    return match.group(1) if match else None

# ✅ 外部URLからJPEG化してアップロード
def download_and_convert_to_jpeg(image_url):
    try:
        res = requests.get(image_url, timeout=10)
        res.raise_for_status()
        img = Image.open(BytesIO(res.content)).convert("RGB")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            img.save(tmp.name, format="JPEG")
            return tmp.name
    except Exception as e:
        st.error(f"画像取得失敗: {e}")
        return None

# ✅ 入力フォーム
st.subheader("🎥 新しい広告を追加")
title = st.text_input("タイトル (title)")
category_name = st.selectbox("カテゴリ (category)", options=list(categories.keys()))
tweet_text = st.text_area("ツイート本文 (tweet_text)")
script = st.text_area("広告スクリプトタグ (script)")

# ✅ ボタン押下時
if st.button("✅ 投稿する（動画なし）"):
    if title and tweet_text and script:
        with st.spinner("📤 サムネイルを取得してアップロード中..."):
            img_url = extract_img_url(script)

            if img_url:
                jpeg_path = download_and_convert_to_jpeg(img_url)
                if jpeg_path:
                    thumb_id, thumb_url = upload_media_to_wp(jpeg_path, "thumbnail.jpg", "image/jpeg")
                else:
                    thumb_id, thumb_url = None, None
            else:
                st.error("❌ スクリプトから画像URLを取得できませんでした")
                thumb_id, thumb_url = None, None

            # ✅ WordPress記事作成
            content = f"{script}\n\n<p>サンプル動画👇</p>"
            category_id = categories.get(category_name, 1)

            if create_wp_post(title, content, category_id, featured_image_id=thumb_id):
                st.success("✅ WordPressに投稿しました！")

                new_row = pd.DataFrame(
                    [[title, category_name, tweet_text, script, thumb_url if thumb_url else ""]],
                    columns=["title", "category", "tweet_text", "script", "thumbnail_url"]
                )
                df = pd.concat([df, new_row], ignore_index=True)
                df.to_csv(CSV_FILE, index=False)
                st.success("✅ CSVに追加しました！")
            else:
                st.error("❌ WordPress記事投稿に失敗しました")
    else:
        st.error("❌ すべての項目を入力してください")

st.subheader("📄 登録済み広告リスト")
st.dataframe(df)