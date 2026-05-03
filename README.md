# Amazon.com.tr Fiyat Takibi

Bu Home Assistant add-on'u `amazon.com.tr` urun sayfalarini ve filtreli arama sonuc sayfalarini belirli araliklarla kontrol eder. Hedef fiyat yakalaninca Pushover bildirimi gonderir.

Ana hedef ortam `Home Assistant OS` yuklu Raspberry Pi'dir. Kodlar GitHub'da saklanir ve Home Assistant'a add-on repository olarak eklenerek guncellenir.

## Guncel Surum

```txt
1.2.10
```

Bu surum sidebar durum ekranina `Loglari Ac` ve `Ayarlari Ac` kisayollari ekler. Butonlar Home Assistant add-on sayfasindaki ilgili sekmeleri acacak sekilde ayarlandi.

## Ne Yapar?

- Dogrudan Amazon urun linklerini takip eder.
- Filtreli Amazon arama sayfalarindaki urun kartlarini takip eder.
- Tek search page altinda iki farkli arama linkini birlikte tarayabilir.
- Ayni urun iki linkte de cikarsa tekillestirir ve en dusuk fiyati kullanir.
- `Diger satin alma secenekleri` altindaki ikinci el teklif fiyatini okuyabilir.
- Arama sonuc sayfasinin altindaki onerilen/alternatif urun bloklarini yok sayar.
- Ayni urun ayni fiyatta kalirsa 24 saat icinde tekrar bildirim gondermez.
- Ayni urun daha dusuk fiyata inerse 24 saati beklemeden yeniden bildirim gonderir.
- Her arama turunun sonunda eslesen urunleri tek fiyat ozeti tablosunda gosterir.
- Home Assistant kenar cubugunda kisa durum sayfasi gosterebilir.
- Sidebar ekranindan Log ve Configuration sekmelerine kisa yol sunar.
- Arama hatalarinda Pushover ile uyari gonderir.
- Amazon gecici `429/5xx` hatalarinda tekrar dener ve gerekirse soguma uygular.
- Loglari yerel saatle yazar ve her turun sonunda sonraki kontrol zamanini gosterir.

## Sidebar Kullanimi

Add-on guncellendikten ve yeniden baslatildiktan sonra Home Assistant add-on Info ekraninda `Show in sidebar` secenegi gorunur.

1. Add-on sayfasinda `Check for updates` ve ardindan `Update` calistir.
2. Add-on'u yeniden baslat.
3. Add-on Info ekraninda `Show in sidebar` secenegini ac.
4. Sol menude `Amazon Tracker` kisayolu gorunur.
5. Sidebar ekranindaki `Loglari Ac` butonu add-on Log sekmesini acar.
6. Sidebar ekranindaki `Ayarlari Ac` butonu add-on Configuration sekmesini acar.

Sidebar sayfasi 60 saniyede bir otomatik yenilenir. Ayar degistirmek icin yine add-on `Configuration` sekmesini, ayrintili takip icin `Log` sekmesini kullan.

## Ornek Log Tablosu

Arama dongusundeki tum hedefler kontrol edildikten sonra loglarda buna benzer bir tablo gorunur:

```txt
[2026-05-02 12:10:05] Ozet: eslesen=3
[2026-05-02 12:10:05]  No | Urun Adi                                 |      Fiyat |      Hedef |       Fark
[2026-05-02 12:10:05] ----+------------------------------------------+------------+------------+-----------
[2026-05-02 12:10:05]   1 | Philips Hue Essential Akilli LED Ampul... |   3.771,49 |   2.000,00 |  +1.771,49
[2026-05-02 12:10:05]   2 | Apple iPad Air 13 inc (M4): Liquid Ret... |  46.169,10 |  40.000,00 |  +6.169,10
[2026-05-02 12:10:05]   3 | Tapo C425 Kablosuz Guvenlik Kamerasi      |   3.424,20 |   3.100,00 |    +324,20
```

Tablodaki `Urun Adi`, Amazon arama sonucunda bulunan gercek urun basligidir. Config ekraninda yazdigin `product_name` ise sadece eslesme yapmak icin kullanilir. Hedef fiyat ve altindaki urunler icin Pushover bildirim akisi aynen calismaya devam eder.

## Ornek Yapilandirma

Tek arama sayfasi kullaniyorsan `search_name` bos kalabilir. `search_url_2` istege baglidir:

```yaml
interval_minutes: 30
request_timeout_seconds: 20
pushover_user_key: "PUSHOVER_USER_KEY"
pushover_api_token: "PUSHOVER_APP_TOKEN"
products: []
search_pages:
  - name: "ipad ikinci el"
    search_url: "https://www.amazon.com.tr/s?k=ipad&i=warehouse-deals"
    search_url_2: "https://www.amazon.com.tr/s?k=ipad&rh=p_n_condition-type%3A13818537031&dc&rnid=13818535031"
    max_items_to_scan: 40
    notify_once_in_24H: true
search_targets:
  - name: "iPad Air 13 M4"
    product_name: "ipad air 13"
    target_price: 35000
  - name: "iPad Pro 13 256"
    product_name: "ipad pro 13 256"
    target_price: 60000
```

Birden fazla arama sayfasi kullaniyorsan `search_name` alanina ilgili `search_pages.name` degerini aynen yaz:

```yaml
search_pages:
  - name: "ipad ikinci el"
    search_url: "https://www.amazon.com.tr/s?k=ipad&i=warehouse-deals"
    search_url_2: "https://www.amazon.com.tr/s?k=ipad&rh=p_n_condition-type%3A13818537031&dc&rnid=13818535031"
    max_items_to_scan: 40
    notify_once_in_24H: true
  - name: "mac ikinci el"
    search_url: "https://www.amazon.com.tr/s?k=macbook&i=warehouse-deals"
    max_items_to_scan: 40
    notify_once_in_24H: true
search_targets:
  - name: "iPad Air 13 M4"
    search_name: "ipad ikinci el"
    product_name: "ipad air 13"
    target_price: 35000
  - name: "MacBook Air M4"
    search_name: "mac ikinci el"
    product_name: "macbook air m4"
    target_price: 45000
```

## UI Uzerinden Giris

1. `search_pages` bolumunde `Add` de.
2. `name` alanina arama sayfasinin kisa adini yaz. Ornek: `ipad ikinci el`.
3. `search_url` alanina ana Amazon arama linkini yapistir.
4. `search_url_2` alanina istersen ikinci arama linkini yapistir.
5. `max_items_to_scan` icin ornek `40` yaz.
6. `notify_once_in_24H` acik kalsin.
7. `search_targets` bolumunde takip edecegin her urun hedefi icin `Add` de.
8. `name` alanina hedefin kisa adini yaz.
9. Tek arama sayfan varsa `search_name` bos kalabilir.
10. Birden fazla arama sayfan varsa `search_name` alanina ilgili arama sayfasi adini aynen yaz.
11. `product_name` alanina Amazon sonuc basliginda aranacak metni yaz.
12. `target_price` alanina hedef fiyati yaz.

## Alanlar

`search_pages` alanlari:

- `name`: Arama sayfasinin kisa adi.
- `search_url`: Amazon'da filtreledigin ana arama veya kategori linki.
- `search_url_2`: Istege bagli ikinci arama linki.
- `max_items_to_scan`: Her arama linkinde ilk kac urun kartinin taranacagi.
- `notify_once_in_24H`: `true` ise ayni hedef urun ayni veya daha yuksek fiyatta 24 saat icinde tekrar bildirilmez; daha dusuk fiyat yakalanirsa sure beklemeden bildirilir.

`search_targets` alanlari:

- `name`: Hedefin kisa adi. Bildirimlerde gorunur.
- `search_name`: Hangi arama sayfasinda aranacagi. Tek arama sayfasi varsa bos olabilir.
- `product_name`: Amazon sonuc basliginda aranacak metin. Log ozet tablosunda gorunen isim degildir; tablo Amazon'dan bulunan gercek urun basligini gosterir.
- `target_price`: Bu fiyat ve altindaki eslesmeler icin bildirim gonderilir.

## Notlar

- Amazon zaman zaman bot korumasi, bolgesel farkliliklar veya HTML degisiklikleri uygulayabilir.
- Cok sik sorgu atmak yerine `15-60 dakika` araligi mantiklidir.
- Pushover anahtarlari ve gercek takip listesi GitHub'a konmamalidir.
