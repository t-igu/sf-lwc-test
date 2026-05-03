# Documentation Index

このディレクトリは、  
**Local Async File Download Demo** の詳細ドキュメントをまとめたものです。

トップ README では概要のみを説明し、  
ここではアーキテクチャ・フロー・API・ログ・トラブルシューティングなど  
開発者・保守者向けの詳細情報を提供します。

---

# 📘 目次（Table of Contents）

## 1. Overview
**プロジェクトの背景・目的・全体像を説明**

→ [overview.md](overview.md)

---

## 2. Architecture
**全体アーキテクチャ図・構成要素・ディレクトリ構造**

→ [architecture.md](architecture.md)

---

## 3. LWC / Apex / CDC Flow
**Salesforce（モック）側の UI → Apex → CDC の動作を詳細に説明**

- LWC の UI フロー  
- Apex の役割  
- CDC push の仕組み  
- シーケンス図  
- DownloadMaster__c の状態遷移  

→ [lwc_flow.md](lwc_flow.md)

---

## 4. Storage Server Flow
**Storage Server（FastAPI）の内部処理フロー**

- `/download-request` の動作  
- queue ジョブ生成  
- `/upload-complete` の動作  
- Worker との連携  

→ [storage_flow.md](storage_flow.md)

---

## 5. Worker Flow
**Worker の内部処理と API 呼び出し順序**

- queue の読み取り  
- ContentVersion chunk upload  
- DownloadMaster__c 更新  
- 完了通知 `/upload-complete`  

→ [worker_flow.md](worker_flow.md)

---

## 6. Queue Management
**非同期処理の中心となる queue の仕様**

- ディレクトリ構造  
- Queue JSON スキーマ  
- 状態遷移図  
- ライフサイクル  

→ [queue.md](queue.md)

---

## 7. API Reference
**Storage / Worker / Mock Salesforce の API 一覧**

- Storage Server API  
- Salesforce Mock API  
- Worker → Storage 通知 API  
- Worker 内部で利用する API（呼び出し順）  

→ [api_reference.md](api_reference.md)

---

## 8. Logging Guide
**保守者向けのログの読み方ガイド**

- request_id を軸にした調査方法  
- start/end ログの意味  
- よくあるログパターン  
- 遅延の特定方法  

→ [logging.md](logging.md)

---

## 9. Troubleshooting
**よくある問題と解決方法**

- Worker が動かない  
- ContentVersion が作成されない  
- DownloadMaster__c が更新されない  
- CDC push が来ない  
- ダウンロードリンクが生成されない  

→ [troubleshooting.md](troubleshooting.md)

---

# 🧭 ドキュメントの読み方（推奨）

1. **まず Overview と Architecture を読む**  
2. UI 開発者は **LWC Flow**  
3. バックエンド開発者は **Storage Flow / Worker Flow**  
4. 運用担当者は **Logging / Troubleshooting**  
5. API 実装者は **API Reference**  

