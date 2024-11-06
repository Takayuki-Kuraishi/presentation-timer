import streamlit as st
import datetime
import json
from pathlib import Path

class PresentationTimer:
    def __init__(self):
        self.COLORS = {
            'presentation': '#4169E1',
            'qa': '#FFD700',
            'overtime': '#FF4444'
        }
        
        self.setup_styles()
        self.initialize_state()
        self.load_presets()

    def setup_styles(self):
        st.markdown("""
            <style>
            .timer {
                font-size: 72px;
                font-family: monospace;
                color: black;
                text-align: center;
                background-color: var(--timer-bg, #4169E1);
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
            }
            .label {
                font-size: 36px;
                color: black;
                text-align: center;
                padding-top: 10px;
                font-weight: bold;
            }
            .overtime {
                animation: blink 1s ease-in-out infinite alternate;
            }
            </style>
            """, unsafe_allow_html=True)

    def initialize_state(self):
        default_states = {
            "timer_running": False,
            "timer_paused": False,
            "current_phase": 'presentation',
            "remaining_time": "00:00:00",
            "is_overtime": False,
            "overtime_start": None,
            "pause_time": None,
            "time_at_pause": None,
            "presets": []
        }
        
        for key, default_value in default_states.items():
            if key not in st.session_state:
                st.session_state[key] = default_value

    def load_presets(self):
        preset_file = Path('presets.json')
        if preset_file.exists():
            try:
                with open(preset_file, 'r', encoding='utf-8') as f:
                    st.session_state.presets = json.load(f)
            except:
                st.session_state.presets = []

    def format_time(self, td):
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def render_ui(self):
        st.title("学会プレゼンタイマー")

        col1, col2 = st.columns(2)
        with col1:
            presentation_duration = st.number_input(
                "発表時間（分）", 
                min_value=1, 
                max_value=60, 
                value=st.session_state.get("last_presentation_duration", 10),
                key="presentation_duration"
            )
        with col2:
            qa_duration = st.number_input(
                "質疑応答時間（分）", 
                min_value=1, 
                max_value=30, 
                value=st.session_state.get("last_qa_duration", 5),
                key="qa_duration"
            )

        st.session_state.last_presentation_duration = presentation_duration
        st.session_state.last_qa_duration = qa_duration

        # タイマーの制御ボタン
        if not st.session_state.timer_running:
            if st.button("タイマー開始"):
                st.session_state.timer_running = True
                st.session_state.timer_paused = False
                st.session_state.is_overtime = False
                st.session_state.start_time = datetime.datetime.now()
                st.session_state.target_duration = datetime.timedelta(
                    minutes=presentation_duration + qa_duration
                )
        else:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("タイマー停止"):
                    st.session_state.timer_running = False

        if st.session_state.timer_running:
            elapsed_time = datetime.datetime.now() - st.session_state.start_time
            target_duration = st.session_state.target_duration

            remaining_time = target_duration - elapsed_time
            if remaining_time.total_seconds() <= 0:
                st.session_state.timer_running = False
                st.session_state.is_overtime = True
                st.session_state.remaining_time = "+" + self.format_time(-remaining_time)
            else:
                st.session_state.remaining_time = self.format_time(remaining_time)

            st.experimental_rerun()  # ページを再描画してリアルタイム更新

        # タイマーと現在のフェーズの表示
        if st.session_state.timer_running or st.session_state.remaining_time != "00:00:00":
            if st.session_state.is_overtime:
                phase_text = "時間超過"
                bg_color = self.COLORS['overtime']
                extra_class = "overtime"
            else:
                phase_text = "発表" if st.session_state.current_phase == 'presentation' else "質疑応答"
                bg_color = self.COLORS[st.session_state.current_phase]
                extra_class = ""
            
            st.markdown(
                f"""
                <div class='timer {extra_class}' style='--timer-bg: {bg_color};'>
                    {st.session_state.remaining_time}
                </div>
                <div class='label' style='color: {bg_color};'>{phase_text}</div>
                """,
                unsafe_allow_html=True
            )

def main():
    timer = PresentationTimer()
    timer.render_ui()

if __name__ == "__main__":
    main()
