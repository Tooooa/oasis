
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import os

# Configuration
# Modified for portable handoff
REDDIT_RESULTS = Path("reddit_results.json")
TWITTER_RESULTS = Path("twitter_results.json")
OUTPUT_FILE = Path("combined_radar_chart.png")
# OUTPUT_FILE = Path("combined_radar_chart_original.png")

# Set Font to Times New Roman
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']

# Metric keys mapping
METRICS_MAP = {
    "logic_score": "LC",
    "memory_score": "MA",
    "stability_score": "CS",
    "norms_score": "SN",
    "diversity_score": "LD",
    "watermark_detection": "WD"
}

def load_results(path):
    if not path.exists():
        print(f"[ERR] File not found: {path}")
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def process_data(results):
    llm_keys = [k for k in METRICS_MAP.keys() if k != "watermark_detection"]
    groups = {
        "Watermarked": {k: [] for k in llm_keys},
        "Control": {k: [] for k in llm_keys}
    }

    for item in results:
        name = item.get('name', '')
        # Handle both 'evaluation' (Reddit) and 'metrics' (Twitter) keys
        scores = item.get('evaluation') or item.get('metrics', {})
        
        # Determine group
        if '_wm_' in name or name.startswith('wm_'):
            group = "Watermarked"
        elif '_ctrl_' in name or name.startswith('ctrl_'):
            group = "Control"
        else:
            continue 

        for key in llm_keys:
            if key in scores:
                groups[group][key].append(scores[key])
    
    averages = {}
    for group_name, metrics in groups.items():
        averages[group_name] = []
        for key in llm_keys:
            vals = metrics[key]
            avg = np.mean(vals) if vals else 0
            averages[group_name].append(avg)
        
        # Add watermark detection score (manual: WM=10, Ctrl=0)
        if group_name == "Watermarked":
            averages[group_name].append(10.0) 
        else:
            averages[group_name].append(0.0)   
            
    return averages

def draw_radar_subplot(ax, averages, title):
    # Data preparation
    labels = ['Watermark\nRate', 'Memory\nAccuracy', 'Character\nStability', 'Social\nNorms', 'Language\nDiversity', 'Logic\nCoherence']
    num_vars = len(labels)
    
    plot_data = {}
    for group, vals in averages.items():
        if len(vals) < 6: continue
        # [LC, MA, CS, SN, LD, WD] -> [WD, MA, CS, SN, LD, LC]
        mapping = [vals[5], vals[1], vals[2], vals[3], vals[4], vals[0]] 
        plot_data[group] = [v / 10.0 for v in mapping]

    # Angles
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1] 

    # Grid Setup
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.spines['polar'].set_visible(False)
    ax.grid(False) 
    
    # Ticks & Labels
    # 仅针对 Watermark Rate (index 0) 和 Social Norms (index 3) 减少距离
    # 其他标签保持默认
    labels_default = ['Watermark\nRate', 'Memory\nAccuracy', 'Character\nStability', 'Social\nNorms', 'Language\nDiversity', 'Logic\nCoherence']
    
    # 设置默认 padding
    ax.tick_params(pad=15)
    plt.sca(ax)
    
    # 先设置空标签，然后手动添加
    plt.xticks(angles[:-1], [''] * num_vars)
    
    # 手动添加标签，调整特定标签的位置
    for i, (angle, label) in enumerate(zip(angles[:-1], labels_default)):
        # Watermark Rate (顶部) 和 Social Norms (底部) 往里移动
        if i == 0:  # Watermark Rate
            # 用户要求: 往下移动 (靠近圆心)
            ax.text(angle, 1.08, label, ha='center', va='bottom', size=10, color='black', fontweight='bold')
        elif i == 3:  # Social Norms
            # 用户要求: 往上移动 (靠近圆心)
            ax.text(angle, 1.08, label, ha='center', va='top', size=10, color='black', fontweight='bold')
        else:
            # 其他标签保持较远距离
            ax.text(angle, 1.20, label, ha='center', va='center', size=10, color='black', fontweight='bold')
    
    # Hexagonal Grid lines
    grid_levels = [0.3, 0.7, 1.0]
    for level in grid_levels:
        grid_values = [level] * (num_vars + 1)
        ax.plot(angles, grid_values, color='gray', linewidth=0.5, linestyle='-', alpha=0.5)
        if level < 1.0:
            ax.text(0, level, f'{level}', color='gray', size=8, ha='center', va='bottom')

    # Axis lines
    for angle in angles[:-1]:
        ax.plot([angle, angle], [0, 1], color='gray', linewidth=0.5, alpha=0.5)

    # Plot Data
    colors = {
        "Watermarked": {"fill": "#ceebce", "edge": "#8ecf8e", "label": "Watermarked"}, # Groups removed
        "Control": {"fill": "#fee4cb", "edge": "#fba95c", "label": "No-Watermark"}      # Control -> No-Watermark
    }

    for group_name, values in plot_data.items():
        data = values + values[:1]
        style = colors.get(group_name, {"fill": "gray", "edge": "black", "label": group_name})
        ax.plot(angles, data, color=style["edge"], linewidth=2, label=style["label"])
        ax.fill(angles, data, color=style["fill"], alpha=0.8)

    ax.set_ylim(0, 1)
    ax.set_yticklabels([])
    # Re-enable title as requested (moved lower), increased fontsize
    ax.set_title(title, y=-0.23, fontsize=16, fontweight='bold')
    
    # Legend
    legend = ax.legend(loc='lower right', bbox_to_anchor=(1.3, -0.1), 
                       fontsize=9, frameon=True, edgecolor='black', 
                       handlelength=1.5, handleheight=1.0,
                       prop={'weight': 'bold', 'size': 9}) # Bold legend

def main():
    print("Loading data...")
    reddit_data = load_results(REDDIT_RESULTS)
    twitter_data = load_results(TWITTER_RESULTS)
    
    if not reddit_data or not twitter_data:
        print("Failed to load data.")
        return

    print("Processing data...")
    reddit_avg = process_data(reddit_data)
    twitter_avg = process_data(twitter_data)
    
    print("Generating combined chart...")
    # Create Figure with 2 subplots
    fig, axes = plt.subplots(1, 2, figsize=(12, 6), subplot_kw=dict(polar=True))
    
    draw_radar_subplot(axes[0], reddit_avg, "(a) Reddit Scenario")
    draw_radar_subplot(axes[1], twitter_avg, "(b) Twitter Scenario")
    
    plt.tight_layout()
    plt.savefig(OUTPUT_FILE, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"[OK] Combined radar chart saved to: {OUTPUT_FILE}")
    
    # Save as PDF
    pdf_file = OUTPUT_FILE.with_suffix('.pdf')
    plt.savefig(pdf_file, format='pdf', bbox_inches='tight')
    print(f"[OK] PDF saved to: {pdf_file}")

if __name__ == "__main__":
    main()
