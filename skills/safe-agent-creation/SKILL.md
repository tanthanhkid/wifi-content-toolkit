# 🤝 Skill: Tạo Agent An Toàn (Safe Agent Creation)

**Mục đích:** Hướng dẫn cách tạo sub-agent/đệ tử mới mà không làm mất agent khác.

---

## ⚠️ Cảnh Báo Quan Trọng

Khi dùng `config.patch` với `agents.list`, OpenClaw **THAY THẾ** toàn bộ mảng, không merge!

```json
// ❌ SAI - Sẽ làm mất agents khác!
{"agents": {"list": [{"id": "NEW_AGENT"}]}}

// ✅ ĐÚNG - Include tất cả agents
{"agents": {"list": [EXISTING_AGENT, NEW_AGENT]}}
```

---

## 📋 Các Bước Tạo Agent An Toàn

### Bước 1: Đọc Config Hiện Tại

```bash
openclaw config get | jq '.agents.list'
```

Hoặc trong code:
```python
import json
with open('~/.openclaw/openclaw.json') as f:
    config = json.load(f)
existing_agents = config['agents']['list']
```

### Bước 2: Chuẩn Bị Config Cho Agent Mới

Tạo file JSON cho agent mới (ví dụ: `bill-config.json`):

```json
{
  "id": "BILL",
  "name": "BILL - Programming Specialist",
  "workspace": "/Users/thanhtran/OFFLINE_FILES/Code/ContentTool/",
  "model": {
    "primary": "alibaba-coding/qwen3.5-plus"
  },
  "skills": ["coding-agent"],
  "subagents": {
    "allowAgents": ["claude-code", "codex"]
  }
}
```

### Bước 3: Chạy Script Helper

```bash
cd /Users/thanhtran/OFFLINE_FILES/Code/ContentTool
./scripts/safe-add-agent.sh BILL bill-config.json
```

Script sẽ tự động:
1. Đọc config hiện tại
2. Kiểm tra agent đã tồn tại chưa
3. Merge agent mới vào list
4. Backup config
5. Patch và restart gateway

### Bước 4: Verify

```bash
openclaw config get | jq '.agents.list[].id'
```

Expected output:
```
"BEN"
"BOB"
"BILL"
```

---

## 🛠️ Template Config Cho Agent Mới

### Programming Agent (như BILL)
```json
{
  "id": "AGENT_ID",
  "name": "Agent Name - Description",
  "workspace": "/path/to/workspace/",
  "model": {
    "primary": "alibaba-coding/qwen3.5-plus"
  },
  "skills": ["coding-agent"],
  "subagents": {
    "allowAgents": ["claude-code", "codex"]
  }
}
```

### Video Specialist (như BEN)
```json
{
  "id": "AGENT_ID",
  "name": "Agent Name - Video Specialist",
  "workspace": "/path/to/workspace/",
  "model": {
    "primary": "alibaba-coding/qwen3.5-plus"
  },
  "skills": ["video-frames", "songsee", "coding-agent"],
  "subagents": {
    "allowAgents": ["claude-code", "codex"]
  }
}
```

### Manager/Coordinator (như BOB)
```json
{
  "id": "AGENT_ID",
  "name": "Agent ID - Manager & Coordinator",
  "workspace": "/path/to/workspace/",
  "model": {
    "primary": "alibaba-coding/qwen3.5-plus"
  },
  "skills": ["coding-agent"],
  "subagents": {
    "allowAgents": ["ben", "bill", "claude-code", "codex"]
  }
}
```

---

## 📝 Checklist Trước Khi Tạo Agent

- [ ] Đã đọc config hiện tại
- [ ] Đã kiểm tra agent chưa tồn tại
- [ ] Đã chuẩn bị config JSON hợp lệ
- [ ] Đã backup config (script tự động làm)
- [ ] Đã verify sau khi thêm

---

## 🔧 Troubleshooting

### Agent bị mất sau khi patch
**Nguyên nhân:** Patch chỉ đưa 1 agent vào list
**Fix:** Đọc lại config, merge tất cả agents, patch lại

### Gateway không restart
**Check:** `openclaw gateway status`
**Fix:** `openclaw gateway restart`

### Config invalid JSON
**Check:** `openclaw config get`
**Fix:** Restore từ backup: `cp ~/.openclaw/openclaw.json.backup.* ~/.openclaw/openclaw.json`

---

## 📚 Related Files

- `scripts/safe-add-agent.sh` - Script tự động thêm agent an toàn
- `docs/safe-agent-creation.md` - Tài liệu chi tiết
- `AGENTS.md` - Workspace guidelines (có cảnh báo ở cuối)

---

*Tài liệu này được tạo để tránh lặp lại sự cố BOB bị đè khi tạo BEN.*
