# AGENTS.md

Bu doküman, bu proje üzerinde çalışacak bir sonraki yapay zeka ajanı için operasyonel rehberdir.

## Proje Özeti
- Proje: **ZuzuMood** (React + TypeScript + Vite).
- Router: `HashRouter` (`/#/shop`, `/#/blog`, `/#/product/:id`).
- Ürün kaynağı: **tek kaynak** `products/EtsyListingsDownload.csv`.
- Ürün datası runtime'da `services/data.ts` içinde CSV parse edilerek üretiliyor.
- AI chat: `components/AIStylist.tsx` içinde Gemini (`@google/genai`) ile çalışıyor.
- Günlük blog otomasyonu: GitHub Actions + Python script ile `public/blog` altına içerik üretir.

## Kritik Mimari Kararlar
1. **Tek kaynak CSV**
   - Sitede gösterilen ürünler yalnızca `products/EtsyListingsDownload.csv` dosyasından gelir.
   - Bu dosyada olmayan ürün listede görünmez.
2. **Görsel kaynağı Etsy CDN**
   - Kart ve detay görseli CSV'deki `IMAGE1` alanından gelir.
   - Bazı ortamlarda Etsy görselleri CORS/CORB yüzünden bloklanabilir; bu durum AI chat ile doğrudan ilgili değildir.
3. **AI API key çözümü (deployment kritik)**
   - Frontend’de kullanılan ana değişken: `VITE_GEMINI_API_KEY`.
   - Fallback sırası: `GEMINI_API_KEY` → `GEMINI_KEY` → `API_KEY`.
   - `vite.config.ts` içinde bu anahtarlar `__GEMINI_API_KEY__` ve eski `process.env.*` tanımlarıyla derleme anında gömülür.
4. **Otomatik güncelleme davranışı**
   - CSV dosyası development ortamında HMR ile yenilenir.
   - Production için yeni build/deploy gerekir.
5. **Kategori çıkarımı**
   - Kategoriler başlık ve etiketlerdeki anahtar kelimelerden türetilir (`services/data.ts`).
6. **Günlük blog mimarisi**
   - Haber kaynağı: Google News RSS (`hl=en-US&gl=US&ceid=US:en`) fashion odaklı sorgular.
   - İçerik üretimi: Gemini metin modeli JSON payload döndürür.
   - Görsel üretimi: Gemini image modeli ile kapak görseli üretilir, başarısız olursa default SVG kullanılır.
   - Workflow yalnız `public/blog` klasörünü commit eder.

## Dosya Yapısı (Önemli)
- `services/data.ts`: CSV parser + ürün oluşturma + kategori çıkarımı.
- `products/EtsyListingsDownload.csv`: Etsy export verisi (tek gerçek kaynak).
- `components/AIStylist.tsx`: Gemini entegrasyonu, chat UI, öneri ürünleri.
- `pages/Shop.tsx`, `pages/Home.tsx`, `pages/ProductDetail.tsx`: Ürün verisini `PRODUCTS` üzerinden kullanır.
- `pages/Blog.tsx`: `public/blog/index.json` ve markdown dosyalarını okuyup blog UI render eder.
- `public/sitemap.xml`, `public/robots.txt`: SEO tarama yapılandırması.
- `vite.config.ts`: env yükleme + anahtar inject + alias.
- `vite-env.d.ts`: Vite `import.meta.env` ve global define tipleri.
- `.github/workflows/daily-fashion-blog.yml`: günlük blog otomasyonu.
- `scripts/gemini_daily_fashion_blog.py`: haber çekme + blog üretme + görsel üretme.
- `public/blog/`: üretilen markdown, index ve görseller.

## AI Stylist Davranışı (Güncel)
- Prompt artık **daha kısa, pratik, kullanıcı diline uyumlu** cevap üretmeye odaklıdır.
- Satın alma/ödeme/kargo niyetli sorularda yanıtın içinde Etsy mağaza linki geçmesi zorunludur: `https://www.etsy.com/shop/ZuzuMood`.
- Öneri ürün sayısı en fazla **4** ile sınırlandı.
- Model boş/bozuk `message` döndürürse UI tarafında güvenli fallback mesajı gösterilir.
- Ürün bağlamına `price` ve `etsyUrl` da eklendi; ürün uydurma riskini azaltır.

## SEO Notları
- `index.html` içinde title/description/keywords tanımlı.
- `public/sitemap.xml` en az `/` ve `/#/shop` içerir.
- Yeni route eklendiğinde `sitemap.xml` ve gerekirse `robots.txt` güncellenmelidir.
- HashRouter kullanıldığı için canonical ve sosyal paylaşım meta stratejisi ayrıca değerlendirilmelidir.
- Blog içerikleri `/#/blog` route'unda runtime fetch ile gösterilir (`public/blog/index.json` + markdown).
- HashRouter kullanımı nedeniyle blog postları query param (`/#/blog?post=<slug>`) ile açılır.

## Chatbot Troubleshooting
1. Tarayıcı console’da `An API Key must be set when running in a browser` görürsen:
   - Netlify environment variables içinde `VITE_GEMINI_API_KEY` tanımlı mı kontrol et.
   - Değişken eklendikten sonra **yeniden deploy** et (eski build’e sonradan eklenen env yansımaz).
2. Sadece `GEMINI_KEY`/`API_KEY` varsa:
   - Uygulama fallback ile çalışabilir ama standart olarak `VITE_GEMINI_API_KEY` kullan.
3. `index.css 404`:
   - `index.html` içinde hardcoded `/index.css` referansı olmamalı.
4. Etsy görsel CORS hataları:
   - Ürün görsellerini etkiler; chatbot text cevap üretimini normalde engellemez.
5. Yanıtlar aşırı “kurumsal/lüks” ise:
   - `components/AIStylist.tsx` içindeki `systemInstruction` kurallarını kontrol et.
   - JSON schema + kısa cevap limiti + dil uyumu maddeleri korunmalı.

## Blog Otomasyonu Troubleshooting
1. Workflow başarısız ve `GEMINI_KEY` yok hatası alıyorsan:
   - Repo secrets altında `GEMINI_KEY` tanımlı olmalı.
2. RSS haber gelmiyorsa:
   - Google News query parametreleri (`hl=en-US&gl=US`) korunmalı.
3. Görsel üretimi başarısızsa:
   - Script default olarak `public/blog/images/default-fashion.svg` kullanır; pipeline durmaz.
4. Blog JSON parse hatası olursa:
   - Gemini promptundaki strict JSON şeması bozulmuş olabilir; promptu sadeleştir.

## Geliştirme Komutları
- `npm install`
- `npm run dev`
- `npm run build`
- `npm run preview`
- `pip install -r requirements.txt`
- `GEMINI_KEY=... python scripts/gemini_daily_fashion_blog.py`

## Değişiklik Yaparken Kontrol Listesi
1. Ürün datası yalnızca CSV'den geliyor mu?
2. CSV parse işlemi quote/newline içeren açıklamalarda bozulmuyor mu?
3. Yeni route eklendiyse sitemap güncellendi mi?
4. Build başarılı mı?
5. Node modules içinde değişiklik yapılmadı mı?
6. AI ile ilgili değişiklikte env isimleri dokümante edildi mi?
7. Chatbot mesaj tonu gerçek kullanıcı sorularında kısa ve net mi?
8. Blog otomasyonunda secret adı `GEMINI_KEY` ile uyumlu mu?
9. Workflow sadece gerekli klasörleri mi commit ediyor?

## Bilinen Kısıt
- Etsy export dosyasında doğrudan listing URL yoksa ürün linki Etsy shop search query ile üretilir.
- Blog içeriği Markdown üretir; frontend tarafında basit markdown blok parse ile render edilir (tam markdown motoru değildir).

## Son Görev Özeti (2026-02-11)
- Kullanıcı geri bildirimi: Anasayfadan bloglara erişimde görünürlük sorunu bildirildi; blog sayfası linklerinin header/footer içinde daha erişilebilir olması istendi.
- Yapılanlar:
  - `components/Header.tsx` sağ aksiyon alanına da doğrudan `Blog` linki eklendi; böylece sticky header durumunda blog erişimi netleşti.
  - `components/Footer.tsx` içinde gezinme alanı `react-router-dom` `Link` ile güçlendirildi ve footer'a blog erişimi (`Daily Blog`) eklendi.
  - Footer'daki "Explore All Pieces" metni de gerçek route (`/shop`) linki olacak şekilde düzeltildi.
- SEO/Sitemap kontrolü:
  - Yeni route eklenmedi; `public/sitemap.xml` içinde `/#/blog` zaten mevcut, ek değişiklik gerekmedi.

## Teslim Standartları
- Kod değişikliği sonrası build çalıştır.
- Commit + PR kaydı oluştur.
- Final raporda dosya ve satır referanslarıyla değişikliği özetle.
