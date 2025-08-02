import streamlit as st
import pandas as pd
import os
import requests
from requests.auth import HTTPBasicAuth
from moviepy.editor import VideoFileClip
import tempfile
from config import WP_USER, WP_APP_PASSWORD, WP_API_URL, CSV_FILE

st.title("📹 アフィリエイト動画登録 & WordPress投稿")

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
    df = pd.DataFrame(columns=["title", "category", "tweet_text", "script", "video_url"])

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

# ✅ サムネイル生成
def generate_thumbnail(video_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
        tmp_video.write(video_file.read())
        tmp_video_path = tmp_video.name

    clip = VideoFileClip(tmp_video_path)
    frame_time = min(3, clip.duration / 2)
    frame = clip.get_frame(frame_time)

    thumb_path = tmp_video_path.replace(".mp4", ".jpg")
    from PIL import Image
    img = Image.fromarray(frame)
    img.save(thumb_path)

    clip.close()
    return thumb_path

# ✅ 入力フォーム
st.subheader("🎥 新しい動画を追加")
title = st.text_input("タイトル (title)")
category_name = st.selectbox("カテゴリ (category)", options=list(categories.keys()))
tweet_text = st.text_area("ツイート本文 (tweet_text)")
script = st.text_area("DTIスクリプトタグ (script)")
video_file = st.file_uploader("サンプル動画 (mp4のみ)", type=["mp4"])

# ✅ ボタン押下時
if st.button("✅ 動画をアップロード & 投稿"):
    if title and tweet_text and script and video_file:
        with st.spinner("📤 動画とサムネイルをアップロード中..."):
            # 🎬 一時ファイルに保存
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(video_file.read())
                video_path = tmp.name

            # ✅ 動画アップロード
            video_id, video_url = upload_media_to_wp(video_path, video_file.name, "video/mp4")

            if video_url:
                # ✅ サムネイル生成 & アップロード
                thumb_path = generate_thumbnail(open(video_path, "rb"))
                thumb_id, thumb_url = upload_media_to_wp(thumb_path, "thumbnail.jpg", "image/jpeg")

                # ✅ WordPress記事作成
                content = f"{script}\n\n<p>サンプル動画👇</p>\n<video src='{video_url}' controls width='480'></video>"
                category_id = categories.get(category_name, 1)

                if create_wp_post(title, content, category_id, featured_image_id=thumb_id):
                    st.success("✅ WordPressに投稿しました！")

                    # ✅ CSV更新
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