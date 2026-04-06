import streamlit as st
import os
import pandas as pd
import ast

# --- 定数・初期設定 ---
CSV_FILE = 'quiz_data.csv'
IMAGE_DIR = 'images'
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

def load_data():
    """CSVからデータを読み込み、リスト形式に変換する"""
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            data = df.to_dict('records')
            for item in data:
                # optionsが文字列( "[...]" )で保存されている場合にリストへ復元
                if isinstance(item.get('options'), str):
                    item['options'] = ast.literal_eval(item['options'])
                # 必須キーの欠損対策
                if 'is_active' not in item: item['is_active'] = True
                if 'image' not in item: item['image'] = None
            return data
        except Exception as e:
            st.error(f"データ読み込みエラー: {e}")
            return []
    return []

def save_data(data):
    """データをCSVに保存する"""
    df = pd.DataFrame(data)
    df.to_csv(CSV_FILE, index=False)

def get_image_list():
    """画像フォルダ内のファイル名を取得"""
    valid_exts = ('.png', '.jpg', '.jpeg', '.webp', '.gif')
    files = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(valid_exts)]
    return ["なし"] + sorted(files)

# セッション状態の初期化
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = load_data()

# --- サイドバー ---
st.sidebar.title("メニュー")

# 💡 ラジオボタンで縦に並べる（セレクトボックスは使いません）
menu = st.sidebar.radio(
    label="画面を切り替え",
    options=["クイズに挑戦", "問題の管理"],
    index=0,
    key="sidebar_nav"
)

st.sidebar.divider() # 区切り線

# ==========================================
# 1. 【クイズに挑戦】タブ
# ==========================================
if menu == "クイズに挑戦":
    
    quiz_pool = [item for item in st.session_state.quiz_data if item.get('is_active', False)]
    
    if not quiz_pool:
        st.warning("⚠️ 出題対象の問題がありません。管理画面で「➕ 出題」を押してください。")
        st.stop()

    if 'q_idx' not in st.session_state: st.session_state.q_idx = 0
    if 'score_dict' not in st.session_state: st.session_state.score_dict = {}
    if 'finished' not in st.session_state: st.session_state.finished = False

    if st.session_state.finished:
        st.header("🏁 クイズ終了")
        correct_count = sum(1 for val in st.session_state.score_dict.values() if val == True)
        st.metric(label="正解数", value=f"{correct_count} / {len(quiz_pool)}")
        if st.button("🔄 最初から解き直す", use_container_width=True):
            st.session_state.q_idx = 0
            st.session_state.score_dict = {}
            st.session_state.finished = False
            st.rerun()
    else:
        idx = st.session_state.q_idx
        item = quiz_pool[idx]
        
        st.progress((idx + 1) / len(quiz_pool))
        st.write(f"### 第 {idx + 1} 問 / 全 {len(quiz_pool)} 問")
        st.write(f"## {item['question']}")
        
        st.divider()
        col_ans, col_img = st.columns([1, 1])
        
        with col_ans:
            for i, opt in enumerate(item['options']):
                if st.button(opt, key=f"q_ans_{idx}_{i}", use_container_width=True):
                    if i == item['answer']:
                        st.toast("正解！✨")
                        st.session_state.score_dict[idx] = True
                    else:
                        st.toast(f"不正解... 正解は「{item['options'][item['answer']]}」")
                        st.session_state.score_dict[idx] = False

        with col_img:
            # 💡 画像データの取得
            img_name = item.get('image')
            
            # 画像が設定されている場合のみ処理
            if img_name and img_name != "なし":
                # フルパスを作成
                img_path = os.path.join(IMAGE_DIR, str(img_name))
                
                if os.path.exists(img_path):
                    # ✅ width でサイズを指定（ピクセル単位）
                    # 💡 数字を変えるだけで大きさが変わります
                    st.image(
                        img_path, 
                        width=300 
                    )
                else:
                    # ⚠️ 画像が見つからない場合のみ警告
                    st.error("🖼️ 画像が見つかりません")
                    with st.expander("詳細なパスを確認"):
                        st.code(f"ファイル名: {img_name}\n場所: {os.path.abspath(img_path)}")
            else:
                st.write(" ")

        st.divider()
        c1, c2, c3 = st.columns(3)
        if c1.button("⬅️ 前へ", use_container_width=True) and idx > 0:
            st.session_state.q_idx -= 1
            st.rerun()
        
        is_last = (idx == len(quiz_pool) - 1)
        btn_label = "結果を見る 🏁" if is_last else "次へ ➡️"
        if c3.button(btn_label, use_container_width=True):
            if is_last: st.session_state.finished = True
            else: st.session_state.q_idx += 1
            st.rerun()

# ==========================================
# 2. 【問題の管理】タブ
# ==========================================
else:
    st.title("⚙️ 問題の編集・カテゴリ管理")
    current_data = st.session_state.quiz_data
    all_cats = sorted(list(set([item.get('category', '未分類') for item in current_data]))) or ["未分類"]
    img_list = get_image_list()

    # --- 2.1 新規追加セクション ---
    with st.expander("➕ 新しい問題を追加する", expanded=False):
        new_q = st.text_input("問題文", key="add_q")
        
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            s_cat = st.selectbox("既存カテゴリ", all_cats, key="add_s_cat")
        with c2:
            n_cat = st.text_input("新規カテゴリ名", key="add_n_cat")
        with c3:
            # 🖼️ パソコンから画像を選択
            uploaded_file = st.file_uploader("画像をアップロード", type=['png', 'jpg', 'jpeg'], key="add_img_up")
        
        # プレビュー表示
        final_img_name = None
        if uploaded_file is not None:
            st.image(uploaded_file, width=150, caption="プレビュー")
            final_img_name = uploaded_file.name

        st.write("---")
        
        # 選択肢の入力（2列レイアウト）
        opts = []
        opt_c1, opt_c2 = st.columns(2)
        for i in range(4):
            with opt_c1 if i % 2 == 0 else opt_c2:
                opts.append(st.text_input(f"選択肢 {i+1}", key=f"add_o_{i}"))
        
        ans = st.selectbox("正解", [0,1,2,3], format_func=lambda x: f"選択肢 {x+1}", key="add_ans")
        
        f_cat = n_cat if n_cat else s_cat

        if st.button("🚀 この問題を追加保存", use_container_width=True):
            if new_q and all(opts):
                # 💡 画像の保存処理
                if uploaded_file is not None:
                    img_path = os.path.join(IMAGE_DIR, uploaded_file.name)
                    # 実際に images フォルダにファイルを書き込む
                    with open(img_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                
                # データ登録
                new_item = {
                    "question": new_q, 
                    "options": opts, 
                    "answer": ans, 
                    "category": f_cat, 
                    "image": final_img_name, 
                    "is_active": True
                }
                current_data.append(new_item)
                save_data(current_data)
                st.success(f"問題を保存しました！{'（画像も保存完了）' if final_img_name else ''}")
                st.rerun()
            else:
                st.error("問題文と全ての選択肢を入力してください。")

    st.divider()

# --- 2.2 並び替えセクション ---
    st.subheader("↕️ 出題順の整理")
    
    if st.button("🗑️ 全ての出題を解除", use_container_width=True):
        for item in current_data: 
            item['is_active'] = False
        save_data(current_data)
        st.rerun()

    # 出題中(is_active=True)のものだけをリスト化
    active_items = []
    for i, item in enumerate(current_data):
        if item.get('is_active', False):
            # ラベルを長めにしたり、改行的な要素を含ませることで縦並びを促す
            label = f"{i}: [{item.get('category', '未分類')}] {item.get('question','')[:40]}"
            active_items.append(label)

    if active_items:
        from streamlit_sortables import sort_items
        
        # direction="vertical" を指定して縦並びを強制
        # justify="stretch" (ライブラリのバージョンによる) または単純な垂直配置を利用
        sorted_res = sort_items(
            active_items, 
            direction="vertical", 
            key=f"sort_v11_{len(active_items)}"
        )
        
        st.write(" ") # 余白
        if st.button("🔃 この順番で出題順を確定", use_container_width=True):
            try:
                new_active_data = []
                for t in sorted_res:
                    original_idx = int(t.split(":")[0])
                    new_active_data.append(current_data[original_idx])
                
                inactive_data = [item for item in current_data if not item.get('is_active', False)]
                final_combined_data = new_active_data + inactive_data
                st.session_state.quiz_data = final_combined_data
                save_data(final_combined_data)
                
                st.success("出題順を更新しました！")
                st.rerun()
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
    else:
        st.info("💡 現在「出題」に設定されている問題はありません。")

    st.divider()

    # --- 2.3 詳細編集セクション ---
    st.subheader("📝 出題の選択 ＆ 内容編集")
    f_cat_edit = st.selectbox("カテゴリ絞り込み", ["すべて"] + all_cats, key="f_v9")
    
    # 表示用リストの固定
    display_list = [(i, item) for i, item in enumerate(current_data) 
                    if f_cat_edit == "すべて" or item.get('category') == f_cat_edit]

    for o_idx, item in display_list:
        is_active = item.get('is_active', False)
        c_btn, c_exp = st.columns([0.2, 0.8])
        
        with c_btn:
            lbl = "➖ 除外" if is_active else "➕ 出題"
            if st.button(lbl, key=f"tgl_{o_idx}", use_container_width=True):
                item['is_active'] = not is_active
                obj = current_data.pop(o_idx)
                if item['is_active']:
                    pos = sum(1 for x in current_data if x.get('is_active', True))
                    current_data.insert(pos, obj)
                else:
                    current_data.append(obj)
                save_data(current_data); st.rerun()

        with c_exp:
            status = "✅" if is_active else "💤"
            with st.expander(f"{status} [{item.get('category')}] {item['question'][:40]}..."):
                e_q = st.text_area("問題文", item['question'], key=f"eq_{o_idx}")
                
                ec1, ec2 = st.columns(2)
                with ec1:
                    e_c = st.text_input("カテゴリ", item['category'], key=f"ec_{o_idx}")
                with ec2:
                    # 🖼️ パソコンから新しい画像をアップロード
                    new_upload = st.file_uploader("画像をアップロードして変更", type=['png', 'jpg', 'jpeg'], key=f"up_img_{o_idx}")
                
                # --- 画像プレビューとファイル名決定ロジック ---
                e_img_final = item.get('image') # デフォルトは現在の画像
                
                st.write("🖼️ 現在の画像プレビュー")
                p1, p2 = st.columns([0.3, 0.7])
                with p1:
                    if new_upload is not None:
                        # 新しくアップロードされた場合
                        st.image(new_upload, width=150, caption="新しく選択中")
                        e_img_final = new_upload.name
                    elif e_img_final and e_img_final != "なし":
                        # 既存の画像がある場合
                        img_path = os.path.join(IMAGE_DIR, e_img_final)
                        if os.path.exists(img_path):
                            st.image(img_path, width=150)
                        else:
                            st.warning("画像ファイルが見つかりません")
                    else:
                        st.caption("画像なし")
                
                # 削除チェックボックス（画像を「なし」にしたい場合用）
                if e_img_final and e_img_final != "なし":
                    if st.checkbox("画像を削除する", key=f"del_img_chk_{o_idx}"):
                        e_img_final = None

                st.write("---")

                # 選択肢の編集
                e_opts = []
                cols = st.columns(2)
                for j in range(4):
                    with cols[j%2]:
                        e_opts.append(st.text_input(f"選 {j+1}", item['options'][j], key=f"eo_{o_idx}_{j}"))
                
                e_ans = st.selectbox("正解", [0,1,2,3], index=int(item['answer']), key=f"ea_{o_idx}")

                b1, b2 = st.columns(2)
                if b1.button("🆙 更新", key=f"up_{o_idx}", use_container_width=True):
                    # 画像がアップロードされていれば保存
                    if new_upload is not None:
                        img_path = os.path.join(IMAGE_DIR, new_upload.name)
                        with open(img_path, "wb") as f:
                            f.write(new_upload.getbuffer())
                    
                    # データの更新
                    current_data[o_idx].update({
                        "question": e_q, 
                        "category": e_c, 
                        "options": e_opts, 
                        "answer": e_ans, 
                        "image": e_img_final
                    })
                    save_data(current_data)
                    st.success("変更を保存しました！")
                    st.rerun()

                if b2.button("🗑️ 削除", key=f"dl_{o_idx}", use_container_width=True):
                    current_data.pop(o_idx)
                    save_data(current_data)
                    st.rerun()