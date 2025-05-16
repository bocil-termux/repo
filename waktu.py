from flask import Flask, render_template_string
import os
import subprocess
import threading
import time

app = Flask(__name__)

@app.route('/')
def index():
    html_code = """
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard Jam Neon</title>                                          <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Montserrat:wght@300;500;700&display=swap');
            :root {
                --neon-primary: #00fff7;
                --neon-secondary: #ff00f7;
                --neon-tertiary: #f7ff00;
                --neon-quaternary: #ff5100;
                --neon-quinary: #9d00ff;
                --neon-senary: #00ff51;
                --neon-septenary: #ff0062;
                --neon-octonary: #009dff;
                --neon-nonary: #ff9100;
                --neon-denary: #d400ff;
                --bg-dark: #0d0d0d;
                --bg-light: #f0f0f0;
                --text-dark: #00fff7;
                --text-light: #111;
                --current-theme: 'primary';
                --button-width: 120px;
            }
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            html, body {
                width: 100%;
                height: 100%;
                overflow: hidden;
            }
            body {
                margin: 0;
                min-height: 100vh;
                background: var(--bg-dark);
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                font-family: 'Orbitron', sans-serif;
                color: var(--text-dark);
                transition: all 0.5s ease;
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
            }
            body::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: linear-gradient(45deg,
                    rgba(0, 255, 247, 0.05) 0%,
                    rgba(255, 0, 247, 0.05) 50%,
                    rgba(247, 255, 0, 0.05) 100%);
                z-index: -1;
                animation: gradientShift 15s ease infinite;
                background-size: 200% 200%;
            }
            @keyframes gradientShift {
                0% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
                100% { background-position: 0% 50%; }
            }
            .particles {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: -2;
                overflow: hidden;
            }
            .particle {
                position: absolute;
                width: 2px;
                height: 2px;
                background: var(--neon-primary);
                border-radius: 50%;
                opacity: 0.5;
                animation: float linear infinite;
            }
            @keyframes float {
                to { transform: translateY(-100vh) rotate(360deg); }
            }
            .clock-container {
                text-align: center;
                padding: 1.5rem;
                background: rgba(13, 13, 13, 0.7);
                border-radius: 15px;
                box-shadow: 0 0 20px rgba(0, 255, 247, 0.2),
                            0 0 40px rgba(0, 255, 247, 0.1);
                backdrop-filter: blur(5px);
                border: 1px solid rgba(0, 255, 247, 0.1);
                transition: all 0.5s ease;
                width: 90%;
                max-width: 800px;
                margin: 0 auto;
                max-height: 90vh;
                overflow: hidden;
            }
            .clock {
                font-size: 5vw;
                font-weight: 700;
                letter-spacing: 2px;
                text-shadow:
                    0 0 5px var(--neon-primary),
                    0 0 10px var(--neon-primary),
                    0 0 20px var(--neon-primary),
                    0 0 40px var(--neon-primary),
                    0 0 80px var(--neon-primary);
                margin-bottom: 0.5rem;
                transition: all 0.5s ease;
                line-height: 1.2;
            }
            .date {
                font-size: 2vw;
                font-family: 'Montserrat', sans-serif;
                font-weight: 300;
                color: #b3ffff;
                text-shadow: 0 0 10px var(--neon-primary);
                margin-bottom: 1.5rem;
                transition: all 0.5s ease;
            }
            .button-group {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                justify-content: center;
                margin-top: 1rem;
            }
            button {
                padding: 10px 0;
                font-size: 0.9em;
                font-family: 'Montserrat', sans-serif;
                font-weight: 500;
                background: transparent;
                color: var(--neon-primary);
                border: 2px solid var(--neon-primary);
                border-radius: 30px;
                cursor: pointer;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
                z-index: 1;
                width: var(--button-width);
                min-width: var(--button-width);
                text-align: center;
                white-space: nowrap;
            }
            button::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg,
                    transparent,
                    rgba(0, 255, 247, 0.2),
                    transparent);
                transition: all 0.5s ease;
                z-index: -1;
            }
            button:hover {
                background: var(--neon-primary);
                color: var(--bg-dark);
                box-shadow: 0 0 10px var(--neon-primary),
                            0 0 20px var(--neon-primary);
                transform: translateY(-2px);
            }
            button:active {
                transform: translateY(0);
            }
            button:hover::before {
                left: 100%;
            }
            .theme-btn {
                width: var(--button-width);
                min-width: var(--button-width);
            }
            .active-theme {
                background: var(--neon-primary) !important;
                color: var(--bg-dark) !important;
                font-weight: 700;
                box-shadow: 0 0 10px var(--neon-primary),
                            0 0 20px var(--neon-primary),
                            inset 0 0 5px rgba(0, 0, 0, 0.3);
            }
            /* Light mode styles */
            body.light {
                background: var(--bg-light);
                color: var(--text-light);
            }
            body.light::before {
                background: linear-gradient(45deg,
                    rgba(0, 200, 247, 0.05) 0%,
                    rgba(247, 0, 255, 0.05) 50%,
                    rgba(255, 200, 0, 0.05) 100%);
            }
            body.light .clock-container {
                background: rgba(240, 240, 240, 0.8);
                box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
                border: 1px solid rgba(0, 0, 0, 0.1);
            }
            body.light .clock,
            body.light .date {
                color: #333;
                text-shadow: none;
            }
            body.light .clock {
                text-shadow: 0 0 5px rgba(0, 0, 0, 0.1);
            }
            body.light button {
                color: #333;
                border-color: #333;
            }
            body.light button:hover {
                background: #333;
                color: #fff;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
            }
            body.light .active-theme {
                background: #333 !important;
                color: #fff !important;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.2),
                            inset 0 0 5px rgba(0, 0, 0, 0.3);
            }
            .color-options {
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 8px;
                transition: all 0.3s ease;
                max-width: 100%;
                padding: 0 10px;
            }
            /* Responsive adjustments */
            @media (max-width: 768px) {
                .clock {
                    font-size: 8vw;
                }
                .date {
                    font-size: 3.5vw;
                }
                :root {
                    --button-width: 100px;
                }
                button {
                    padding: 8px 0;
                    font-size: 0.8em;
                }
                .button-group {
                    gap: 8px;
                }
                .clock-container {
                    padding: 1rem;
                    width: 95%;
                }
            }
            @media (max-width: 480px) {
                .clock {
                    font-size: 10vw;
                }
                .date {
                    font-size: 4.5vw;
                }
                :root {
                    --button-width: 80px;
                }
                button {
                    padding: 6px 0;
                    font-size: 0.7em;
                }
                .color-options {
                    gap: 5px;
                }
            }
        </style>
    </head>
    <body>
        <div class="particles" id="particles"></div>
        <div class="clock-container">
            <div class="clock" id="clock">00 : 00 : 00</div>
            <div class="date" id="date">Memuat tanggal...</div>
            <div class="button-group">
                <button onclick="toggleMode()">Ubah Tema</button>
            </div>
            <div class="button-group color-options" id="colorOptions">
                <button class="theme-btn active-theme" onclick="changeColor('primary')">Biru</button>
                <button class="theme-btn" onclick="changeColor('secondary')">Pink</button>
                <button class="theme-btn" onclick="changeColor('tertiary')">Kuning</button>
                <button class="theme-btn" onclick="changeColor('quaternary')">Oranye</button>
                <button class="theme-btn" onclick="changeColor('quinary')">Ungu</button>
                <button class="theme-btn" onclick="changeColor('senary')">Hijau</button>
                <button class="theme-btn" onclick="changeColor('septenary')">Merah</button>
                <button class="theme-btn" onclick="changeColor('octonary')">Biru Langit</button>
                <button class="theme-btn" onclick="changeColor('nonary')">Emas</button>
                <button class="theme-btn" onclick="changeColor('denary')">Ungu Muda</button>
            </div>
        </div>

        <script>
            let currentTheme = 'primary';
            let colorOptionsVisible = true;
            function updateClock() {
                const now = new Date();
                const h = String(now.getHours()).padStart(2, '0');
                const m = String(now.getMinutes()).padStart(2, '0');
                const s = String(now.getSeconds()).padStart(2, '0');
                document.getElementById('clock').textContent = `${h} : ${m} : ${s}`;
                const dayNames = ["Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"];
                const monthNames = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
                                  "Juli", "Agustus", "September", "Oktober", "November", "Desember"];
                const day = dayNames[now.getDay()];
                const date = now.getDate();
                const month = monthNames[now.getMonth()];
                const year = now.getFullYear();

                document.getElementById('date').textContent = `${day}, ${date} ${month} ${year}`;
            }

            function toggleMode() {
                document.body.classList.toggle('light');
                updateParticles();
                colorOptionsVisible = !colorOptionsVisible;
                const colorOptions = document.getElementById('colorOptions');
                if (colorOptionsVisible) {
                    colorOptions.style.display = 'flex';
                } else {
                    colorOptions.style.display = 'none';
                }
            }

            function changeColor(theme) {
                const root = document.documentElement;
                currentTheme = theme;
                switch(theme) {
                    case 'primary':
                        root.style.setProperty('--neon-primary', '#00fff7');
                        root.style.setProperty('--text-dark', '#00fff7');
                        break;
                    case 'secondary':
                        root.style.setProperty('--neon-primary', '#ff00f7');
                        root.style.setProperty('--text-dark', '#ff00f7');
                        break;
                    case 'tertiary':
                        root.style.setProperty('--neon-primary', '#f7ff00');
                        root.style.setProperty('--text-dark', '#f7ff00');
                        break;
                    case 'quaternary':
                        root.style.setProperty('--neon-primary', '#ff5100');
                        root.style.setProperty('--text-dark', '#ff5100');
                        break;
                    case 'quinary':
                        root.style.setProperty('--neon-primary', '#9d00ff');
                        root.style.setProperty('--text-dark', '#9d00ff');
                        break;
                    case 'senary':
                        root.style.setProperty('--neon-primary', '#00ff51');
                        root.style.setProperty('--text-dark', '#00ff51');
                        break;
                    case 'septenary':
                        root.style.setProperty('--neon-primary', '#ff0062');
                        root.style.setProperty('--text-dark', '#ff0062');
                        break;
                    case 'octonary':
                        root.style.setProperty('--neon-primary', '#009dff');
                        root.style.setProperty('--text-dark', '#009dff');
                        break;
                    case 'nonary':
                        root.style.setProperty('--neon-primary', '#ff9100');
                        root.style.setProperty('--text-dark', '#ff9100');
                        break;
                    case 'denary':
                        root.style.setProperty('--neon-primary', '#d400ff');
                        root.style.setProperty('--text-dark', '#d400ff');
                        break;
                }
                document.querySelectorAll('.theme-btn').forEach(btn => {
                    btn.classList.remove('active-theme');
                });
                event.target.classList.add('active-theme');
                updateParticles();
            }

            function createParticles() {
                const particlesContainer = document.getElementById('particles');
                const particleCount = Math.floor(window.innerWidth / 5);
                for (let i = 0; i < particleCount; i++) {
                    const particle = document.createElement('div');
                    particle.classList.add('particle');
                    const size = Math.random() * 3 + 1;
                    const posX = Math.random() * window.innerWidth;
                    const posY = Math.random() * window.innerHeight;
                    const duration = Math.random() * 20 + 10;
                    const delay = Math.random() * 5;
                    const opacity = Math.random() * 0.5 + 0.2;
                    particle.style.width = `${size}px`;
                    particle.style.height = `${size}px`;
                    particle.style.left = `${posX}px`;
                    particle.style.top = `${posY}px`;
                    particle.style.background = `var(--neon-primary)`;
                    particle.style.opacity = opacity;
                    particle.style.animationDuration = `${duration}s`;
                    particle.style.animationDelay = `${delay}s`;
                    particlesContainer.appendChild(particle);
                }
            }
            function updateParticles() {
                const particles = document.querySelectorAll('.particle');
                particles.forEach(particle => {
                    particle.style.background = `var(--neon-primary)`;
                });
            }

            window.addEventListener('load', () => {
                updateClock();
                setInterval(updateClock, 1000);
                createParticles();
                document.body.style.overflow = 'hidden';
                document.addEventListener('touchmove', function(e) {
                    e.preventDefault();
                }, { passive: false });
            });

            window.addEventListener('resize', () => {
                document.getElementById('particles').innerHTML = '';
                createParticles();
            });
            document.addEventListener('keydown', (e) => {
                if (e.key === 't' || e.key === 'T') {
                    toggleMode();
                }
                if (e.key === 'c' || e.key === 'C') {
                    const themes = ['primary', 'secondary', 'tertiary', 'quaternary', 'quinary',
                                  'senary', 'septenary', 'octonary', 'nonary', 'denary'];
                    const currentIndex = themes.indexOf(currentTheme);
                    const nextIndex = (currentIndex + 1) % themes.length;
                    changeColor(themes[nextIndex]);
                }
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html_code)

if __name__ == '__main__':
    def buka_browser():
        time.sleep(0.5)
        subprocess.run(["xdg-open", "http://127.0.0.1:5000"])

    threading.Thread(target=buka_browser).start()
    app.run(debug=True)
