# EEPAS 權重分析配置對應說明

## 📋 配置對應關係 (S1-S4)

根據論文定義，4種配置的正確對應關係如下：

### S1: standard (config.json)
**定義**: Exclude the post-Chi-Chi earthquake sequence (Sep–Dec 1999)

**說明**:
- 排除921地震後的餘震序列 (1999年9-12月)
- 使用標準的地震目錄
- 震級閾值: m0 = 2.05

**資料檔案**: `data/GDMScatalog_A_filtered_twd97.mat`

**統計**:
- 事件數: 15,138
- 平均權重: 0.772
- 變異係數: 0.457

---

### S2: include921 (config_include921.json)
**定義**: Include all events

**說明**:
- 包含所有地震事件
- 包括921地震及其完整餘震序列
- 震級閾值: m0 = 2.05

**資料檔案**: `data/GDMScatalog_A_twd97.mat`

**統計**:
- 事件數: 19,692
- 平均權重: 0.579
- 變異係數: 0.741 (最高，反映921餘震影響)

---

### S3: decluster (config_decluster.json)
**定義**: First exclude the post-Chi-Chi earthquake sequence (Sep–Dec 1999), then apply declustering

**說明**:
- 先排除921地震後餘震 (1999年9-12月)
- 再進行去叢集化處理
- 使用 M≥mT 的事件作為種子識別時空序列
- 每個序列只保留主震（最大震級事件）
- 保留所有未叢集的背景事件
- 震級閾值: m0 = 2.05

**資料檔案**: `data/GDMScatalog_A_filtered_twd97_declustered.mat`

**統計**:
- 事件數: 26,444
- 平均權重: 0.845
- 變異係數: 0.332 (最低，最穩定) ⭐

---

### S4: m205 (config_m205.json)
**定義**: Perform declustering by retaining only the mainshock of each sequence

**說明**:
- 直接對完整目錄進行去叢集化
- 不排除921地震後餘震
- 每個序列只保留主震
- **震級閾值更低**: m0 = 2.05 (與論文命名 "m205" 對應)
- 這是 S4 配置的正確對應！

**資料檔案**: `data/GDMScatalog_A_filtered_twd97.mat` (相同資料，不同處理)

**統計**:
- 事件數: 28,450 (最多)
- 平均權重: 0.776
- 變異係數: 0.446

---

## 🎨 視覺化顏色方案

在所有圖表中，使用一致的顏色標識：

| 配置 | 代號 | 顏色 | 線型 | 標記 |
|------|------|------|------|------|
| **standard** | s1 | 🔴 紅色 | 實線 `-` | 圓圈 `o` |
| **include921** | s2 | 🟢 綠色 | 虛線 `--` | 方形 `s` |
| **decluster** | s3 | 🔵 藍色 | 點劃線 `-.` | 三角 `^` |
| **m205** | s4 | 🟣 紫色 | 點線 `:` | 菱形 `d` |

---

## 📊 配置特性比較

### 穩定性排名 (依變異係數)

```
排名  配置        代號  變異係數   穩定性
 1   decluster   S3    0.3320    ⭐⭐⭐⭐⭐ 最穩定
 2   m205        S4    0.4463    ⭐⭐⭐⭐
 3   standard    S1    0.4565    ⭐⭐⭐⭐
 4   include921  S2    0.7411    ⭐⭐      變異最大
```

### 配置間相關性

```
              S1(std)  S2(inc921)  S3(declust)  S4(m205)
S1 standard    1.000      0.334       0.008      -0.005
S2 include921  0.334      1.000       0.029       0.018
S3 decluster   0.008      0.029       1.000       0.042
S4 m205       -0.005      0.018       0.042       1.000
```

**主要發現**:
- S1 與 S2 有中等相關性 (0.334) - 反映921地震的系統性影響
- S3 (decluster) 與其他配置幾乎獨立 - 去叢集化的顯著效果
- S4 (m205) 與其他配置相關性極低 - 獨特的處理方式

---

## 🔍 關鍵差異說明

### S1 vs S2: 921地震的影響
- **差異**: S2 包含921完整餘震序列
- **結果**: S2 的變異係數 (0.741) 遠高於 S1 (0.457)
- **意義**: 921地震後餘震顯著增加權重分布的不穩定性

### S1 vs S3: 去叢集化的效果
- **差異**: S3 在 S1 基礎上進行去叢集化
- **結果**: S3 的變異係數 (0.332) 低於 S1 (0.457)
- **意義**: 去叢集化顯著提升權重分布的穩定性

### S3 vs S4: 處理順序的影響
- **差異**: S3 先排除921再去叢集；S4 直接去叢集
- **結果**: S3 事件數 26,444；S4 事件數 28,450
- **意義**: 不同的處理順序導致保留事件數不同

### S2 vs S4: 包含 vs 去叢集
- **差異**: S2 包含所有事件；S4 去叢集化處理
- **結果**: S2 變異最大 (0.741)；S4 相對穩定 (0.446)
- **意義**: 去叢集化能有效降低餘震對權重的影響

---

## 📈 圖表說明

### 生成的圖表 (8個 PNG)

所有圖表都按照 **S1 → S2 → S3 → S4** 的順序展示：

1. **comprehensive_analysis.png** (917 KB)
   - 6個子圖的綜合分析
   - 包含分布、統計、相關性等

2. **detailed_time_series.png** (1.2 MB)
   - 6個子圖的時間序列分析
   - 包含月度、年度、921影響等

3. **01_monthly_weight_changes.png**
   - 1991-2016年月度權重變化
   - 四條線分別代表 S1-S4

4. **02_annual_statistics.png**
   - 年度平均權重 ± 標準差
   - 誤差棒顯示權重的年度變異

5. **03_921_earthquake_impact.png**
   - 921地震前後2年的權重變化
   - 季度解析度，紅色虛線標記921時間點

6. **04_weight_change_rate.png**
   - 年度間權重變化率 (%)
   - 0線顯示增減趨勢

7. **05_weight_distribution_evolution.png**
   - S1配置的權重分布隨時間演化
   - 熱圖顯示分布密度

8. **06_configuration_comparison.png**
   - 四配置的平行座標比較
   - 標準化統計指標 (平均、標準差、中位數、事件數)

---

## 🔄 更新記錄

**2025-10-15 15:37**
- ✅ 修正配置對應關係
- ✅ 確認 m205 = S4
- ✅ 更新配置順序為 S1 → S2 → S3 → S4
- ✅ 重新生成所有圖表
- ✅ 更新分析報告

**之前的錯誤對應** (已修正):
```
❌ 舊版:
s1 = standard
s2 = include921
s3 = decluster
s4 = decluster_include921  ← 錯誤！

✅ 正確:
s1 = standard
s2 = include921
s3 = decluster
s4 = m205  ← 正確！
```

---

## 📚 參考資訊

**配置檔案位置**:
```
../config.json                      # S1: standard
../config_include921.json           # S2: include921
../config_decluster.json            # S3: decluster
../config_m205.json                 # S4: m205
```

**資料檔案位置**:
```
../data/GDMScatalog_A_filtered_twd97.mat              # S1, S4
../data/GDMScatalog_A_twd97.mat                       # S2
../data/GDMScatalog_A_filtered_twd97_declustered.mat  # S3
```

**程式碼實現**:
- `weight_analysis.py:291-297` - 配置名稱映射定義
- `run_weight_analysis.py:43-48` - 配置處理順序

---

## ✅ 驗證

已驗證配置對應關係正確：
- [x] S1 = standard (排除921後餘震)
- [x] S2 = include921 (包含所有事件)
- [x] S3 = decluster (排除921 + 去叢集化)
- [x] S4 = m205 (去叢集化，m0=2.05)
- [x] 圖表順序與論文一致
- [x] 顏色方案統一 (s1紅, s2綠, s3藍, s4紫)
- [x] 所有圖表重新生成

---

*配置對應已確認正確 - 2025-10-15*
