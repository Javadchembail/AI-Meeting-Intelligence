import streamlit as st


def load_custom_css() -> None:
    """
    Load global application styling.
    """

    st.markdown(
        """
        <style>

        /* ==================================================
           GLOBAL
        ================================================== */

        .stApp {
            background:
                radial-gradient(
                    circle at 10% 10%,
                    rgba(99, 102, 241, 0.16),
                    transparent 30%
                ),
                radial-gradient(
                    circle at 90% 20%,
                    rgba(168, 85, 247, 0.12),
                    transparent 30%
                ),
                #070711;

            color: #f8fafc;
        }

        .block-container {
            max-width: 1400px;
            padding-top: 2.5rem;
            padding-bottom: 3rem;
        }

        /* ==================================================
           HEADER
        ================================================== */

        .main-title {
            font-size: 3rem;
            font-weight: 800;
            letter-spacing: -0.05em;
            line-height: 1.1;
            margin-bottom: 0.4rem;

            background:
                linear-gradient(
                    90deg,
                    #ffffff,
                    #a78bfa,
                    #60a5fa
                );

            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .subtitle {
            color: #94a3b8;
            font-size: 1.05rem;
            margin-bottom: 2.2rem;
        }

        /* ==================================================
           HERO
        ================================================== */

        .hero-card {
            padding: 2.5rem;
            border-radius: 24px;
            margin-bottom: 1.5rem;

            background:
                linear-gradient(
                    135deg,
                    rgba(30, 27, 75, 0.85),
                    rgba(15, 23, 42, 0.92)
                );

            border:
                1px solid rgba(
                    148,
                    163,
                    184,
                    0.16
                );

            box-shadow:
                0 20px 60px rgba(
                    0,
                    0,
                    0,
                    0.35
                );

            text-align: center;
        }

        .hero-icon {
            font-size: 4rem;
            margin-bottom: 0.5rem;
        }

        .hero-title {
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 0.4rem;
        }

        .hero-description {
            color: #94a3b8;
            font-size: 1rem;
            margin-bottom: 1.5rem;
        }

        /* ==================================================
           RECORDING
        ================================================== */

        .recording-card {
            padding: 1.8rem;
            border-radius: 22px;
            margin-bottom: 1.5rem;

            background:
                linear-gradient(
                    135deg,
                    rgba(127, 29, 29, 0.24),
                    rgba(30, 41, 59, 0.75)
                );

            border:
                1px solid rgba(
                    248,
                    113,
                    113,
                    0.25
                );

            box-shadow:
                0 15px 45px rgba(
                    0,
                    0,
                    0,
                    0.28
                );
        }

        .recording-status {
            display: flex;
            align-items: center;
            gap: 0.6rem;

            color: #fca5a5;

            font-weight: 700;
            font-size: 0.9rem;

            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .recording-dot {
            width: 11px;
            height: 11px;

            border-radius: 50%;

            background: #ef4444;

            box-shadow:
                0 0 8px #ef4444,
                0 0 18px rgba(
                    239,
                    68,
                    68,
                    0.7
                );

            animation:
                pulse-recording
                1.3s infinite;
        }

        @keyframes pulse-recording {

            0% {
                transform: scale(1);
                opacity: 1;
            }

            50% {
                transform: scale(1.35);
                opacity: 0.55;
            }

            100% {
                transform: scale(1);
                opacity: 1;
            }
        }

        /* ==================================================
           METRICS
        ================================================== */

        .metric-card {
            padding: 1.4rem;
            border-radius: 18px;

            background:
                rgba(
                    15,
                    23,
                    42,
                    0.72
                );

            border:
                1px solid rgba(
                    148,
                    163,
                    184,
                    0.14
                );

            text-align: center;

            box-shadow:
                0 10px 30px rgba(
                    0,
                    0,
                    0,
                    0.22
                );
        }

        .metric-label {
            color: #94a3b8;

            font-size: 0.8rem;

            text-transform: uppercase;

            letter-spacing: 0.08em;
        }

        .metric-value {
            color: #f8fafc;

            font-size: 2rem;

            font-weight: 800;

            margin-top: 0.25rem;
        }

        /* ==================================================
           CONTENT
        ================================================== */

        .content-card {
            padding: 1.5rem;

            min-height: 360px;

            border-radius: 22px;

            background:
                linear-gradient(
                    145deg,
                    rgba(
                        15,
                        23,
                        42,
                        0.9
                    ),
                    rgba(
                        17,
                        24,
                        39,
                        0.78
                    )
                );

            border:
                1px solid rgba(
                    148,
                    163,
                    184,
                    0.14
                );

            box-shadow:
                0 15px 45px rgba(
                    0,
                    0,
                    0,
                    0.25
                );
        }

        .content-title {
            font-size: 1.05rem;
            font-weight: 700;
            margin-bottom: 1rem;
        }

        /* ==================================================
           TRANSCRIPT
        ================================================== */

        .transcript-box {
            padding: 1rem 1.1rem;

            border-radius: 14px;

            background:
                rgba(
                    2,
                    6,
                    23,
                    0.65
                );

            border:
                1px solid rgba(
                    96,
                    165,
                    250,
                    0.14
                );

            color: #ffffff;

            line-height: 1.9;

            font-size: 1rem;

            max-height: 420px;

            overflow-y: auto;
        }

        .transcript-word {
            color: #ffffff;

            transition:
                background 0.12s ease,
                font-weight 0.12s ease,
                padding 0.12s ease;
        }

        .transcript-word.active {
            color: #ffffff;

            font-weight: 800;

            background:
                rgba(
                    129,
                    140,
                    248,
                    0.24
                );

            border-radius: 5px;

            padding:
                2px 4px;
        }

        /* ==================================================
           AI INSIGHTS
        ================================================== */

        .insight-item {
            padding: 0.9rem 1rem;

            margin-bottom: 0.7rem;

            border-radius: 13px;

            background:
                rgba(
                    30,
                    41,
                    59,
                    0.55
                );

            border:
                1px solid rgba(
                    167,
                    139,
                    250,
                    0.12
                );
        }

        /* ==================================================
           AUDIO
        ================================================== */

        .audio-card {
            padding: 1.3rem;

            border-radius: 18px;

            background:
                linear-gradient(
                    135deg,
                    rgba(
                        30,
                        27,
                        75,
                        0.72
                    ),
                    rgba(
                        15,
                        23,
                        42,
                        0.85
                    )
                );

            border:
                1px solid rgba(
                    167,
                    139,
                    250,
                    0.18
                );

            margin-top: 1rem;
        }

        /* ==================================================
           BUTTONS
        ================================================== */

        .stButton > button {

            min-height: 48px;

            border-radius: 14px;

            border:
                1px solid rgba(
                    148,
                    163,
                    184,
                    0.18
                );

            background:
                linear-gradient(
                    135deg,
                    #4f46e5,
                    #7c3aed
                );

            color: white;

            font-weight: 700;

            font-size: 0.95rem;

            transition:
                transform 0.2s ease,
                box-shadow 0.2s ease,
                opacity 0.2s ease;
        }

        .stButton > button:hover {

            transform:
                translateY(-2px);

            box-shadow:
                0 10px 28px
                rgba(
                    99,
                    102,
                    241,
                    0.35
                );
        }

        .stButton > button:active {
            transform:
                translateY(0);
        }

        /* ==================================================
           DIVIDER
        ================================================== */

        hr {
            border-color:
                rgba(
                    148,
                    163,
                    184,
                    0.1
                );
        }

        /* ==================================================
           ALERTS
        ================================================== */

        [data-testid="stAlert"] {
            border-radius: 14px;
        }

        /* ==================================================
           TEXT AREA
        ================================================== */

        textarea {
            background:
                rgba(
                    2,
                    6,
                    23,
                    0.72
                ) !important;

            color:
                #ffffff !important;

            border-radius:
                14px !important;

            border:
                1px solid rgba(
                    148,
                    163,
                    184,
                    0.14
                ) !important;
        }

        /* ==================================================
           FOOTER
        ================================================== */

        .footer {
            text-align: center;

            color: #64748b;

            font-size: 0.8rem;

            margin-top: 3rem;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )