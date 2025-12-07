#!/bin/bash
# 一鍵修復大檔案問題並重新上傳

set -e

echo "========================================="
echo "  🔧 修復大檔案問題"
echo "========================================="
echo ""

# 步驟 1：移除大檔案
echo "📁 [步驟 1/5] 從 Git 索引移除大檔案..."
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

echo "✅ 大檔案已從 git 索引移除（但保留在本地）"
echo ""

# 步驟 2：配置 Git
echo "⚙️  [步驟 2/5] 配置 Git 以處理大型推送..."
git config http.postBuffer 524288000  # 500MB buffer
git config http.timeout 300           # 5 分鐘 timeout
git config http.lowSpeedLimit 0       # 禁用低速限制
git config http.lowSpeedTime 999999   # 禁用低速超時

echo "✅ Git 配置已更新"
echo ""

# 步驟 3：提交變更
echo "📝 [步驟 3/5] 提交變更..."
git add .gitignore
git commit -m "移除大檔案，減少上傳大小

- 從 git 移除大型文字目錄檔案（.txt，~680MB）
- 從 git 移除大型 .mat 檔案（>30MB，保留小型檔案）
- 從 git 移除 PDF 和 zip 檔案
- 從 git 移除 Sphinx doctrees 快取
- 更新 .gitignore 防止未來加入

檔案仍保留在本地工作目錄，但不上傳到 GitHub

預計減少上傳大小：200MB → 30-50MB

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com)"

echo "✅ 變更已提交"
echo ""

# 步驟 4：檢查上傳大小
echo "📊 [步驟 4/5] 檢查上傳大小..."
echo ""
git count-objects -vH
echo ""

# 估算實際上傳大小
echo "📦 準備上傳的檔案數量："
git ls-files | wc -l
echo ""

# 步驟 5：推送
echo "🚀 [步驟 5/5] 推送到 GitHub..."
echo ""
echo "⚠️  即將推送到 GitHub，確認繼續？"
read -p "按 Enter 繼續，Ctrl+C 取消..." dummy

git push -u origin master

echo ""
echo "========================================="
echo "  ✅ 上傳成功！"
echo "========================================="
echo ""
echo "🎉 問題已解決！大檔案已從 git 移除。"
echo ""
echo "📝 注意事項："
echo "   - 大檔案仍保留在本地工作目錄"
echo "   - 未來新增檔案時，.gitignore 會自動忽略大檔案"
echo "   - 如需上傳大檔案，請考慮使用 Git LFS"
echo ""
echo "========================================="
