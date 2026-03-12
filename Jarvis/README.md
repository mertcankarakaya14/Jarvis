# 🤖 JARVIS - Kişisel AI Asistan

> *"Bu proje Claude (Anthropic) ve Google Gemini yardımıyla geliştirilmiştir."*

JARVIS, sesli komutlar, sistem kontrolü ve yapay zeka destekli sohbet özelliklerini bir arada sunan, tamamen yerel çalışan kişisel bir masaüstü asistanıdır. Normal konuşmalar için **Ollama (LLaMA 3.1)**, kod üretimi için **Google Gemini 2.5 Flash** kullanır.

---

## ✨ Özellikler

- 🎙️ **Sesli Komut** — Türkçe konuşma tanıma ile elleri serbest kullanım
- 🔊 **Ses Kontrolü** — Sistem sesini yüzde olarak ayarlama, sessize alma
- 💻 **Kod Yazma** — Gemini 2.5 Flash ile otomatik Python kodu üretimi ve masaüstüne kaydetme
- 🎵 **Medya Kontrolü** — Şarkıyı durdur/başlat/başa sar
- 📸 **Ekran Görüntüsü** — Masaüstüne otomatik kaydetme
- 🌐 **Akıllı Arama** — YouTube arama veya uygulama açma
- 📜 **Konuşma Geçmişi** — ChatGPT tarzı sidebar ile tüm hafıza
- 🧠 **Kalıcı Hafıza** — `hafiza.txt` ile oturumlar arası hafıza

---

## 🛠️ Kurulum

### Gereksinimler

- Python 3.10+
- Windows 10/11
- [Ollama](https://ollama.com/) kurulu ve çalışıyor olmalı
- Google Gemini API anahtarı

### 1. Repoyu Klonla

```bash
git clone https://github.com/kullanici_adin/jarvis.git
cd jarvis
```

### 2. Bağımlılıkları Yükle

```bash
pip install -r requirements.txt
```

### 3. Ollama Kurulumu

```bash
# Ollama'yı kur: https://ollama.com/download
ollama pull llama3.1
ollama serve
```

### 4. API Anahtarını Ayarla

`jarvis.py` dosyasını aç ve şu satırı düzenle:

```python
API_KEY = "buraya_gemini_api_anahtarini_yaz"
```

> Gemini API anahtarını [Google AI Studio](https://aistudio.google.com/)'dan ücretsiz alabilirsin.

### 5. Kişiselleştirme (Opsiyonel)

```python
SISTEM_MESAJI = "Sen Jarvis'sin, (Kendi Adın)'ın asistanısın..."
```

`(Kendi Adın)` kısmını kendi adınla değiştir.

Kendi program klasörünü de ekleyebilirsin:
```python
aranacak_yollar = [
    r"C:\Users\SenimAdin\AppData\Roaming",  # Örnek
    ...
]
```

---

## 🚀 Çalıştırma

```bash
python jarvis.py
```

Tarayıcıda aç: [http://localhost:5001](http://localhost:5001)

---

## 🎤 Komut Örnekleri

| Komut | Ne Yapar |
|-------|----------|
| `sesi 50 yap` | Sistem sesini %50'ye ayarlar |
| `sistemi sessize al` | Mute yapar |
| `ekran görüntüsü al` | Masaüstüne PNG kaydeder |
| `kod yaz hesap makinesi` | Python kodu üretip açar |
| `youtube aç` | YouTube'u tarayıcıda açar |
| `lofi aç` | YouTube'da arar ve çalar |
| `duraklat` | Müziği durdurur |
| `sekmeyi kapat` | Aktif tarayıcı sekmesini kapatır |
| `sus` | JARVIS'in sesini keser |

---

## 🏗️ Mimari

```
Kullanıcı Mesajı
      │
      ▼
 Özel Komut? ──── Evet ──▶ Sistem İşlemi (ses, ekran, medya...)
      │
      Hayır
      │
      ▼
   Ollama (LLaMA 3.1) ──▶ Normal Sohbet
      
 "kod yaz" ──▶ Gemini 2.5 Flash ──▶ .py dosyası üret
```

---

## 📁 Dosya Yapısı

```
jarvis/
├── jarvis.py          # Ana uygulama
├── hafiza.txt         # Konuşma geçmişi (otomatik oluşur)
├── requirements.txt   # Python bağımlılıkları
└── README.md
```

---

## ⚠️ Notlar

- Yalnızca **Windows** üzerinde çalışır (`pycaw`, `pyautogui` Windows bağımlıdır)
- Ollama arka planda çalışıyor olmalı (`ollama serve`)
- `hafiza.txt` dosyasını `.gitignore`'a eklemeyi unutma (kişisel konuşmalar içerir)

---

## 📄 Lisans

MIT License — dilediğin gibi kullan, fork'la, geliştir.
