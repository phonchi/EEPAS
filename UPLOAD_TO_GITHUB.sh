#!/bin/bash
# 一鍵上傳到 GitHub 的腳本
# 使用前請先設定 GITHUB_USERNAME 變數

set -e

# ===== 配置區域 =====
GITHUB_USERNAME="${GITHUB_USERNAME:-YOUR_USERNAME}"  # 請替換為您的 GitHub 用戶名
REPO_NAME="EEPAS_Taiwan"
BRANCH="master"

# ===== 檢查配置 =====
echo "========================================="
echo "  EEPAS GitHub 上傳腳本"
echo "========================================="
echo ""

if [ "$GITHUB_USERNAME" = "YOUR_USERNAME" ]; then
    echo "⚠️  錯誤：請先設定 GitHub 用戶名！"
    echo ""
    echo "方法 1：環境變數"
    echo "  export GITHUB_USERNAME=your_username"
    echo "  bash UPLOAD_TO_GITHUB.sh"
    echo ""
    echo "方法 2：直接編輯此腳本"
    echo "  將第 6 行的 YOUR_USERNAME 改為您的用戶名"
    echo ""
    exit 1
fi

echo "GitHub 用戶名：$GITHUB_USERNAME"
echo "Repository：$REPO_NAME"
echo "Branch：$BRANCH"
echo ""

# ===== 步驟 1：準備檔案 =====
echo "📁 [步驟 1/6] 執行準備腳本..."
bash prepare_github_upload.sh
echo ""

# ===== 步驟 2：確認繼續 =====
echo "========================================="
echo "  準備提交以下檔案："
echo "========================================="
git status --short | head -50
echo ""
echo "將被忽略的檔案（前 20 個）："
git status --ignored --short 2>/dev/null | head -20
echo ""

read -p "是否繼續？(y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消上傳"
    exit 1
fi

# ===== 步驟 3：添加檔案 =====
echo ""
echo "📦 [步驟 3/6] 添加檔案到 Git..."
git add .gitignore
git add GITHUB_UPLOAD_PLAN.md
git add GITHUB_READY_SUMMARY.md
git add prepare_github_upload.sh
git add UPLOAD_TO_GITHUB.sh
git add results_italy_causal_ew0/.gitkeep
git add results_italy_causal_ew0_accurate/.gitkeep

# 添加 Sphinx 編譯結果
if [ -d "docs/build/html" ]; then
    git add docs/build/html/
    echo "✅ 已添加 Sphinx HTML 文檔"
fi

# 添加 Jupyter Notebooks
git add analysis/*.ipynb 2>/dev/null || true
echo "✅ 檔案已添加"
echo ""

# ===== 步驟 4：提交 =====
echo "📝 [步驟 4/6] 提交變更..."
git commit -m "準備 GitHub 上傳：精簡專案，保留 Sphinx 必要內容

## 變更摘要

### 新增
- 更新 .gitignore，排除快取、結果、測試檔案
- 新增 GITHUB_UPLOAD_PLAN.md（詳細上傳計劃）
- 新增 GITHUB_READY_SUMMARY.md（準備完成報告）
- 新增 prepare_github_upload.sh（自動化腳本）
- 新增 UPLOAD_TO_GITHUB.sh（一鍵上傳腳本）
- 新增結果目錄佔位檔案（.gitkeep）

### 保留（Sphinx 必要）
- 5 個核心主程式
- 8 個 utils/ 工具模組
- 9 個 analysis/ 分析模組
- 4 個 Jupyter Notebooks
- 6 個主要配置檔案
- Sphinx 完整文檔（原始碼 + HTML）

### 排除
- Python 快取（__pycache__/）
- 結果檔案（results_*/）
- 大型文字目錄（data/*.txt, ~540MB）
- 測試和臨時檔案
- 非 Sphinx 引用的工具腳本

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

echo "✅ 變更已提交"
echo ""

# ===== 步驟 5：設定 Remote =====
echo "🔗 [步驟 5/6] 設定 GitHub Remote..."
REMOTE_URL="https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"

# 檢查 remote 是否存在
if git remote | grep -q "^origin$"; then
    echo "Remote 'origin' 已存在，更新 URL..."
    git remote set-url origin "$REMOTE_URL"
else
    echo "添加新 remote 'origin'..."
    git remote add origin "$REMOTE_URL"
fi

echo "Remote URL: $REMOTE_URL"
echo ""

# ===== 步驟 6：推送 =====
echo "🚀 [步驟 6/6] 推送到 GitHub..."
echo "即將推送到：$REMOTE_URL"
echo ""

read -p "確認推送？(y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消推送"
    echo ""
    echo "提示：您可以稍後手動推送："
    echo "  git push -u origin $BRANCH"
    exit 1
fi

git push -u origin $BRANCH

echo ""
echo "========================================="
echo "  ✅ 上傳成功！"
echo "========================================="
echo ""
echo "🌐 GitHub Repository:"
echo "   https://github.com/$GITHUB_USERNAME/$REPO_NAME"
echo ""
echo "📚 接下來設定 GitHub Pages（可選）："
echo "   1. 進入 https://github.com/$GITHUB_USERNAME/$REPO_NAME/settings/pages"
echo "   2. Source: Deploy from a branch"
echo "   3. Branch: $BRANCH"
echo "   4. Folder: /docs/build/html"
echo "   5. Save"
echo ""
echo "📖 文檔將發布在："
echo "   https://$GITHUB_USERNAME.github.io/$REPO_NAME/"
echo ""
echo "========================================="
