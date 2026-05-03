# Logging Guide (for Maintainers)

このドキュメントは、Storage / Worker / Mock Salesforce のログを  
**保守者が効率よく読み解き、原因を特定するためのガイド**です。

本プロジェクトのログはすべて JSON 形式で統一され、  
`request_id` によって LWC → Apex → Storage → Worker → Mock → CDC の全処理が紐づきます。

---

# 📁 ログ出力先

```text
project_root/logs/
 ├── storage.log
 ├── worker.log
 └── salesforce_mock.log
```

---

# 📘 ログの基本構造（ordered_log）

すべてのログは以下の順序で出力されます：

```json
{
  "request_id": "abc-123",
  "timestamp": "2026-05-02T07:22:48",
  "function": "execute_download_job",
  "method": null,
  "url": null,
  "path": null,
  "parameters": {},
  "status_code": null,
  "elapsed_ms": 119,
  "return_value": null,
  "event": "end"
}
```

## 重要フィールド

| フィールド | 説明 |
|-----------|------|
| **request_id** | Apex が生成し、全処理に伝播する一意の ID |
| **function** | trace_action により記録される関数名 |
| **parameters** | start ログでの入力値 |
| **elapsed_ms** | end ログでの処理時間 |
| **event** | `"start"` or `"end"` |

---

# 🔍 最初に見るべきは request_id

1 回のダウンロード要求は **すべて同じ request_id** を持つため、  
まずはこれでログを絞り込むのが最速です。

```bash
grep "abc-123" logs/*.log
```

これだけで、  
**Storage → Worker → Mock Salesforce → CDC**  
すべての処理が一気に追えます。

---

# 🔄 処理の流れをログで追う方法

## ① Storage（/download-request）

```
event=start  function=download_request
event=end    function=download_request  status=accepted
```

→ queue にジョブが作成されたことを確認。

---

## ② Worker（execute_download_job）

```
event=start  function=execute_download_job
event=end    function=execute_download_job  elapsed_ms=xxx
```

Worker 内部の詳細ログ：

- decrypt_filepath  
- split_into_chunks  
- post_content_version  
- patch_version_data  
- post_content_document_link  
- update_download_master  

---

## ③ Mock Salesforce（ContentVersion）

```
POST /sobjects/ContentVersion  status_code=200
```

→ chunk アップロード成功。

---

## ④ Storage（/upload-complete）

```
event=start function=upload_complete
event=end   function=upload_complete status=completed
```

→ DownloadMaster__c が「ダウンロード可」に更新された。

---

# ⚠️ エラーの見方

## Worker 側のエラー

```
status=error
last_error="ContentVersion upload failed"
retry_count=3
```

→ ContentVersion API が 3 回失敗。

---

## Storage 側のエラー

```
function=download_request
event=end
return_value={"error": "invalid parameters"}
```

→ download-request のパラメータ不正。

---

## Mock Salesforce 側のエラー

```
status_code=500
path=/sobjects/ContentVersion
```

→ モック API の内部エラー。

---

# 🧪 よくあるトラブルと確認ポイント

## ❗ Worker が動かない  
**症状：** queue にファイルが溜まり続ける  
**確認：**

```bash
grep "start worker loop" logs/worker.log
```

- Worker が起動していない  
- queue のパスが間違っている  

---

## ❗ ContentVersion が作成されない  
**症状：** DownloadMaster__c が「準備中」のまま  
**確認：**

```bash
grep ContentVersion logs/worker.log
```

- トークン取得失敗  
- ファイル読み込み失敗  
- chunk 分割失敗  

---

## ❗ ダウンロード可にならない  
**症状：** Worker は成功しているが UI が更新されない  
**確認：**

```bash
grep DownloadMaster logs/salesforce_mock.log
```

- DownloadMaster__c 更新 API が失敗  
- CDC push が行われていない  

---

# 🧩 start / end ログの読み方

trace_action により、すべての関数は以下の 2 行で構成されます：

```
event=start  function=xxx  parameters={...}
event=end    function=xxx  elapsed_ms=123
```

### ✔ start ログ  
- 入力値（parameters）が分かる  
- どの関数が呼ばれたか分かる  

### ✔ end ログ  
- 処理時間（elapsed_ms）が分かる  
- return_value が分かる  

### ✔ start があるのに end が無い  
→ **例外発生 or プロセス強制終了**

---

# 🐢 処理の遅延を見つける方法(linux)

```bash
grep "elapsed_ms" logs/worker.log | sort -t= -k2 -nr | head
```

→ 遅い処理が一目で分かる。

---

# 📦 どのファイルが処理されたか確認する

queue の filename がログに出る：

```
parameters={"filename": "file_1.pdf"}
```

または：

```
return_value={"id": "069xx0000001234"}
```

