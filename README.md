# Amazon.com.tr Fiyat Takibi

Bu Home Assistant add-on'u `amazon.com.tr` urun sayfalarini ve filtreli arama sonuc sayfalarini belirli araliklarla kontrol eder. Hedef fiyat yakalaninca Pushover bildirimi gonderir.

Ana hedef ortam `Home Assistant OS` yuklu Raspberry Pi'dir. Kodlar GitHub'da saklanir ve Home Assistant'a add-on repository olarak eklenerek guncellenir.

## Guncel Surum

```txt
1.2.0
```

Bu surum kod temizligi ve sadeleştirme surumudur. Eski `notify_once` gecis katmani, `run.sh` icindeki config donusturme kodu ve eski `notified_items` bildirim bastirma listesi kaldirildi. Artik tek gecerli alan `notify_once_in_24H`.

Ilk calistirmada eski arama bildirimi susturma kayitlari bir defaya mahsus sifirlanir. Bu nedenle daha once susturulmus uygun firsatlar yeniden bildirim gonderebilir.

## Ne Yapar?

- Dogrudan Amazon urun linklerini takip eder.
- Filtreli Amazon arama sayfalarindaki urun kartlarini takip eder.
- Tek search page altinda iki farkli arama linkini birlikte tarayabilir.
- Ayni urun iki linkte de cikarsa tekillestirir ve en dusuk fiyati kullanir.
- `Diger satin alma secenekleri` altindaki ikinci el teklif fiyatini okuyabilir.
- Arama sonuc sayfasinin altindaki onerilen/alternatif urun bloklarini yok sayar.
- Ayni urun ayni fiyatta kalirsa 24 saat icinde tekrar bildirim gondermez.
- Ayni urun daha dusuk fiyata inerse 24 saati beklemeden yeniden bildirim gonderir.
- Arama hatalarinda Pushover ile uyari gonderir.
- Amazon gecici `429/5xx` hatalarinda tekrar dener ve gerekirse soguma uygular.
- Loglari yerel saatle yazar ve her turun sonunda sonraki kontrol zamanini gosterir.

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
- `product_name`: Amazon sonuc basliginda aranacak metin.
- `target_price`: Bu fiyat ve altindaki eslesmeler icin bildirim gonderilir.

## Notlar

- Amazon zaman zaman bot korumasi, bolgesel farkliliklar veya HTML degisiklikleri uygulayabilir.
- Cok sik sorgu atmak yerine `15-60 dakika` araligi mantiklidir.
- Pushover anahtarlari ve gercek takip listesi GitHub'a konmamalidir.
