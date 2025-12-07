#!/bin/bash
# GitHub 上傳準備腳本
# 用途：清理快取、檢查大檔案、驗證上傳內容

set -e

echo "========================================="
echo "  EEPAS GitHub 上傳準備腳本"
echo "========================================="
echo ""

# 步驟 1：清理 Python 快取
echo "📁 [步驟 1/5] 清理 Python 快取..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
echo "✅ Python 快取已清理"
echo ""

# 步驟 2：檢查大檔案
echo "📊 [步驟 2/5] 檢查大檔案（>50MB）..."
large_files=$(find . -type f -size +50M 2>/dev/null | grep -v ".git" || true)
if [ -z "$large_files" ]; then
    echo "✅ 沒有超過 50MB 的檔案"
else
    echo "⚠️  發現大檔案："
    find . -type f -size +50M -exec ls -lh {} \; 2>/dev/null | grep -v ".git"
    echo ""
    echo "⚠️  建議：考慮使用 Git LFS 或外部儲存"
fi
echo ""

# 步驟 3：檢查數據檔案大小
echo "📦 [步驟 3/5] 檢查數據檔案大小..."
echo "data/ 目錄中的 .mat 檔案："
find data -name "*.mat" -exec du -h {} \; 2>/dev/null | sort -rh | head -10
total_data_size=$(du -sh data 2>/dev/null | awk '{print $1}')
echo ""
echo "data/ 總大小：$total_data_size"
echo ""

# 步驟 4：檢查 Sphinx 文檔
echo "📚 [步驟 4/5] 檢查 Sphinx 文檔..."
if [ -d "docs/build/html" ]; then
    docs_size=$(du -sh docs/build/html | awk '{print $1}')
    echo "✅ Sphinx HTML 已編譯：$docs_size"
else
    echo "⚠️  Sphinx HTML 尚未編譯"
    echo "   執行：cd docs && make html"
fi
echo ""

# 步驟 5：預覽將被上傳的檔案
echo "📋 [步驟 5/5] 預覽將被上傳的檔案（前 100 個）..."
echo ""
echo "=== 新增的未追蹤檔案 ==="
git status --short | grep "^??" | head -30
echo ""

echo "=== 已修改的檔案 ==="
git status --short | grep "^ M" | head -30
echo ""

echo "=== 將被忽略的檔案（前 30 個）==="
git status --ignored --short 2>/dev/null | head -30
echo ""

# 總結
echo "========================================="
echo "  準備完成！"
echo "========================================="
echo ""
echo "📊 檔案統計："
echo "   - Python 檔案：$(find . -name "*.py" -not -path "./.git/*" -not -path "./__pycache__/*" | wc -l)"
echo "   - Jupyter Notebooks：$(find . -name "*.ipynb" -not -path "./.git/*" -not -path "./docs/build/*" | wc -l)"
echo "   - 配置檔案：$(find . -name "config*.json" -not -path "./.git/*" | wc -l)"
echo "   - 數據檔案：$(find data -name "*.mat" 2>/dev/null | wc -l)"
echo ""

# 下一步指示
echo "🚀 下一步操作："
echo ""
echo "1. 檢查 .gitignore 是否正確："
echo "   cat .gitignore"
echo ""
echo "2. 檢查將被提交的檔案："
echo "   git status"
echo ""
echo "3. 添加所有檔案："
echo "   git add ."
echo ""
echo "4. 提交變更："
echo '   git commit -m "準備 GitHub 上傳：精簡專案，保留 Sphinx 必要內容"'
echo ""
echo "5. 推送到 GitHub："
echo "   git remote add origin https://github.com/YOUR_USERNAME/EEPAS_Taiwan.git"
echo "   git push -u origin master"
echo ""
echo "========================================="
