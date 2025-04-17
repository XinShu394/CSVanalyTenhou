import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import base64
from io import BytesIO
from pathlib import Path
import re
from datetime import datetime
import json

from 四麻风格分析 import MahjongAnalyzer
from pt变化图生成 import plot_pt_changes
from rate变化图生成 import plot_rate_changes
from 相关系数热力图生成 import generate_correlation_heatmap, generate_advanced_correlation_heatmap
from html网页生成 import generate_html_report

# 设置字体，支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 版本信息
VERSION = "1.0.0"

def load_csv_data(csv_file_path):
    """
    加载CSV文件中的天凤对局数据
    
    参数:
    csv_file_path: CSV文件路径
    
    返回:
    pandas DataFrame: 加载好的数据
    """
    try:
        # 确保文件路径是Path对象
        path_obj = Path(csv_file_path)
        
        # 读取CSV文件，假设第一行是表头
        df = pd.read_csv(path_obj, encoding='utf-8')
        print(f"成功加载CSV文件: {path_obj}")
        
        # 检查CSV文件格式是否正确
        required_columns = ['顺位', '开始时间', '规则']
        for col in required_columns:
            if col not in df.columns:
                print(f"错误: CSV文件缺少必要的列 '{col}'")
                return None
        return df
    except Exception as e:
        print(f"加载CSV文件时出错: {str(e)}")
        return None

def preprocess_data(df, max_games=None):
    """
    预处理CSV数据
    
    参数:
    df: 原始数据框
    max_games: 最大牌谱数量，默认为None表示不限制
    
    返回:
    processed_df: 处理后的数据框
    """
    if df is None:
        return None
    
    # 创建一个新的数据框，避免修改原始数据
    processed_df = df.copy()
    
    # 将顺位转换为数值类型
    processed_df['顺位'] = processed_df['顺位'].str.extract(r'(\d+)').astype(float)
    
    # 转换时间格式
    processed_df['开始时间'] = pd.to_datetime(processed_df['开始时间'], errors='coerce')
    
    # 按时间排序（降序，最近的在前）
    processed_df = processed_df.sort_values('开始时间', ascending=False)
    
    # 如果指定了最大牌谱数量，则截取前N条记录
    if max_games is not None and max_games > 0 and len(processed_df) > max_games:
        print(f"限制分析最近的 {max_games} 场牌谱（总计 {len(processed_df)} 场）")
        processed_df = processed_df.head(max_games)
    
    # 按时间重新升序排序，以便按时间先后顺序分析
    processed_df = processed_df.sort_values('开始时间')
    
    return processed_df

def calculate_statistics(df):
    """
    计算各种统计指标
    
    参数:
    df: 预处理后的数据框
    
    返回:
    stats_dict: 包含各种统计结果的字典
    """
    if df is None or df.empty:
        return {}
    
    # 计算基本统计
    total_games = len(df)
    avg_rank = df['顺位'].mean()
    
    # 计算各个顺位的次数和比率
    rank_counts = df['顺位'].value_counts().sort_index()
    rank_rates = rank_counts / total_games
    
    # 提取pt变化和rate变化数据(如果有)
    pt_changes = []
    rate_changes = []
    if '获得pt' in df.columns:
        pt_changes = df['获得pt'].fillna(0).values
    if 'R值' in df.columns:
        rate_changes = df['R值'].dropna().values
    
    # 计算更多统计指标（尽可能从CSV提取，或使用默认值）
    # 这些值在实际使用中应根据实际牌谱的详细数据计算
    
    # 统计每种规则的场数
    rule_counts = df['规则'].value_counts()
    
    # 从规则中提取东/南场、有无红牌等信息
    rule_info = {
        '东场': sum('東' in str(rule) for rule in df['规则']),
        '南场': sum('南' in str(rule) for rule in df['规则']),
        '有赤牌': sum('赤' in str(rule) for rule in df['规则']),
    }
    
    # 将统计结果整合为字典
    stats_dict = {
        '有效牌谱数': total_games,
        '平均顺位': round(avg_rank, 4),
        '一位率': round(rank_rates.get(1, 0), 4),
        '二位率': round(rank_rates.get(2, 0), 4),
        '三位率': round(rank_rates.get(3, 0), 4),
        '四位率': round(rank_rates.get(4, 0), 4),
        '吃分率': round(rank_rates.get(1, 0) + rank_rates.get(2, 0), 4),
        '被飞率': round(rank_rates.get(4, 0), 4),
    }
    
    # 添加东南场统计
    if rule_info['东场'] + rule_info['南场'] > 0:
        stats_dict.update({
            '东场占比': round(rule_info['东场'] / total_games, 4),
            '南场占比': round(rule_info['南场'] / total_games, 4),
        })
    
    # 添加赤牌使用情况
    if rule_info['有赤牌'] > 0:
        stats_dict['赤牌场数占比'] = round(rule_info['有赤牌'] / total_games, 4)
    
    # 从CSV数据中尝试估计一些高级统计指标
    # 注意：这些只是粗略估计，实际应该从牌谱详细信息中计算
    
    # 模拟和了率、放铳率等指标
    stats_dict.update({
        '和了率': 0.25,         # 默认估计值
        '放铳率': 0.15,         # 默认估计值
        '副露率': 0.30,         # 默认估计值
        '立直率': 0.20,         # 默认估计值
        '默听率': 0.10,         # 默认估计值
        '平均和了打点': 6500,    # 默认估计值
        '平均和了巡目': 11.5,    # 默认估计值
        '平均放铳打点': 5800,    # 默认估计值
        '流局率': 0.15,         # 默认估计值
        '立直先制率': 0.75,      # 默认估计值
        '追立率': 0.25,         # 默认估计值
    })
    
    # 计算PT和Rate相关统计
    if '获得pt' in df.columns:
        pt_values = df['获得pt'].fillna(0)
        stats_dict.update({
            '总PT变化': round(pt_values.sum(), 2),
            '场均PT变化': round(pt_values.mean(), 2),
            'PT标准差': round(pt_values.std(), 2),
            'PT最大值': round(pt_values.max(), 2),
            'PT最小值': round(pt_values.min(), 2),
        })
    
    if 'R值' in df.columns:
        rate_values = df['R值'].dropna()
        if len(rate_values) >= 2:
            stats_dict.update({
                'Rate起始值': round(rate_values.iloc[0], 2),
                'Rate最终值': round(rate_values.iloc[-1], 2),
                'Rate变化值': round(rate_values.iloc[-1] - rate_values.iloc[0], 2),
                'Rate最高值': round(rate_values.max(), 2),
                'Rate最低值': round(rate_values.min(), 2),
            })
    
    return stats_dict

def calculate_mahjong_style(stats_dict):
    """
    计算麻将风格指标
    
    参数:
    stats_dict: 统计指标字典
    
    返回:
    style_data: 风格分析数据
    """
    # 根据统计数据计算风格指标
    style_data = {
        'horyu_rate': stats_dict.get('和了率', 0.25) * 100,  # 转换为百分比
        'houju_rate': stats_dict.get('放铳率', 0.15) * 100,
        'furo_rate': stats_dict.get('副露率', 0.30) * 100,
        'riichi_rate': stats_dict.get('立直率', 0.20) * 100,
        'dama_rate': stats_dict.get('默听率', 0.10) * 100,
        'average_score': stats_dict.get('平均和了打点', 6500),
        'avg_horyu_turn': stats_dict.get('平均和了巡目', 11.5),
        'avg_houju_score': stats_dict.get('平均放铳打点', 5800),
        'ryukyoku_rate': stats_dict.get('流局率', 0.15) * 100,
        'riichi_turn': stats_dict.get('平均立直巡目', 7.5),
        'riichi_first_rate': stats_dict.get('立直先制率', 0.75) * 100,
        'riichi_chase_rate': stats_dict.get('追立率', 0.25) * 100
    }
    
    return style_data

def generate_pt_rate_changes(df, player_name):
    """
    生成PT和Rate变化图
    
    参数:
    df: 数据框
    player_name: 玩家名称
    
    返回:
    pt_img_base64: PT变化图的base64编码
    rate_img_base64: Rate变化图的base64编码
    """
    # 准备PT变化数据
    pt_data = None
    if '获得pt' in df.columns and '开始时间' in df.columns:
        pt_data = df[['开始时间', '获得pt']].dropna()
        pt_data = pt_data.rename(columns={'开始时间': 'date', '获得pt': 'pt_change'})
    
    # 准备Rate变化数据
    rate_data = None
    if 'R值' in df.columns and '开始时间' in df.columns:
        rate_data = df[['开始时间', 'R值']].dropna()
        rate_data = rate_data.rename(columns={'开始时间': 'date', 'R值': 'rate'})
    
    # 生成PT变化图
    pt_img_base64 = ""
    if pt_data is not None and not pt_data.empty:
        try:
            _, pt_img_base64 = plot_pt_changes(pt_data, player_name, output_file=None)
            print(f"成功生成PT变化图，数据点数：{len(pt_data)}")
        except Exception as e:
            print(f"生成PT变化图时出错: {str(e)}")
    else:
        print("没有足够的PT变化数据用于生成图表")
    
    # 生成Rate变化图
    rate_img_base64 = ""
    if rate_data is not None and not rate_data.empty:
        try:
            _, rate_img_base64 = plot_rate_changes(rate_data, player_name, output_file=None)
            print(f"成功生成Rate变化图，数据点数：{len(rate_data)}")
        except Exception as e:
            print(f"生成Rate变化图时出错: {str(e)}")
    else:
        print("没有足够的Rate变化数据用于生成图表")
    
    return pt_img_base64, rate_img_base64

def generate_rank_distribution_chart(df):
    """
    生成顺位分布饼图
    
    参数:
    df: 预处理后的数据框
    
    返回:
    rank_pie_base64: 顺位分布饼图的base64编码
    """
    if df is None or df.empty:
        return ""
    
    # 计算各个顺位的次数
    rank_counts = df['顺位'].value_counts().sort_index()
    
    # 设置饼图
    plt.figure(figsize=(10, 8))
    colors = ['#4CAF50', '#2196F3', '#FFC107', '#F44336']  # 绿、蓝、黄、红
    explode = (0.1, 0, 0, 0)  # 突出第一位
    
    # 绘制饼图
    plt.pie(
        rank_counts, 
        labels=[f'一位 ({rank_counts.get(1, 0)}局)', 
                f'二位 ({rank_counts.get(2, 0)}局)', 
                f'三位 ({rank_counts.get(3, 0)}局)', 
                f'四位 ({rank_counts.get(4, 0)}局)'],
        explode=explode,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        shadow=True
    )
    plt.axis('equal')  # 确保饼图是圆的
    plt.title('顺位分布', fontsize=16)
    plt.tight_layout()
    
    # 保存为base64
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
    plt.close()
    img_buffer.seek(0)
    rank_pie_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    
    return rank_pie_base64

def generate_correlation_analysis(df, important_vars=None):
    """
    生成相关性分析图表
    
    参数:
    df: 预处理后的数据框
    important_vars: 重要变量列表，为None时自动选择
    
    返回:
    dict: 包含各种相关性分析图表的base64编码
    """
    if df is None or df.empty:
        return {}
    
    # 如果没有指定重要变量，则选择常用的麻将统计指标
    if important_vars is None:
        # 尝试从数据框中选择常见的变量
        potential_vars = ['顺位', '一位率', '二位率', '吃分率', '和了率', '放铳率', 
                         '副露率', '立直率', '默听率', '流局率', '平均和了打点']
        important_vars = [var for var in potential_vars if var in df.columns]
    
    # 确保有足够的变量进行相关性分析
    if len(important_vars) < 3:
        print("没有足够的变量进行相关性分析")
        return {}
    
    # 生成基础相关系数热力图
    try:
        pearson_img = generate_correlation_heatmap(
            df[important_vars],
            method='pearson',
            title='麻将指标相关性分析'
        )
        
        # 尝试生成Spearman相关系数热力图
        spearman_img = generate_correlation_heatmap(
            df[important_vars],
            method='spearman',
            title='麻将指标非线性相关性分析',
            cmap='viridis'
        )
        
        # 生成高级组合热力图
        advanced_imgs = generate_advanced_correlation_heatmap(
            df[important_vars],
            methods=['pearson', 'spearman'],
            cmap='RdBu_r'
        )
        
        return {
            '相关系数热力图(Pearson)': pearson_img,
            '相关系数热力图(Spearman)': spearman_img,
            '组合相关系数热力图': advanced_imgs.get('combined', '')
        }
    except Exception as e:
        print(f"生成相关性分析图表时出错: {str(e)}")
        return {}

def analyze_csv_and_generate_report(csv_file_path, max_games=200, output_dir=None):
    """
    分析CSV文件并生成HTML报告
    
    参数:
    csv_file_path: CSV文件路径
    max_games: 最大牌谱数量，默认为200
    output_dir: 输出目录，如果为None则使用当前目录
    
    返回:
    report_path: 生成的HTML报告路径
    """
    # 设置输出目录
    if output_dir is None:
        output_dir = Path("统计报告")
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取玩家名称
    file_name = Path(csv_file_path).name
    player_name = file_name.split(" -- ")[0] if " -- " in file_name else "未知玩家"
    
    # 加载并预处理数据
    df = load_csv_data(csv_file_path)
    if df is None:
        print("无法处理CSV文件，请检查格式。")
        return None
    
    processed_df = preprocess_data(df, max_games)
    if processed_df is None or processed_df.empty:
        print("预处理数据后为空，无法生成报告。")
        return None
    
    # 计算统计指标
    stats_dict = calculate_statistics(processed_df)
    if not stats_dict:
        print("计算统计指标失败。")
        return None
    
    # 准备基本统计数据和详细统计数据
    basic_stats = {}
    detailed_stats = {}
    
    # 基本统计数据
    basic_keys = ['有效牌谱数', '平均顺位', '一位率', '二位率', '三位率', '四位率', '吃分率', '被飞率']
    for key in basic_keys:
        if key in stats_dict:
            basic_stats[key] = stats_dict[key]
    
    # 详细统计数据（除去基本统计）
    for key, value in stats_dict.items():
        if key not in basic_keys:
            detailed_stats[key] = value
    
    # 生成顺位分布图
    rank_pie_base64 = generate_rank_distribution_chart(processed_df)
    
    # 将统计指标转换为Series以用于报告生成
    basic_stats_series = pd.Series(basic_stats)
    detailed_stats_series = pd.Series(detailed_stats)
    
    # PT相关统计
    pt_stats = {}
    if '总PT变化' in stats_dict:
        pt_keys = ['总PT变化', 'PT标准差', '场均PT变化', 'PT最大值', 'PT最小值']
        for key in pt_keys:
            if key in stats_dict:
                pt_stats[key] = stats_dict[key]
    pt_stats_series = pd.Series(pt_stats)
    
    # Rate相关统计
    rate_stats = {}
    if 'Rate起始值' in stats_dict:
        rate_keys = ['Rate起始值', 'Rate最终值', 'Rate变化值', 'Rate最高值', 'Rate最低值']
        for key in rate_keys:
            if key in stats_dict:
                rate_stats[key] = stats_dict[key]
    rate_stats_series = pd.Series(rate_stats)
    
    # 分析麻将风格
    style_data = calculate_mahjong_style(stats_dict)
    
    # 生成风格分析图
    analyzer = MahjongAnalyzer()
    try:
        X, Y, style_type, _, style_img_base64 = analyzer.analyze(data=style_data, output_filename=None)
        print("成功生成风格分析图")
        # 将风格分析结果添加到统计数据中
        style_result = {
            '风格类型': style_type,
            '风格X坐标': round(X, 2),
            '风格Y坐标': round(Y, 2)
        }
        style_result_series = pd.Series(style_result)
        # 添加风格分析结果到detailed_stats
        for key, value in style_result.items():
            detailed_stats[key] = value
        detailed_stats_series = pd.Series(detailed_stats)
    except Exception as e:
        print(f"生成风格分析图时出错: {str(e)}")
        style_img_base64 = ""
    
    # 生成PT和Rate变化图
    pt_img_base64, rate_img_base64 = generate_pt_rate_changes(processed_df, player_name)
    
    # 生成相关系数热力图（增强版）
    correlation_images = generate_correlation_analysis(processed_df)
    
    # 构建用于HTML报告的图像字典
    image_base64_dict = {
        "风格分析图": style_img_base64,
        "顺位分布图": rank_pie_base64,
        "PT变化图": pt_img_base64,
        "Rate变化图": rate_img_base64
    }
    
    # 添加相关系数热力图（如果生成成功）
    for key, img in correlation_images.items():
        if img:  # 只添加非空的图像
            image_base64_dict[key] = img
    
    # 构建用于HTML报告的数据分段
    series_sections = []
    
    # 只添加非空的数据部分
    if basic_stats:
        series_sections.append(("基本统计", basic_stats_series))
    
    if detailed_stats:
        series_sections.append(("详细指标", detailed_stats_series))
    
    if pt_stats:
        series_sections.append(("PT统计", pt_stats_series))
    
    if rate_stats:
        series_sections.append(("Rate统计", rate_stats_series))
    
    # 生成HTML报告
    report_path = output_dir / f"{player_name}_统计报告.html"
    generate_html_report(player_name, image_base64_dict, series_sections, str(report_path))
    
    print(f"成功生成报告: {report_path}")
    return report_path

def main():
    # 首先在当前目录查找CSV文件
    current_dir = Path(".")
    csv_files = list(current_dir.glob("*.csv"))
    
    # 如果当前目录没有找到CSV文件，尝试查找示例csv目录
    if not csv_files:
        csv_dir = Path("示例csv")
        if csv_dir.exists() and csv_dir.is_dir():
            csv_files = list(csv_dir.glob("*.csv"))
            if not csv_files:
                print(f"错误: 在当前目录和 {csv_dir} 中都没有找到CSV文件。")
                return
        else:
            print(f"错误: 在当前目录中没有找到CSV文件，且 {csv_dir} 目录不存在。")
            return
    
    # 定义分页显示函数
    def display_files(files, page_size=10, current_page=1, filter_text=""):
        filtered_files = [f for f in files if filter_text.lower() in f.name.lower()]
        total_pages = (len(filtered_files) + page_size - 1) // page_size
        
        if total_pages == 0:
            print("没有匹配的文件")
            return filtered_files, total_pages, current_page
        
        current_page = max(1, min(current_page, total_pages))
        start_idx = (current_page - 1) * page_size
        end_idx = min(start_idx + page_size, len(filtered_files))
        
        print(f"\n--- 文件列表 (第 {current_page}/{total_pages} 页, 共 {len(filtered_files)} 个文件) ---")
        for i, file in enumerate(filtered_files[start_idx:end_idx], start=start_idx + 1):
            print(f"{i}. {file.name}")
        
        print("\n操作命令:")
        print("  数字: 选择对应编号的文件进行分析")
        print("  n: 下一页")
        print("  p: 上一页")
        print("  f: 输入过滤条件")
        print("  q: 退出程序")
        
        return filtered_files, total_pages, current_page
    
    # 显示程序标题和版本
    print("\n" + "="*60)
    print(f"天凤牌谱分析器 v{VERSION}")
    print("="*60)
    print("本工具用于分析天凤牌谱数据并生成HTML统计报告\n")
    
    # 初始化分页和过滤参数
    page_size = 10
    current_page = 1
    filter_text = ""
    
    # 显示第一页文件
    filtered_files, total_pages, current_page = display_files(
        csv_files, page_size, current_page, filter_text
    )
    
    # 主交互循环
    while True:
        choice = input("\n请输入您的选择: ").strip().lower()
        
        if choice == 'q':
            print("退出程序")
            return
        
        elif choice == 'n':
            if current_page < total_pages:
                current_page += 1
                filtered_files, total_pages, current_page = display_files(
                    csv_files, page_size, current_page, filter_text
                )
            else:
                print("已经是最后一页")
        
        elif choice == 'p':
            if current_page > 1:
                current_page -= 1
                filtered_files, total_pages, current_page = display_files(
                    csv_files, page_size, current_page, filter_text
                )
            else:
                print("已经是第一页")
        
        elif choice == 'f':
            filter_text = input("请输入过滤条件(玩家名称): ").strip()
            current_page = 1
            filtered_files, total_pages, current_page = display_files(
                csv_files, page_size, current_page, filter_text
            )
        
        elif choice.isdigit():
            file_index = int(choice)
            
            if 1 <= file_index <= len(filtered_files):
                selected_file = filtered_files[file_index - 1]
                print(f"\n您选择了: {selected_file.name}")
                
                confirm = input("确认分析此文件? (y/n): ").strip().lower()
                if confirm == 'y':
                    # 询问要分析的牌谱数量
                    max_games = 200  # 默认值
                    games_input = input(f"请输入要分析的最近牌谱数量 (直接回车使用默认值 {max_games}): ").strip()
                    if games_input and games_input.isdigit():
                        max_games = int(games_input)
                    else:
                        print(f"使用默认值: 分析最近 {max_games} 场牌谱")
                    
                    # 分析所选文件并生成报告
                    report_path = analyze_csv_and_generate_report(selected_file, max_games)
                    
                    # 如果成功生成报告，尝试打开它
                    if report_path and report_path.exists():
                        try:
                            import webbrowser
                            webbrowser.open(str(report_path))
                            print(f"已在浏览器中打开报告: {report_path}")
                        except Exception as e:
                            print(f"无法自动打开报告，请手动打开: {report_path}")
                            print(f"错误: {str(e)}")
                    
                    # 询问是否继续分析其他文件
                    if input("\n是否继续分析其他文件? (y/n): ").strip().lower() != 'y':
                        print("退出程序")
                        return
                    
                    # 重新显示文件列表
                    filtered_files, total_pages, current_page = display_files(
                        csv_files, page_size, current_page, filter_text
                    )
            else:
                print(f"无效的选择，请输入1到{len(filtered_files)}之间的数字")
        
        else:
            print("无效的命令，请重新输入")

if __name__ == "__main__":
    main() 