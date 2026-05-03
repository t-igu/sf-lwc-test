import { LightningElement, track } from 'lwc';

export default class Download extends LightningElement {
    @track records = [];
    @track showPopup = false;
    @track selectedFiles = [];

    schema = null;

    connectedCallback() {
        this.loadSchema().then(() => {
            this.refresh();
        });
    }

    async loadSchema() {
        try {
            const response = await fetch('/apex/schema');
            const data = await response.json();
            this.schema = data.models?.DownloadMaster__c?.fields || {};
        } catch (e) {
            console.error("Failed to load schema", e);
            this.schema = {};
        }
    }

    async refresh() {
        try {
            const response = await fetch('/apex/api/download-masters');
            const data = await response.json();

            this.records = data.map(record => {
                const safeRecord = {};

                // スキーマに定義されているフィールドだけコピー
                for (const fieldName of Object.keys(this.schema)) {
                    if (record[fieldName] !== undefined) {
                        safeRecord[fieldName] = record[fieldName];
                    }
                }

                // LWC 固有の UI 状態
                safeRecord.id = record.id || record.Id;
                safeRecord.checked = false;
                safeRecord.requested = false;
                safeRecord.status = '未リクエスト';

                return safeRecord;
            });

        } catch (error) {
            console.error('Failed to fetch records', error);
        }
    }

    // チェックボックスの状態変更をハンドル
    handleCheckboxChange(event) {
        const recordId = event.target.dataset.id;
        const isChecked = event.target.checked;
        
        const record = this.records.find(r => r.id === recordId);
        if (record) {
            record.checked = isChecked;
        }
    }

    // ダウンロードボタンの有効/無効判定
    get isDownloadDisabled() {
        return !this.records.some(record => record.checked);
    }

    async handleDownloadSelected() {
        const targets = this.records.filter(record => record.checked);

        this.selectedFiles = targets.map(t => ({
            id: t.id,
            name: t.filename_disp,
            status: '準備中...'
        }));

        this.showPopup = true;
        await Promise.resolve();

        // ★ ここが重要：ID のリストを 1 回だけ送る
        const fileIds = targets.map(t => t.id);

        try {
            const response = await fetch('/apex/download-request', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ file_ids: fileIds })
            });

            const data = await response.json();
            console.log("download-request response:", data);

            // ★ 配列でなければ配列に変換する
            const list = Array.isArray(data) ? data : [data];

            console.log("download-request list:", list);

            list.forEach(item => {
                const record = targets.find(t => t.id === item.id);
                if (!record) {
                    console.warn("No matching record for id:", item.id);
                    return;
                }

                record.requested = true;
                this.subscribeCdc(record);
            });


            // // apex から返ってくるのは DownloadResponseModel のリスト
            // data.forEach((item, index) => {
            //     const record = targets[index];
            //     record.id = item.id;
            //     record.requested = true;

            //     // CDC 監視開始
            //     this.subscribeCdc(record);
            // });

        } catch (error) {
            console.error('Download Request Failed', error);
            targets.forEach(t => this.updateSelectedFileStatus(t.id, 'エラー ❌'));
        }
    }

    subscribeCdc(record) {
        const id = record.id;

        // すでに購読していたら閉じる
        if (record._es) {
            record._es.close();
        }

        const es = new EventSource(`/cdc/stream/${id}`);
        record._es = es;

        console.log("SSE connected:", id);

        es.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log("SSE event:", data);
            if (data.status === "Completed" || data.status === "completed") {
                this.updateSelectedFileStatus(record.id, "完了 ✅");

                const docId = data.ContentDocumentId__c || data.content_document_id;

                if (docId) {
                    this.triggerBrowserDownload(
                        docId,
                        record.name   // 修正
                    );
                }

                es.close();
            }

        };

        es.onerror = (err) => {
            console.error("SSE error:", err);
            es.close();
        };
    }


    async monitorStatus(record) {
        let retryCount = 0;
        const MAX_RETRIES = 30; // 2秒間隔 × 30回 = 最大60秒間でタイムアウト

        const poll = async () => {
            try {
                // 1. タイムアウト判定
                if (retryCount >= MAX_RETRIES) {
                    console.warn(`Polling timed out for ${record.id}`);
                    this.updateSelectedFileStatus(record.id, 'タイムアウト ❌');
                    return;
                }
                retryCount++;

                const response = await fetch(`/cdc-stream?id=${record.id}`);
                const rawText = await response.text();

                console.log(`Polling attempt ${retryCount} for ${record.id}`, { rawText });

                // レスポンスが空（イベントがまだサーバーに届いていない）場合は2秒後に再試行
                if (!rawText || rawText.trim() === '') {
                    setTimeout(poll, 2000);
                    return;
                }

                // サーバーからの通知に「完了」や「069(ContentDocumentIdの頭)」が含まれているか
                const isFinished = rawText.includes('完了') || 
                                   rawText.includes('\\u5b8c\\u4e86') || 
                                   rawText.includes('069');
                const isTarget = rawText.includes(String(record.id || '').replace('DM-', ''));

                if (isFinished && isTarget) {
                    console.log('Match found! Updating UI to complete.');
                    this.updateSelectedFileStatus(record.id, '完了 ✅');

                    // ファイルIDの抽出とダウンロードの実行
                    const match = rawText.match(/"ContentDocumentId__c":\s*"([^"]+)"/);
                    if (match && match[1]) {
                        const fileId = match[1];
                        this.triggerBrowserDownload(fileId, record.fileName);
                    }
                    return; // 完了したら終了
                }
                // まだ完了していなければ 2秒後に再試行
                setTimeout(poll, 2000);
            } catch (err) {
                console.error('Status monitor error', err);
            }
        };
        poll();
    }

    updateSelectedFileStatus(recordId, status) {
        const targetId = String(recordId).trim();
        console.log(`Updating UI: Record ${targetId} -> ${status}`);

        // 1. メインリスト(this.records)側のステータスを更新
        this.records = this.records.map(item => {
            if (String(item.id).trim() === targetId) {
                return { ...item, status: status };
            }
            return item;
        });

        // 2. ポップアップ(selectedFiles)側のステータスを更新
        // indexを直接見つけることで確実にマッチさせる
        const newSelectedFiles = this.selectedFiles.map(item => {
            // 両方のID（idプロパティとIdプロパティ）を念のためチェック
            const itemId = String(item.id || item.Id || '').trim();
            if (itemId === targetId) {
                return { ...item, status: status };
            }
            return item;
        });

        // 配列の参照を完全に新しくして、子コンポーネントへの変更通知を強制する
        this.selectedFiles = [...newSelectedFiles];
    }

    // ブラウザのダウンロード機能をキックする
    triggerBrowserDownload(fileId, fileName) {
        // 本来はSalesforceのサーブレットURLだが、ここではMockエンドポイントを想定
        const downloadUrl = `/sfc/servlet.shepherd/version/download/${fileId}?asNamesFile=${fileName}`;
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = fileName;
        document.body.appendChild(link); // DOMに一時的に追加
        link.click();
        document.body.removeChild(link); // 実行後に削除
    }

    handleBack() {
        // Homeに戻るロジック（必要に応じて実装）
    }

    handlePopupClose() {
        this.showPopup = false;
    }
}