# 🚀 快速開始：上傳到 GitHub

**只需 3 步，立即上傳您的 EEPAS 專案到 GitHub！**

---

## 方法 A：一鍵上傳（推薦）⚡

```bash
# 1. 設定您的 GitHub 用戶名
export GITHUB_USERNAME=your_username

# 2. 執行上傳腳本
bash UPLOAD_TO_GITHUB.sh

# 3. 完成！
```

**就這麼簡單！** 腳本會自動：
- ✅ 清理快取
- ✅ 檢查大檔案
- ✅ 添加檔案
- ✅ 提交變更
- ✅ 推送到 GitHub

---

## 方法 B：手動上傳（完全控制）📝

### 步驟 1：準備檔案

```bash
# 執行準備腳本
bash prepare_github_upload.sh
```

### 步驟 2：檢查狀態

```bash
# 查看將被上傳的檔案
git status

# 查看將被忽略的檔案
git status --ignored
```

### 步驟 3：提交變更

```bash
# 添加所有檔案
git add .

# 提交
git commit -m "準備 GitHub 上傳：精簡專案，保留 Sphinx 必要內容

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### 步驟 4：推送到 GitHub

```bash
# 設定 remote（首次）
git remote add origin https://github.com/YOUR_USERNAME/EEPAS_Taiwan.git

# 推送
git push -u origin master
```

---

## 📊 上傳內容概覽

### ✅ 將被上傳（~170 MB）

- **Python 原始碼**：30 個模組（核心 + utils + analysis）
- **Jupyter Notebooks**：4 個（Sphinx 引用）
- **配置檔案**：6 個主要配置
- **數據檔案**：15 個 .mat 檔案（~150 MB）
- **Sphinx 文檔**：完整原始碼 + HTML（17 MB）
- **文檔**：README, USAGE, LICENSE 等

### ❌ 已排除（~540 MB）

- Python 快取（`__pycache__/`）
- 結果檔案（`results_*/`）
- 大型文字檔案（`data/*.txt`）
- 測試和臨時檔案
- 非 Sphinx 引用的工具腳本

---

## 📚 啟用 GitHub Pages（可選）

上傳後，啟用文檔網站：

1. 進入 GitHub repo → **Settings** → **Pages**
2. **Source**: Deploy from a branch
3. **Branch**: `master`
4. **Folder**: `/docs/build/html`
5. 點擊 **Save**

**文檔網址**：`https://YOUR_USERNAME.github.io/EEPAS_Taiwan/`

---

## ❓ 常見問題

### Q1: 如何修改 GitHub 用戶名？

**方法 1**：環境變數
```bash
export GITHUB_USERNAME=your_username
bash UPLOAD_TO_GITHUB.sh
```

**方法 2**：編輯腳本
打開 `UPLOAD_TO_GITHUB.sh`，修改第 6 行：
```bash
GITHUB_USERNAME="your_username"
```

### Q2: 如何檢查將被上傳的檔案？

```bash
# 執行準備腳本（包含詳細報告）
bash prepare_github_upload.sh

# 或直接查看 git 狀態
git status
```

### Q3: 上傳失敗怎麼辦？

**常見原因**：

1. **Remote 已存在**
   ```bash
   # 更新 remote URL
   git remote set-url origin https://github.com/YOUR_USERNAME/EEPAS_Taiwan.git
   ```

2. **需要 GitHub 認證**
   - 使用 Personal Access Token（推薦）
   - 或設定 SSH key

3. **檔案過大（>100MB）**
   ```bash
   # 檢查大檔案
   find . -type f -size +100M
   ```

### Q4: 如何重新編譯 Sphinx 文檔？

```bash
cd docs
make clean
make html
cd ..
```

### Q5: 我想排除更多檔案怎麼辦？

編輯 `.gitignore`，添加您想忽略的檔案或目錄。

---

## 📖 詳細文檔

- **`GITHUB_UPLOAD_PLAN.md`**：完整上傳計劃（必讀）
- **`GITHUB_READY_SUMMARY.md`**：準備完成報告
- **`prepare_github_upload.sh`**：自動化準備腳本
- **`UPLOAD_TO_GITHUB.sh`**：一鍵上傳腳本

---

## ✅ 檢查清單

上傳前確認：

- [ ] 已設定 GitHub 用戶名
- [ ] 已執行 `prepare_github_upload.sh`
- [ ] 已檢查 `git status`
- [ ] 確認無敏感資訊
- [ ] 確認所有必要檔案都在
- [ ] 準備好推送！

---

**準備好了嗎？立即開始！** 🚀

```bash
export GITHUB_USERNAME=your_username
bash UPLOAD_TO_GITHUB.sh
```

---

**版本**：v1.3.0
**日期**：2025-12-07
