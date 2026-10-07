import matplotlib.pyplot as plt
import numpy as np

# 1. 準備資料
categories = ['Imp', 'Exp', 'Prog', 'Obs']

# 左圖資料 (Panel 1)
p1_power = [0.11, 0.26, 0.46, 0.51]
p1_stress = [0.2, 0.23, 0.57, 0.57]
p1_oxygen = [0, 0.4, 0.6, 0.66]
p1_overall = [0.1, 0.3, 0.54, 0.58]

# 右圖資料 (Panel 2)
p2_power = [0.1, 0.1, 0.23, 0.4]
p2_stress = [0.05, 0.3, 0.63, 0.7]
p2_oxygen = [0.18, 0.43, 0.65, 0.73]
p2_overall = [0.11, 0.28, 0.5, 0.61]

# 2. X 軸位置與柱體寬度
x = np.arange(len(categories))
width = 0.18  # 1. 縮小寬度，讓柱體變細並留出組別間距

# 3. 建立 1 列 2 欄的圖表
fig, axes = plt.subplots(1, 2, figsize=(15, 5.5), sharey=True)

# ------------------ 左邊 Panel (axes[0]) ------------------
# 2. 套用 4 支柱子對齊 x 軸中心的偏移量
r1 = axes[0].bar(x - 1.5*width, p1_power,   width, label='Power')
r2 = axes[0].bar(x - 0.5*width, p1_stress,  width, label='Stress')
r3 = axes[0].bar(x + 0.5*width, p1_oxygen,  width, label='Oxygen')
r4 = axes[0].bar(x + 1.5*width, p1_overall, width, label='Overall')

axes[0].set_ylabel('Value')
axes[0].set_title('Constrained Setting Performance (Left)')
axes[0].set_xticks(x)
axes[0].set_xticklabels(categories)
axes[0].legend()

# 數字標籤調整字體大小 (fontsize=8)，避免標籤互相重疊
axes[0].bar_label(r1, padding=3, fmt='%.2f', fontsize=8)
axes[0].bar_label(r2, padding=3, fmt='%.2f', fontsize=8)
axes[0].bar_label(r3, padding=3, fmt='%.2f', fontsize=8)
axes[0].bar_label(r4, padding=3, fmt='%.2f', fontsize=8)

# ------------------ 右邊 Panel (axes[1]) ------------------
r5 = axes[1].bar(x - 1.5*width, p2_power,   width, label='Power')
r6 = axes[1].bar(x - 0.5*width, p2_stress,  width, label='Stress')
r7 = axes[1].bar(x + 0.5*width, p2_oxygen,  width, label='Oxygen')
r8 = axes[1].bar(x + 1.5*width, p2_overall, width, label='Overall')

axes[1].set_title('Open-Ended Setting Performance (Right)')
axes[1].set_xticks(x)
axes[1].set_xticklabels(categories)
axes[1].legend()

axes[1].bar_label(r5, padding=3, fmt='%.2f', fontsize=8)
axes[1].bar_label(r6, padding=3, fmt='%.2f', fontsize=8)
axes[1].bar_label(r7, padding=3, fmt='%.2f', fontsize=8)
axes[1].bar_label(r8, padding=3, fmt='%.2f', fontsize=8)

plt.tight_layout()
plt.show()