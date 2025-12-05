"""
인터랙티브 반도체 공정 시뮬레이터
NotebookLM과의 핵심 차별점 - 실시간 파라미터 조작 및 시각화
"""

import gradio as gr
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


class ProcessSimulator:
    """반도체 공정 시뮬레이터"""
    
    def __init__(self):
        self.current_process = None
    
    def simulate_cvd(self, pressure, temperature, flow_rate, time):
        """CVD 공정 시뮬레이션"""
        
        # 증착 속도 모델 (경험식 기반)
        # Rate ∝ P * exp(-Ea/kT) * FlowRate
        Ea = 0.5  # 활성화 에너지 (eV)
        k = 8.617e-5  # 볼츠만 상수 (eV/K)
        T_kelvin = temperature + 273.15
        
        base_rate = pressure * np.exp(-Ea / (k * T_kelvin)) * (flow_rate / 100)
        deposition_rate = base_rate * 50  # nm/min
        
        # 박막 두께
        thickness = deposition_rate * time
        
        # 균일도 (압력이 낮고 온도가 적절할수록 좋음)
        uniformity = 100 - abs(pressure - 5) * 2 - abs(temperature - 400) * 0.05
        uniformity = max(min(uniformity, 100), 60)
        
        # 입자 형성 위험 (압력이 높을수록 위험)
        particle_risk = (pressure / 50) * 100
        particle_risk = min(particle_risk, 100)
        
        # 결정성 (온도가 높을수록 좋음)
        crystallinity = min((temperature / 600) * 100, 100)
        
        return {
            'deposition_rate': deposition_rate,
            'thickness': thickness,
            'uniformity': uniformity,
            'particle_risk': particle_risk,
            'crystallinity': crystallinity
        }
    
    def simulate_rie(self, rf_power, pressure, gas_ratio, time):
        """RIE 식각 시뮬레이션"""
        
        # 식각 속도 (RF 파워와 압력에 비례)
        etch_rate = (rf_power / 100) * (pressure / 10) * 80  # nm/min
        
        # 식각 깊이
        etch_depth = etch_rate * time
        
        # 이방성 (RF 파워가 높고 압력이 낮을수록 이방성↑)
        anisotropy = (rf_power / 200) * (20 / pressure) * 100
        anisotropy = min(anisotropy, 100)
        
        # 선택비 (가스 비율 CF4/O2에 따라 변화)
        # CF4가 많으면 SiO2 식각↑, O2가 많으면 PR 제거↑
        selectivity = 10 - abs(gas_ratio - 80) * 0.05
        selectivity = max(selectivity, 1)
        
        # 표면 거칠기 (파워가 너무 높으면 거칠어짐)
        roughness = abs(rf_power - 150) * 0.02
        roughness = max(roughness, 0.1)
        
        return {
            'etch_rate': etch_rate,
            'etch_depth': etch_depth,
            'anisotropy': anisotropy,
            'selectivity': selectivity,
            'roughness': roughness
        }
    
    def simulate_sputtering(self, dc_power, pressure, ar_flow, substrate_temp):
        """스퍼터링 증착 시뮬레이션"""
        
        # 증착 속도 (DC 파워에 비례, 압력 최적점 존재)
        pressure_factor = 1 - abs(pressure - 3) * 0.1
        pressure_factor = max(pressure_factor, 0.3)
        
        deposition_rate = (dc_power / 200) * pressure_factor * (ar_flow / 50) * 100
        
        # 박막 밀도 (기판 온도가 높을수록 밀도↑)
        density = min((substrate_temp / 300) * 100, 100)
        
        # 비저항 (밀도와 결정성에 반비례)
        resistivity = 1e-3 / (density / 100)
        
        # 부착력 (기판 온도가 적절할수록 좋음)
        adhesion = 100 - abs(substrate_temp - 250) * 0.2
        adhesion = max(min(adhesion, 100), 40)
        
        return {
            'deposition_rate': deposition_rate,
            'density': density,
            'resistivity': resistivity,
            'adhesion': adhesion
        }
    
    def create_3d_profile(self, process_type, params):
        """3D 박막/식각 프로파일 시각화"""
        
        x = np.linspace(-5, 5, 50)
        y = np.linspace(-5, 5, 50)
        X, Y = np.meshgrid(x, y)
        
        if process_type == 'cvd':
            # 박막 두께 프로파일 (균일도 반영)
            uniformity = params['uniformity']
            Z = params['thickness'] * (1 + 0.01 * (100 - uniformity) * (X**2 + Y**2) / 50)
        
        elif process_type == 'rie':
            # 식각 프로파일 (이방성 반영)
            anisotropy = params['anisotropy']
            # 이방성이 높으면 수직, 낮으면 언더컷
            undercut = (100 - anisotropy) / 200
            Z = -params['etch_depth'] * (1 - undercut * (X**2 + Y**2) / 50)
        
        else:  # sputtering
            Z = params.get('thickness', 0) * np.ones_like(X)
        
        return X, Y, Z
    
    def get_recommendations(self, process_type, params):
        """공정 파라미터 추천"""
        
        recommendations = []
        warnings = []
        
        if process_type == 'cvd':
            if params['uniformity'] < 85:
                recommendations.append("💡 균일도 개선: 압력을 5mTorr 근처로 조정하세요")
            if params['particle_risk'] > 60:
                warnings.append("⚠️ 입자 형성 위험: 압력을 낮추세요 (< 10mTorr)")
            if params['crystallinity'] < 70:
                recommendations.append("💡 결정성 향상: 온도를 500℃ 이상으로 높이세요")
            if params['deposition_rate'] < 50:
                recommendations.append("💡 증착 속도 증가: 가스 유량을 높이세요")
        
        elif process_type == 'rie':
            if params['anisotropy'] < 70:
                recommendations.append("💡 이방성 향상: RF 파워를 높이고 압력을 낮추세요")
            if params['selectivity'] < 5:
                warnings.append("⚠️ 선택비 부족: CF4/O2 비율을 조정하세요")
            if params['roughness'] > 5:
                warnings.append("⚠️ 표면 거칠기 과다: RF 파워를 낮추세요")
        
        return recommendations, warnings


def create_simulator_interface():
    """시뮬레이터 Gradio 인터페이스"""
    
    simulator = ProcessSimulator()
    
    with gr.Blocks(theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🔬 반도체 공정 인터랙티브 시뮬레이터
        ### 실시간 파라미터 조작으로 공정 이해하기
        
        **NotebookLM과의 차별점**: 텍스트 설명이 아닌 **직접 체험**하며 배우기!
        """)
        
        with gr.Tabs():
            # === CVD 시뮬레이터 ===
            with gr.Tab("🔹 CVD 공정"):
                gr.Markdown("""
                ### Chemical Vapor Deposition
                화학 기상 증착 공정의 주요 파라미터를 조작하며 결과를 실시간 확인하세요.
                """)
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### 공정 파라미터")
                        
                        cvd_pressure = gr.Slider(
                            1, 50, value=5, step=1,
                            label="압력 (mTorr)",
                            info="낮을수록 균일하지만 느림"
                        )
                        cvd_temp = gr.Slider(
                            200, 800, value=400, step=10,
                            label="온도 (℃)",
                            info="높을수록 결정성↑, 하지만 열 손상 주의"
                        )
                        cvd_flow = gr.Slider(
                            50, 500, value=200, step=10,
                            label="가스 유량 (sccm)",
                            info="전구체 공급량"
                        )
                        cvd_time = gr.Slider(
                            1, 60, value=10, step=1,
                            label="증착 시간 (분)"
                        )
                        
                        cvd_run = gr.Button("▶️ 시뮬레이션 실행", variant="primary")
                    
                    with gr.Column():
                        gr.Markdown("#### 실시간 결과")
                        cvd_results = gr.Markdown()
                        cvd_plot = gr.Plot(label="박막 특성 그래프")
                        cvd_3d = gr.Plot(label="3D 박막 프로파일")
                        cvd_recommendations = gr.Markdown()
                
                def run_cvd_sim(p, t, f, time):
                    results = simulator.simulate_cvd(p, t, f, time)
                    
                    # 결과 텍스트
                    result_text = f"""
### 📊 CVD 시뮬레이션 결과

| 항목 | 값 | 평가 |
|------|-----|------|
| **증착 속도** | {results['deposition_rate']:.1f} nm/min | {'✅ 양호' if results['deposition_rate'] > 50 else '⚠️ 느림'} |
| **박막 두께** | {results['thickness']:.1f} nm | - |
| **균일도** | {results['uniformity']:.1f}% | {'✅ 우수' if results['uniformity'] > 90 else '⚠️ 개선 필요' if results['uniformity'] > 80 else '❌ 불량'} |
| **입자 위험도** | {results['particle_risk']:.1f}% | {'✅ 안전' if results['particle_risk'] < 30 else '⚠️ 주의' if results['particle_risk'] < 60 else '❌ 위험'} |
| **결정성** | {results['crystallinity']:.1f}% | {'✅ 양호' if results['crystallinity'] > 70 else '⚠️ 개선 필요'} |
"""
                    
                    # 그래프
                    fig = make_subplots(
                        rows=2, cols=2,
                        subplot_titles=("증착 속도", "균일도", "입자 위험", "결정성"),
                        specs=[[{"type": "indicator"}, {"type": "indicator"}],
                               [{"type": "indicator"}, {"type": "indicator"}]]
                    )
                    
                    # 게이지 차트
                    fig.add_trace(go.Indicator(
                        mode="gauge+number",
                        value=results['deposition_rate'],
                        title={'text': "nm/min"},
                        gauge={'axis': {'range': [0, 200]},
                               'bar': {'color': "darkblue"},
                               'steps': [{'range': [0, 50], 'color': "lightgray"},
                                        {'range': [50, 100], 'color': "gray"}],
                               'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 150}}
                    ), row=1, col=1)
                    
                    fig.add_trace(go.Indicator(
                        mode="gauge+number+delta",
                        value=results['uniformity'],
                        title={'text': "%"},
                        delta={'reference': 95},
                        gauge={'axis': {'range': [60, 100]},
                               'bar': {'color': "green" if results['uniformity'] > 90 else "orange"},
                               'steps': [{'range': [60, 80], 'color': "lightcoral"},
                                        {'range': [80, 90], 'color': "lightyellow"},
                                        {'range': [90, 100], 'color': "lightgreen"}]}
                    ), row=1, col=2)
                    
                    fig.add_trace(go.Indicator(
                        mode="gauge+number",
                        value=results['particle_risk'],
                        title={'text': "위험도 %"},
                        gauge={'axis': {'range': [0, 100]},
                               'bar': {'color': "red" if results['particle_risk'] > 60 else "orange" if results['particle_risk'] > 30 else "green"},
                               'steps': [{'range': [0, 30], 'color': "lightgreen"},
                                        {'range': [30, 60], 'color': "lightyellow"},
                                        {'range': [60, 100], 'color': "lightcoral"}]}
                    ), row=2, col=1)
                    
                    fig.add_trace(go.Indicator(
                        mode="gauge+number",
                        value=results['crystallinity'],
                        title={'text': "%"},
                        gauge={'axis': {'range': [0, 100]},
                               'bar': {'color': "purple"}}
                    ), row=2, col=2)
                    
                    fig.update_layout(height=500)
                    
                    # 3D 프로파일
                    X, Y, Z = simulator.create_3d_profile('cvd', results)
                    
                    fig_3d = go.Figure(data=[go.Surface(x=X, y=Y, z=Z, colorscale='Viridis')])
                    fig_3d.update_layout(
                        title="박막 두께 프로파일 (균일도 반영)",
                        scene=dict(
                            xaxis_title="X (mm)",
                            yaxis_title="Y (mm)",
                            zaxis_title="두께 (nm)"
                        ),
                        height=400
                    )
                    
                    # 추천사항
                    recommendations, warnings = simulator.get_recommendations('cvd', results)
                    
                    rec_text = "\n### 🎯 추천 사항\n\n"
                    if warnings:
                        rec_text += "**경고:**\n" + "\n".join(warnings) + "\n\n"
                    if recommendations:
                        rec_text += "**개선 제안:**\n" + "\n".join(recommendations)
                    else:
                        rec_text += "✅ **최적 조건입니다!**"
                    
                    return result_text, fig, fig_3d, rec_text
                
                cvd_run.click(
                    run_cvd_sim,
                    inputs=[cvd_pressure, cvd_temp, cvd_flow, cvd_time],
                    outputs=[cvd_results, cvd_plot, cvd_3d, cvd_recommendations]
                )
            
            # === RIE 시뮬레이터 ===
            with gr.Tab("⚡ RIE 식각"):
                gr.Markdown("""
                ### Reactive Ion Etching
                플라즈마 식각 공정을 시뮬레이션하고 이방성과 선택비를 최적화하세요.
                """)
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### 공정 파라미터")
                        
                        rie_power = gr.Slider(
                            50, 300, value=150, step=10,
                            label="RF 파워 (W)",
                            info="높을수록 식각 빠르지만 거칠어짐"
                        )
                        rie_pressure = gr.Slider(
                            1, 50, value=10, step=1,
                            label="압력 (mTorr)",
                            info="낮을수록 이방성↑"
                        )
                        rie_gas = gr.Slider(
                            0, 100, value=80, step=5,
                            label="CF₄ 비율 (%)",
                            info="나머지는 O₂, 비율이 선택비 결정"
                        )
                        rie_time = gr.Slider(
                            1, 30, value=5, step=1,
                            label="식각 시간 (분)"
                        )
                        
                        rie_run = gr.Button("▶️ 시뮬레이션 실행", variant="primary")
                    
                    with gr.Column():
                        gr.Markdown("#### 실시간 결과")
                        rie_results = gr.Markdown()
                        rie_plot = gr.Plot()
                        rie_3d = gr.Plot(label="3D 식각 프로파일")
                
                def run_rie_sim(power, pressure, gas, time):
                    results = simulator.simulate_rie(power, pressure, gas, time)
                    
                    result_text = f"""
### 📊 RIE 시뮬레이션 결과

| 항목 | 값 | 평가 |
|------|-----|------|
| **식각 속도** | {results['etch_rate']:.1f} nm/min | {'✅ 빠름' if results['etch_rate'] > 80 else '⚠️ 보통'} |
| **식각 깊이** | {results['etch_depth']:.1f} nm | - |
| **이방성** | {results['anisotropy']:.1f}% | {'✅ 우수' if results['anisotropy'] > 80 else '⚠️ 개선 필요'} |
| **선택비** | {results['selectivity']:.1f}:1 | {'✅ 양호' if results['selectivity'] > 5 else '⚠️ 낮음'} |
| **표면 거칠기** | {results['roughness']:.2f} nm RMS | {'✅ 매끄러움' if results['roughness'] < 2 else '⚠️ 거침'} |
"""
                    
                    # 3D 프로파일
                    X, Y, Z = simulator.create_3d_profile('rie', results)
                    
                    fig_3d = go.Figure(data=[go.Surface(x=X, y=Y, z=Z, colorscale='RdBu')])
                    fig_3d.update_layout(
                        title=f"식각 프로파일 (이방성 {results['anisotropy']:.0f}%)",
                        scene=dict(
                            xaxis_title="X (μm)",
                            yaxis_title="Y (μm)",
                            zaxis_title="깊이 (nm)"
                        ),
                        height=400
                    )
                    
                    # 간단한 결과 그래프
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=['식각 속도', '이방성', '선택비×10', '거칠기×10'],
                        y=[results['etch_rate'], results['anisotropy'], 
                           results['selectivity']*10, results['roughness']*10],
                        marker_color=['blue', 'green', 'orange', 'red']
                    ))
                    fig.update_layout(title="RIE 특성 요약", yaxis_title="값", height=300)
                    
                    return result_text, fig, fig_3d
                
                rie_run.click(
                    run_rie_sim,
                    inputs=[rie_power, rie_pressure, rie_gas, rie_time],
                    outputs=[rie_results, rie_plot, rie_3d]
                )
        
        gr.Markdown("""
        ---
        ### 💡 학습 포인트
        
        이 시뮬레이터로 다음을 배울 수 있습니다:
        - 각 파라미터가 결과에 미치는 영향 **직접 체험**
        - 최적 조건을 찾는 **트레이드오프** 이해
        - 실제 공정 데이터와 **비교 학습**
        - 면접 질문 대비: "압력을 높이면 어떻게 되나요?" → 직접 확인!
        """)
    
    return demo


if __name__ == "__main__":
    demo = create_simulator_interface()
    demo.launch(server_name="0.0.0.0", server_port=7861, share=False)
