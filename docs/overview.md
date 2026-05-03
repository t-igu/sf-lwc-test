# Overview

本プロジェクトは、Salesforce 互換 API を用いた **非同期ファイルダウンロード機能** を  
ローカル環境で再現するデモ環境です。

- 実際の Salesforce® は一切使用しない
- 完全ローカルのモックサーバーで動作
- LWC → Apex → Storage → Worker → Mock Salesforce → CDC の一連の流れを再現
- Chunk Upload / 非同期処理 / 状態管理 / ログ基盤を統合

## 前提となる制約

- Salesforce 利用者は **Salesforce からのみ通信可能**
- 外部の Storage サーバーへ **直接アクセスできない**
- 実ファイルは Salesforce ではなく **Storage サーバー側で管理**
- ユーザーは Salesforce の画面から **複数ファイルを選択してダウンロードしたい**

## 解決するアーキテクチャ

**Salesforce 画面で操作 → Storage が裏側で非同期アップロード  
→ Salesforce が CDC で UI に通知 → ユーザーがダウンロード**

という非同期フローを、ローカル環境で再現します。
