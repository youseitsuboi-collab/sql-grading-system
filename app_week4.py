
import os
import csv
import io
import zipfile
import tempfile
from pathlib import Path

import streamlit as st

from utils.docx_reader import read_docx
from utils.question_splitter_week4 import split_week4_report
from week4_grader import grade_week4


# ============================================================
# ページ設定
# ============================================================

st.set_page_config(
    page_title="情報システム実験 第4週 採点システム",
    page_icon="📝",
    layout="wide"
)

st.title("情報システム実験 第4週 採点システム")

st.write(
    "第4週のレポート（Wordファイル）をアップロードすると、"
    "課題2（SQL1～SQL8）と課題4（企画クエリ）を一括で採点します。"
    "複数のWordファイルをまとめて採点することもできます。"
)


# ============================================================
# 未記入項目の取得
# ============================================================

def get_missing_fields(parsed_report):
    """
    クエリ設計フォームの未記入項目を取得する。
    """

    missing_fields = {}

    # 課題2
    for sql_name, query in parsed_report.get(
        "assignment2", {}
    ).items():

        missing = query.get("missing_fields", [])

        if missing:
            missing_fields[sql_name] = missing

    # 課題4
    for project_name, project in parsed_report.get(
        "assignment4", {}
    ).items():

        if not project.get("answered", False):
            continue

        design = project.get("design", {})
        missing = design.get("missing_fields", [])

        if missing:
            missing_fields[project_name] = missing

    return missing_fields


# ============================================================
# CSV・TXT生成
# ============================================================

def create_result_files(result, missing_fields):
    """
    採点結果からCSVとTXTを生成する。
    画面表示と一括ZIP出力の両方で利用する。
    """

    csv_buffer = io.StringIO()
    txt_lines = []

    writer = csv.writer(csv_buffer)

    writer.writerow([
        "課題", "設問", "評価項目",
        "回答", "判定", "点数", "理由"
    ])

    txt_lines.append("情報システム実験 第4週 採点結果")
    txt_lines.append("=" * 50)

    # --------------------------------------------------------
    # 未記入項目
    # --------------------------------------------------------

    if missing_fields:

        txt_lines.append(
            "\n【クエリ設計フォームの未記入項目】"
        )

        txt_lines.append(
            "該当する条件がない場合も「なし」と記入してください。"
        )

        for query_name, fields in missing_fields.items():
            txt_lines.append(
                f"{query_name}：{', '.join(fields)}"
            )

    # --------------------------------------------------------
    # 課題2
    # --------------------------------------------------------

    a2 = result["assignment2"]

    txt_lines.append("\n【課題2 SQL1～SQL8】")

    for sql_name, sql_result in a2["queries"].items():

        txt_lines.append(
            f'\n【{sql_name}】'
            f' {sql_result["score"]} / '
            f'{sql_result["max_score"]} 点'
        )

        for item in sql_result.get("items", []):

            name = item.get("item", "")
            answer = item.get("answer", "") or "（未回答）"
            grade = item.get("grade", "×")
            score = item.get("score", 0)
            reason = item.get("reason", "")

            writer.writerow([
                "課題2", sql_name, name,
                answer, grade, score, reason
            ])

            txt_lines.append(
                f'{grade} {name} [{score}点]\n'
                f'  回答：{answer}\n'
                f'  理由：{reason}'
            )

    txt_lines.append(
        f'\n課題2 合計：{a2["total_score"]} / '
        f'{a2["max_score"]} 点'
    )

    # --------------------------------------------------------
    # 課題4
    # --------------------------------------------------------

    a4 = result["assignment4"]

    txt_lines.append("\n【課題4 企画クエリ】")

    for project_name, project in a4["projects"].items():

        project_type = project.get("type", "")

        txt_lines.append(
            f'\n【{project_name} {project_type}】'
            f' {project["total_score"]} / 15 点'
        )

        for key, label in [
            ("validity", "妥当性"),
            ("originality", "オリジナリティ"),
            ("usefulness", "有用性")
        ]:

            data = project.get(key, {})
            score = data.get("score", 0)
            reason = data.get("reason", "")

            writer.writerow([
                "課題4", project_name, label,
                "", "", score, reason
            ])

            txt_lines.append(
                f'{label}：{score} / 5点\n'
                f'  理由：{reason}'
            )

    txt_lines.append(
        f'\n課題4 合計：{a4["total_score"]} / '
        f'{a4["max_score"]} 点'
    )

    # --------------------------------------------------------
    # 総合得点
    # --------------------------------------------------------

    txt_lines.append("\n" + "=" * 50)

    txt_lines.append(
        f'総合得点：{result["total_score"]} / '
        f'{result["max_score"]} 点'
    )

    csv_data = csv_buffer.getvalue().encode("utf-8-sig")
    txt_data = "\n".join(txt_lines)

    return csv_data, txt_data


# ============================================================
# ファイルアップロード
# ============================================================

uploaded_files = st.file_uploader(
    "採点するWordファイルを選択してください（複数選択可能）",
    type=["docx"],
    accept_multiple_files=True
)


# ============================================================
# 一括採点
# ============================================================

if uploaded_files:

    st.success(
        f"{len(uploaded_files)}件のWordファイルを選択しました。"
    )

    if st.button("採点開始", type="primary"):

        results = {}
        missing_by_file = {}
        errors = {}

        progress = st.progress(0)

        status = st.empty()

        for index, uploaded_file in enumerate(uploaded_files):

            temp_path = None
            filename = uploaded_file.name

            status.info(
                f"採点中：{filename} "
                f"({index + 1}/{len(uploaded_files)})"
            )

            try:

                # ------------------------------------------------
                # 一時Wordファイルを作成
                # ------------------------------------------------

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".docx"
                ) as tmp:

                    tmp.write(uploaded_file.getbuffer())
                    temp_path = tmp.name

                # ------------------------------------------------
                # Word読み込み
                # ------------------------------------------------

                text = read_docx(temp_path)

                # ------------------------------------------------
                # 第4週レポート解析
                # ------------------------------------------------

                parsed_report = split_week4_report(text)

                # ------------------------------------------------
                # 課題2＋課題4を一括採点
                # ------------------------------------------------

                result = grade_week4(parsed_report)

                # ------------------------------------------------
                # 未記入項目取得
                # ------------------------------------------------

                missing_fields = get_missing_fields(
                    parsed_report
                )

                # ------------------------------------------------
                # 採点結果を保存
                # ------------------------------------------------

                results[filename] = result
                missing_by_file[filename] = missing_fields

            except Exception as e:

                errors[filename] = str(e)

            finally:

                # 一時ファイル削除
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)

                progress.progress(
                    (index + 1) / len(uploaded_files)
                )

        # --------------------------------------------------------
        # 結果をセッションに保持
        # --------------------------------------------------------

        st.session_state["week4_results"] = results

        st.session_state["week4_missing_by_file"] = (
            missing_by_file
        )

        st.session_state["week4_errors"] = errors

        status.empty()

        if results:
            st.success(
                f"{len(results)}件の採点が完了しました。"
            )

        if errors:
            st.warning(
                f"{len(errors)}件の採点に失敗しました。"
            )

            for filename, error in errors.items():
                st.error(
                    f"{filename}：{error}"
                )


# ============================================================
# 採点結果表示
# ============================================================

if "week4_results" in st.session_state:

    results = st.session_state["week4_results"]

    if results:

        st.divider()

        st.header("採点結果")

        # --------------------------------------------------------
        # 表示対象ファイル選択
        # --------------------------------------------------------

        selected_filename = st.selectbox(
            "表示する採点結果を選択してください",
            options=list(results.keys())
        )

        result = results[selected_filename]

        missing_fields = st.session_state.get(
            "week4_missing_by_file", {}
        ).get(selected_filename, {})

        # --------------------------------------------------------
        # 未記入項目の警告
        # --------------------------------------------------------

        if missing_fields:

            st.warning(
                "クエリ設計フォームに未記入の項目があります。"
                "該当する条件がない場合も「なし」と記入してください。"
            )

            for query_name, fields in missing_fields.items():

                st.write(
                    f"**{query_name}：** "
                    + "、".join(fields)
                )

        # --------------------------------------------------------
        # 総合結果
        # --------------------------------------------------------

        col1, col2, col3 = st.columns(3)

        assignment2 = result["assignment2"]
        assignment4 = result["assignment4"]

        col1.metric(
            "課題2",
            f'{assignment2["total_score"]} / '
            f'{assignment2["max_score"]} 点'
        )

        col2.metric(
            "課題4",
            f'{assignment4["total_score"]} / '
            f'{assignment4["max_score"]} 点'
        )

        col3.metric(
            "合計",
            f'{result["total_score"]} / '
            f'{result["max_score"]} 点'
        )

        st.divider()

        # --------------------------------------------------------
        # 課題2
        # --------------------------------------------------------

        st.header("課題2 SQL1～SQL8")

        for sql_name, sql_result in assignment2["queries"].items():

            score = sql_result.get("score", 0)
            max_score = sql_result.get("max_score", 0)

            with st.expander(
                f"{sql_name}　{score} / {max_score} 点",
                expanded=False
            ):

                for item in sql_result.get("items", []):

                    grade = item.get("grade", "×")
                    item_name = item.get("item", "")
                    item_score = item.get("score", 0)
                    answer = item.get("answer", "")
                    reason = item.get("reason", "")

                    if not str(answer).strip():
                        answer = "（未回答）"

                    st.markdown(
                        f"### {grade} {item_name}　[{item_score}点]"
                    )

                    st.write(f"**回答：** {answer}")
                    st.write(f"**理由：** {reason}")

        st.subheader(
            f'課題2 合計：{assignment2["total_score"]} / '
            f'{assignment2["max_score"]} 点'
        )

        st.divider()

        # --------------------------------------------------------
        # 課題4
        # --------------------------------------------------------

        st.header("課題4 企画クエリ")

        for project_name, project_result in (
            assignment4["projects"].items()
        ):

            query_type = project_result.get("type", "")
            total = project_result.get("total_score", 0)

            title = project_name

            if query_type:
                title += f" {query_type}"

            with st.expander(
                f"{title}　{total} / 15 点",
                expanded=False
            ):

                for key, label in [
                    ("validity", "妥当性"),
                    ("originality", "オリジナリティ"),
                    ("usefulness", "有用性")
                ]:

                    data = project_result.get(key, {})

                    score = data.get("score", 0)
                    reason = data.get("reason", "")

                    st.markdown(
                        f"### {label}：{score} / 5点"
                    )

                    st.write(f"**理由：** {reason}")

        st.subheader(
            f'課題4 合計：{assignment4["total_score"]} / '
            f'{assignment4["max_score"]} 点'
        )

        st.divider()

        st.header(
            f'総合得点：{result["total_score"]} / '
            f'{result["max_score"]} 点'
        )

        # --------------------------------------------------------
        # 個別CSV・TXTダウンロード
        # --------------------------------------------------------

        csv_data, txt_data = create_result_files(
            result,
            missing_fields
        )

        base_name = Path(selected_filename).stem

        st.divider()

        st.subheader("選択中のファイルの採点結果")

        col_csv, col_txt = st.columns(2)

        with col_csv:

            st.download_button(
                "CSVをダウンロード",
                data=csv_data,
                file_name=f"{base_name}_result.csv",
                mime="text/csv",
                key="download_csv"
            )

        with col_txt:

            st.download_button(
                "TXTをダウンロード",
                data=txt_data.encode("utf-8-sig"),
                file_name=f"{base_name}_result.txt",
                mime="text/plain",
                key="download_txt"
            )

        # --------------------------------------------------------
        # ZIP一括ダウンロード
        # --------------------------------------------------------

        st.divider()

        st.subheader("全件の採点結果を一括ダウンロード")

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(
            zip_buffer,
            mode="w",
            compression=zipfile.ZIP_DEFLATED
        ) as zip_file:

            for filename, file_result in results.items():

                file_missing = st.session_state.get(
                    "week4_missing_by_file", {}
                ).get(filename, {})

                _, file_txt = create_result_files(
                    file_result,
                    file_missing
                )

                output_name = (
                    f"{Path(filename).stem}_result.txt"
                )

                zip_file.writestr(
                    output_name,
                    file_txt.encode("utf-8-sig")
                )

        st.download_button(
            "全件の採点結果をZIPでダウンロード",
            data=zip_buffer.getvalue(),
            file_name="week4_grading_results.zip",
            mime="application/zip",
            type="primary",
            key="download_zip"
        )
