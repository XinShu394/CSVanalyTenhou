"""Rate变化分析图生成工具"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import base64
from io import BytesIO

def plot_rate_changes(
    df: pd.DataFrame,
    player_name: str = "",
    time_col: str = 'date',
    rate_col: str = 'rate',
    figsize: tuple = (18, 12),
    font_scale: float = 2.5,
    max_bar_labels: int = 15,
    first_rate: int = 0,
    output_file: str = None
) -> tuple:
    """
    绘制Rate变动分析图（双图布局）

    参数说明：
    ----------
    df : 包含时间和Rate值数据的数据框
    player_name : 玩家名称，用于图表标题
    time_col : 时间列名（需可转为datetime）
    rate_col : Rate值列名
    figsize : 图表尺寸（英寸）
    font_scale : 字体缩放系数（基准为10pt）
    max_bar_labels : X轴最大柱状图标注数
    first_rate : 初始Rate值，若未提供则使用第一个值
    output_file : 输出文件路径，为None时不保存文件

    返回：
    -------
    tuple: (matplotlib.figure.Figure, str) 图表对象和base64编码的图像
    """
    
    #=== 数据预处理 ================================================
    plot_df = df.copy()
    plot_df['time_formatted'] = pd.to_datetime(plot_df[time_col])
    plot_df = plot_df.sort_values('time_formatted').reset_index(drop=True)
    
    # 生成可视化辅助列
    plot_df['order'] = plot_df.index
    
    # 对于CSV格式的数据，通常直接有最终的Rate值而不是变动
    # 计算Rate的变动值
    if 'rate_change' not in plot_df.columns:
        # 如果没有rate_change列，则从rate列计算变动值
        plot_df['rate_change'] = plot_df[rate_col].diff().fillna(0)
        # 第一个值特殊处理
        if len(plot_df) > 0:
            if first_rate == 0 and len(plot_df) > 0:
                first_rate = plot_df[rate_col].iloc[0] - plot_df['rate_change'].iloc[0]
    
    plot_df['date_label'] = plot_df['time_formatted'].dt.strftime('%m-%d')
    
    #=== 可视化配置 ================================================
    plt.close('all')
    style_list = ['seaborn-v0_8', 'seaborn', 'ggplot', 'classic']
    plt.style.use(next((s for s in style_list if s in plt.style.available), 'classic'))
    
    base_font = 10 * font_scale
    plt.rcParams.update({
        'font.size': base_font,
        'axes.titlesize': base_font + 4,
        'axes.labelsize': base_font + 1,
        'xtick.labelsize': base_font - 2,
        'ytick.labelsize': base_font - 2,
        'font.sans-serif': ['SimHei'],
        'axes.unicode_minus': False
    })
    
    #=== 图表初始化 ================================================
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)
    fig.subplots_adjust(hspace=0.15)
    
    #=== 智能柱状图系统 ============================================
    def get_mode_pd(values):
        """用pandas计算众数，处理多众数和无众数的情况"""
        if values.empty:
            return None
        modes = values.mode()
        if not modes.empty:
            # 取第一个众数（可自定义逻辑，例如取平均值：modes.mean()）
            return modes.iloc[0]
        return None

    # 分离正负值（排除0）
    positive_values = plot_df['rate_change'][plot_df['rate_change'] > 0]
    negative_values = plot_df['rate_change'][plot_df['rate_change'] < 0]

    # 计算众数（若无众数则回退到中位数）
    pos_mode = get_mode_pd(positive_values) or positive_values.median()
    neg_mode = get_mode_pd(negative_values) or negative_values.median()

    # 设置归一化范围
    vmin = neg_mode if not negative_values.empty else plot_df['rate_change'].min()
    vmax = pos_mode if not positive_values.empty else plot_df['rate_change'].max()

    color_norm = plt.Normalize(vmin=vmin, vmax=vmax)
    colors = plt.cm.RdYlGn(color_norm(plot_df['rate_change']))
    
    # 柱体参数配置
    dense = len(plot_df) > 200
    bar_config = {
        'width': 1.0 if dense else 0.8,
        'alpha': 0.7 if dense else 0.8,
        'edgecolor': 'none' if dense else 'k',
        'linewidth': 0 if dense else 0.5,
        'color': colors,
    }
    
    # 绘制Rate变动柱状图
    bars = ax1.bar('order', plot_df['rate_change'], data=plot_df, **bar_config)
    
    # 标注系统
    label_interval = max(1, len(plot_df) // max_bar_labels)
    seen_values = set()
    for idx, bar in enumerate(bars):
        if idx % label_interval != 0: continue
        current_value = plot_df.at[idx, 'rate_change']
        if current_value in seen_values:
            continue
        
        # 动态位置计算
        if current_value > 0:
            y_pos = bar.get_height() - abs(bar.get_height())*0.15
            va = 'top'
        else:
            y_pos = bar.get_height() + abs(bar.get_height())*0.15
            va = 'bottom'
        
        # 边界保护
        y_min, y_max = ax1.get_ylim()
        if y_min != y_max:  # 防止相等时出错
            safe_range = 0.05 * (y_max - y_min)
            y_pos = np.clip(y_pos, y_min + safe_range, y_max - safe_range)

        # 添加标注
        ax1.text(
            bar.get_x() + bar.get_width()/2, y_pos,
            f'{current_value:.1f}',
            ha='center', va=va,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.9),
            fontsize=max(8, min(14, 72 * figsize[0] / (len(plot_df)*0.6))),
            color='black'
        )
        seen_values.add(current_value)

    #=== 图表装饰 =================================================
    title_prefix = f"{player_name} - " if player_name else ""
    ax1.set(title=f'{title_prefix}Rate变动分析（共{len(plot_df)}局）', ylabel='Rate变动值')
    ax1.grid(axis='y', linestyle='--', alpha=0.7)
    ax1.set_xlim(-0.5, len(plot_df)-0.5)
    
    #=== 折线图系统 ================================================
    # 绘制Rate变化趋势线
    ax2.plot('order', rate_col, data=plot_df, linestyle='-', 
            linewidth=2*font_scale, color='#2196F3', alpha=0.8)
    
    # 极值标注
    if len(plot_df) > 1:  # 防止只有一条数据时出错
        rate_range = plot_df[rate_col].max() - plot_df[rate_col].min()
        if rate_range > 0:  # 防止所有值相同时出错
            for ext_type, color, offset in [('max', 'red', 1), ('min', 'blue', -1)]:
                idx = getattr(plot_df[rate_col], f'idx{ext_type}')()
                value = plot_df.at[idx, rate_col]
                ax2.annotate(
                    f'{value}', (idx, value),
                    xytext=(idx, value + rate_range*0.1*offset),
                    arrowprops=dict(arrowstyle='->', color=color, linewidth=1.5*font_scale),
                    ha='center', fontsize=base_font*0.9, color=color,
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8)
                )
    
    ax2.set(title='Rate变化趋势', ylabel='当前Rate值')
    ax2.grid(axis='both', linestyle='--', alpha=0.7)
    
    #=== 智能坐标轴优化 ============================================
    def set_smart_ticks(ax, plot_df):
        n = len(plot_df)
        if n <= 1:
            return
        num_ticks = min(n, 10)
        indices = np.linspace(0, n-1, num_ticks, dtype=int)
        labels = [plot_df.at[i, 'date_label'] for i in indices]
        ax.set_xticks(indices)
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.tick_params(axis='x', labelsize=max(8, base_font - 2))

    set_smart_ticks(ax2, plot_df)  # 共享x轴，只需设置ax2
    
    plt.tight_layout()
    
    # 保存图像为base64
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
    plt.close()
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    
    # 保存到文件（如果指定了输出路径）
    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
    
    return fig, img_base64

if __name__ == '__main__':
    np.random.seed(42)
    # 生成测试数据
    test_df = pd.DataFrame({
        'date': pd.date_range('2023-01-01', periods=50, freq='D'),
        'rate': np.linspace(1500, 2000, 50) + np.random.normal(0, 50, 50),
    })
    
    fig, _ = plot_rate_changes(test_df, "测试玩家", output_file='rate_changes_demo.png')
    plt.show()
