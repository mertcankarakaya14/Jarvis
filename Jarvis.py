import os, json, time, webbrowser, psutil, pyautogui
from flask import Flask, request, jsonify, render_template_string
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL, CoInitialize
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from google import genai
import requests 
import urllib.parse

# Windows ses sistemini bir kez başlatıyoruz
try:
    CoInitialize()
except:
    pass

# --- AYARLAR ---
API_KEY = ""
MODEL_ADI = "models/gemini-2.5-flash"
OLLAMA_URL = "http://localhost:11434/api/generate"  # Ollama API
OLLAMA_MODEL = "llama3.1"
SISTEM_MESAJI = "Sen Jarvis'sin, (Kendi Adın)'ın asistanısın. . (Kendi Adın)'a  her zaman 'Efendim' de. Cevapların kısa, öz ve karizmatik olsun."

client = genai.Client(api_key=API_KEY)
app = Flask(__name__)

KLASOR_YOLU = os.path.dirname(os.path.abspath(__file__))
DOSYA_YOLU = os.path.join(KLASOR_YOLU, "hafiza.txt")

def hafizayi_yukle():
    if os.path.exists(DOSYA_YOLU):
        try:
            with open(DOSYA_YOLU, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    if item.get('role') == 'assistant':
                        item['role'] = 'model'
                return data
        except: 
            return []
    return []

hafiza = hafizayi_yukle()

# --- OLLAMA İLE SOHBET (Normal konuşmalar için) ---
def ollama_ile_konus(soru, gecmis):
    try:
        # Son 20 mesajı al
        context = ""
        for msg in gecmis[-20:]:
            role = "Mert" if msg['role'] == 'user' else "Jarvis"
            context += f"{role}: {msg['content']}\n"
        
        prompt = f"{SISTEM_MESAJI}\n\n{context}Mert: {soru}\nJarvis:"
        
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json().get("response", "Anlamadım Efendim.")
        else:
            return "Ollama'ya ulaşamadım Efendim."
    except Exception as e:
        print(f"Ollama hatası: {str(e)}")
        return f"Sistem hatası: {str(e)}"

# --- JARVIS KOD YAZMA (Sadece Gemini kullanacak) ---
def jarvis_kod_yazsin(istek):
    print(f">>> {MODEL_ADI} ile kod üretiliyor...")
    try:
        response = client.models.generate_content(
            model=MODEL_ADI,
            contents=istek,
            config={
                'system_instruction': "Sadece Python kodu ver, açıklama yapma, Markdown (```) kullanma."
            }
        )
        kod = response.text.replace("```python", "").replace("```", "").strip()

        try:
            desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
            dosya_adi = f"jarvis_kod_{int(time.time())}.py"
            kod_dosya = os.path.join(desktop, dosya_adi)
            
            with open(kod_dosya, 'w', encoding='utf-8') as f:
                f.write(kod)
            
            os.startfile(kod_dosya)
            return f"Kod '{dosya_adi}' dosyasına kaydedildi ve açıldı Efendim."
            
        except Exception as e:
            print(f"Dosya oluşturma hatası: {str(e)}")
            return f"Dosya oluşturma hatası: {str(e)}"
            
    except Exception as e:
        print(f"Kod yazma hatası: {str(e)}")
        return f"Kod üretme hatası: {str(e)}"

# --- ÖZEL KOMUTLAR ---
def ozel_komutlar(mesaj):
    m = mesaj.lower().strip()
    print(f">>> Analiz: {m}")

    # 1. --- SES KONTROL MERKEZİ ---
    if "ses" in m and any(x in m for x in ["ayarla", "yap", "seviye"]):
        rakamlar = [int(s) for s in m.split() if s.isdigit()]
        if rakamlar:
            try:
                yeni_seviye = rakamlar[0]
                if 0 <= yeni_seviye <= 100:
                    devices = AudioUtilities.GetSpeakers()
                    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                    volume = cast(interface, POINTER(IAudioEndpointVolume))
                    volume.SetMasterVolumeLevelScalar(yeni_seviye / 100.0, None)
                    return f"Ses seviyesini yüzde {yeni_seviye} yaptım Efendim."
            except:
                pyautogui.press("volumedown", presses=50) 
                pyautogui.press("volumeup", presses=yeni_seviye // 2)
                return f"Ses seviyesini yüzde {yeni_seviye} yaptım Efendim."

        if any(k in m for k in ["fulle", "max", "maks"]):
            pyautogui.press("volumeup", presses=100)
            return "Ses köklendi!"
        elif any(k in m for k in ["kapat", "sustur", "mute", "sessiz"]):
            pyautogui.press("volumemute")
            return "Sistemi sessize aldım Efendim."

    # 2. --- KOD YAZMA (Sadece bu Gemini'ye gidecek) ---
    if "kod yaz" in m or "projesi yap" in m or "kod oluştur" in m:
        istek = m.replace("kod yaz", "").replace("projesi yap", "").replace("kod oluştur", "").strip()
        if not istek:
            return "Ne tür bir kod yazmamı istiyorsun Efendim?"
        return jarvis_kod_yazsin(istek)

    # 3. --- SİTE / PROGRAM KAPATMA ---
    if any(k in m for k in ["kapat", "çık", "sil"]):
        if any(k in m for k in ["sekme", "sayfa", "site", "youtube", "şarkı"]):
            pyautogui.hotkey('ctrl', 'w')
            return "Sekmeyi kapattım Efendim."
        elif "not" in m or "defter" in m:
            for proc in psutil.process_iter():
                if proc.name().lower() == "notepad.exe": 
                    proc.kill()
            return "Not defterini kapattım Efendim."

    # 4. --- EKRAN GÖRÜNTÜSÜ ---
    if "ekran" in m and "görüntü" in m:
        try:
            desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
            ss_yolu = os.path.join(desktop, f"jarvis_ss_{int(time.time())}.png")
            pyautogui.screenshot(ss_yolu)
            return "Ekran görüntüsünü masaüstüne bıraktım Efendim."
        except: 
            return "Ekran görüntüsü alınamadı."

    # 5. --- ŞARKI KONTROL ---
    if any(k in m for k in ["durdur", "beklet", "duraklat", "devam", "oynat"]):
        pyautogui.press('playpause')
        return "İşlem tamam Efendim."
    if "yeniden" in m and ("başlat" in m or "çal" in m):
        pyautogui.press('0')
        return "Şarkıyı senin için başa sardım Efendim."

    # 6. --- AKILLI ARAMA VE AÇMA ---
    if "aç" in m:
        hedef = m.replace("aç", "").strip()
        
        # YouTube için güvenli hale getirme (SİHİRLİ SATIR)
        guvenli_hedef = urllib.parse.quote(hedef)
        
        # YouTube özel durumu
        if hedef == "youtube":
            webbrowser.open("https://www.youtube.com")
            return "YouTube açılıyor Efendim."
        
        aranacak_yollar = [
            ##Kendi Dosya Adresini  Yaz r"XXXXX", 
            os.path.join(os.environ['USERPROFILE'], 'Desktop'), 
            r"C:\Program Files", 
            r"C:\Program Files (x86)"
        ]
        
        bulunan_dosya = None
        for yol in aranacak_yollar:
            if os.path.exists(yol):
                for dosya in os.listdir(yol):
                    if hedef in dosya.lower() and (dosya.endswith(".exe") or dosya.endswith(".lnk") or dosya.endswith(".url") or dosya.endswith(".cmd")):
                        bulunan_dosya = os.path.join(yol, dosya)
                        break
            if bulunan_dosya: 
                break

        if bulunan_dosya:
            os.startfile(bulunan_dosya)
            return f"{hedef} uygulamasını başlattım Efendim."
        else:
            browser_acik = any("chrome" in proc.info['name'].lower() for proc in psutil.process_iter(['name']))
            if browser_acik:
                pyautogui.hotkey('ctrl', 'l') 
                time.sleep(0.5)
                # BURAYI GÜNCELLEDİK: guvenli_hedef kullandık
                pyautogui.write(f"https://www.youtube.com/results?search_query={guvenli_hedef}")
                pyautogui.press('enter')
            else:
                # BURAYI GÜNCELLEDİK: guvenli_hedef kullandık
                webbrowser.open(f"https://www.youtube.com/results?search_query={guvenli_hedef}")
            
            time.sleep(4) 
            pyautogui.click(800, 550) 
            pyautogui.press('enter')
            return f"{hedef} YouTube üzerinden açılıyor Efendim."

    if m == "sus" or "kes sesini" in m: 
        return "TAMAM_SUS"

    return None

# --- WEB ARAYÜZÜ (ChatGPT/Gemini tarzı sidebar) ---
index_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>JARVIS v4.5 ULTIMATE</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { background: radial-gradient(circle, #00151a 0%, #000 100%); color: #0ef; font-family: 'Share Tech Mono', monospace; height: 100vh; overflow: hidden; }
            
            /* Sidebar (ChatGPT/Gemini tarzı - overlay) */
            .sidebar { 
                position: fixed; 
                top: 0; 
                left: 0; 
                width: 280px; 
                height: 100vh; 
                background: rgba(0, 15, 20, 0.98); 
                border-right: 1px solid rgba(0, 238, 255, 0.4); 
                padding: 15px; 
                overflow-y: auto; 
                transform: translateX(-100%); 
                transition: transform 0.3s ease; 
                z-index: 1000; 
                box-shadow: 5px 0 15px rgba(0, 0, 0, 0.5);
            }
            .sidebar.open { transform: translateX(0); }
            .sidebar h3 { 
                color: #0ef; 
                margin-bottom: 20px; 
                text-align: center; 
                letter-spacing: 2px; 
                font-size: 0.9rem; 
                padding-bottom: 10px; 
                border-bottom: 1px solid rgba(0, 238, 255, 0.3); 
            }
            
            /* Konuşma başlıkları - ChatGPT tarzı */
            .conversation-item { 
                padding: 12px 10px; 
                margin-bottom: 5px; 
                background: rgba(0, 40, 50, 0.3); 
                border-radius: 5px; 
                cursor: pointer; 
                font-size: 0.75rem; 
                transition: all 0.2s; 
                border-left: 2px solid transparent;
            }
            .conversation-item:hover { 
                background: rgba(0, 238, 255, 0.15); 
                border-left-color: #0ef; 
            }
            .conversation-title { 
                color: #0ef; 
                font-weight: bold; 
                margin-bottom: 3px; 
                white-space: nowrap; 
                overflow: hidden; 
                text-overflow: ellipsis; 
            }
            .conversation-time { 
                color: #888; 
                font-size: 0.65rem; 
            }
            
            /* Overlay arka plan */
            .overlay { 
                position: fixed; 
                top: 0; 
                left: 0; 
                width: 100vw; 
                height: 100vh; 
                background: rgba(0, 0, 0, 0.5); 
                z-index: 999; 
                display: none; 
            }
            .overlay.active { display: block; }
            
            /* Ana Kapsayıcı - artık sabit genişlikte */
            .main-container { 
                width: 100%; 
                height: 100vh; 
                display: flex; 
                flex-direction: column; 
                padding: 15px; 
                position: relative; 
            }
            
            /* Hamburger Butonu */
            .menu-btn { 
                position: absolute; 
                top: 15px; 
                left: 15px; 
                background: transparent; 
                border: 1px solid #0ef; 
                color: #0ef; 
                padding: 10px 15px; 
                cursor: pointer; 
                font-size: 1.2rem; 
                z-index: 5; 
                border-radius: 3px; 
            }
            .menu-btn:hover { background: #0ef; color: #000; }
            
            h2 { text-align: center; letter-spacing: 5px; text-shadow: 0 0 10px #0ef; font-size: 1.1rem; margin: 10px 0 20px 0; }
            #chat { flex: 1; overflow-y: auto; border: 1px solid rgba(0, 238, 255, 0.3); padding: 15px; margin-bottom: 15px; border-radius: 5px; background: rgba(0, 20, 30, 0.6); }
            .input-container { display: flex; flex-direction: column; gap: 8px; }
            input { width: 100%; padding: 12px; background: rgba(0, 40, 50, 0.4); color: #fff; border: 1px solid #0ef; border-radius: 3px; outline: none; font-family: 'Share Tech Mono', monospace; }
            .button-group { display: flex; gap: 8px; }
            .btn { flex: 1; padding: 12px; background: transparent; border: 1px solid #0ef; color: #0ef; font-weight: bold; cursor: pointer; text-transform: uppercase; font-family: 'Share Tech Mono', monospace; font-size: 0.8rem; }
            .btn:hover { background: #0ef; color: #000; box-shadow: 0 0 10px #0ef; }
            .stop-btn { border-color: #f44; color: #f44; }
            .mic-btn { border-color: #fffb00; color: #fffb00; }
            .bot { color: #fff; margin-bottom: 15px; border-left: 2px solid #0ef; padding-left: 10px; font-size: 0.85rem; }
            .user { color: #0ef; text-align: right; margin-bottom: 15px; font-weight: bold; font-size: 0.85rem; }
        </style>
    </head>
    <body>
        <!-- Overlay (sidebar açıkken arka plan) -->
        <div class="overlay" id="overlay" onclick="toggleMenu()"></div>
        
        <!-- Sidebar - ChatGPT Tarzı -->
        <div class="sidebar" id="sidebar">
            <h3>📜 KONUŞMA GEÇMİŞİ</h3>
            <div id="historyList"></div>
        </div>
        
        <!-- Ana Alan -->
        <div class="main-container">
            <button class="menu-btn" onclick="toggleMenu()">☰</button>
            <h2>KARAKAYA INDUSTRIES - JARVIS</h2>
            <div id="chat"></div>
            <div class="input-container">
                <input type="text" id="soru" placeholder="MERT: KOMUT BEKLENİYOR..." onkeypress="if(event.key=='Enter') gonder()">
                <div class="button-group">
                    <button class="btn" onclick="gonder()">GÖNDER</button>
                    <button class="btn mic-btn" id="micBtn" onclick="sesiDinle()">DİNLE</button>
                    <button class="btn stop-btn" onclick="sesiDurdur()">SUS</button>
                </div>
            </div>
        </div>
        
        <script>
            const sentez = window.speechSynthesis;
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            let recognizer;
            let sesli = false;

            if (SpeechRecognition) {
                recognizer = new SpeechRecognition();
                recognizer.lang = 'tr-TR';

                recognizer.onresult = (e) => { 
                    document.getElementById('soru').value = e.results[0][0].transcript; 
                    sesli = true;
                    gonder(); 
                };

                recognizer.onend = () => { 
                    document.getElementById('micBtn').innerText = "DİNLE";
                    document.getElementById('micBtn').style.borderColor = "#fffb00";
                    document.getElementById('micBtn').style.color = "#fffb00";
                };
            }

            // Copilot tuşu - Shift+Win+F24 veya herhangi bir kombinasyon
            let pressedKeys = new Set();
            
            document.addEventListener('keydown', (e) => {
                pressedKeys.add(e.code);
                
                // F24 tuşu basıldıysa (Shift ve Win ile birlikte veya tek başına)
                if (e.code === 'F24' || e.key === 'F24') {
                    e.preventDefault(); // Copilot açılmasını engelle
                    sesiDinle();
                    pressedKeys.clear();
                }
                
                // Alternatif: Eğer Shift+Win+F23 kombinasyonu istiyorsan
                // if (pressedKeys.has('ShiftLeft') && pressedKeys.has('MetaLeft') && e.code === 'F24') {
                //     e.preventDefault();
                //     sesiDinle();
                //     pressedKeys.clear();
                // }
            });
            
            document.addEventListener('keyup', (e) => {
                pressedKeys.delete(e.code);
            });

            function toggleMenu() {
                const sidebar = document.getElementById('sidebar');
                const overlay = document.getElementById('overlay');
                
                sidebar.classList.toggle('open');
                overlay.classList.toggle('active');
                
                if (sidebar.classList.contains('open')) {
                    loadHistory();
                }
            }

            function loadHistory() {
                fetch('/get_hafiza')
                .then(r => r.json())
                .then(data => {
                    const historyDiv = document.getElementById('historyList');
                    historyDiv.innerHTML = '';
                    
                    // Konuşmaları grupla - sadece konu değişince yeni başlık
                    let conversations = [];
                    let currentConv = null;
                    let lastUserMessage = '';
                    
                    data.hafiza.forEach((item, index) => {
                        if (item.role === 'user') {
                            // Yeni konuşma başlat (ilk 30 karakter farklıysa)
                            const shortMessage = item.content.substring(0, 30);
                            
                            if (!currentConv || shortMessage !== lastUserMessage) {
                                // Önceki konuşmayı kaydet
                                if (currentConv) conversations.push(currentConv);
                                
                                // Yeni konuşma başlat
                                currentConv = {
                                    title: item.content.substring(0, 35) + (item.content.length > 35 ? '...' : ''),
                                    time: new Date().toLocaleTimeString('tr-TR', {hour: '2-digit', minute: '2-digit'}),
                                    startIndex: index,
                                    messages: [item]
                                };
                                lastUserMessage = shortMessage;
                            } else {
                                // Aynı konuya devam
                                currentConv.messages.push(item);
                            }
                        } else if (currentConv) {
                            currentConv.messages.push(item);
                        }
                    });
                    if (currentConv) conversations.push(currentConv);
                    
                    // Son 20 konuşmayı göster (ters sırada)
                    conversations.slice(-20).reverse().forEach(conv => {
                        const div = document.createElement('div');
                        div.className = 'conversation-item';
                        div.innerHTML = `
                            <div class="conversation-title">💬 ${conv.title}</div>
                            <div class="conversation-time">${conv.time}</div>
                        `;
                        
                        // Tıklayınca o konuşmayı göster
                        div.onclick = () => {
                            loadConversation(conv.messages);
                            toggleMenu(); // Menüyü kapat
                        };
                        
                        historyDiv.appendChild(div);
                    });
                });
            }

            // Konuşmayı chat ekranına yükle
            function loadConversation(messages) {
                const c = document.getElementById('chat');
                c.innerHTML = ''; // Ekranı temizle
                
                messages.forEach(msg => {
                    if (msg.role === 'user') {
                        c.innerHTML += '<div class="user">> MERT: ' + msg.content + '</div>';
                    } else {
                        c.innerHTML += '<div class="bot"><b>> JARVIS:</b> ' + msg.content + '</div>';
                    }
                });
                
                c.scrollTop = c.scrollHeight;
            }

            function sesiDinle() { 
                const btn = document.getElementById('micBtn');
                btn.innerText = "DİNLİYORUM...";
                btn.style.borderColor = "#0f0";
                btn.style.color = "#0f0";
                recognizer.start(); 
            }

            function sesiDurdur() { sentez.cancel(); }

            function gonder() {
                let i = document.getElementById('soru');
                let c = document.getElementById('chat');
                if(!i.value) return;
                
                let s = i.value;
                i.value = '';
                
                c.innerHTML += '<div class="user">> MERT: ' + s + '</div>';
                
                fetch('/sor', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({soru: s}) })
                .then(r => r.json()).then(d => {
                    if(d.cevap === "TAMAM_SUS") { 
                        sesiDurdur(); 
                    } else {
                        c.innerHTML += '<div class="bot"><b>> JARVIS:</b> ' + d.cevap + '</div>';
                        c.scrollTop = c.scrollHeight;
                        
                        if (sesli) {
                            const u = new SpeechSynthesisUtterance(d.cevap);
                            u.lang = 'tr-TR'; 
                            u.rate = 1.1; 
                            sentez.speak(u);
                            sesli = false;
                        }
                    }
                }).catch(err => {
                    c.innerHTML += '<div class="bot"><b>> JARVIS:</b> Bağlantı hatası: ' + err + '</div>';
                });
            }
        </script>
    </body>
    </html>
"""

@app.route('/')
def index():
    return render_template_string(index_html)

@app.route('/get_hafiza', methods=['GET'])
def get_hafiza():
    return jsonify({"hafiza": hafiza}), 200
                                     
@app.route('/sor', methods=['POST'])
def ask_jarvis():
    global hafiza
    try:
        data = request.json
        soru = data.get("soru")
        
        if not soru:
            return jsonify({"cevap": "Soru algılanamadı Efendim."}), 400
        
        # 1. Özel Komut Kontrolü
        cevap = ozel_komutlar(soru)
        if cevap:
            # Özel komutları da hafızaya kaydet
            hafiza.append({'role': 'user', 'content': soru})
            hafiza.append({'role': 'model', 'content': cevap})
            
            with open(DOSYA_YOLU, 'w', encoding='utf-8') as f:
                json.dump(hafiza, f, ensure_ascii=False, indent=2)
            
            return jsonify({"cevap": cevap}), 200

        # 2. Normal Sohbet - OLLAMA ile
        try:
            cevap = ollama_ile_konus(soru, hafiza)
            
            # Hafızayı Güncelle ve Kaydet
            hafiza.append({'role': 'user', 'content': soru})
            hafiza.append({'role': 'model', 'content': cevap})
            
            with open(DOSYA_YOLU, 'w', encoding='utf-8') as f:
                json.dump(hafiza, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            cevap = f"Sistem hatası: {str(e)}"
            print(f"Ollama hatası: {str(e)}")
            
        return jsonify({"cevap": cevap}), 200
        
    except Exception as e:
        print(f"Genel hata: {str(e)}")
        return jsonify({"cevap": f"Genel sistem hatası: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)