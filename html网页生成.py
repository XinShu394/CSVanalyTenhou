import json
import base64
from pathlib import Path
import pandas as pd
from datetime import datetime

def generate_html_report(player_name, image_base64_dict, series_sections, output_path):
    """
    生成HTML报告页面
    
    参数:
    player_name: 玩家名称
    image_base64_dict: 包含图像的base64编码字典，格式为{图像名称: base64编码字符串}
    series_sections: 包含数据分段的列表，格式为[(分段名称, pandas.Series)]
    output_path: 输出HTML文件的路径
    """
    # 过滤掉空图像
    filtered_images = {k: v for k, v in image_base64_dict.items() if v}
    
    # HTML头部
    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{player_name} - 天凤牌谱分析报告</title>
        <style>
            :root {{
                --main-bg-color: #f8f9fa;
                --card-bg-color: #ffffff;
                --primary-color: #4a6bff;
                --secondary-color: #6d757d;
                --success-color: #28a745;
                --danger-color: #dc3545;
                --warning-color: #ffc107;
                --info-color: #17a2b8;
                --border-radius: 8px;
                --shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                --transition: all 0.3s ease;
            }}
            
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Microsoft YaHei', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }}
            
            body {{
                background-color: var(--main-bg-color);
                color: #333;
                line-height: 1.6;
                padding-top: 20px;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            
            header {{
                background: linear-gradient(135deg, var(--primary-color), #3a56d4);
                color: white;
                padding: 20px;
                border-radius: var(--border-radius);
                margin-bottom: 30px;
                box-shadow: var(--shadow);
                text-align: center;
                position: relative;
            }}
            
            h1, h2, h3 {{
                margin-bottom: 15px;
                font-weight: 600;
            }}
            
            .header-content {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
            }}
            
            .player-info {{
                flex-grow: 1;
                text-align: left;
            }}
            
            .report-meta {{
                text-align: right;
                font-size: 0.9em;
                opacity: 0.9;
            }}
            
            .card {{
                background-color: var(--card-bg-color);
                border-radius: var(--border-radius);
                box-shadow: var(--shadow);
                margin-bottom: 30px;
                overflow: hidden;
                transition: var(--transition);
            }}
            
            .card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
            }}
            
            .card-header {{
                background-color: var(--primary-color);
                color: white;
                padding: 15px 20px;
                font-weight: bold;
                font-size: 1.2em;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            
            .card-body {{
                padding: 20px;
            }}
            
            .button-container {{
                display: flex;
                justify-content: center;
                flex-wrap: wrap;
                gap: 15px;
                margin-bottom: 30px;
            }}
            
            .btn {{
                display: inline-block;
                padding: 10px 20px;
                background-color: var(--primary-color);
                color: white;
                border: none;
                border-radius: var(--border-radius);
                cursor: pointer;
                font-size: 1rem;
                font-weight: 500;
                text-align: center;
                text-decoration: none;
                transition: var(--transition);
                min-width: 120px;
            }}
            
            .btn:hover {{
                background-color: #3a56d4;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            }}
            
            .btn-secondary {{
                background-color: var(--secondary-color);
            }}
            
            .btn-secondary:hover {{
                background-color: #5a6268;
            }}
            
            .stats-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }}
            
            .stats-table th, .stats-table td {{
                padding: 12px 15px;
                text-align: left;
                border-bottom: 1px solid #e0e0e0;
            }}
            
            .stats-table th {{
                background-color: #f0f4ff;
                font-weight: 600;
                color: var(--primary-color);
            }}
            
            .stats-table tr:hover {{
                background-color: #f5f8ff;
            }}
            
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }}
            
            .stat-card {{
                background-color: #fff;
                border-radius: var(--border-radius);
                padding: 15px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                transition: var(--transition);
            }}
            
            .stat-card:hover {{
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }}
            
            .stat-name {{
                font-size: 0.9em;
                color: var(--secondary-color);
                margin-bottom: 5px;
            }}
            
            .stat-value {{
                font-size: 1.4em;
                font-weight: 600;
                color: var(--primary-color);
            }}
            
            .chart-container {{
                margin-top: 20px;
                text-align: center;
            }}
            
            .chart-img {{
                max-width: 100%;
                height: auto;
                border-radius: var(--border-radius);
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }}
            
            .section {{
                display: none;
            }}
            
            .section.active {{
                display: block;
                animation: fadeIn 0.5s;
            }}
            
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            
            .tab-group {{
                display: flex;
                flex-wrap: wrap;
                margin-bottom: 20px;
            }}
            
            .tab {{
                background-color: #e9ecef;
                color: var(--secondary-color);
                padding: 10px 20px;
                cursor: pointer;
                border-radius: var(--border-radius) var(--border-radius) 0 0;
                margin-right: 5px;
                transition: var(--transition);
            }}
            
            .tab:hover {{
                background-color: #d2d8df;
            }}
            
            .tab.active {{
                background-color: var(--primary-color);
                color: white;
            }}
            
            .chart-section {{
                display: none;
            }}
            
            .chart-section.active {{
                display: block;
                animation: fadeIn 0.5s;
            }}
            
            .chart-wrapper {{
                width: 100%;
                padding: 20px;
                box-shadow: var(--shadow);
                text-align: center;
                margin-bottom: 20px;
            }}
            
            .chart-single {{
                width: 100%;
                max-width: 800px;
                margin: 0 auto;
            }}
            
            .chart-title {{
                font-size: 1.2em;
                margin-bottom: 15px;
                color: var(--primary-color);
            }}
            
            footer {{
                text-align: center;
                margin-top: 50px;
                padding: 20px;
                background-color: var(--card-bg-color);
                border-radius: var(--border-radius);
                box-shadow: var(--shadow);
                color: var(--secondary-color);
                font-size: 0.9em;
            }}
            
            @media (max-width: 768px) {{
                .container {{
                    padding: 10px;
                }}
                
                header {{
                    padding: 15px;
                }}
                
                .header-content {{
                    flex-direction: column;
                    text-align: center;
                }}
                
                .player-info, .report-meta {{
                    text-align: center;
                    margin-bottom: 10px;
                }}
                
                .button-container {{
                    flex-direction: column;
                    align-items: center;
                }}
                
                .stats-grid {{
                    grid-template-columns: 1fr;
                }}
                
                .tab {{
                    flex-grow: 1;
                    text-align: center;
                    margin-bottom: 5px;
                }}
            }}
            
            .tooltip {{
                position: relative;
                display: inline-block;
                cursor: help;
            }}
            
            .tooltip .tooltiptext {{
                visibility: hidden;
                width: 200px;
                background-color: #555;
                color: #fff;
                text-align: center;
                border-radius: 6px;
                padding: 5px;
                position: absolute;
                z-index: 1;
                bottom: 125%;
                left: 50%;
                margin-left: -100px;
                opacity: 0;
                transition: opacity 0.3s;
                font-size: 0.85em;
            }}
            
            .tooltip:hover .tooltiptext {{
                visibility: visible;
                opacity: 1;
            }}
            
            #about-modal {{
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.7);
                z-index: 1000;
                overflow: auto;
                animation: fadeIn 0.3s;
            }}
            
            .modal-content {{
                background-color: white;
                margin: 10% auto;
                padding: 30px;
                border-radius: var(--border-radius);
                width: 80%;
                max-width: 700px;
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
                position: relative;
            }}
            
            .close-modal {{
                position: absolute;
                top: 15px;
                right: 20px;
                font-size: 28px;
                cursor: pointer;
                color: var(--secondary-color);
                transition: var(--transition);
            }}
            
            .close-modal:hover {{
                color: var(--danger-color);
            }}
            
            .highlight {{
                background-color: #fff8e1;
                padding: 2px 5px;
                border-radius: 3px;
                font-weight: 500;
                color: #ff6d00;
            }}
            
            .progress-bar-container {{
                width: 100%;
                height: 20px;
                background-color: #e9ecef;
                border-radius: 10px;
                margin-top: 5px;
                overflow: hidden;
            }}
            
            .progress-bar {{
                height: 100%;
                text-align: center;
                color: white;
                font-size: 12px;
                line-height: 20px;
                background: linear-gradient(90deg, var(--primary-color), #3a56d4);
                border-radius: 10px;
                transition: width 0.5s ease-in-out;
            }}
            
            .badge {{
                display: inline-block;
                padding: 3px 8px;
                border-radius: 12px;
                font-size: 0.75em;
                font-weight: 500;
                margin-left: 5px;
            }}
            
            .badge-primary {{
                background-color: var(--primary-color);
                color: white;
            }}
            
            .badge-success {{
                background-color: var(--success-color);
                color: white;
            }}
            
            .badge-warning {{
                background-color: var(--warning-color);
                color: #212529;
            }}
            
            .badge-danger {{
                background-color: var(--danger-color);
                color: white;
            }}
            
            .stats-section {{
                display: none;
            }}
            
            .stats-section.active {{
                display: block;
                animation: fadeIn 0.5s;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <div class="header-content">
                    <div class="player-info">
                        <h1>{player_name}</h1>
                        <p>天凤牌谱分析报告</p>
                    </div>
                    <div class="report-meta">
                        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                </div>
            </header>
            
            <div class="button-container">
                <button class="btn" onclick="switchSection('overview')">牌谱概览</button>
                <button class="btn" onclick="switchSection('statistics')">统计指标</button>
                <button class="btn" onclick="switchSection('charts')">图表分析</button>
                <button class="btn btn-secondary" onclick="toggleAboutModal()">关于项目</button>
            </div>
            
            <!-- 概览部分 -->
            <section id="overview" class="section active">
                <div class="card">
                    <div class="card-header">
                        <span>牌谱概览</span>
                    </div>
                    <div class="card-body">
                        <div class="stats-grid">
    """
    
    # 添加基本统计的卡片
    for section_name, series in series_sections:
        if section_name == "基本统计":
            for idx, (name, value) in enumerate(series.items()):
                # 对于某些指标，设置特定样式和进度条
                bar_style = ""
                badge = ""
                
                if name in ['一位率', '二位率', '三位率', '四位率', '吃分率']:
                    percentage = float(value) * 100
                    value_display = f"{percentage:.1f}%"
                    
                    if name == '一位率':
                        bar_style = f"""
                        <div class="progress-bar-container">
                            <div class="progress-bar" style="width: {percentage}%">{value_display}</div>
                        </div>
                        """
                        if percentage >= 30:
                            badge = '<span class="badge badge-success">优秀</span>'
                        elif percentage >= 25:
                            badge = '<span class="badge badge-primary">良好</span>'
                        elif percentage <= 15:
                            badge = '<span class="badge badge-danger">不佳</span>'
                    
                    if name == '四位率' and float(value) >= 0.3:
                        badge = '<span class="badge badge-danger">高飞率</span>'
                else:
                    value_display = str(value)
                
                html_template += f"""
                <div class="stat-card">
                    <div class="stat-name">{name} {badge}</div>
                    <div class="stat-value">{value_display}</div>
                    {bar_style}
                </div>
                """
    
    html_template += """
                        </div>
                    </div>
                </div>
            </section>
            
            <!-- 统计指标部分 -->
            <section id="statistics" class="section">
                <div class="tab-group">
    """
    
    # 生成统计指标选项卡按钮
    for i, (section_name, _) in enumerate(series_sections):
        active_class = "active" if i == 0 else ""
        html_template += f"""
        <div class="tab {active_class}" onclick="showStats('{section_name}')">{section_name}</div>
        """
    
    html_template += """
                </div>
                <div class="card">
                    <div class="card-body">
    """
    
    # 生成统计指标选项卡内容
    for i, (section_name, series) in enumerate(series_sections):
        active_class = "active" if i == 0 else ""
        html_template += f"""
        <div id="{section_name}" class="stats-section {active_class}">
                <table class="stats-table">
                    <thead>
                        <tr>
                            <th>指标</th>
                            <th>数值</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # 添加每个指标的行
        for name, value in series.items():
            # 为不同类型的指标设置不同的显示格式
            if name in ['一位率', '二位率', '三位率', '四位率', '吃分率', '被飞率', '东场占比', '南场占比', '赤牌场数占比']:
                value_display = f"{float(value) * 100:.1f}%"
            else:
                value_display = str(value)
            
            html_template += f"""
            <tr>
                <td>{name}</td>
                <td>{value_display}</td>
            </tr>
            """
        
        html_template += """
                    </tbody>
                </table>
        </div>
        """
    
    html_template += """
                    </div>
                </div>
            </section>
            
            <!-- 图表分析部分 -->
            <section id="charts" class="section">
                <div class="tab-group">
    """
    
    # 生成图表分析选项卡按钮
    chart_names = list(filtered_images.keys())
    for i, chart_name in enumerate(chart_names):
        active_class = "active" if i == 0 else ""
        # 格式化图表名称
        formatted_name = chart_name.replace("_", " ").replace("图", "").replace(player_name, "")
        if formatted_name.startswith(" "):
            formatted_name = formatted_name[1:]
        
        html_template += f"""
        <div class="tab {active_class}" onclick="showChart('{chart_name}')">{formatted_name}</div>
        """
    
    html_template += """
                </div>
                <div class="card">
                    <div class="card-body">
    """
    
    # 生成图表分析选项卡内容
    for i, (chart_name, base64_str) in enumerate(filtered_images.items()):
        active_class = "active" if i == 0 else ""
        # 格式化图表名称
        formatted_name = chart_name.replace("_", " ").replace("图", "").replace(player_name, "")
        if formatted_name.startswith(" "):
            formatted_name = formatted_name[1:]
        
        html_template += f"""
        <div id="chart-{chart_name}" class="chart-section {active_class}">
            <div class="chart-single">
                <div class="chart-title">{formatted_name}</div>
                <img src="data:image/png;base64,{base64_str}" alt="{chart_name}" class="chart-img">
            </div>
        </div>
        """
    
    html_template += """
                    </div>
                </div>
            </section>
            
            <!-- 关于项目模态框 -->
            <div id="about-modal">
                <div class="modal-content">
                    <span class="close-modal" onclick="toggleAboutModal()">&times;</span>
                    <h2>关于天凤牌谱分析器</h2>
                    <p>本工具用于分析天凤的牌谱数据，帮助玩家了解自己的打牌风格和表现情况。</p>
                    <h3>数据来源</h3>
                    <p>分析数据来自天凤导出的CSV文件，包含牌谱的基本信息、对局结果和部分统计数据。</p>
                    <h3>分析方法</h3>
                    <p>通过对牌谱数据的统计分析，计算各种指标，并使用可视化方式呈现结果。</p>
                    <h3>使用说明</h3>
                    <p>在程序中选择CSV文件，设置分析的牌谱数量，即可生成完整的分析报告。</p>
                    <p>报告包含基本统计、详细指标和图表分析等多个部分。</p>
                </div>
            </div>
            
            <footer>
                <p>天凤牌谱分析器 &copy; 2023-2024</p>
            </footer>
        </div>
        
        <script>
            // 切换不同部分
            function switchSection(sectionId) {
                const sections = document.querySelectorAll('.section');
                sections.forEach(section => {
                    section.classList.remove('active');
                });
                document.getElementById(sectionId).classList.add('active');
                
                // 更新按钮状态
                const buttons = document.querySelectorAll('.button-container .btn');
                buttons.forEach(button => {
                    button.classList.remove('active');
                });
                event.target.classList.add('active');
            }
            
            // 切换统计选项卡
            function showStats(tabName) {
                // 更新选项卡按钮状态
                const tabs = document.querySelectorAll('#statistics .tab');
                tabs.forEach(tab => {
                    tab.classList.remove('active');
                });
                event.currentTarget.classList.add('active');
                
                // 更新选项卡内容显示
                const statsSections = document.querySelectorAll('.stats-section');
                statsSections.forEach(section => {
                    section.classList.remove('active');
                });
                document.getElementById(tabName).classList.add('active');
            }
            
            // 切换图表选项卡
            function showChart(chartName) {
                // 更新选项卡按钮状态
                const tabs = document.querySelectorAll('#charts .tab');
                tabs.forEach(tab => {
                    tab.classList.remove('active');
                });
                event.currentTarget.classList.add('active');
                
                // 更新选项卡内容显示
                const chartSections = document.querySelectorAll('.chart-section');
                chartSections.forEach(section => {
                    section.classList.remove('active');
                });
                document.getElementById('chart-' + chartName).classList.add('active');
            }
            
            // 切换关于模态框
            function toggleAboutModal() {
                const modal = document.getElementById('about-modal');
                const currentDisplay = modal.style.display;
                modal.style.display = currentDisplay === 'block' ? 'none' : 'block';
            }
            
            // 当用户点击模态框外部时关闭它
            window.onclick = function(event) {
                const modal = document.getElementById('about-modal');
                if (event.target === modal) {
                    modal.style.display = 'none';
                }
            }
            
            // 页面加载完成后的初始化
            window.onload = function() {
                // 设置初始激活状态
                document.querySelector('.button-container .btn').classList.add('active');
                
                // 确保默认显示第一个统计选项卡
                if (document.querySelectorAll('.stats-section').length > 0) {
                    // 默认激活第一个选项卡按钮
                    document.querySelector('#statistics .tab').classList.add('active');
                    // 默认显示第一个选项卡内容
                    document.querySelector('.stats-section').classList.add('active');
                }
                
                // 确保默认显示第一个图表选项卡
                if (document.querySelectorAll('.chart-section').length > 0) {
                    // 默认激活第一个选项卡按钮
                    document.querySelector('#charts .tab').classList.add('active');
                    // 默认显示第一个选项卡内容
                    document.querySelector('.chart-section').classList.add('active');
                }
                
                // 为百分比值添加进度条
                const statCards = document.querySelectorAll('.stat-card');
                statCards.forEach(card => {
                    const valueTxt = card.querySelector('.stat-value').textContent;
                    if (valueTxt.includes('%')) {
                        const percentage = parseFloat(valueTxt);
                        // 进度条逻辑...
                    }
                });
            }
        </script>
    </body>
    </html>
    """
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(html_template)
    
    print(f"HTML报告已生成: {output_path}")
    return output_path

# 使用示例
if __name__ == "__main__":
    # 原始数据（示例）
    data = {
        "有效牌谱数": 89,
        "平均顺位": 2.3258,
        "一位率": 0.2697,
        "和了率": 0.2436,
        "立直率": 0.1683,
        "副露率": 0.3987,
        # 其他数据...
    }
    original_series = pd.Series(data)

    # 数据分段
    series_sections = [
        ("基础统计", original_series[["有效牌谱数", "平均顺位"]]),
        ("和牌分析", original_series[["一位率", "和了率"]]),
        ("战术特征", original_series[["立直率", "副露率"]])
    ]

    # 生成报告
    generate_html_report(
        player_name="示例用户",
        image_dir="./images",
        series_sections=series_sections,
        output_path="./analysis_report.html"
    )