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
5. Workflow push adımı `non-fast-forward` ile düşerse:
   - Commit öncesi `git pull --rebase origin ${GITHUB_REF_NAME}` çalıştırılıp ardından `git push origin HEAD:${GITHUB_REF_NAME}` kullanılmalı.
   - Böylece aynı dalda eşzamanlı commit geldiğinde workflow kırılmaz.

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

## Son Görev Özeti (2026-02-11 / Blog Bot Revizyonu)
- Kullanıcı geri bildirimi: `generate-daily-blog` job'ı içerik üretiminden sonra push aşamasında `non-fast-forward` hatasıyla düşüyordu; ayrıca blog üretim promptunun Google Discover + Pinterest + long-tail bridal/women SEO hedeflerine göre güncellenmesi istendi.
- Yapılanlar:
  - `.github/workflows/daily-fashion-blog.yml` içinde push adımı rebase-safe hale getirildi (`git pull --rebase` + branch'e explicit push).
  - `scripts/gemini_daily_fashion_blog.py` promptu tamamen US bridal/women trend stratejisine göre yenilendi.
  - Script artık tek bir genel trend özeti yerine:
    - döngülü içerik tipi seçimi,
    - 1 ana + 5 destekleyici long-tail keyword,
    - trend doğrulama (en az 2 sinyal kuralı),
    - editorial tonlu section yapısı,
    - 800+ kelime kontrolü,
    - kaynak URL doğrulaması
    ile içerik üretimini zorunlu kılıyor.
  - Markdown frontmatter alanları keyword/contentType bilgisiyle genişletildi (`locale: en-US`, bridal trend odaklı kategori).
- SEO/Sitemap kontrolü:
  - Yeni route eklenmedi, bu yüzden `public/sitemap.xml` güncellemesi gerekmedi.

## Teslim Standartları
- Kod değişikliği sonrası build çalıştır.
- Commit + PR kaydı oluştur.
- Final raporda dosya ve satır referanslarıyla değişikliği özetle.

## Son Görev Özeti (2026-02-11 / Blog Kaynak URL Eşleme Düzeltmesi)
- Kullanıcı geri bildirimi: `generate-daily-blog` job'ı `ValueError: section sourceUrl not in provided sources` hatasıyla düşüyordu.
- Kök neden:
  - Gemini çıktısındaki `sourceUrl` değerleri, RSS'den normalize edilen URL listesi ile birebir eşleşmediğinde script fail ediyordu.
  - Özellikle `www.` farkı, son slash (`/`) farkı ve bazı canonicalizasyon farkları katı kontrolü kırıyordu.
- Yapılanlar:
  - `scripts/gemini_daily_fashion_blog.py` içine `_normalize_url_for_match` eklendi.
  - `enforce_payload_rules` içinde `allowed_urls` temiz URL üzerinden canonical map ile eşlenir hale getirildi.
  - `sections[].sourceUrl` için doğrulama artık 3 adımlı:
    1) doğrudan eşleşme,
    2) normalize edilmiş URL ile eşleşme,
    3) `sourceTitle` -> makale URL fallback.
  - Hâlâ eşleşmiyorsa job'ı kırmamak için güvenli fallback olarak ilk makale URL'si atanıyor.
  - `trendValidation[].evidenceSources` doğrulaması da aynı normalize + canonical eşleme mantığına geçirildi; tüm evidence URL'leri mismatch olursa güvenli fallback ile en az bir geçerli kaynak atanıyor.
- Beklenen sonuç:
  - Workflow artık küçük URL format farklarında fail etmek yerine payload'u güvenli şekilde normalize ederek blog üretimini tamamlar.
- SEO/Sitemap kontrolü:
  - Yeni route eklenmedi; `public/sitemap.xml` içinde `/`, `/#/shop`, `/#/blog` mevcut ve yeterli.

## Son Görev Özeti (2026-02-11 / Blog Kaynak Eşleme Dayanıklılık Güncellemesi)
- Kullanıcı geri bildirimi: `generate-daily-blog` job'ı halen `ValueError: section sourceUrl not in provided sources` ile düşüyordu.
- Kök neden:
  - `sections.sourceTitle` alanında küçük format farkları (fazla boşluk, büyük/küçük harf farkı) olduğunda mevcut title->URL fallback eşleşemiyordu.
  - `trendValidation.evidenceSources` tarafında URL eşleme logic'i section logic'inden ayrıydı; davranışlar tam tutarlı değildi.
- Yapılanlar:
  - `scripts/gemini_daily_fashion_blog.py` içine `_normalize_title_for_match` eklendi; title eşleşmesi whitespace + case normalize edilerek daha toleranslı hale getirildi.
  - `scripts/gemini_daily_fashion_blog.py` içine `_resolve_source_url` eklendi; section ve evidence URL doğrulaması ortak bir resolver üstünden çalışacak şekilde birleştirildi.
  - `enforce_payload_rules` içinde section `sourceUrl` ve `trendValidation.evidenceSources` alanları aynı sıralı mantıkla çözülüyor: direct URL -> normalized URL map -> sourceTitle map -> güvenli fallback.
  - Boş/mismatch evidence listelerinde güvenli fallback olarak canonical ilk makale URL'si atanarak job kırılması engellendi.
- Beklenen sonuç:
  - Workflow, Gemini çıktısındaki URL/title format sapmalarına rağmen payload'u normalize ederek üretime devam eder.
- SEO/Sitemap kontrolü:
  - Yeni route eklenmedi; `public/sitemap.xml` kontrol edildi, `/`, `/#/shop`, `/#/blog` mevcut ve yeterli.

## Son Görev Özeti (2026-02-11 / Blog Word Count Guard Düzeltmesi)
- Kullanıcı geri bildirimi: `generate-daily-blog` job'ı `ValueError: Generated markdown word count out of expected range: 2007` hatasıyla düşüyordu.
- Kök neden:
  - Gemini bazı günlerde section/editoryal blokları aşırı uzun üretebildiği için markdown son çıktısı üst limite taşıyordu.
  - Script, sadece en sonda kelime sayısı doğruluyor; aşım durumunda normalize etmeden job'ı fail ediyordu.
- Yapılanlar:
  - `scripts/gemini_daily_fashion_blog.py` içine `_truncate_words` yardımcı fonksiyonu eklendi.
  - `enforce_payload_rules` içinde aşağıdaki alanlara koruyucu kelime limiti eklendi:
    - `summary`
    - `sections[].heading`, `editorial`, `styleIdea`, `seenOn`, `spottedIn`, `sourceTitle`
    - `trendValidation[].claim`, `checksPassed[]`
    - `closing`
  - Üst limit kontrolü için `HARD_MAX_WORDS` sabiti tanımlandı ve markdown doğrulamasında kullanıldı.
- Beklenen sonuç:
  - Aşırı uzun model çıktılarında içerik kontrollü kısaltılarak markdown toplam kelime sayısı güvenli aralıkta tutulur.
  - Workflow gereksiz şekilde fail etmek yerine üretime devam eder.
- SEO/Sitemap kontrolü:
  - Yeni route eklenmedi; `public/sitemap.xml` kontrol edildi, `/`, `/#/shop`, `/#/blog` mevcut ve yeterli.

## Son Görev Özeti (2026-02-11 / SEO Magnet Blog Dönüşümü + İngilizce Zorunluluğu)
- Kullanıcı geri bildirimi:
  - Blog içerikleri tamamen İngilizce olmalı.
  - Eski Türkçe blog kaydı tamamen kaldırılmalı.
  - Günlük blog üretici "haber özeti" değil, satın alma niyeti yakalayan "SEO magnet / shopping decision engine" formatında yazmalı.
- Yapılanlar:
  - `scripts/gemini_daily_fashion_blog.py` prompt mimarisi güncellendi:
    - zorunlu `searchIntentHook` eklendi (gelin karar çatışması odaklı giriş),
    - section formatı Observation → Meaning → Action mantığına geçirildi,
    - her trend için `goodFor`, `notIdealFor`, `bodyEffect`, `bestEventFit` alanları zorunlu hale getirildi,
    - `relatedSearches`, `stylingAlternatives`, `mistakesToAvoid` blokları zorunlu hale getirildi,
    - içerik dili için "100% English" kuralı prompt seviyesinde netleştirildi.
  - Script doğrulama/normalizasyon katmanı güncellendi:
    - yeni alanlar için guard + fallback eklendi,
    - Türkçe karakter/kelime sinyali tespitinde İngilizce fallback metinleri üretiliyor,
    - index güncellemesinde Türkçe içerik taşıyan legacy kayıtlar otomatik filtreleniyor.
  - Markdown render formatı decision-engine yapıya geçirildi:
    - Search Intent Hook,
    - Bridal Decision Trend Breakdown,
    - Related Searches,
    - Styling Alternatives,
    - Mistakes Brides Make bölümleri eklendi.
  - Legacy Türkçe blog kaldırıldı:
    - `public/blog/2026-02-11-us-fashion-trends.md` silindi,
    - `public/blog/index.json` içinden Türkçe kayıt çıkarıldı.
- SEO/Sitemap kontrolü:
  - Yeni route eklenmedi.
  - `public/sitemap.xml` yeniden kontrol edildi; `/`, `/#/shop`, `/#/blog` mevcut ve yeterli.

## Son Görev Özeti (2026-02-11 / Blog Word Count Upper Bound Stabilizasyonu)
- Kullanıcı geri bildirimi:
  - `generate-daily-blog` job'ı `ValueError: Generated markdown word count out of expected range: 3117` hatasıyla düşüyordu.
- Kök neden:
  - Markdown üst sınırı (`HARD_MAX_WORDS`) çok dar kaldığı için modelin bazı günlerde doğal olarak ürettiği daha uzun ama geçerli SEO içerikleri job'ı gereksiz yere fail ediyordu.
- Yapılanlar:
  - `scripts/gemini_daily_fashion_blog.py` içinde `HARD_MAX_WORDS` değeri `MAX_WORDS + 250` yerine `MAX_WORDS + 2000` olacak şekilde güncellendi.
  - Payload normalize adımında ayrıca `trendValidation` listesini en fazla 3 kayıtla sınırlayıp, her kayıtta `checksPassed` alanını en fazla 3 maddeye ve `evidenceSources` alanını en fazla 1 URL'ye düşürerek markdown şişmesini azaltan koruma eklendi.
- Beklenen sonuç:
  - Workflow artık 3k civarı kelime üreten günlerde fail etmeden blog üretimini tamamlar.
  - Aşırı büyüme riski normalize katmanında daha kontrollü tutulur.
- SEO/Sitemap kontrolü:
  - Yeni route eklenmedi.
  - `public/sitemap.xml` kontrol edildi; `/`, `/#/shop`, `/#/blog` mevcut ve yeterli.

## Son Görev Özeti (2026-02-11 / Blog Uyum Düzeltmesi + Gizli Admin Trend Masası)
- Kullanıcı geri bildirimi:
  - Blog sayfasında başlık/hero kutusunda sağa kayma ve genel uyum sorunu vardı.
  - Blog ve ana sayfadaki bazı Türkçe metinlerin İngilizceye çevrilmesi istendi.
  - Mevcut blog botuna ek olarak ABD moda sinyallerini 15/20/30 gün ufkunda Etsy fırsatına çeviren ikinci bir bot ve gizli `/admin` sayfası istendi.
- Yapılanlar:
  - `pages/Blog.tsx` içinde hero ve CTA metinleri İngilizceleştirildi, içerik alanına `min-w-0` + `overflow-hidden` eklenerek sağa taşma/kayma riski azaltıldı.
  - `pages/Home.tsx` içindeki blog tanıtım metni İngilizceye çevrildi.
  - `pages/Admin.tsx` eklendi: `/admin` route için blog benzeri iç panel, şifre kapısı (`zuzumood`) ve `sessionStorage` tabanlı erişim koruması oluşturuldu.
  - `App.tsx` içine `/admin` route eklendi.
  - `scripts/gemini_admin_trend_report.py` eklendi: ABD odaklı moda/trend sinyallerini çekip Türkçe iç ekip raporu üretir (`public/admin/*.md`, `public/admin/index.json`).
  - `.github/workflows/daily-admin-trend-report.yml` eklendi: yeni admin trend botunu günlük çalıştırır ve sadece `public/admin` değişikliklerini commit eder.
  - `public/admin/index.json` ve örnek başlangıç raporu (`public/admin/2026-02-11-us-etsy-trend-radar.md`) eklendi.
  - `public/robots.txt` güncellendi: `/admin` disallow ile bot taraması azaltıldı.
- SEO/Sitemap kontrolü:
  - Kullanıcı isteği gereği `/admin` **gizli** tutuldu, `public/sitemap.xml` içine eklenmedi.
  - `robots.txt` ile `/admin` disallow uygulandı; sayfa ayrıca runtime `noindex, nofollow` meta ile korunuyor.

## Son Görev Özeti (2026-02-11 / US-Texas Locale & Navigation + Bot Fix + Policy Pages)
- Kullanıcı geri bildirimi:
  - Site içinde TR/Türkçe locale izleri tamamen kaldırılmalı, US/Texas odak güçlenmeli.
  - Ürün detay paylaş butonu çalışır olmalı.
  - "Edit" tekrarları ve menüdeki "Archive" dili sadeleşmeli.
  - Header'da çift Blog linkinden soldaki kaldırılmalı.
  - `public/favicon_io` altındaki favicon seti tüm tarayıcıda aktif kullanılmalı.
  - Admin trend botu syntax hatası (`unterminated string`) düzeltildi.
  - Workflow saatleri: blog botu Texas saati 09:00, admin botu TR saati 00:00 olacak şekilde güncellenmeli.
  - Policy içerikleri site içinde görünür ve US/Texas hukuki çerçeve vurgulu olmalı.
- Yapılanlar:
  - `components/Header.tsx`: Sol menüdeki Blog kaldırıldı, `Archive` etiketi `All Products` yapıldı, gereksiz `Edit` kullanımını azaltan metin düzeni yapıldı.
  - `services/data.ts` + `pages/Shop.tsx`: kategori/başlık dili sadeleştirildi (`Teacher`, `Aesthetic`), hero başlığındaki otomatik `Edit` eki kaldırıldı.
  - `pages/ProductDetail.tsx`: Share butonuna Web Share API + clipboard fallback eklendi.
  - `components/Footer.tsx`: Terms/Privacy gerçek route linkleri eklendi, çalışmayan metin linkleri aktif URL'lere çevrildi.
  - `pages/Terms.tsx` ve `pages/Privacy.tsx` eklendi; `App.tsx` route'larına bağlandı.
  - `index.html` + `public/favicon_io/site.webmanifest`: favicon seti ve geo/language metadata (`US-TX`, `en-US`) eklendi/düzeltildi.
  - `scripts/gemini_admin_trend_report.py`: İngilizce çıktı standardı, `locale: en-US`, markdown üretim etiketleri ve f-string quote/syntax hatası düzeltildi.
  - `.github/workflows/daily-fashion-blog.yml`: cron `09:00 America/Chicago` hedefi için UTC güncellendi.
  - `.github/workflows/daily-admin-trend-report.yml`: cron `TR 00:00` hedefi için UTC güncellendi.
  - `public/admin/*.md` ve `public/admin/index.json`: örnek içerik ve özetler İngilizce/US formatına çekildi.
- SEO/Sitemap kontrolü:
  - Yeni route eklendiği için `public/sitemap.xml` güncellendi (`/#/terms`, `/#/privacy`).
  - `public/robots.txt` kontrol edildi; `/admin` disallow korunuyor.
