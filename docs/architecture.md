# Architecture

## 全体アーキテクチャ図

```mermaid
flowchart TD

    subgraph Client["Client (Browser UI)"]
        A1["/upload-form"]
        A1 --> A2["select files"]
        A2 --> A3["download click"]
        A4["complete popup"]
    end

    subgraph LWC_Apex_CDC["LWC / Apex / CDC"]
        A3 --> B1["POST /download-request (Apex → Storage)"]
        B3["CDC callback"]
        B3 --> B4["file download (ContentVersion URL)"]
        B4 --> A4
    end

    subgraph API["storage_server (FastAPI)"]
        B1 --> C1["enqueue job (queue JSON)"]
        C1 --> Q1["job entry"]
    end

    subgraph Worker["worker (asyncio)"]
        Q1 --> W1["read job"]
        W1 --> W2["POST ContentVersion"]
        W2 --> W3["POST /upload-complete"]
    end

    subgraph Mock["salesforce_server (mock)"]
        W2 --> M1["/sobjects/ContentVersion"]
        W3 --> M4["/upload-complete (update DownloadMaster__c)"]
        M4 --> M5["CDC push"]
        M5 --> B3
    end
