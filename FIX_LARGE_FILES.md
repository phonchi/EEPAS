# 🔧 修復大檔案上傳問題

## 問題分析

上傳失敗原因：
- **總大小**：200.54 MB（超過 GitHub 建議的單次推送大小）
- **HTTP 408 timeout**：檔案太多太大，連線逾時

## 🔍 發現的大檔案

### 超大文字檔案（已在 .gitignore，但被 git 追蹤了）
```
159M  data/HORUS_Ita_DataOrigin_o.txt
159M  data/HORUS_Ita_DataOrigin.txt
121M  data/HORUS_Ita_Catalog_o.txt
121M  data/HORUS_Ita_Catalog.txt
121M  test_data/HORUS_Ita_Catalog.txt
```

### 大型 .mat 檔案
```
34M   data/HORUS_Italy_polygon_filtered.mat
34M   data/HORUS_Italy_RDN2008_polygon_filtered.mat
32M   data/HORUS_Italy_filtered.mat
32M   data/HORUS_Italy_RDN2008_filtered.mat
```

### 其他大檔案
```
18M   docs/build.zip
12M   analysis/[2024] psi.pdf
7.9M  docs/build/doctrees/environment.pickle
7.6M  ggad123.pdf
```

---

## ✅ 解決方案

### 方案 A：清理 Git 歷史並重新上傳（推薦）

#### 步驟 1：從 Git 歷史中移除大檔案

```bash
# 1. 從 Git 索引中移除大檔案（但保留在工作目錄）
git rm --cached data/HORUS_Ita_*.txt
git rm --cached data/HORUS_Italy_polygon_filtered.mat
git rm --cached data/HORUS_Italy_RDN2008_polygon_filtered.mat
git rm --cached data/HORUS_Italy_filtered.mat
git rm --cached data/HORUS_Italy_RDN2008_filtered.mat
git rm --cached test_data/HORUS_Ita_Catalog.txt
git rm --cached docs/build.zip
git rm --cached 'analysis/[2024] psi.pdf'
git rm --cached ggad123.pdf
git rm --cached -r docs/build/doctrees/

# 2. 確認 .gitignore 已更新
cat .gitignore | grep -A 5 "Large"

# 3. 提交變更
git add .gitignore
git commit -m "移除大檔案，減少上傳大小

- 從 git 移除大型文字目錄檔案（.txt，~680MB）
- 從 git 移除大型 .mat 檔案（>30MB）
- 從 git 移除 PDF 和 zip 檔案
- 更新 .gitignore 防止未來加入

檔案仍保留在本地，但不上傳到 GitHub

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 4. 配置 Git 以處理大型推送
git config http.postBuffer 524288000  # 500MB
git config http.timeout 300           # 5 分鐘

# 5. 重新推送（應該小很多）
git push -u origin master
```

#### 預期結果

移除後上傳大小應該降到 **~30-50 MB**：
- ✅ Python 原始碼：~1 MB
- ✅ Sphinx HTML（無 doctrees）：~10 MB
- ✅ 小型 .mat 檔案（<5MB）：~20 MB
- ✅ 配置和文檔：~1 MB
- ✅ Notebooks：~2 MB

---

### 方案 B：只上傳 Sphinx HTML，不上傳編譯快取

如果方案 A 還是太大，可以進一步精簡：

```bash
# 移除 Sphinx 編譯快取
git rm --cached -r docs/build/doctrees/

# 只保留 HTML（不含快取）
git add docs/build/html/

git commit -m "精簡 Sphinx 文檔：只保留 HTML

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push -u origin master
```

---

### 方案 C：使用 Git LFS（大檔案儲存）

如果需要上傳大型數據檔案：

```bash
# 1. 安裝 Git LFS
git lfs install

# 2. 追蹤大型 .mat 檔案
git lfs track "data/*.mat"
git lfs track "*.pdf"

# 3. 提交 .gitattributes
git add .gitattributes
git commit -m "使用 Git LFS 追蹤大檔案"

# 4. 推送
git push -u origin master
```

**注意**：GitHub 免費帳號的 LFS 配額有限（1GB 儲存，1GB/月 頻寬）

---

### 方案 D：不上傳數據檔案（最精簡）

如果數據檔案不需要放在 GitHub：

```bash
# 1. 更新 .gitignore，排除所有 data/
echo "data/" >> .gitignore

# 2. 從 git 移除（但保留本地）
git rm --cached -r data/

# 3. 在 README 提供數據下載連結
# 建議：上傳到 Zenodo、Google Drive 或其他儲存服務

# 4. 提交並推送
git add .gitignore README.md
git commit -m "移除數據檔案，提供外部下載連結"
git push -u origin master
```

在 README.md 中加入：

```markdown
## 數據下載

由於檔案過大，數據檔案未包含在此 repository。請從以下連結下載：

- **義大利地震目錄**: [下載連結]
- **台灣地震目錄**: [下載連結]

下載後，解壓縮到 `data/` 目錄。
```

---

## 🚀 立即執行（推薦方案 A）

```bash
# 一鍵清理腳本
bash << 'EOF'
#!/bin/bash
set -e

echo "🔧 正在清理大檔案..."

# 移除大檔案
git rm --cached data/HORUS_Ita_*.txt 2>/dev/null || true
git rm --cached data/HORUS_Italy_polygon_filtered.mat 2>/dev/null || true
git rm --cached data/HORUS_Italy_RDN2008_polygon_filtered.mat 2>/dev/null || true
git rm --cached data/HORUS_Italy_filtered.mat 2>/dev/null || true
git rm --cached data/HORUS_Italy_RDN2008_filtered.mat 2>/dev/null || true
git rm --cached test_data/HORUS_Ita_Catalog.txt 2>/dev/null || true
git rm --cached docs/build.zip 2>/dev/null || true
git rm --cached 'analysis/[2024] psi.pdf' 2>/dev/null || true
git rm --cached ggad123.pdf 2>/dev/null || true
git rm --cached -r docs/build/doctrees/ 2>/dev/null || true

echo "✅ 大檔案已從 git 索引移除"

# 配置 Git
git config http.postBuffer 524288000
git config http.timeout 300

echo "✅ Git 配置已更新"

# 提交變更
git add .gitignore
git commit -m "移除大檔案，減少上傳大小

- 從 git 移除大型文字目錄檔案（.txt，~680MB）
- 從 git 移除大型 .mat 檔案（>30MB）
- 從 git 移除 PDF 和 zip 檔案
- 更新 .gitignore 防止未來加入

檔案仍保留在本地，但不上傳到 GitHub

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

echo "✅ 變更已提交"
echo ""
echo "📊 預計上傳大小："
git count-objects -vH

echo ""
echo "🚀 準備推送到 GitHub..."
echo "執行：git push -u origin master"

EOF
```

---

## 📊 檔案大小對比

| 方案 | 上傳大小 | 說明 |
|------|---------|------|
| **原始** | 200 MB | ❌ 太大，上傳失敗 |
| **方案 A** | ~30-50 MB | ✅ 推薦，移除大檔案 |
| **方案 B** | ~20-30 MB | ✅ 進一步精簡 |
| **方案 D** | ~10-20 MB | ✅ 最精簡，不含數據 |

---

## ✅ 檢查清單

- [ ] 執行清理腳本移除大檔案
- [ ] 確認 .gitignore 已更新
- [ ] 配置 Git http.postBuffer 和 timeout
- [ ] 提交變更
- [ ] 檢查上傳大小（應 < 50MB）
- [ ] 重新推送到 GitHub

---

**準備好了嗎？執行上方的一鍵清理腳本即可！** 🚀
