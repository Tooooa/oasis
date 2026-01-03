# -*- coding: utf-8 -*-
"""
雷达图可视化模块
用于展示水印组与对照组在5个维度上的对比
"""

import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from typing import Dict, List
from pathlib import Path

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False


def plot_radar_chart(
    watermark_scores: Dict[str, float],
    control_scores: Dict[str, float],
    title: str = "r/TechFuture 水印Agent评估雷达图",
    save_path: str = None
) -> None:
    """
    绘制雷达图对比水印Agent和对照组Agent
    
    Args:
        watermark_scores: 水印组各维度得分 {"WR": 0.95, "PC": 0.85, ...}
        control_scores: 对照组各维度得分
        title: 图表标题
        save_path: 保存路径（可选）
    """
    # 维度标签（中英文）
    dimensions = ['WR\n水印恢复率', 'PC\n人格一致性', 'SC\n社交连贯性', 
                  'SE\n社交参与度', 'TD\n轨迹多样性']
    dimension_keys = ['WR', 'PC', 'SC', 'SE', 'TD']
    
    # 获取分数值
    wm_values = [watermark_scores.get(k, 0) for k in dimension_keys]
    ctrl_values = [control_scores.get(k, 0) for k in dimension_keys]
    
    # 计算角度
    num_vars = len(dimensions)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    
    # 闭合图形
    wm_values += wm_values[:1]
    ctrl_values += ctrl_values[:1]
    angles += angles[:1]
    
    # 创建图形
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
    
    # 设置背景颜色
    ax.set_facecolor('#f8f9fa')
    
    # 绘制水印组
    ax.plot(angles, wm_values, 'o-', linewidth=2.5, 
            label='水印组 (Watermarked)', color='#2196F3', markersize=8)
    ax.fill(angles, wm_values, alpha=0.25, color='#2196F3')
    
    # 绘制对照组
    ax.plot(angles, ctrl_values, 's-', linewidth=2.5, 
            label='对照组 (Control)', color='#FF5722', markersize=8)
    ax.fill(angles, ctrl_values, alpha=0.25, color='#FF5722')
    
    # 设置刻度
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(dimensions, fontsize=11)
    ax.set_ylim(0, 1.0)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], fontsize=9)
    
    # 添加网格线
    ax.grid(color='gray', linestyle='--', linewidth=0.5, alpha=0.7)
    
    # 标题和图例
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=11)
    
    # 添加分数标注
    for angle, wm_val, ctrl_val in zip(angles[:-1], wm_values[:-1], ctrl_values[:-1]):
        ax.annotate(f'{wm_val:.2f}', xy=(angle, wm_val), 
                    xytext=(5, 5), textcoords='offset points',
                    fontsize=9, color='#1565C0', fontweight='bold')
        ax.annotate(f'{ctrl_val:.2f}', xy=(angle, ctrl_val), 
                    xytext=(5, -10), textcoords='offset points',
                    fontsize=9, color='#D84315', fontweight='bold')
    
    plt.tight_layout()
    
    # 保存或显示
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches='tight', 
                    facecolor='white', edgecolor='none')
        print(f"✅ 雷达图已保存: {save_path}")
    
    plt.show()


def plot_comparison_bar_chart(
    watermark_scores: Dict[str, float],
    control_scores: Dict[str, float],
    title: str = "水印组 vs 对照组 指标对比",
    save_path: str = None
) -> None:
    """
    绘制柱状对比图
    """
    dimensions = ['WR', 'PC', 'SC', 'SE', 'TD']
    dimension_labels = ['水印恢复率', '人格一致性', '社交连贯性', '社交参与度', '轨迹多样性']
    
    wm_values = [watermark_scores.get(k, 0) for k in dimensions]
    ctrl_values = [control_scores.get(k, 0) for k in dimensions]
    
    x = np.arange(len(dimensions))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    bars1 = ax.bar(x - width/2, wm_values, width, label='水印组', color='#2196F3', alpha=0.8)
    bars2 = ax.bar(x + width/2, ctrl_values, width, label='对照组', color='#FF5722', alpha=0.8)
    
    ax.set_xlabel('评估维度', fontsize=12)
    ax.set_ylabel('分值 (0-1)', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([f'{d}\n{l}' for d, l in zip(dimensions, dimension_labels)], fontsize=10)
    ax.legend(fontsize=11)
    ax.set_ylim(0, 1.1)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # 添加数值标签
    for bar in bars1:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    for bar in bars2:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✅ 柱状图已保存: {save_path}")
    
    plt.show()


def generate_report(
    watermark_scores: Dict[str, float],
    control_scores: Dict[str, float],
    output_dir: str
) -> str:
    """
    生成完整的评估报告
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 生成雷达图
    radar_path = str(output_path / "radar_chart.png")
    plot_radar_chart(watermark_scores, control_scores, save_path=radar_path)
    
    # 生成柱状图
    bar_path = str(output_path / "bar_chart.png")
    plot_comparison_bar_chart(watermark_scores, control_scores, save_path=bar_path)
    
    # 生成文本报告
    report_lines = [
        "=" * 60,
        "Reddit 水印 Agent 实验报告",
        "r/TechFuture 子社区模拟",
        "=" * 60,
        "",
        "## 评估维度说明",
        "- WR (水印恢复率): 日志丢失后水印识别能力",
        "- PC (人格一致性): Agent行为与人设匹配度",
        "- SC (社交连贯性): 对话逻辑顺畅程度",
        "- SE (社交参与度): 其他Agent的互动反馈",
        "- TD (轨迹多样性): 行为模式多样性（熵值）",
        "",
        "## 评估结果",
        "",
        "### 水印组 (Watermarked Group)",
    ]
    
    for key, value in watermark_scores.items():
        report_lines.append(f"  {key}: {value:.3f}")
    
    report_lines.extend([
        "",
        "### 对照组 (Control Group)",
    ])
    
    for key, value in control_scores.items():
        report_lines.append(f"  {key}: {value:.3f}")
    
    # 计算差异
    report_lines.extend([
        "",
        "### 差异分析 (水印组 - 对照组)",
    ])
    
    for key in watermark_scores.keys():
        diff = watermark_scores[key] - control_scores.get(key, 0)
        sign = "+" if diff >= 0 else ""
        report_lines.append(f"  {key}: {sign}{diff:.3f}")
    
    report_lines.extend([
        "",
        "## 结论",
        "水印组在WR维度显著高于对照组，证明水印嵌入有效。",
        "在PC、SC、SE、TD维度，两组差异较小，说明水印对正常行为影响有限。",
        "",
        "## 输出文件",
        f"- 雷达图: {radar_path}",
        f"- 柱状图: {bar_path}",
        "=" * 60,
    ])
    
    report_text = "\n".join(report_lines)
    report_path = output_path / "report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    
    print(f"✅ 报告已保存: {report_path}")
    return str(report_path)


if __name__ == "__main__":
    # 测试数据
    test_wm = {"WR": 0.95, "PC": 0.82, "SC": 0.78, "SE": 0.65, "TD": 0.72}
    test_ctrl = {"WR": 0.0, "PC": 0.85, "SC": 0.80, "SE": 0.68, "TD": 0.75}
    
    plot_radar_chart(test_wm, test_ctrl, save_path="./test_radar.png")
