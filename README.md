# YükTakip 🚚

**Lojistik operasyonlarını tek platformda yönetmek için geliştirilmiş web tabanlı yük takip ve operasyon yönetim uygulaması.**

Yük oluşturma, firma ve adres yönetimi, araç/şoför planlama, yük durum takibi, depo operasyonu ve rol tabanlı kullanıcı yönetimini tek bir uygulamada birleştirir.

> **Building Turkey 2026 – Yük Operasyon** kapsamında geliştirilen MVP.
>
> Proje, **Emergent AI** kullanılarak tasarlanmış ve geliştirilmiştir.

## 🔗 Demo & Proje

- **Canlı Demo:** https://yuk-takip.vercel.app/
- **GitHub:** https://github.com/bilisimfatihi/yuk-takip
- **Emergent Building Turkey:** https://emergent.sh/ai-contests/building-turkiye

## 🎯 Projenin Amacı

Lojistik operasyonlarında Excel, telefon ve WhatsApp gibi dağınık araçlarla yürütülen yük takibi ve planlama süreçlerini tek bir dijital operasyon panelinde birleştirmek.

YükTakip; yükün oluşturulmasından araç planlamasına, sevkiyat sürecinden depoya ulaşmasına kadar temel operasyon akışını görünür ve takip edilebilir hale getirir.

## ✨ Temel Özellikler

### 📦 Yük Yönetimi

- Yeni yük oluşturma
- Müşteri firması ve firmaya ait adres seçimi
- Yük tarihi ve operasyon bilgileri
- Gönderim şekli seçimi
- Yük detay ekranı
- Durum geçmişi / zaman çizelgesi
- Yük arama ve filtreleme
- Sayfalama ile büyük veri setlerinde daha verimli listeleme

### 🚛 Araç & Sevkiyat Planlama

- Araç yönetimi
- Şoför yönetimi
- İç nakliye yükleri için araç ve şoför planlama
- Planlanan yüklerin takip edilmesi
- Şoföre WhatsApp üzerinden operasyon bilgisinin gönderilebilmesi

### 🏢 Firma & Adres Yönetimi

- Müşteri firma CRUD işlemleri
- Bir firmaya birden fazla adres tanımlama
- Yük oluştururken seçilen firmaya ait adreslerin listelenmesi
- Adres bilgilerini yük detayında görüntüleme

### 📊 Dashboard

- Toplam yük
- Bekleyen yükler
- Planlama bekleyen yükler
- Planlanan yükler
- Teslim/depo durumları
- Son yükler

### 👥 Rol Tabanlı Kullanıcı Yönetimi

Uygulamada dört temel rol bulunur:

| Rol | Ana Sorumluluk |
|---|---|
| **Admin** | Sistem ve kullanıcı yönetimi |
| **Yük Sorumlusu** | Yük, firma ve adres operasyonları |
| **Araç Planlama** | Araç, şoför ve sevkiyat planlama |
| **Depocu** | Yüklerin depo operasyonundaki takibi |

Kullanıcılar birden fazla role sahip olabilir. Yetkilendirme hem frontend hem backend tarafında uygulanır.

### 🔐 Kimlik Doğrulama & Güvenlik

- Kullanıcı adı veya e-posta ile giriş
- Token tabanlı oturum yönetimi
- Rol bazlı backend authorization
- Şifrelerin `scrypt` ile hashlenmesi
- Kullanıcının kendi şifresini değiştirebilmesi
- Admin tarafından kullanıcı oluşturma, düzenleme, aktifleştirme/pasifleştirme ve silme
- Admin tarafından şifre sıfırlama
- Son aktif admin hesabının korunması
- Kullanıcı şifrelerinin API yanıtlarında döndürülmemesi

## 🧭 Operasyon Akışı

```text
Yük Oluştur
    ↓
Firma + Adres Seç
    ↓
Gönderim Şeklini Belirle
    ↓
İç Nakliye ise
    ↓
Araç + Şoför Planla
    ↓
Şoföre Bilgi Gönder
    ↓
Yük Yolda
    ↓
Depoya Ulaştı
```

## 🏗️ Teknik Mimari

YükTakip, Next.js tabanlı full-stack bir uygulama olarak geliştirilmiştir.

```text
┌──────────────────────────────────────────┐
│              Next.js Frontend             │
│        React + Tailwind CSS + UI          │
└────────────────────┬─────────────────────┘
                     │
                     │ REST-style API
                     ▼
┌──────────────────────────────────────────┐
│        Next.js API Route Handler          │
│   Authentication / Authorization / CRUD   │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│                  MongoDB                  │
│ users · sessions · loads · companies     │
│ addresses · drivers · vehicles           │
└──────────────────────────────────────────┘
```

### Teknolojiler

- **Next.js 15**
- **React 18**
- **JavaScript**
- **MongoDB**
- **Tailwind CSS**
- **Radix UI**
- **Lucide React**
- **TanStack React Query / Table**
- **Axios**
- **Zod**
- **Framer Motion**
- **Vercel**
- **Emergent AI**

## ⚡ Performans

Yük listesi için server-side pagination ve filtreleme uygulanmıştır. API; sayfa, sayfa boyutu, durum, firma, gönderim tipi, tarih ve metin araması gibi parametreleri destekler.

Dashboard sayaçları da yüklerin tamamını belleğe almak yerine MongoDB üzerinde paralel `countDocuments` sorguları kullanacak şekilde optimize edilmiştir.

## 🧪 Test & Kalite

Projenin geliştirme sürecinde backend ve rol/yetki değişiklikleri için otomatik test senaryoları kullanılmıştır.

Özellikle rol tabanlı erişim, kullanıcı yönetimi, authentication ve pagination değişikliklerinde mevcut MVP davranışının korunması doğrulanmıştır.

## 🗂️ Proje Yapısı

```text
.
├── app/
│   ├── api/
│   │   └── [[...path]]/
│   │       └── route.js       # API, auth ve backend işlemleri
│   ├── globals.css
│   ├── layout.js
│   ├── page.js                # Ana frontend uygulaması
│   └── providers.js
├── components/
│   └── ui/                    # UI bileşenleri
├── hooks/
├── lib/
├── backend_test.py
├── backend_test_admin.py
├── backend_test_auth.py
├── backend_test_pagination.py
├── components.json
├── jsconfig.json
└── package.json
```

## 🚀 Yerel Geliştirme

### Gereksinimler

- Node.js
- npm
- MongoDB

### Kurulum

```bash
git clone https://github.com/bilisimfatihi/yuk-takip.git
cd yuk-takip
npm install
```

Gerekli ortam değişkenlerini `.env.local` dosyanıza ekleyin:

```env
MONGO_URL=your_mongodb_connection_string
DB_NAME=yuktakip
ADMIN_EMAIL=your_admin_email
ADMIN_PASSWORD=your_admin_password
```

Geliştirme sunucusunu başlatın:

```bash
npm run dev
```

Uygulama varsayılan olarak `http://localhost:3000` adresinde çalışır.

Production build için:

```bash
npm run build
npm start
```

## 🔒 Güvenlik Notu

Gerçek kullanımda yönetici şifresi ve veritabanı bağlantı bilgileri kaynak koda eklenmemeli, yalnızca güvenli environment variable yönetimi üzerinden sağlanmalıdır.

Demo/test hesapları yalnızca geliştirme ve yarışma demosu amacıyla kullanılmalıdır.

## 🛣️ Yol Haritası

MVP sonrasında değerlendirilen geliştirmeler:

- [ ] Depocu için özel bekleyen yükler ekranı
- [ ] Yük etiketi yazdırma
- [ ] A5 etiket + QR kod
- [ ] Kullanıcı aktivite/denetim kaydı
- [ ] Toplu rol değişimi
- [ ] Gelişmiş raporlama
- [ ] Türkçe karakter duyarlı gelişmiş arama
- [ ] Yük fotoğrafı ekleme

## 🏆 Building Turkey 2026

YükTakip, **Building Turkey 2026** yarışması kapsamında lojistik operasyonlarında gerçek bir iş problemini çözmek amacıyla geliştirilen bir MVP'dir.

Projenin temel yaklaşımı; mevcut operasyon deneyimini, yapay zekâ destekli hızlı ürün geliştirme süreciyle birleştirerek kısa sürede çalışan, test edilebilir ve geliştirilebilir bir ürün ortaya çıkarmaktır.

## 👨‍💻 Geliştirici

**Fatih Fındık**

- GitHub: https://github.com/bilisimfatihi

---

> Bu proje bir MVP'dir. Üretim ortamında kullanılmadan önce güvenlik, gözlemlenebilirlik, test kapsamı, veri yedekleme ve operasyonel gereksinimler ayrıca değerlendirilmelidir.
