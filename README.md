# Amazon.com.tr Fiyat Takibi

Bu proje, `amazon.com.tr` urun sayfalarini veya filtreli arama sonuc sayfalarini belirli araliklarla kontrol edip hedef fiyatin altina inildiginde `Pushover` uzerinden bildirim gonderen Home Assistant add-on'udur.

Ana hedef ortam `Home Assistant OS` yuklu Raspberry Pi'dir. Kodlar GitHub'da saklanir ve Home Assistant'a add-on repository olarak eklenerek guncellenebilir.

## Guncel Surum

```txt
1.1.0
```

Bu surumde `notify_once: true` davranisi 24 saatlik tekrar susturma olarak guncellendi. Ayni urun ayni veya daha yuksek fiyatta kalirsa 24 saat icinde tekrar bildirim gelmez; 24 saat dolduktan sonra hala hedef fiyat altindaysa tekrar hatirlatabilir. Fiyat daha once bildirilen fiyattan daha dusuge inerse 24 saat beklemeden yeniden bildirim gelir.

`1.0.4` surumunde arama sonuc sayfasinin altindaki onerilen/alternatif urun bolumleri tarama disi birakildi. Bot su basliklardan herhangi birini gordugu noktadan sonraki urun kartlarini okumaz: `Yardima mi ihtiyaciniz var?`, `Baktiginiz Urunlere Gore Belirlenen Urunler`, `Tarama gecmisinizdeki urunleri goruntuleyen musteriler ayrica sunlari da goruntuledi:`.

`1.0.3` surumunde her `search_pages` kaydina istege bagli `search_url_2` alani eklendi. Boylece ayni arama hedefleri icin hem Amazon Depo linki hem de Amazon'un sol menuden secilen Ikinci El filtreli linki birlikte taranabilir. Bot iki linkten gelen ayni urunu tekillestirir.

`1.0.2` surumunde arama sonuc kartlarinda `Diger satin alma secenekleri` altinda gorunen `Ikinci El` teklif fiyati okunur. Bir urun kartinda hem sifir urun fiyati hem de ikinci el teklif fiyati varsa bot ikinci el teklif fiyatini oncelikli kullanir.

`1.0.1` surumunde Home Assistant add-on gorselleri yenilendi: `icon.png` 128x128, `logo.png` 250x100 olcusunu korur; logoda Amazon yazisi, smile isareti ve bildirim cani bulunur.

`1.0.0` surumu stabil ve gunluk kullanima uygun ilk ana surum olarak isaretlendi. Dogrudan urun linki takibi, filtreli arama sayfasi takibi, tekrar bildirim engelleme, arama hata bildirimi, Amazon gecici hata bekleme/tekrar deneme ve yerel saatli loglar dahildir.

Her kontrol turu bittikten sonra loga bir sonraki kontrol zamani yazilir.

Ornek:

```txt
Sonraki kontrol: 2026-04-30 21:15:00
```

## Ne yapıyor?

- Amazon Turkiye urun sayfasini duzenli araliklarla indirir.
- Filtreli arama sonuc sayfasindaki urun kartlarini tarayabilir.
- Arama sonuc sayfasinin altindaki onerilen/alternatif urun bloklarini yok sayar.
- Ayni search page altinda iki farkli Amazon arama linkini birlikte kontrol edebilir.
- Arama sonucunda `Diger satin alma secenekleri` altindaki ikinci el teklif fiyatini okuyabilir.
- Tek bir arama sayfasinda birden fazla urun hedefi ve hedef fiyat kontrol edebilir.
- Fiyat hedef degerin altina inerse Pushover bildirimi yollar.
- Ayni urun ayni fiyatta kalirsa 24 saat icinde tekrar bildirim gondermez.
- Ayni urun daha dusuk fiyata inerse 24 saati beklemeden yeniden bildirim gonderir.
- Arama takibinde hata olursa Pushover ile hangi aramada hata oldugunu bildirir.
- Amazon gecici `429/5xx` hatalarinda bekleyip tekrar dener.
- Arama sayfalarinda Amazon korumasi devam ederse 45 dakika soguma uygular.
- Log satirlarini yerel saatle yazar.

## Örnek Yapılandırma

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
    notify_once: true
search_targets:
  - name: "iPad Air 13 M4"
    product_name: "ipad air 13"
    target_price: 35000
  - name: "iPad Pro 13 256"
    product_name: "ipad pro 13 256"
    target_price: 60000
```

Birden fazla arama sayfasi kullaniyorsan `search_name` yaz:

```yaml
search_pages:
  - name: "ipad ikinci el"
    search_url: "https://www.amazon.com.tr/s?k=ipad&i=warehouse-deals"
    search_url_2: "https://www.amazon.com.tr/s?k=ipad&rh=p_n_condition-type%3A13818537031&dc&rnid=13818535031"
    max_items_to_scan: 40
    notify_once: true
  - name: "mac ikinci el"
    search_url: "https://www.amazon.com.tr/s?k=macbook&i=warehouse-deals"
    max_items_to_scan: 40
    notify_once: true
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

## UI Üzerinden Nasıl Girilir?

1. `search_pages` bolumunde `Add` de.
2. `name` alanina bu arama sayfasinin kisa adini yaz. Ornek: `ipad ikinci el`.
3. `search_url` alanina Amazon Depo veya ana arama linkini yapistir.
4. `search_url_2` alanina istersen ikinci arama linkini yapistir. Ornek: Amazon sol menuden `Ikinci El` secince olusan link.
5. `max_items_to_scan` icin ornek `40` yaz. Bu deger her link icin ayri ayri uygulanir.
6. `notify_once` acik kalsin.
7. `search_targets` bolumunde her urun hedefi icin `Add` de.
8. `name` alanina hedefin kisa adini yaz. Ornek: `iPad Air 13 M4`.
9. Sadece tek arama sayfan varsa `search_name` alanini bos birakabilirsin.
10. Birden fazla arama sayfan varsa `search_name` alanina ilgili `search_pages.name` degerini aynen yaz.
11. `product_name` alanina Amazon sonuc basliginda aranacak metni yaz. Ornek: `ipad air 13`.
12. `target_price` alanina hedef fiyati yaz.

## Alanlar

`search_pages` alanlari:

- `name`: Bu arama sayfasinin kisa adi.
- `search_url`: Amazon'da filtreledigin ana arama veya kategori linki.
- `search_url_2`: Istege bagli ikinci arama linki. Ayni hedefler bu linkte de aranir.
- `max_items_to_scan`: Her arama linkinde ilk kac urun kartinin taranacagi.
- `notify_once`: `true` ise ayni hedef urun ayni veya daha yuksek fiyatta 24 saat icinde tekrar bildirilmez; daha dusuk fiyat yakalanirsa sure beklemeden bildirilir.

`search_targets` alanlari:

- `name`: Bu hedefin kisa adi. Bildirimlerde gorunur.
- `search_name`: Hangi arama sayfasinda aranacagi. Tek arama sayfasi varsa bos olabilir.
- `product_name`: Amazon sonuc basliginda aranacak metin.
- `target_price`: Bu fiyat ve altindaki eslesmeler icin bildirim.

## Arama Hata Bildirimleri

Arama takiplerinden biri hata verirse bot Pushover'a `Amazon arama hatasi` baslikli ayri bir bildirim yollar. Ayni arama ve ayni hata tekrar ederse bildirim yaklasik 6 saatte bir gonderilir.

Bir `search_pages` kaydinda iki link varsa ve linklerden biri gecici hata verirken digeri okunabiliyorsa bot calismaya devam eder, basarili linkten gelen urunleri kontrol eder ve loga kismi hata yazar.

## 503 ve Amazon Koruması

Amazon bazen ozellikle arama sayfalarinda `503 Service Unavailable` dondurur. Bot once kisa beklemelerle tekrar dener, yine basarisiz olursa o arama kaydini yaklasik 45 dakika sogumaya alir.

## Notlar

- Amazon zaman zaman bot korumasi, bolgesel farkliliklar veya HTML degisiklikleri uygulayabilir.
- Cok sik sorgu atmak yerine `15-60 dakika` araligi mantiklidir.
- Pushover anahtarlari ve gercek takip listesi GitHub'a konmamalidir.
