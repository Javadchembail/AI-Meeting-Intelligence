import base64
import html
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


def render_header() -> None:
    """Render the main application header."""

    st.html(
        """
        <div style="
            display:flex;
            align-items:center;
            gap:16px;
            margin-bottom:0.5rem;
        ">

            <div style="
                font-size:3.2rem;
                filter:drop-shadow(
                    0 0 14px rgba(129,140,248,0.45)
                );
            ">
                🎙️
            </div>

            <div>

                <div class="main-title">
                    AI Meeting Intelligence
                </div>

                <div class="subtitle">
                    Your intelligent meeting companion
                    <span style="color:#818cf8;"> • </span>
                    Listen
                    <span style="color:#818cf8;"> • </span>
                    Understand
                    <span style="color:#818cf8;"> • </span>
                    Remember
                </div>

            </div>

        </div>
        """
    )


def render_hero() -> None:
    """Render the landing-page hero section."""

    st.html(
        """
        <div class="hero-card">

            <div class="hero-icon">
                🎧
            </div>

            <div class="hero-title">
                Ready to capture your meeting?
            </div>

            <div class="hero-description">
                Record conversations, generate transcripts,
                and let AI turn your meeting into actionable intelligence.
            </div>

            <div style="
                display:flex;
                justify-content:center;
                gap:28px;
                flex-wrap:wrap;
                margin-top:1.2rem;
                color:#94a3b8;
                font-size:0.85rem;
            ">

                <span>
                    🎙️ High-quality recording
                </span>

                <span>
                    📝 Live transcription
                </span>

                <span>
                    🧠 AI analysis
                </span>

            </div>

        </div>
        """
    )


def render_end_meeting_button() -> bool:
    """Render the End Meeting button."""

    col1, col2, col3 = st.columns(
        [1, 2, 1]
    )

    with col2:

        return st.button(
            "⏹️  End Meeting",
            use_container_width=True,
            key="end_meeting_button",
        )


def render_empty_state() -> None:
    """Render the empty dashboard state."""

    st.html(
        """
        <div style="
            text-align:center;
            padding:2rem 1rem 1rem;
            color:#64748b;
        ">

            <div style="
                font-size:2rem;
                margin-bottom:0.5rem;
            ">
                ✨
            </div>

            <div style="
                font-size:0.95rem;
                color:#94a3b8;
            ">
                Your next intelligent meeting starts here.
            </div>

            <div style="
                font-size:0.8rem;
                margin-top:0.35rem;
            ">
                Click Start Meeting when you're ready.
            </div>

        </div>
        """
    )


def render_capability_cards() -> None:
    """Render product capability cards."""

    col1, col2, col3 = st.columns(3)

    cards = [
        (
            col1,
            "🎙️",
            "Smart Recording",
            "Capture clear meeting audio with automatic level control.",
        ),
        (
            col2,
            "📝",
            "Live Transcript",
            "Watch your conversation turn into text while you speak.",
        ),
        (
            col3,
            "🧠",
            "AI Intelligence",
            "Extract summaries, decisions and actionable tasks.",
        ),
    ]

    for column, icon, title, description in cards:

        with column:

            st.html(
                f"""
                <div style="
                    min-height:150px;
                    padding:1.35rem;
                    border-radius:18px;

                    background:
                        linear-gradient(
                            145deg,
                            rgba(15,23,42,0.78),
                            rgba(30,27,75,0.48)
                        );

                    border:
                        1px solid rgba(
                            148,
                            163,
                            184,
                            0.12
                        );

                    box-shadow:
                        0 10px 30px
                        rgba(0,0,0,0.18);
                ">

                    <div style="
                        font-size:1.8rem;
                        margin-bottom:0.65rem;
                    ">
                        {icon}
                    </div>

                    <div style="
                        font-size:0.98rem;
                        font-weight:700;
                        color:#f8fafc;
                        margin-bottom:0.35rem;
                    ">
                        {title}
                    </div>

                    <div style="
                        color:#94a3b8;
                        font-size:0.78rem;
                        line-height:1.55;
                    ">
                        {description}
                    </div>

                </div>
                """
            )


def render_recording_status(
    duration: str = "00:00:00",
    audio_level: float = 0.0,
) -> None:
    """Render the live recording interface driven by real microphone level."""

    audio_level = max(0.0, min(1.0, float(audio_level)))

    bar_multipliers = [
        0.42, 0.58, 0.72, 0.50, 0.86, 0.64,
        0.94, 0.76, 1.00, 0.68, 0.88, 0.55,
        0.78, 0.96, 0.61, 0.84, 0.48, 0.73,
        0.91, 0.57, 0.82, 0.98, 0.66, 0.44,
        0.70, 0.90, 0.53, 0.75, 0.86, 0.62,
        0.45,
    ]

    bars_html = ""
    for index, multiplier in enumerate(bar_multipliers):
        height = 6 + 76 * audio_level * multiplier
        bars_html += f"""
        <span class="voice-bar" style="--bar-height:{height:.1f}px; animation-delay:{-(index * 0.045):.3f}s;"></span>
        """

    glow_opacity = 0.18 + (audio_level * 0.65)

    recording_html = """
<style>
@keyframes voicePulse {
    0%, 100% { transform:scaleY(0.72); opacity:0.72; }
    50% { transform:scaleY(1); opacity:1; }
}
@keyframes recordingDot {
    0%, 100% { transform:scale(1); opacity:1; }
    50% { transform:scale(1.45); opacity:0.45; }
}
.voice-bar {
    display:block; width:5px; height:var(--bar-height); min-height:6px;
    border-radius:999px; transform-origin:center;
    background:linear-gradient(180deg,#c4b5fd 0%,#8b5cf6 45%,#6366f1 100%);
    box-shadow:0 0 8px rgba(129,140,248,0.75),0 0 18px rgba(99,102,241,0.35);
    animation:voicePulse 0.65s ease-in-out infinite;
    transition:height 0.18s ease-out,opacity 0.18s ease-out;
}
.live-wave-container {
    display:flex; align-items:center; justify-content:center; gap:5px;
    height:100px; margin-top:1.1rem; padding:0 1rem;
}
.live-wave-glow {
    position:absolute; width:300px; height:90px; border-radius:50%;
    background:radial-gradient(ellipse,rgba(99,102,241,0.20),transparent 70%);
    filter:blur(12px); pointer-events:none; transition:opacity 0.25s ease;
}
.live-audio-label {
    text-align:center; color:#818cf8; font-size:0.68rem; font-weight:700;
    letter-spacing:0.16em; margin-top:0.2rem;
}
</style>

<div style="position:relative;overflow:hidden;padding:2rem;border-radius:26px;
background:radial-gradient(circle at 50% 100%,rgba(99,102,241,0.20),transparent 40%),
linear-gradient(135deg,rgba(69,10,10,0.34),rgba(15,23,42,0.96) 58%,rgba(30,27,75,0.90));
border:1px solid rgba(248,113,113,0.24);box-shadow:0 25px 70px rgba(0,0,0,0.38);margin-bottom:1.4rem;">

<div style="position:absolute;width:280px;height:280px;right:-120px;top:-180px;border-radius:50%;
background:radial-gradient(circle,rgba(139,92,246,0.20),transparent 70%);pointer-events:none;"></div>

<div style="display:flex;align-items:center;justify-content:center;gap:9px;color:#fca5a5;font-size:0.78rem;font-weight:800;letter-spacing:0.14em;text-transform:uppercase;">
<span style="display:block;width:12px;height:12px;border-radius:50%;background:#ef4444;box-shadow:0 0 8px #ef4444,0 0 20px rgba(239,68,68,0.70);animation:recordingDot 1s ease-in-out infinite;"></span>
Recording in progress
</div>

<div style="text-align:center;margin-top:1.1rem;">
<div style="color:#64748b;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.18em;">Recording Time</div>
<div style="color:#ffffff;font-size:3.8rem;line-height:1.1;font-weight:900;letter-spacing:0.04em;margin-top:0.25rem;text-shadow:0 0 30px rgba(129,140,248,0.25);">__DURATION__</div>
</div>

<div class="live-wave-container">
<div class="live-wave-glow" style="opacity:__GLOW_OPACITY__;"></div>
__WAVEFORM__
</div>

<div class="live-audio-label">● LIVE AUDIO</div>
</div>
"""

    recording_html = (
        recording_html
        .replace("__DURATION__", html.escape(duration))
        .replace("__WAVEFORM__", bars_html)
        .replace("__GLOW_OPACITY__", f"{glow_opacity:.2f}")
    )

    st.html(recording_html)


def render_meeting_metrics(
    duration: str = "00:00:00",
    words: int = 0,
    participants: int = 0,
) -> None:
    """Render meeting statistics."""

    metrics = [
        ("⏱️", "Duration", duration),
        ("💬", "Words", str(words)),
        ("👥", "Participants", str(participants)),
    ]

    columns = st.columns(3)

    for column, (
        icon,
        label,
        value,
    ) in zip(
        columns,
        metrics,
    ):

        with column:

            st.html(
                f"""
                <div class="metric-card">

                    <div style="
                        font-size:1.2rem;
                        margin-bottom:0.35rem;
                    ">
                        {icon}
                    </div>

                    <div class="metric-label">
                        {label}
                    </div>

                    <div class="metric-value">
                        {value}
                    </div>

                </div>
                """
            )


def render_transcript_panel(
    transcript: str = "",
) -> None:
    """Render a large readable transcript panel."""

    st.html(
        """
        <div class="content-title">
            📝 Transcript
        </div>
        """
    )

    if transcript and transcript.strip():

        safe_transcript = html.escape(
            transcript
        )

        st.html(
            f"""
            <div class="content-card">

                <div class="transcript-box"
                     style="
                        font-size:1.08rem;
                        line-height:2.05;
                        min-height:420px;
                     ">

                    {safe_transcript}

                </div>

            </div>
            """
        )

    else:

        st.html(
            """
            <div class="content-card">

                <div style="
                    min-height:360px;

                    display:flex;
                    flex-direction:column;

                    align-items:center;
                    justify-content:center;

                    text-align:center;
                ">

                    <div style="
                        font-size:2.7rem;
                        margin-bottom:0.9rem;
                    ">
                        🎧
                    </div>

                    <div style="
                        color:#ffffff;
                        font-size:1rem;
                        font-weight:700;
                        margin-bottom:0.4rem;
                    ">
                        Listening for conversation...
                    </div>

                    <div style="
                        color:#64748b;
                        font-size:0.82rem;
                    ">
                        Your live transcript will appear here.
                    </div>

                </div>

            </div>
            """
        )


def render_synced_audio_transcript(
    audio_path: str | None,
    words: list[dict],
) -> None:
    """
    Render a premium synchronized audio player
    with clickable word-level transcript.
    """

    if not audio_path:

        st.error(
            "No recording is available."
        )

        return

    path = Path(audio_path)

    if not path.exists():

        st.error(
            "The recording file could not be found."
        )

        return

    if not words:

        st.warning(
            "Word timestamps are not available "
            "for this recording."
        )

        return

    try:

        audio_bytes = path.read_bytes()

        audio_base64 = (
            base64.b64encode(
                audio_bytes
            ).decode("utf-8")
        )

        transcript_words = []

        valid_index = 0

        for word_data in words:

            word = str(
                word_data.get(
                    "word",
                    "",
                )
            ).strip()

            if not word:
                continue

            start = float(
                word_data.get(
                    "start",
                    0,
                )
            )

            end = float(
                word_data.get(
                    "end",
                    0,
                )
            )

            safe_word = html.escape(
                word
            )

            transcript_words.append(
                '<span '
                'class="transcript-word" '
                f'data-index="{valid_index}" '
                f'data-start="{start}" '
                f'data-end="{end}"'
                '>'
                f'{safe_word}'
                '</span>'
            )

            valid_index += 1

        transcript_html = " ".join(
            transcript_words
        )

        player_html = """
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<style>

* {
    box-sizing:border-box;
}

body {

    margin:0;
    padding:0;

    background:transparent;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;

    color:#ffffff;
}


.player {

    padding:24px;

    border-radius:24px;

    background:
        radial-gradient(
            circle at 50% 0%,
            rgba(99,102,241,0.15),
            transparent 38%
        ),

        linear-gradient(
            145deg,
            rgba(30,27,75,0.92),
            rgba(15,23,42,0.97)
        );

    border:
        1px solid
        rgba(167,139,250,0.22);

    box-shadow:
        0 25px 70px
        rgba(0,0,0,0.35);
}


/* HEADER */

.player-header {

    display:flex;

    align-items:center;

    justify-content:space-between;

    margin-bottom:20px;
}


.player-title {

    display:flex;

    align-items:center;

    gap:10px;

    color:#f8fafc;

    font-size:0.95rem;

    font-weight:800;
}


.player-icon {

    width:38px;
    height:38px;

    display:flex;

    align-items:center;
    justify-content:center;

    border-radius:12px;

    background:
        linear-gradient(
            135deg,
            #6366f1,
            #a855f7
        );

    box-shadow:
        0 8px 24px
        rgba(99,102,241,0.30);
}


.audio-status {

    display:flex;

    align-items:center;

    gap:6px;

    color:#94a3b8;

    font-size:0.7rem;

    text-transform:uppercase;

    letter-spacing:0.1em;
}


.status-dot {

    width:7px;
    height:7px;

    border-radius:50%;

    background:#34d399;

    box-shadow:
        0 0 10px
        rgba(52,211,153,0.75);
}


/* CONTROLS */

.controls {

    display:flex;

    align-items:center;

    gap:16px;
}


.play-button {

    width:58px;
    height:58px;

    flex-shrink:0;

    border:0;

    border-radius:50%;

    cursor:pointer;

    color:white;

    font-size:1.35rem;

    display:flex;

    align-items:center;
    justify-content:center;

    background:
        linear-gradient(
            135deg,
            #6366f1,
            #8b5cf6
        );

    box-shadow:
        0 10px 30px
        rgba(99,102,241,0.38);

    transition:
        transform 0.18s ease,
        box-shadow 0.18s ease;
}


.play-button:hover {

    transform:scale(1.06);

    box-shadow:
        0 14px 36px
        rgba(99,102,241,0.48);
}


.play-button:active {

    transform:scale(0.97);
}


.timeline-area {

    flex:1;

    min-width:0;
}


.time-row {

    display:flex;

    align-items:center;

    justify-content:space-between;

    margin-bottom:9px;

    color:#94a3b8;

    font-size:0.72rem;

    font-variant-numeric:tabular-nums;
}


/* PROGRESS */

.progress-track {

    position:relative;

    width:100%;

    height:7px;

    border-radius:999px;

    cursor:pointer;

    background:
        rgba(148,163,184,0.15);
}


.progress-fill {

    position:absolute;

    top:0;
    left:0;

    width:0%;

    height:100%;

    border-radius:999px;

    background:
        linear-gradient(
            90deg,
            #6366f1,
            #a855f7
        );

    box-shadow:
        0 0 15px
        rgba(129,140,248,0.55);
}


.progress-thumb {

    position:absolute;

    top:50%;
    left:0%;

    width:15px;
    height:15px;

    border-radius:50%;

    transform:
        translate(-50%,-50%);

    background:#ffffff;

    box-shadow:
        0 0 0 4px
        rgba(129,140,248,0.18),

        0 0 14px
        rgba(129,140,248,0.65);
}


/* VOLUME */

.volume-area {

    display:flex;

    align-items:center;

    gap:7px;

    color:#94a3b8;
}


.volume-slider {

    width:70px;

    accent-color:#818cf8;

    cursor:pointer;
}


/* PLAYER VISUALIZER */

.visualizer {

    height:42px;

    margin-top:20px;

    display:flex;

    align-items:center;

    justify-content:center;

    gap:4px;

    opacity:0.9;
}


.visual-bar {

    width:4px;

    border-radius:999px;

    background:
        linear-gradient(
            180deg,
            #a78bfa,
            #6366f1
        );

    animation:
        player-wave
        1.05s
        ease-in-out
        infinite;

    animation-play-state:paused;
}


.player.playing .visual-bar {

    animation-play-state:running;
}


.visual-bar:nth-child(1) {
    height:12px;
    animation-delay:-0.1s;
}

.visual-bar:nth-child(2) {
    height:20px;
    animation-delay:-0.2s;
}

.visual-bar:nth-child(3) {
    height:28px;
    animation-delay:-0.3s;
}

.visual-bar:nth-child(4) {
    height:18px;
    animation-delay:-0.4s;
}

.visual-bar:nth-child(5) {
    height:35px;
    animation-delay:-0.5s;
}

.visual-bar:nth-child(6) {
    height:24px;
    animation-delay:-0.6s;
}

.visual-bar:nth-child(7) {
    height:31px;
    animation-delay:-0.7s;
}

.visual-bar:nth-child(8) {
    height:38px;
    animation-delay:-0.8s;
}

.visual-bar:nth-child(9) {
    height:26px;
    animation-delay:-0.9s;
}

.visual-bar:nth-child(10) {
    height:34px;
    animation-delay:-1.0s;
}

.visual-bar:nth-child(11) {
    height:20px;
    animation-delay:-0.25s;
}

.visual-bar:nth-child(12) {
    height:30px;
    animation-delay:-0.45s;
}

.visual-bar:nth-child(13) {
    height:16px;
    animation-delay:-0.65s;
}


@keyframes player-wave {

    0%,
    100% {
        transform:scaleY(0.35);
        opacity:0.55;
    }

    50% {
        transform:scaleY(1);
        opacity:1;
    }
}


/* TRANSCRIPT */

.transcript {

    margin-top:20px;

    padding:24px;

    min-height:420px;

    max-height:520px;

    overflow-y:auto;

    border-radius:18px;

    background:
        rgba(2,6,23,0.78);

    border:
        1px solid
        rgba(148,163,184,0.13);

    color:#f8fafc;

    font-size:17px;

    line-height:2.15;

    letter-spacing:0.005em;

    scroll-behavior:smooth;
}


.transcript::-webkit-scrollbar {

    width:7px;
}


.transcript::-webkit-scrollbar-track {

    background:
        rgba(15,23,42,0.4);

    border-radius:10px;
}


.transcript::-webkit-scrollbar-thumb {

    background:
        rgba(129,140,248,0.35);

    border-radius:10px;
}


.transcript-word {

    color:#e2e8f0;

    font-weight:400;

    cursor:pointer;

    border-radius:6px;

    padding:3px 4px;

    transition:
        background 0.12s ease,
        color 0.12s ease,
        font-weight 0.12s ease,
        box-shadow 0.12s ease;
}


.transcript-word:hover {

    background:
        rgba(129,140,248,0.13);

    color:#ffffff;
}


.transcript-word.active {

    color:#ffffff;

    font-weight:800;

    background:
        rgba(129,140,248,0.30);

    box-shadow:
        0 0 14px
        rgba(129,140,248,0.14);

    padding:
        3px 6px;
}


.transcript-word.past {

    color:#a5b4fc;
}


/* MOBILE */

@media(max-width:700px) {

    .player {

        padding:18px;
    }

    .controls {

        gap:10px;
    }

    .play-button {

        width:50px;
        height:50px;
    }

    .volume-area {

        display:none;
    }

    .transcript {

        font-size:15px;

        line-height:2;

        padding:18px;

        min-height:340px;
    }
}

</style>

</head>


<body>

<div
    class="player"
    id="player"
>


    <div class="player-header">

        <div class="player-title">

            <div class="player-icon">
                🎙️
            </div>

            <div>
                Meeting Recording
            </div>

        </div>


        <div class="audio-status">

            <span class="status-dot"></span>

            Audio Ready

        </div>

    </div>


    <audio
        id="meetingAudio"
        preload="metadata"
    >

        <source
            id="audioSource"
            type="audio/wav"
        >

    </audio>


    <div class="controls">

        <button
            id="playButton"
            class="play-button"
            title="Play / Pause"
        >
            ▶
        </button>


        <div class="timeline-area">

            <div class="time-row">

                <span id="currentTime">
                    00:00
                </span>

                <span id="duration">
                    00:00
                </span>

            </div>


            <div
                class="progress-track"
                id="progressTrack"
            >

                <div
                    class="progress-fill"
                    id="progressFill"
                ></div>

                <div
                    class="progress-thumb"
                    id="progressThumb"
                ></div>

            </div>

        </div>


        <div class="volume-area">

            <span>
                🔊
            </span>

            <input
                id="volumeSlider"
                class="volume-slider"
                type="range"
                min="0"
                max="1"
                step="0.01"
                value="1"
            >

        </div>

    </div>


    <div
        class="visualizer"
        id="visualizer"
    >

        <span class="visual-bar"></span>
        <span class="visual-bar"></span>
        <span class="visual-bar"></span>
        <span class="visual-bar"></span>
        <span class="visual-bar"></span>
        <span class="visual-bar"></span>
        <span class="visual-bar"></span>
        <span class="visual-bar"></span>
        <span class="visual-bar"></span>
        <span class="visual-bar"></span>
        <span class="visual-bar"></span>
        <span class="visual-bar"></span>
        <span class="visual-bar"></span>

    </div>


    <div
        id="transcript"
        class="transcript"
    >
        __TRANSCRIPT__
    </div>

</div>


<script>

const audio =
    document.getElementById(
        "meetingAudio"
    );

const audioSource =
    document.getElementById(
        "audioSource"
    );

const player =
    document.getElementById(
        "player"
    );

const playButton =
    document.getElementById(
        "playButton"
    );

const progressTrack =
    document.getElementById(
        "progressTrack"
    );

const progressFill =
    document.getElementById(
        "progressFill"
    );

const progressThumb =
    document.getElementById(
        "progressThumb"
    );

const currentTimeLabel =
    document.getElementById(
        "currentTime"
    );

const durationLabel =
    document.getElementById(
        "duration"
    );

const volumeSlider =
    document.getElementById(
        "volumeSlider"
    );


audioSource.src =
    "data:audio/wav;base64,__AUDIO_BASE64__";

audio.load();


const words =
    Array.from(
        document.querySelectorAll(
            ".transcript-word"
        )
    );


let activeIndex = -1;


function formatTime(seconds) {

    if (
        !Number.isFinite(seconds)
    ) {

        return "00:00";
    }

    const minutes =
        Math.floor(
            seconds / 60
        );

    const remainingSeconds =
        Math.floor(
            seconds % 60
        );

    return (
        String(minutes).padStart(2, "0")
        + ":"
        + String(
            remainingSeconds
        ).padStart(2, "0")
    );
}


function updatePlayButton() {

    if (audio.paused) {

        playButton.textContent =
            "▶";

        player.classList.remove(
            "playing"
        );

    } else {

        playButton.textContent =
            "Ⅱ";

        player.classList.add(
            "playing"
        );
    }
}


function updateProgress() {

    const current =
        audio.currentTime || 0;

    const duration =
        audio.duration || 0;

    currentTimeLabel.textContent =
        formatTime(current);

    durationLabel.textContent =
        formatTime(duration);


    if (duration > 0) {

        const percentage =
            (
                current / duration
            ) * 100;

        progressFill.style.width =
            percentage + "%";

        progressThumb.style.left =
            percentage + "%";
    }
}


function updateActiveWord() {

    const currentTime =
        audio.currentTime;

    let newIndex = -1;


    for (
        let i = 0;
        i < words.length;
        i++
    ) {

        const word =
            words[i];

        const start =
            parseFloat(
                word.dataset.start
            );

        const end =
            parseFloat(
                word.dataset.end
            );


        if (
            currentTime >= start &&
            currentTime <= end
        ) {

            newIndex = i;

            break;
        }
    }


    if (
        newIndex === activeIndex
    ) {

        return;
    }


    if (
        activeIndex >= 0 &&
        words[activeIndex]
    ) {

        words[
            activeIndex
        ].classList.remove(
            "active"
        );
    }


    activeIndex =
        newIndex;


    for (
        let i = 0;
        i < words.length;
        i++
    ) {

        if (
            activeIndex >= 0 &&
            i < activeIndex
        ) {

            words[i].classList.add(
                "past"
            );

        } else {

            words[i].classList.remove(
                "past"
            );
        }
    }


    if (
        activeIndex >= 0 &&
        words[activeIndex]
    ) {

        const activeWord =
            words[
                activeIndex
            ];


        activeWord.classList.add(
            "active"
        );


        activeWord.scrollIntoView(
            {
                behavior: "smooth",
                block: "center"
            }
        );
    }
}


playButton.addEventListener(
    "click",
    function() {

        if (audio.paused) {

            audio.play().catch(
                function(error) {
                    console.error(error);
                }
            );

        } else {

            audio.pause();
        }

    }
);


progressTrack.addEventListener(
    "click",
    function(event) {

        const rect =
            progressTrack.getBoundingClientRect();

        const percentage =
            (
                event.clientX
                - rect.left
            )
            / rect.width;


        if (
            Number.isFinite(
                audio.duration
            )
        ) {

            audio.currentTime =
                Math.max(
                    0,
                    Math.min(
                        1,
                        percentage
                    )
                )
                * audio.duration;
        }

    }
);


volumeSlider.addEventListener(
    "input",
    function() {

        audio.volume =
            parseFloat(
                volumeSlider.value
            );
    }
);


words.forEach(
    function(word) {

        word.addEventListener(
            "click",
            function() {

                const start =
                    parseFloat(
                        word.dataset.start
                    );


                if (
                    Number.isFinite(start)
                ) {

                    audio.currentTime =
                        start;


                    if (audio.paused) {

                        audio.play().catch(
                            function(error) {
                                console.error(error);
                            }
                        );
                    }
                }

            }
        );

    }
);


audio.addEventListener(
    "loadedmetadata",
    updateProgress
);


audio.addEventListener(
    "timeupdate",
    function() {

        updateProgress();

        updateActiveWord();

    }
);


audio.addEventListener(
    "play",
    updatePlayButton
);


audio.addEventListener(
    "pause",
    updatePlayButton
);


audio.addEventListener(
    "ended",
    function() {

        updatePlayButton();

        updateProgress();


        if (
            activeIndex >= 0 &&
            words[activeIndex]
        ) {

            words[
                activeIndex
            ].classList.remove(
                "active"
            );
        }


        activeIndex = -1;
    }
);


audio.addEventListener(
    "seeking",
    updateActiveWord
);


audio.addEventListener(
    "seeked",
    function() {

        updateProgress();

        updateActiveWord();

    }
);


updatePlayButton();

</script>

</body>

</html>
"""

        player_html = (
            player_html
            .replace(
                "__TRANSCRIPT__",
                transcript_html,
            )
            .replace(
                "__AUDIO_BASE64__",
                audio_base64,
            )
        )

        components.html(
            player_html,
            height=780,
            scrolling=False,
        )

    except Exception as exc:

        st.error(
            f"Unable to load the synchronized player: {exc}"
        )


def render_audio_player(
    audio_path: str | None,
) -> None:
    """Render a standard audio player."""

    st.html(
        """
        <div class="content-title">
            🔊 Meeting Recording
        </div>
        """
    )

    if not audio_path:

        st.info(
            "No recording is available."
        )

        return

    try:

        path = Path(audio_path)

        if not path.exists():

            st.error(
                "The recording file could not be found."
            )

            return

        audio_bytes = path.read_bytes()

        st.audio(
            audio_bytes,
            format="audio/wav",
        )

    except Exception as exc:

        st.error(
            f"Unable to load the recording: {exc}"
        )


def render_insights_panel() -> None:
    """Render AI meeting insights."""

    st.html(
        """
        <div class="content-title">
            🧠 AI Meeting Intelligence
        </div>

        <div class="content-card">

            <div class="insight-item">

                <div style="
                    color:#a78bfa;
                    font-weight:700;
                    font-size:0.82rem;
                ">
                    ✨ SUMMARY
                </div>

                <div style="
                    color:#64748b;
                    font-size:0.8rem;
                    margin-top:0.35rem;
                ">
                    AI-generated meeting summary will appear here.
                </div>

            </div>


            <div class="insight-item">

                <div style="
                    color:#60a5fa;
                    font-weight:700;
                    font-size:0.82rem;
                ">
                    💡 KEY POINTS
                </div>

                <div style="
                    color:#64748b;
                    font-size:0.8rem;
                    margin-top:0.35rem;
                ">
                    Important discussion points will be extracted automatically.
                </div>

            </div>


            <div class="insight-item">

                <div style="
                    color:#34d399;
                    font-weight:700;
                    font-size:0.82rem;
                ">
                    🎯 ACTION ITEMS
                </div>

                <div style="
                    color:#64748b;
                    font-size:0.8rem;
                    margin-top:0.35rem;
                ">
                    Tasks, owners and deadlines will appear here.
                </div>

            </div>


            <div class="insight-item">

                <div style="
                    color:#fbbf24;
                    font-weight:700;
                    font-size:0.82rem;
                ">
                    ⚡ DECISIONS
                </div>

                <div style="
                    color:#64748b;
                    font-size:0.8rem;
                    margin-top:0.35rem;
                ">
                    Important decisions will be detected from the conversation.
                </div>

            </div>

        </div>
        """
    )


def render_completed_banner() -> None:
    """Render completed meeting status."""

    st.html(
        """
        <div style="
            padding:1rem 1.3rem;
            border-radius:16px;

            background:
                linear-gradient(
                    135deg,
                    rgba(6,78,59,0.35),
                    rgba(15,23,42,0.8)
                );

            border:
                1px solid
                rgba(52,211,153,0.2);

            margin-bottom:1.3rem;
        ">

            <div style="
                color:#6ee7b7;
                font-weight:700;
                font-size:0.95rem;
            ">
                ✅ Meeting completed
            </div>

            <div style="
                color:#64748b;
                font-size:0.78rem;
                margin-top:0.3rem;
            ">
                Your recording and transcript are ready.
            </div>

        </div>
        """
    )


def render_footer() -> None:
    """Render application footer."""

    st.html(
        """
        <div class="footer">

            AI Meeting Intelligence

            <span style="color:#6366f1;">
                •
            </span>

            Powered by Whisper + AI

        </div>
        """
    )