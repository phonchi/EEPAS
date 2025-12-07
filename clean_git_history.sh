#!/bin/bash
# 從 Git 歷史中徹底移除大檔案

set -e

echo "========================================="
echo "  🔧 從 Git 歷史中徹底移除大檔案"
echo "========================================="
echo ""

echo "⚠️  警告：此操作會重寫 Git 歷史！"
echo "⚠️  建議：先備份整個目錄"
echo ""
read -p "確認繼續？(y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消操作"
    exit 1
fi

echo ""
echo "📁 正在從 Git 歷史中移除大檔案..."
echo ""

# 使用 git filter-branch 或 git filter-repo 移除大檔案
# 方法 1: 使用 git filter-branch（內建，但較慢）

git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch \
    python_src/data/HORUS_Ita_Catalog.txt \
    python_src/data/HORUS_Ita_Catalog_o.txt \
    python_src/data/HORUS_Ita_DataOrigin.txt \
    python_src/data/HORUS_Ita_DataOrigin_o.txt \
    python_src/data/HORUS_Italy_polygon_filtered.mat \
    python_src/data/HORUS_Italy_RDN2008_polygon_filtered.mat \
    python_src/data/HORUS_Italy_filtered.mat \
    python_src/data/HORUS_Italy_RDN2008_filtered.mat \
    python_src/test_data/HORUS_Ita_Catalog.txt \
    python_src/docs/build.zip \
    "python_src/analysis/[2024] psi.pdf" \
    python_src/ggad123.pdf' \
  --prune-empty --tag-name-filter cat -- --all

echo ""
echo "✅ 大檔案已從歷史中移除"
echo ""

# 清理 reflog 和垃圾回收
echo "🧹 正在清理 Git 倉庫..."
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo "✅ Git 倉庫已清理"
echo ""

# 顯示新的倉庫大小
echo "📊 新的倉庫大小："
git count-objects -vH
echo ""

echo "========================================="
echo "  ✅ 清理完成！"
echo "========================================="
echo ""
echo "🚀 下一步：強制推送到 GitHub"
echo ""
echo "執行："
echo "  git push -f origin master"
echo ""
echo "⚠️  注意：使用 -f (force) 會覆蓋遠端歷史"
echo "========================================="
