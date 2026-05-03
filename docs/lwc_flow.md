# LWC / Apex / CDC Flow

このドキュメントでは、Salesforce（モック）側の  
**LWC → Apex → Storage → CDC → LWC** の一連の動作をまとめています。

LWC はユーザー操作を受け取り、Apex を経由して Storage に非同期リクエストを送信し、  
CDC による DownloadMaster__c の更新通知を受けて UI を更新します。

---

# 📘 LWC 側の処理フロー（概要）

1. DownloadMaster__c を読み込み、画面に一覧表示  
2. ユーザーが複数ファイルを選択  
3. 「ダウンロード」ボタン押下  
4. ポップアップ表示（ステータス＝準備中）  
5. Apex が Storage の `/download-request` を呼び出す  
6. CDC により DownloadMaster__c の更新通知を受信  
7. ContentVersion の URL を DOM に追加  
8. ユーザーがファイルをダウンロード  
9. ポップアップを「完了」に更新  

---

# 🧩 シーケンス図（LWC / Apex / CDC）

```mermaid
sequenceDiagram
    autonumber

    participant U as User
    participant LWC as LWC (download.js)
    participant Apex as Apex Controller
    participant CDC as CDC Listener
    participant API as storage_server
    participant SF as Mock Salesforce API
    participant DOM as Browser DOM

    U->>LWC: ① ファイル選択
    U->>LWC: ② ダウンロードボタン押下

    LWC->>LWC: ③ ポップアップ表示（準備中）
    LWC->>Apex: ④ downloadRequest(fileList)

    Apex->>Apex: ⑤ request_id 生成
    Apex->>API: ⑥ POST /download-request

    API-->>Apex: ⑦ 202 Accepted
    Apex->>CDC: ⑧ CDC 購読開始

    Note over API: ⑨ Storage 側で非同期アップロード開始

    SF-->>CDC: ⑩ DownloadMaster__c 更新（ダウンロード可）

    CDC-->>LWC: ⑪ 更新通知 push

    LWC->>DOM: ⑫ ContentVersion の URL を生成
    DOM->>U: ⑬ ユーザーがダウンロード

    LWC->>LWC: ⑭ ポップアップを「完了」に更新
```

# DownloadMaster__c の状態遷移（LWC 視点）

```mermaid
stateDiagram-v2
    [*] --> Initial

    Initial --> Ready: 画面ロード

    Ready --> Preparing: ダウンロードボタン押下\nStatus=準備中

    Preparing --> Queued: Storage が queue 作成

    Queued --> Uploading: Worker がアップロード開始

    Uploading --> Downloadable: アップロード完了\nStatus=ダウンロード可

    Downloadable --> Downloaded: ユーザーがダウンロード完了

    Preparing --> Error: パラメータ不正
    Uploading --> Error: API 失敗（3回）

    Error --> [*]
    Downloaded --> [*]
```