import streamlit as st
import time
import datetime
import json
from pathlib import Path
from threading import Thread
from typing import Dict, List, Optional

try:
    from pygame import mixer
except ImportError:
    mixer = None
    st.warning("pygameがインストールされていないため、音声再生は動作しません。")

class PresentationTimer:
    def __init__(self):
        self.COLORS = {
            'presentation': '#4169E1',
            'qa': '#FFD700',
            'overtime': '#FF4444'
        }
        
        self.SOUNDS = {
            'presentation_end': 'sounds/presentation_end.mp3',
            'qa_end': 'sounds/qa_end.mp3',
            'overtime': 'sounds/overtime.mp3'
        }
        
        self.sound_files = {}
        if mixer:
            self.initialize_mixer()
        self.setup_styles()
        self.initialize_state()
        self.load_presets()

    def initialize_mixer(self):
        """音声再生の初期化"""
        try:
            mixer.init()
            for sound_key, sound_path in self.SOUNDS.items():
                path = Path(sound_path)
                if path.exists():
                    self.sound_files[sound_key] = mixer.Sound(str(path))
                else:
                    default_bell = Path('bell.mp3')
                    if default_bell.exists():
                        self.sound_files[sound_key] = mixer.Sound(str(default_bell))
                    
            st.session_state.volume = st.session_state.get("volume", 0.5)
            for sound in self.sound_files.values():
                sound.set_volume(st.session_state.volume)
                
        except Exception as e:
            st.error(f"音声の初期化に失敗しました: {e}")

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
            @keyframes blink {
                from { opacity: 1; }
                to { opacity: 0.7; }
            }
            .preset-card {
                border: 1px solid #ddd;
                padding: 10px;
                margin: 5px 0;
                border-radius: 5px;
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
            "volume": 0.5,
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

    def save_presets(self):
        with open('presets.json', 'w', encoding='utf-8') as f:
            json.dump(st.session_state.presets, f, ensure_ascii=False)

    def play_sound(self, sound_key: str, count: int = 1):
        if sound_key in self.sound_files:
            for _ in range(count):
                self.sound_files[sound_key].play()
                time.sleep(1)

    def format_time(self, td):
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def countdown(self, presentation_mins: int, qa_mins: int, bell_count: int):
        if st.session_state.time_at_pause:
            remaining_time = datetime.datetime.strptime(st.session_state.time_at_pause, "%H:%M:%S")
            total_seconds = remaining_time.hour * 3600 + remaining_time.minute * 60 + remaining_time.second
            
            if st.session_state.current_phase == 'presentation':
                self.countdown_phase(total_seconds, 'presentation')
                if st.session_state.timer_running:
                    self.play_sound('presentation_end', bell_count)
                    self.countdown_phase(qa_mins * 60, 'qa')
            else:
                self.countdown_phase(total_seconds, 'qa')
            
            if st.session_state.timer_running:
                self.play_sound('qa_end', bell_count)
        else:
            self.countdown_phase(presentation_mins * 60, 'presentation')
            if st.session_state.timer_running:
                self.play_sound('presentation_end', bell_count)
                
                self.countdown_phase(qa_mins * 60, 'qa')
                if st.session_state.timer_running:
                    self.play_sound('qa_end', bell_count)

        if st.session_state.timer_running:
            st.session_state.is_overtime = True
            st.session_state.overtime_start = datetime.datetime.now()
            self.play_sound('overtime', 1)
            self.count_up()

    def countdown_phase(self, duration: int, phase: str):
        if duration <= 0:
            return

        end_time = datetime.datetime.now() + datetime.timedelta(seconds=duration)
        st.session_state.current_phase = phase
        st.session_state.is_overtime = False

        while datetime.datetime.now() < end_time and st.session_state.timer_running:
            if st.session_state.timer_paused:
                st.session_state.time_at_pause = self.format_time(end_time - datetime.datetime.now())
                st.session_state.pause_time = datetime.datetime.now()
                break
            remaining_time = end_time - datetime.datetime.now()
            st.session_state.remaining_time = self.format_time(remaining_time)
            time.sleep(1)

    def count_up(self):
        while st.session_state.timer_running:
            if st.session_state.timer_paused:
                break
            elapsed = datetime.datetime.now() - st.session_state.overtime_start
            st.session_state.remaining_time = "+" + self.format_time(elapsed)
            time.sleep(1)

    def render_ui(self):
        st.title("学会プレゼンタイマー")

        volume = st.slider(
            "音量", 
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.volume,
            step=0.1
        )
        if volume != st.session_state.volume:
            st.session_state.volume = volume
            for sound in self.sound_files.values():
                sound.set_volume(volume)

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

        bell_count = st.number_input(
            "ベルの回数", 
            min_value=1, 
            max_value=5, 
            value=st.session_state.get("last_bell_count", 1),
            key="bell_count"
        )

        st.session_state.last_presentation_duration = presentation_duration
        st.session_state.last_qa_duration = qa_duration
        st.session_state.last_bell_count = bell_count

        if not st.session_state.timer_running:
            if st.button("タイマー開始"):
                st.session_state.timer_running = True
                st.session_state.timer_paused = False
                st.session_state.is_overtime = False
                st.session_state.time_at_pause = None
                timer_thread = Thread(
                    target=self.countdown,
                    args=(presentation_duration, qa_duration, bell_count)
                )
                timer_thread.start()
        else:
            col1, col2 = st.columns(2)
            with col1:
                if not st.session_state.timer_paused:
                    if st.button("一時停止"):
                        st.session_state.timer_paused = True
                else:
                    if st.button("再開"):
                        st.session_state.timer_paused = False
                        if not st.session_state.is_overtime:
                            timer_thread = Thread(
                                target=self.countdown,
                                args=(presentation_duration, qa_duration, bell_count)
                            )
                            timer_thread.start()
                        else:
                            st.session_state.overtime_start = (
                                datetime.datetime.now() - 
                                (st.session_state.pause_time - st.session_state.overtime_start)
                            )
                            timer_thread = Thread(target=self.count_up)
                            timer_thread.start()
            
            with col2:
                if st.button("タイマー停止"):
                    st.session_state.timer_running = False
                    st.session_state.timer_paused = False
                    st.session_state.time_at_pause = None

        if st.session_state.timer_running or st.session_state.remaining_time != "00:00:00":
            if st.session_state.is_overtime:
                phase_text = "時間超過"
                bg_color = self.COLORS['overtime']
                extra_class = "overtime"
            else:
                phase_text = "発表" if st.session_state.current_phase == 'presentation' else "質疑応答"
                bg_color = self.COLORS[st.session_state.current_phase]
                extra_class = ""
            
            if st.session_state.timer_paused:
                phase_text += "（一時停止中）"
            
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
