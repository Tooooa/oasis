
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import os

# Configuration
# User provided path: D:\_Development\Agentguide\OASIS\oasis\outputs\twitter_exp\20260101_152409\evaluation_results.json
# Using raw string for Windows path or Path object
RESULTS_FILE = Path(r"D:\_Development\Agentguide\OASIS\oasis\outputs\twitter_exp\20260101_152409\evaluation_results.json")
OUTPUT_FILE = RESULTS_FILE.parent / "radar_chart.png"

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
    # Initialize aggregators
    llm_keys = [k for k in METRICS_MAP.keys() if k != "watermark_detection"]
    groups = {
        "Watermarked": {k: [] for k in llm_keys},
        "Control": {k: [] for k in llm_keys}
    }

    for item in results:
        # Agent names in Twitter exp might follow different pattern, e.g., "Geek_wm_0", "Geek_ctrl_5"
        name = item.get('name', '')
        # FIX: The JSON uses 'metrics' key, not 'evaluation'
        scores = item.get('metrics', {})
        
        # Determine group based on name containing '_wm_' or '_ctrl_'
        if '_wm_' in name:
            group = "Watermarked"
        elif '_ctrl_' in name:
            group = "Control"
        else:
            # Fallback checks if user used different naming in previous runs
            if name.startswith('wm_'):
                group = "Watermarked"
            elif name.startswith('ctrl_'):
                group = "Control"
            else:
                continue 

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
    labels = ['Watermark\nRate', 'Memory\nAccuracy', 'Character\nStability', 'Social\nNorms', 'Language\nDiversity', 'Logic\nCoherence']
    num_vars = len(labels)
    
    # averages 映射顺序: [LC, MA, CS, SN, LD, WD] -> [WD, MA, CS, SN, LD, LC]
    # WD (idx 5), MA (idx 1), CS (idx 2), SN (idx 3), LD (idx 4), LC (idx 0)
    
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
    ax.spines['polar'].set_visible(False) # 隐藏最外圈的圆
    ax.grid(False) # 隐藏默认圆形网格
    
    # 设置顶点标签
    # 增加 padding 避免文字太近
    ax.tick_params(pad=20)
    plt.xticks(angles[:-1], labels, color='black', size=11)
    
    # 绘制 0.3, 0.7, 1.0 的六边形线
    grid_levels = [0.3, 0.7, 1.0]
    for level in grid_levels:
        grid_values = [level] * (num_vars + 1)
        ax.plot(angles, grid_values, color='gray', linewidth=0.5, linestyle='-', alpha=0.5)
        if level < 1.0:
            ax.text(0, level, f'{level}', color='gray', size=8, ha='center', va='bottom')

    # 绘制轴线
    for angle in angles[:-1]:
        ax.plot([angle, angle], [0, 1], color='gray', linewidth=0.5, alpha=0.5)

    # 4. 绘图数据
    # WM: Fill #ceebce, Edge #8ecf8e
    # Ctrl: Fill #fee4cb, Edge #fba95c
    colors = {
        "Watermarked": {"fill": "#ceebce", "edge": "#8ecf8e", "label": "Watermarked Group"},
        "Control": {"fill": "#fee4cb", "edge": "#fba95c", "label": "Control Group"}
    }

    for group_name, values in plot_data.items():
        data = values + values[:1]
        style = colors.get(group_name, {"fill": "gray", "edge": "black", "label": group_name})
        
        ax.plot(angles, data, color=style["edge"], linewidth=2, label=style["label"])
        ax.fill(angles, data, color=style["fill"], alpha=0.8)

    # 5. 细节美化
    ax.set_ylim(0, 1)
    ax.set_yticklabels([])
    
    # 图例
    legend = plt.legend(loc='lower right', bbox_to_anchor=(1.15, 0.0), 
                        fontsize=10, frameon=True, edgecolor='black', 
                        handlelength=1.5, handleheight=1.0)
    legend.get_frame().set_linewidth(0.5)
    
    plt.savefig(OUTPUT_FILE, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"[OK] Radar chart saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    print(f"Loading results from: {RESULTS_FILE}")
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
