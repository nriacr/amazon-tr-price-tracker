# Amazon.com.tr Fiyat Takibi

Bu proje, `amazon.com.tr` urun sayfalarini veya filtreli arama sonuc sayfalarini belirli araliklarla kontrol edip hedef fiyatin altina inildiginde `Pushover` uzerinden bildirim gonderen Home Assistant add-on'udur.

Ana hedef ortam `Home Assistant OS` yuklu Raspberry Pi'dir. Kodlar GitHub'da saklanir ve Home Assistant'a add-on repository olarak eklenerek guncellenebilir.

## Guncel Surum

```txt
0.2.3
```

Bu surumde `search_targets` alan sirasi daha okunur hale getirildi: once hedefin kendi `name` alani, sonra gerekirse baglanacagi `search_name` gelir.

## Ne yapıyor?

- Amazon Turkiye urun sayfasini duzenli araliklarla indirir.
- Filtreli arama sonuc sayfasindaki urun kartlarini tarayabilir.
- Tek bir arama sayfasinda birden fazla urun hedefi ve hedef fiyat kontrol edebilir.
- Fiyat hedef degerin altina inerse Pushover bildirimi yollar.
- Ayni fiyat icin gereksiz tekrar bildirimini engeller.
- Arama takibinde hata olursa Pushover ile hangi aramada hata oldugunu bildirir.
- Amazon gecici `429/5xx` hatalarinda bekleyip tekrar dener.
- Arama sayfalarinda Amazon korumasi devam ederse 45 dakika soguma uygular.
- Log satirlarini yerel saatle yazar.

## Örnek Yapılandırma

Tek arama sayfasi kullaniyorsan `search_name` bos kalabilir:

```yaml
interval_minutes: 30
request_timeout_seconds: 20
pushover_user_key: "PUSHOVER_USER_KEY"
pushover_api_token: "PUSHOVER_APP_TOKEN"
products: []
search_pages:
  - name: "ipad ikinci el"
    search_url: "https://www.amazon.com.tr/s?k=ipad&i=warehouse-deals"
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
3. `search_url` alanina Amazon arama linkini yapistir.
4. `max_items_to_scan` icin ornek `40` yaz.
5. `notify_once` acik kalsin.
6. `search_targets` bolumunde her urun hedefi icin `Add` de.
7. `name` alanina hedefin kisa adini yaz. Ornek: `iPad Air 13 M4`.
8. Sadece tek arama sayfan varsa `search_name` alanini bos birakabilirsin.
9. Birden fazla arama sayfan varsa `search_name` alanina ilgili `search_pages.name` degerini aynen yaz.
10. `product_name` alanina Amazon sonuc basliginda aranacak metni yaz. Ornek: `ipad air 13`.
11. `target_price` alanina hedef fiyati yaz.

## Alanlar

`search_pages` alanlari:

- `name`: Bu arama sayfasinin kisa adi.
- `search_url`: Amazon'da filtreledigin arama veya kategori linki.
- `max_items_to_scan`: O arama sayfasinda ilk kac urun kartinin taranacagi.
- `notify_once`: `true` ise ayni hedef urun bir kez bildirildikten sonra tekrar bildirilmez.

`search_targets` alanlari:

- `name`: Bu hedefin kisa adi. Bildirimlerde gorunur.
- `search_name`: Hangi arama sayfasinda aranacagi. Tek arama sayfasi varsa bos olabilir.
- `product_name`: Amazon sonuc basliginda aranacak metin.
- `target_price`: Bu fiyat ve altindaki eslesmeler icin bildirim.

## Arama Hata Bildirimleri

Arama takiplerinden biri hata verirse bot Pushover'a `Amazon arama hatasi` baslikli ayri bir bildirim yollar. Ayni arama ve ayni hata tekrar ederse bildirim yaklasik 6 saatte bir gonderilir.

## 503 ve Amazon Koruması

Amazon bazen ozellikle arama sayfalarinda `503 Service Unavailable` dondurur. Bot once kisa beklemelerle tekrar dener, yine basarisiz olursa o arama kaydini yaklasik 45 dakika sogumaya alir.

## Notlar

- Amazon zaman zaman bot korumasi, bolgesel farkliliklar veya HTML degisiklikleri uygulayabilir.
- Cok sik sorgu atmak yerine `15-60 dakika` araligi mantiklidir.
- Pushover anahtarlari ve gercek takip listesi GitHub'a konmamalidir.
