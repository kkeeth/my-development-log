#!/usr/bin/env python3
"""配信管理スプレッドシートを読み書きするクライアント（標準ライブラリのみ）.

Google Sheets API は使わない. スプレッドシートにバインド済みの Apps Script
ウェブアプリ (scripts/gas/Code.gs) に JSON を POST する.

【なぜ Apps Script なのか】
Sheets API を直接叩く場合, gcloud の ADC は内蔵の共有 OAuth クライアントを使うため
spreadsheets のような機微スコープを要求できず「このアプリはブロックされます」で弾かれる.
サービスアカウント方式なら通るが GCP プロジェクトが要る. Apps Script なら
スプレッドシートの所有者権限でそのまま動くので, GCP も OAuth も不要になる.
またデスクトップアプリの定期タスクが既に同じウェブアプリを使っているため, 窓口を 1 つに保てる.

【必要な環境変数】
  PODCAST_SHEET_WEBAPP_URL  Apps Script のデプロイ URL (.../exec で終わるもの)
  PODCAST_SHEET_TOKEN       スクリプトプロパティ API_TOKEN と同じ値
  PODCAST_SHEET_TAB         既定のタブ名 (--tab で上書き可)

列はすべて「ヘッダ名」で指定する. 列の位置は増減し得るため, 位置指定で書くと
列が 1 つ増えた瞬間に別の列を壊す.

使い方:
  sheets.py tabs
  sheets.py header
  sheets.py rows [--max N]
  sheets.py find --key-col タイトル --key "..."
  sheets.py append --fields '{"タイトル":"...","ステータス":"未配信"}'
  sheets.py update --key-col タイトル --key "..." --fields '{"ステータス":"配信済み"}'

  # デスクトップアプリの定期タスクと同じ経路（トークン不要・列名固定）
  sheets.py update-episode --title "..." [--status 配信済み] [--date 2026-08-15]
  sheets.py update-stock   --title "..." --usage 使用
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def post(url: str, payload: dict) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=90) as res:
            body = res.read().decode()
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:800]
        hint = ""
        if e.code in (401, 403):
            hint = ("\nヒント: デプロイの「アクセスできるユーザー」が『全員』に"
                    "なっているか確認してください．")
        elif e.code == 404:
            hint = "\nヒント: デプロイ URL が誤っている可能性があります（/exec で終わるもの）．"
        sys.exit(f"HTTP {e.code}: {detail}{hint}")
    except urllib.error.URLError as e:
        sys.exit(
            f"接続に失敗しました: {e.reason}\n"
            "ヒント: サンドボックスが script.google.com / script.googleusercontent.com を"
            "遮断している可能性があります．settings.local.json で許可してください．"
        )

    try:
        out = json.loads(body)
    except ValueError:
        sys.exit(
            "JSON でない応答が返りました．デプロイ設定（アクセスできるユーザー＝全員，"
            "実行するユーザー＝自分）を確認してください．\n"
            f"先頭 300 文字: {body[:300]}"
        )

    if not out.get("success"):
        err = out.get("error", "")
        hint = ""
        if "Unknown action" in str(err):
            hint = ("\nヒント: Apps Script が古い可能性があります．Code.gs を貼り直して"
                    "**再デプロイ**（デプロイを管理 → 編集 → 新バージョン）してください．")
        sys.exit(f"Apps Script エラー: {err}{hint}")

    # 追加アクションは result に包む．既存の update_episode / update_stock は包まない
    return out.get("result", out)


def parse_json_arg(raw: str, name: str) -> dict:
    try:
        val = json.loads(raw)
    except ValueError as e:
        sys.exit(f"{name} が JSON として読めません: {e}")
    if not isinstance(val, dict):
        sys.exit(f"{name} は JSON オブジェクト（連想配列）で指定してください")
    return val


def main() -> None:
    # 共通オプションはサブコマンドの後ろに書けるよう parents で配る．
    # 親パーサだけに置くと `rows --tab X` が通らず `--tab X rows` しか受け付けなくなる．
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--url", default=os.environ.get("PODCAST_SHEET_WEBAPP_URL"))
    common.add_argument("--token", default=os.environ.get("PODCAST_SHEET_TOKEN"))
    common.add_argument("--tab", default=os.environ.get("PODCAST_SHEET_TAB"))

    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("tabs", parents=[common])
    sub.add_parser("header", parents=[common])

    p_rows = sub.add_parser("rows", parents=[common])
    p_rows.add_argument("--max", type=int, default=200)

    p_find = sub.add_parser("find", parents=[common])
    p_find.add_argument("--key-col", required=True, help="ヘッダ名 (例: タイトル)")
    p_find.add_argument("--key", required=True)

    p_app = sub.add_parser("append", parents=[common])
    p_app.add_argument("--fields", required=True, help='JSON オブジェクト {"ヘッダ名": 値}')

    p_upd = sub.add_parser("update", parents=[common])
    p_upd.add_argument("--key-col", required=True, help="ヘッダ名 (例: タイトル)")
    p_upd.add_argument("--key", required=True)
    p_upd.add_argument("--fields", required=True, help='JSON オブジェクト {"ヘッダ名": 値}')

    p_ep = sub.add_parser("update-episode", parents=[common])
    p_ep.add_argument("--title", required=True)
    p_ep.add_argument("--status")
    p_ep.add_argument("--date", help="配信日 (例: 2026-08-15)")

    p_st = sub.add_parser("update-stock", parents=[common])
    p_st.add_argument("--title", required=True, help="タイトル案の値")
    p_st.add_argument("--usage", required=True, help="使用 / ボツ")

    a = p.parse_args()
    if not a.url:
        sys.exit("ウェブアプリ URL が未指定です (PODCAST_SHEET_WEBAPP_URL か --url)")

    # 既存アクションはトークン不要（デスクトップアプリとの後方互換）
    legacy = a.cmd in ("update-episode", "update-stock")
    if not legacy and not a.token:
        sys.exit("トークンが未指定です (PODCAST_SHEET_TOKEN か --token)")

    payload: dict = {"token": a.token}

    if a.cmd == "update-episode":
        payload.update({"action": "update_episode", "title": a.title})
        if a.status:
            payload["status"] = a.status
        if a.date:
            payload["publishedDate"] = a.date
    elif a.cmd == "update-stock":
        payload.update({"action": "update_stock", "title": a.title, "usage": a.usage})
    else:
        payload["action"] = {"append": "append_row", "update": "update_row"}.get(a.cmd, a.cmd)
        if a.cmd != "tabs":
            if not a.tab:
                sys.exit("タブ名が未指定です (PODCAST_SHEET_TAB か --tab)．"
                         "`tabs` で一覧を確認してください")
            payload["tab"] = a.tab
        if a.cmd == "rows":
            payload["max"] = a.max
        elif a.cmd == "find":
            payload.update({"keyCol": a.key_col, "key": a.key})
        elif a.cmd == "append":
            payload["fields"] = parse_json_arg(a.fields, "--fields")
        elif a.cmd == "update":
            payload.update({"keyCol": a.key_col, "key": a.key,
                            "fields": parse_json_arg(a.fields, "--fields")})

    print(json.dumps(post(a.url, payload), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
