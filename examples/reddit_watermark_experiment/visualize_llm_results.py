
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import os

# Configuration
RESULTS_FILE = Path(__file__).parent / "evaluation_results.json"
OUTPUT_FILE = Path(__file__).parent / "llm_evaluation_radar.png"

# Metric keys mapping (5 from LLM + 1 manual)
METRICS_MAP = {
    "logic_score": "LC",          # Logic Coherence
    "memory_score": "MA",          # Memory Accuracy
    "stability_score": "CS",       # Character Stability
    "norms_score": "SN",           # Social Norms
    "diversity_score": "LD",       # Language Diversity
    "watermark_detection": "WD"    # Watermark Detection (manual)
}

def load_results():
    if not RESULTS_FILE.exists():
        print(f"[ERR] File not found: {RESULTS_FILE}")
        return []
    with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def process_data(results):
    # Initialize aggregators (exclude watermark_detection, will add manually)
    llm_keys = [k for k in METRICS_MAP.keys() if k != "watermark_detection"]
    groups = {
        "Watermarked": {k: [] for k in llm_keys},
        "Control": {k: [] for k in llm_keys}
    }

    for item in results:
        name = item.get('name', '')
        scores = item.get('evaluation', {})
        
        # Determine group
        if name.startswith('wm_'):
            group = "Watermarked"
        elif name.startswith('ctrl_'):
            group = "Control"
        else:
            continue # Skip unknown

        # Collect scores
        for key in llm_keys:
            if key in scores:
                groups[group][key].append(scores[key])
    
    # Calculate averages
    averages = {}
    for group_name, metrics in groups.items():
        averages[group_name] = []
        for key in llm_keys:
            vals = metrics[key]
            avg = np.mean(vals) if vals else 0
            averages[group_name].append(avg)
        
        # Add watermark detection score (manual: WM=10, Ctrl=0)
        if group_name == "Watermarked":
            averages[group_name].append(10.0)  # WD = 1.0 scaled to 10
        else:
            averages[group_name].append(0.0)   # WD = 0.0
            
    return averages

def create_radar_chart(averages):
    # 1. 数据准备
    # 确保顺序和原图一致: Watermark Rate, Memory Accuracy, Character Stability, Social Norms, Language Diversity, Logic Coherence
    labels = ['Watermark\nRate', 'Memory\nAccuracy', 'Character\nStability', 'Social\nNorms', 'Language\nDiversity', 'Logic\nCoherence']
    num_vars = len(labels)
    
    # 这里的 averages 需要按上述 labels 顺序重新整理数据
    # 原始顺序是: [LC, MA, CS, SN, LD, WD]
    # 映射到: 
    # WR -> WD (index 5)
    # PPC -> MA (index 1)
    # IISC -> CS (index 2)
    # FER -> SN (index 3)
    # SIAA -> LD (index 4)
    # OIAA -> LC (index 0)
    
    plot_data = {}
    for group, vals in averages.items():
        if len(vals) < 6:
            continue
        mapping = [vals[5], vals[1], vals[2], vals[3], vals[4], vals[0]] 
        plot_data[group] = [v / 10.0 for v in mapping] # 映射到 0-1

    # 计算角度
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1] # 闭合

    # 2. 创建画布
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    
    # 设置起始角度（正上方）和方向（顺时针）
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    # 3. 绘制六边形背景网格
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.spines['polar'].set_visible(False) # 隐藏最外圈的圆
    ax.grid(False) # 修复：重新添加此行以隐藏默认圆形网格
    
    # 修复：添加 padding 避免遮挡
    # 使用 set_rlabel_position 调整径向标签位置，或直接在 xticks 增加垂直距离是不行的，因为它是极坐标
    # 我们可以通过调整 labels 的位置或者简单地接受默认，通常 matplotlib 处理得还行，但用户要求“不要太近”
    # 这里的 tick_params pad 参数可以增加标签距离
    ax.tick_params(pad=20) 
    
    plt.xticks(angles[:-1], labels, color='black', size=11) 
    
    # 绘制 0.3, 0.7, 1.0 的六边形线
    # 用户要求: 底线变成 0.3, 0.7, 1.0
    grid_levels = [0.3, 0.7, 1.0] 
    for level in grid_levels:
        grid_values = [level] * (num_vars + 1)
        ax.plot(angles, grid_values, color='gray', linewidth=0.5, linestyle='-', alpha=0.5)
        # 添加刻度文字 (仅在上方显示，不显示1.0的文字避免重叠)
        if level < 1.0:
            ax.text(0, level, f'{level}', color='gray', size=8, ha='center', va='bottom')

    # 绘制从中心发散的 6 条轴线
    for angle in angles[:-1]:
        ax.plot([angle, angle], [0, 1], color='gray', linewidth=0.5, alpha=0.5)

    # 4. 绘图数据
    # 颜色参考: 严格使用用户指定的浅色配色
    # WM: Fill #ceebce, Edge #8ecf8e
    # Ctrl: Fill #fee4cb, Edge #fba95c
    colors = {
        "Watermarked": {"fill": "#ceebce", "edge": "#8ecf8e", "label": "Watermarked Group"}, # 修改图例中文
        "Control": {"fill": "#fee4cb", "edge": "#fba95c", "label": "Control Group"}      # 修改图例中文
    }

    for group_name, values in plot_data.items():
        data = values + values[:1]
        style = colors.get(group_name, {"fill": "gray", "edge": "black", "label": group_name})
        
        ax.plot(angles, data, color=style["edge"], linewidth=2, label=style["label"])
        ax.fill(angles, data, color=style["fill"], alpha=0.8) # 提高不透明度以显示更准确的填充色

    # 5. 细节美化
    ax.set_ylim(0, 1) # 统一刻度范围
    ax.set_yticklabels([]) # 隐藏默认的圆形刻度标签
    
    # 图例设置
    legend = plt.legend(loc='lower right', bbox_to_anchor=(1.15, 0.0), 
                        fontsize=10, frameon=True, edgecolor='black', 
                        handlelength=1.5, handleheight=1.0)
    legend.get_frame().set_linewidth(0.5)
    
    # Update output file name if desired or keep existing
    plt.savefig(OUTPUT_FILE, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"[OK] Radar chart saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    print("Loading results...")
    results = load_results()
    if results:
        print(f"Processing {len(results)} agents...")
        averages = process_data(results)
        print("Scores per group:")
        for g, vals in averages.items():
            print(f"  {g}: {vals}")
            
        print("Generating chart...")
        create_radar_chart(averages)
    else:
        print("No results to visualize.")

