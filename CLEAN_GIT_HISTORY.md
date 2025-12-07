# 🔧 徹底清理 Git 歷史中的大檔案

## 問題分析

即使從當前 commit 中移除了大檔案，它們仍然存在於 **Git 歷史記錄**中，導致推送失敗：

```
remote: error: File python_src/data/HORUS_Ita_Catalog.txt is 120.01 MB
remote: error: File python_src/data/HORUS_Ita_DataOrigin.txt is 158.89 MB
```

需要從整個 Git 歷史中**徹底移除**這些檔案。

---

## ✅ 解決方案（推薦順序）

### 方案 A：使用內建 git filter-branch（最簡單）⚡

```bash
# 執行自動清理腳本
bash clean_git_history.sh

# 然後強制推送
git push -f origin master
```

### 方案 B：手動執行（更多控制）

```bash
# 1. 從整個 Git 歷史中移除大檔案
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch \
    data/HORUS_Ita_*.txt \
    data/HORUS_Italy_*_filtered.mat \
    data/HORUS_Italy_*_polygon_filtered.mat \
    test_data/HORUS_Ita_Catalog.txt \
    docs/build.zip \
    "analysis/[2024] psi.pdf" \
    ggad123.pdf' \
  --prune-empty --tag-name-filter cat -- --all

# 2. 清理 reflog 和垃圾回收
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 3. 檢查新的倉庫大小
git count-objects -vH

# 4. 強制推送（覆蓋遠端歷史）
git push -f origin master
```

---

### 方案 C：使用 BFG Repo-Cleaner（最快，需安裝）

如果有 Java，可以使用 BFG（比 filter-branch 快 10-100 倍）：

```bash
# 1. 下載 BFG（如果沒有）
wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar
# 或使用 curl
curl -o bfg.jar https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar

# 2. 移除大於 50MB 的檔案
java -jar bfg.jar --strip-blobs-bigger-than 50M .

# 3. 清理
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 4. 強制推送
git push -f origin master
```

---

### 方案 D：重新開始（最徹底，但會失去歷史）

如果不需要保留 Git 歷史，可以重新初始化：

```bash
# 1. 備份當前程式碼
cd ..
cp -r python_src python_src_backup

# 2. 刪除 .git 目錄
cd python_src
rm -rf .git

# 3. 重新初始化 Git
git init
git add .
git commit -m "Initial commit: EEPAS v1.3.0

包含所有核心 Python 模組、Sphinx 文檔、配置檔案
（不含大型數據檔案，已在 .gitignore 中排除）

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 4. 設定 remote 並推送
git remote add origin https://github.com/phonchi/EEPAS.git
git push -f origin master
```

---

## 📊 預期效果

| 方法 | 執行時間 | 倉庫大小 | 優點 | 缺點 |
|------|---------|---------|------|------|
| **方案 A** | 1-5 分鐘 | ~30 MB | 簡單，不需安裝 | 較慢 |
| **方案 B** | 1-5 分鐘 | ~30 MB | 完全控制 | 需手動執行 |
| **方案 C** | <1 分鐘 | ~30 MB | 最快 | 需要 Java |
| **方案 D** | <1 分鐘 | ~20 MB | 最乾淨 | 失去歷史 |

---

## 🚀 推薦執行步驟

### 快速解決（方案 A）

```bash
# 1. 執行清理腳本
bash clean_git_history.sh

# 2. 檢查倉庫大小（應該 < 50 MB）
du -sh .git

# 3. 強制推送
git push -f origin master
```

### 如果方案 A 失敗，使用方案 D（重新開始）

```bash
# 1. 備份
cd ..
cp -r python_src python_src_backup

# 2. 重新初始化
cd python_src
rm -rf .git
git init

# 3. 提交所有檔案
git add .
git commit -m "Initial commit: EEPAS v1.3.0"

# 4. 強制推送
git remote add origin https://github.com/phonchi/EEPAS.git
git push -f origin master
```

---

## ⚠️ 重要注意事項

### 關於 `git push -f`（強制推送）

- ✅ **安全**：如果這是新的 repository 或您是唯一開發者
- ⚠️ **危險**：如果有其他人已經 clone 了這個 repository
- 📝 **建議**：推送前告知其他協作者

### 強制推送後，其他人需要：

```bash
# 其他協作者需要重新 clone
git clone https://github.com/phonchi/EEPAS.git

# 或強制更新本地副本
git fetch origin
git reset --hard origin/master
```

---

## ✅ 驗證步驟

清理並推送後，驗證成功：

```bash
# 1. 檢查本地倉庫大小
du -sh .git
# 應該 < 50 MB

# 2. 檢查 GitHub 上的倉庫大小
# 訪問 https://github.com/phonchi/EEPAS
# 右上角應顯示倉庫大小 < 50 MB

# 3. 測試 clone
cd /tmp
git clone https://github.com/phonchi/EEPAS.git
cd EEPAS/src/python_src
ls -lh  # 確認檔案完整
```

---

## 📝 總結

**推薦執行順序**：

1. 先嘗試 **方案 A**（自動清理腳本）
2. 如果失敗或太慢，使用 **方案 D**（重新開始）
3. 推送成功後，確認 GitHub 上的檔案完整性

**立即執行**：

```bash
# 方案 A
bash clean_git_history.sh
git push -f origin master

# 或方案 D（如果方案 A 失敗）
rm -rf .git
git init
git add .
git commit -m "Initial commit: EEPAS v1.3.0"
git remote add origin https://github.com/phonchi/EEPAS.git
git push -f origin master
```

---

**準備好了嗎？選擇一個方案並執行！** 🚀
