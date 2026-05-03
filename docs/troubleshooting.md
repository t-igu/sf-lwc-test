# Troubleshooting Guide

このドキュメントは、非同期ファイルダウンロード処理において  
**実際に発生しやすい問題とその解決方法** をまとめています。

問題は主に以下の 4 つのレイヤーで発生します：

- **LWC / Apex**
- **Storage Server**
- **Worker**
- **Mock Salesforce**

どこで問題が起きているかを素早く切り分けるために、  
症状ベースで確認ポイントを整理しています。

---

# 🧭 まず最初にやるべきこと

## ✔ request_id を特定する

Apex が生成する `request_id` は  
**LWC → Apex → Storage → Worker → Mock → CDC**  
すべてのログに伝播します。

まずは request_id を grep して全体像を把握します。

```bash
grep "abc-123" logs/*.log
```

---

# 🚨 よくある問題と対処法

---

# 1. Worker が動いていない / queue が溜まり続ける

## 症状
- `storage/queue/accepted/` にファイルが溜まり続ける
- DownloadMaster__c が「準備中」のまま

## 原因
- Worker が起動していない
- queue のパス設定が間違っている
- Worker が例外で落ちている

## 確認ポイント

```bash
grep "start worker loop" logs/worker.log
```

Worker が起動していない場合は何も出ません。

## 解決策
- Worker を再起動する  
- `config.toml` の queue パスを確認  
- Worker の例外ログを確認  

---

# 2. ContentVersion が作成されない

## 症状
- DownloadMaster__c が「準備中」のまま
- Worker は動いているがアップロードされない

## 原因
- トークン取得失敗
- ファイル読み込み失敗
- chunk 分割エラー
- Mock Salesforce 側の API エラー

## 確認ポイント

```bash
grep ContentVersion logs/worker.log
```

## 解決策
- Mock Salesforce が起動しているか確認  
- `/services/oauth2/token` のレスポンスを確認  
- ファイルパス復号処理のエラーを確認  

---

# 3. DownloadMaster__c が「ダウンロード可」にならない

## 症状
- Worker の ContentVersion アップロードは成功している
- しかし UI が更新されない

## 原因
- DownloadMaster__c 更新 API が失敗
- CDC push が行われていない
- Storage の `/upload-complete` が呼ばれていない

## 確認ポイント

```bash
grep DownloadMaster logs/salesforce_mock.log
```

## 解決策
- Mock Salesforce の DownloadMaster__c 更新 API を確認  
- Storage の `/upload-complete` のログを確認  
- CDC push のログを確認  

---

# 4. LWC が更新通知（CDC）を受け取らない

## 症状
- モック Salesforce 側では DownloadMaster__c が更新されている
- しかし LWC の UI が変わらない

## 原因
- CDC push が発火していない
- LWC の subscribe が失敗している
- request_id が一致していない

## 確認ポイント

```bash
grep "CDC" logs/salesforce_mock.log
```

## 解決策
- Apex 側の subscribe コードを確認  
- request_id が一致しているか確認  
- LWC の console.log を確認  

---

# 5. ダウンロードリンクが生成されない

## 症状
- UI が「ダウンロード可」になっているのにリンクが出ない

## 原因
- ContentVersion の URL が正しく生成されていない
- Mock Salesforce 側のファイル保存に失敗

## 確認ポイント

```bash
curl http://localhost:8000/debug/files
```

## 解決策
- ContentVersion の保存先ディレクトリを確認  
- LWC の URL 生成ロジックを確認  

---

# 6. Worker が error 状態で終了する

## 症状
- queue が `error/` に移動する
- DownloadMaster__c が Error になる

## 原因
- ContentVersion API が 3 回失敗
- DownloadMaster__c 更新 API が 3 回失敗
- Worker 内部例外

## 確認ポイント

```bash
grep "error" logs/worker.log
```

## 解決策
- Mock Salesforce の API を確認  
- Storage の `/upload-complete` のログを確認  
- Worker の retry_count を確認  

---

# 7. Storage の `/download-request` が 400 / 500 を返す

## 症状
- ダウンロード開始直後に UI が Error になる

## 原因
- file list の形式が不正
- request_id が欠落
- DownloadMaster__c の ID が不正

## 確認ポイント

```bash
grep download_request logs/storage.log
```

## 解決策
- Apex のリクエストパラメータを確認  
- request_id の生成を確認  

---

# 8. ファイルが壊れてダウンロードされる

## 症状
- ダウンロードしたファイルが開けない
- サイズが一致しない

## 原因
- chunk の順序が崩れている
- Base64 エンコード/デコードの不整合
- Mock Salesforce 側の保存処理の不具合

## 確認ポイント

```bash
grep VersionData logs/worker.log
```

## 解決策
- chunk サイズと順序を確認  
- Mock Salesforce のファイル保存処理を確認  

---

# 🧭 トラブル発生時の調査手順（推奨）

1. **request_id を特定**
2. **Storage → Worker → Mock の順にログを追う**
3. **queue の状態を確認**
4. **DownloadMaster__c の状態を確認**
5. **ContentVersion の存在を確認**
6. **CDC push を確認**
7. **LWC の UI を確認**

