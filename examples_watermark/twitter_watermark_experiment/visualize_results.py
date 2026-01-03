# -*- coding: utf-8 -*-
"""
Visualization Script for Twitter Experiment
Plots Radar Chart for LLM Evaluation Metrics
"""

import json
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from pathlib import Path
from typing import Dict, List

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Fonts
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

def load_results(json_path: Path):
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def plot_radar_chart(
    watermark_scores: Dict[str, float],
    control_scores: Dict[str, float],
    title: str = "Twitter Agent Evaluation (LLM)",
    save_path: str = None
):
    """Plot Radar Chart for 5 Dimensions"""
    
    # Dimensions
    dimensions = [
        'Logic\n逻辑连贯', 
        'Memory\n记忆准确', 
        'Stability\n人设稳定', 
        'Norms\n社会规范', 
        'Diversity\n语言多样'
    ]
    keys = ['logic_score', 'memory_score', 'stability_score', 'norms_score', 'diversity_score']
    
    # Get Values (normalize to 1-10 scale usually, but here we keep 1-10 or normalize to 0-1?)
    # Most radar charts look better 0-10 or 0-1. Let's stick to 0-10 since LLM gave 1-10.
    
    wm_values = [watermark_scores.get(k, 0) for k in keys]
    ctrl_values = [control_scores.get(k, 0) for k in keys]
    
    # Angles
    num_vars = len(dimensions)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    
    # Close Loop
    wm_values += wm_values[:1]
    ctrl_values += ctrl_values[:1]
    angles += angles[:1]
    
    # Create Plot
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
    ax.set_facecolor('#f8f9fa')
    
    # Watermark Group (Blue)
    ax.plot(angles, wm_values, 'o-', linewidth=2.5, label='Watermark Group', color='#2196F3', markersize=8)
    ax.fill(angles, wm_values, alpha=0.25, color='#2196F3')
    
    # Control Group (Orange)
    ax.plot(angles, ctrl_values, 's-', linewidth=2.5, label='Control Group', color='#FF5722', markersize=8)
    ax.fill(angles, ctrl_values, alpha=0.25, color='#FF5722')
    
    # Ticks & Labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(dimensions, fontsize=11)
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(['2', '4', '6', '8', '10'], fontsize=9)
    
    ax.grid(color='gray', linestyle='--', linewidth=0.5, alpha=0.7)
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=11)
    
    # Add values
    for angle, wm_val, ctrl_val in zip(angles[:-1], wm_values[:-1], ctrl_values[:-1]):
        ax.annotate(f'{wm_val:.1f}', xy=(angle, wm_val), 
                    xytext=(5, 5), textcoords='offset points',
                    fontsize=9, color='#1565C0', fontweight='bold')
        ax.annotate(f'{ctrl_val:.1f}', xy=(angle, ctrl_val), 
                    xytext=(5, -10), textcoords='offset points',
                    fontsize=9, color='#D84315', fontweight='bold')

    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        print(f"✅ Radar chart saved: {save_path}")
    
    # plt.show() # Cannot show in headless

def main():
    # Find latest results
    base_dir = PROJECT_ROOT / "outputs" / "twitter_exp"
    if not base_dir.exists():
        print("❌ No data found.")
        return

    latest_dir = max([d for d in base_dir.iterdir() if d.is_dir()], key=os.path.getmtime, default=None)
    if not latest_dir:
        print("❌ No data found.")
        return

    json_path = latest_dir / "evaluation_results.json"
    if not json_path.exists():
        print(f"❌ Results file not found: {json_path}")
        return
        
    print(f"📂 Loading results from: {json_path}")
    results = load_results(json_path)
    
    # Group Scores
    wm_scores = {"logic_score": [], "memory_score": [], "stability_score": [], "norms_score": [], "diversity_score": []}
    ctrl_scores = {"logic_score": [], "memory_score": [], "stability_score": [], "norms_score": [], "diversity_score": []}
    
    for item in results:
        group = item.get("group")
        metrics = item.get("metrics", {})
        
        target = wm_scores if group == "Watermark" else ctrl_scores
        
        for k in target.keys():
            if k in metrics:
                target[k].append(metrics[k])
    
    # Average
    def avg(lst):
        return sum(lst) / len(lst) if lst else 0
        
    wm_avg = {k: avg(v) for k, v in wm_scores.items()}
    ctrl_avg = {k: avg(v) for k, v in ctrl_scores.items()}
    
    print("\n📊 Average Scores:")
    print("Watermark:", wm_avg)
    print("Control:  ", ctrl_avg)
    
    # Plot
    output_path = latest_dir / "radar_chart_llm.png"
    plot_radar_chart(wm_avg, ctrl_avg, save_path=str(output_path))

if __name__ == "__main__":
    main()
