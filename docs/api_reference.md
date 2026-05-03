# API Reference

このドキュメントでは、本プロジェクトで利用される  
**Storage Server / Salesforce Mock Server / Worker 通知 API**  
をすべて一覧化します。

---

# 🗂️ 1. Storage Server API（FastAPI / ポート 8080）

Storage Server は、Apex からのダウンロード要求を受け取り、  
queue にジョブを作成し、Worker の完了通知を受け取ります。

| メソッド | パス | 説明 | リクエスト | レスポンス |
|---------|------|------|------------|-------------|
| **POST** | `/download-request` | ダウンロード要求を受け取り queue にジョブを作成 | Header: `request_id` / Body: file list | 202 Accepted |
| **POST** | `/upload-complete` | Worker からの完了通知を受け取り DownloadMaster__c を更新 | `{ id, status }` | 200 OK |
| **GET** | `/upload-form` | デモ用のファイルアップロードフォーム | なし | HTML |
| **GET** | `/health` | ヘルスチェック | なし | 200 OK |

---

# 🗂️ 2. Salesforce Mock Server API（FastAPI / ポート 8000）

Salesforce® の REST API を模した **互換 API** です。  
Worker がファイルをアップロードする際に利用します。

---

## 📄 ContentVersion API

| メソッド | パス | 説明 | リクエスト | レスポンス |
|---------|------|------|------------|-------------|
| **POST** | `/services/data/v60.0/sobjects/ContentVersion` | ContentVersion を新規作成（初回 chunk） | JSON（Title, PathOnClient, VersionData, FirstPublishLocationId） | 200 OK（id 返却） |
| **PATCH** | `/services/data/v60.0/sobjects/ContentVersion/{id}/VersionData` | 追加 chunk をアップロード | Base64 chunk | 200 OK |
| **POST** | `/services/data/v60.0/sobjects/ContentDocumentLink` | ContentDocument と DownloadMaster__c を紐付け | JSON | 200 OK |

---

## 📄 DownloadMaster__c API

| メソッド | パス | 説明 | リクエスト |
|---------|------|------|------------|
| **PATCH** | `/services/data/v60.0/sobjects/DownloadMaster__c/{id}` | DownloadMaster__c のステータス更新 | `{ Status__c: "ダウンロード可" }` |

---

## 📄 OAuth（モック）

| メソッド | パス | 説明 |
|---------|------|------|
| **POST** | `/services/oauth2/token` | モックアクセストークンを返す |

---

## 📄 Debug API

| メソッド | パス | 説明 |
|---------|------|------|
| **GET** | `/debug/files` | モック Salesforce 側に保存された ContentVersion の一覧 |

---

# 🗂️ 3. Worker → Storage 通知 API

Worker が処理完了後に呼び出す API。

| メソッド | パス | 説明 | Body |
|---------|------|------|------|
| **POST** | `/upload-complete` | ContentVersion アップロード完了通知 | `{ "id": "DM-1", "status": "Completed" }` |

---

# 🗂️ 4. Worker 内部で利用する API（呼び出し順）

Worker が queue を処理する際に呼び出す API を時系列で整理。

| 順序 | メソッド | パス | 説明 |
|------|----------|------|------|
| 1 | POST | `/services/oauth2/token` | アクセストークン取得 |
| 2 | POST | `/services/data/v60.0/sobjects/ContentVersion` | 初回 chunk アップロード |
| 3 | PATCH | `/services/data/v60.0/sobjects/ContentVersion/{id}/VersionData` | 追加 chunk アップロード |
| 4 | POST | `/services/data/v60.0/sobjects/ContentDocumentLink` | 紐付け作成 |
| 5 | PATCH | `/services/data/v60.0/sobjects/DownloadMaster__c/{id}` | ステータス更新 |
| 6 | POST | `/upload-complete` | Storage へ完了通知 |

