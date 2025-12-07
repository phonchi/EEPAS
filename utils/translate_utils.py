#!/usr/bin/env python3
"""
Batch translation script for EEPAS utils directory
Translates all Traditional Chinese comments and docstrings to English
"""

import re
import os

def translate_file(filepath, translations):
    """Apply translations to a file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    for old, new in translations:
        content = content.replace(old, new)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f'Translated: {filepath}')

# Define all translations for all files
translations = {
    'data_loader.py': [
        ('        # 判斷區域類型\n        # 預設：testing region 總是 grid',
         '        # Determine region type\n        # Default: testing region is always grid'),
        ('        # neighborhood region 類型判斷\n        # 若為 regionConfig 中明確指定，使用指定值\n        # 否則根據數據形狀自動判斷',
         '        # Determine neighborhood region type\n        # If explicitly specified in regionConfig, use that value\n        # Otherwise auto-detect based on data shape'),
    ],

    'catalog_processor.py': [
        ('"""\nCatalogProcessor - 地震目錄預處理工具類\n提供統一的地震目錄品質控制、時間轉換和篩選功能\n"""',
         '"""\nCatalogProcessor - Seismic Catalog Preprocessing Utility Class\nProvides unified earthquake catalog quality control, time conversion, and filtering functions\n"""'),
        ('def decyear(date_array):\n    """\n    將日期轉換為十進制年份\n\n    Args:\n        date_array: Nx6 矩陣 [年, 月, 日, 時, 分, 秒]\n\n    Returns:\n        np.array: 十進制年份\n    """',
         'def decyear(date_array):\n    """\n    Convert date to decimal year.\n\n    Args:\n        date_array: Nx6 matrix [year, month, day, hour, minute, second]\n\n    Returns:\n        np.array: Decimal year\n    """'),
        ('        # 處理異常的秒數值（有些數據集可能有 second >= 60）\n        # 將超過 60 的秒數轉換為分鐘',
         '        # Handle anomalous second values (some datasets may have second >= 60)\n        # Convert seconds over 60 to minutes'),
        ('        # 處理異常的分鐘值', '        # Handle anomalous minute values'),
        ('        # 處理異常的小時值', '        # Handle anomalous hour values'),
        ('        # 計算該年的第幾天（使用總秒數方法以處理跨月問題）',
         '        # Calculate day of year (using total seconds method to handle month overflow)'),
        ('            # 如果日期仍然無效（例如月份溢出），使用近似值\n            # 這是容錯處理，確保程序能繼續運行',
         '            # If date is still invalid (e.g. month overflow), use approximation\n            # This is fault-tolerant handling to ensure program continues'),
        ('            # 添加總秒數', '            # Add total seconds'),
        ('class CatalogProcessor:\n    """地震目錄預處理工具類"""',
         'class CatalogProcessor:\n    """Seismic catalog preprocessing utility class"""'),
    ],
}

# Apply translations
base_dir = '/home/math/EEPAS_Taiwan-main/src/python_src/utils'
for filename, trans_list in translations.items():
    filepath = os.path.join(base_dir, filename)
    if os.path.exists(filepath):
        translate_file(filepath, trans_list)

print('\nCompleted batch translation')
