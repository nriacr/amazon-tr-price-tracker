# Amazon.com.tr Fiyat Takibi

Bu proje, `amazon.com.tr` urun sayfalarini veya filtreli arama sonuc sayfalarini belirli araliklarla kontrol edip hedef fiyatin altina inildiginde `Pushover` uzerinden bildirim gonderen Home Assistant add-on'udur.

Ana hedef ortam `Home Assistant OS` yuklu Raspberry Pi'dir. Kodlar GitHub'da saklanir ve Home Assistant'a add-on repository olarak eklenerek guncellenebilir.

## Guncel Surum

```txt
0.1.9
```

Bu surumde arama takiplerinde hata olursa Pushover uzerinden ayrica haber verilir. Ayni arama ve ayni hata surekli tekrar ederse telefonunu bildirimle doldurmamak icin ayni hata yaklasik 6 saatte bir bildirilir.

## Ne yapıyor?

- Amazon Turkiye urun sayfasini duzenli araliklarla indirir.
- Filtreli arama sonuc sayfasindaki urun kartlarini tarayabilir.
- Sayfadan urun adi ve fiyat cikarmaya calisir.
- Fiyat hedef degerin altina inerse Pushover bildirimi yollar.
- Ayni fiyat icin gereksiz tekrar bildirimini engeller.
- Arama sonucunda bildirilen urunleri kalici olarak hatirlayip tekrar bildirmez.
- Arama takibinde hata olursa Pushover ile hangi aramada hata oldugunu bildirir.
- Amazon gecici `429/5xx` hatalarinda bekleyip tekrar dener.
- Arama sayfalarinda Amazon korumasi devam ederse 45 dakika soguma uygular.
- Log satirlarini yerel saatle yazar.
- Durumu `/data/state.json` icinde saklar.

## Klasörler

- `ha-addon/`: Home Assistant add-on dosyalari
- `YEDEKTEN_YENIDEN_KURULUM.md`: Yedekten yeniden kurulum rehberi
- `repository.yaml`: Home Assistant add-on repository metadata dosyasi

## GitHub Uzerinden Kolay Kurulum

Home Assistant'in add-on repository alanina su repo adresi eklenir:

```txt
https://github.com/nriacr/amazon-tr-price-tracker
```

Adimlar:

1. Home Assistant'ta `Settings > Add-ons > Add-on Store` ekranini ac.
2. Sag ustteki uc nokta menusunden `Repositories` bolumunu ac.
3. Repo adresini ekle.
4. Add-on Store ekranini yenile.
5. `Amazon TR Price Tracker` add-on'unu bul.
6. `Install` yap.
7. `Configuration` sekmesine kendi ayarlarini yapistir.
8. `Save` ve sonra `Start` yap.

Not: Repo private ise Home Assistant repo URL'sini dogrudan okuyamayabilir. Bu durumda `Code > Download ZIP` ile indirip `ha-addon` klasorunu Home Assistant'ta `/addons/local/amazon_tr_price_tracker` konumuna koymak gerekir. Detayli anlatim icin `YEDEKTEN_YENIDEN_KURULUM.md` dosyasina bak.

## Örnek Yapılandırma

```yaml
interval_minutes: 30
request_timeout_seconds: 20
pushover_user_key: "PUSHOVER_USER_KEY"
pushover_api_token: "PUSHOVER_APP_TOKEN"
products:
  - name: "iPhone 16"
    url: "https://www.amazon.com.tr/dp/B0XXXXXXXX"
    target_price: 24999.90
  - name: "Kulaklik"
    url: "https://www.amazon.com.tr/dp/B0YYYYYYYY"
    target_price: 1299
search_watches:
  - name: "iPad ikinci el arama"
    search_url: "https://www.amazon.com.tr/s?k=ipad&i=warehouse-deals"
    product_name: "ipad"
    target_price: 22000
    max_items_to_scan: 24
    notify_once: true
```

`search_watches` modu su sekilde calisir:

- `search_url`: Amazon'da filtreledigin arama veya kategori linki.
- `product_name`: Sonuclarda aranacak metin.
- `target_price`: Bu fiyat ve altindaki eslesmeler icin bildirim.
- `name`: Configuration ekraninda ve bildirimlerde gorunecek kisa ad.
- `max_items_to_scan`: Ilk kac urun kartinin taranacagi.
- `notify_once`: `true` ise ayni urun bir kez bildirildikten sonra tekrar bildirilmez.

Home Assistant Configuration ekraninda liste satirlarini daha kolay ayirt etmek icin `name` alani zorunludur ve her urun/arama kaydinda en uste yazilmalidir.

Arama modu varsayilan olarak `notify_once: true` calisir. Ayni urun hedef fiyat altinda bir kez bildirildikten sonra kalici `notified_items` listesine eklenir; indirim devam ettigi surece her 15 dakikada tekrar bildirim gonderilmez. Fiyat daha da dustugunde de bildirim almak istersen ilgili arama kaydinda `notify_once: false` yapabilirsin.

## Arama Hata Bildirimleri

Arama takiplerinden biri hata verirse bot Pushover'a `Amazon arama hatasi` baslikli ayri bir bildirim yollar.

Bildirimde sunlar bulunur:

- Hangi arama kaydinda hata oldugu
- `product_name` filtresi
- Hata mesaji
- Sorunlu arama linki

Ayni arama ve ayni hata tekrar ederse bildirim yaklasik 6 saatte bir gonderilir. Hata degisirse yeni hata tekrar bildirilir. Bu sayede link bozuldugunda veya Amazon sayfa yapisi degistiginde haberin olur, ama telefonun her kontrol turunda ayni hatayla dolmaz.

## 503 ve Amazon Koruması

Amazon bazen ozellikle arama sayfalarinda `503 Service Unavailable` dondurur. Bu genelde link formatinin bozuk oldugu anlamina gelmez; Amazon o anda otomatik istegi kabul etmiyor demektir.

Botun davranisi:

- Once arama isteginden once rastgele kisa bir bekleme yapar.
- Amazon `503/429/5xx` dondururse `10`, `30`, `75` saniye bekleyerek tekrar dener.
- Yine basarisiz olursa o arama kaydini yaklasik 45 dakika sogumaya alir.
- Soguma sirasinda logda `Arama gecici olarak atlandi` satiri gorunur.
- Soguma bitince otomatik yeniden dener.

Bu davranis Amazon'u daha az zorlamak ve ayni hatanin logu surekli doldurmasini engellemek icindir.

## Notlar

- Amazon zaman zaman bot korumasi, bolgesel farkliliklar veya HTML degisiklikleri uygulayabilir.
- Cok sik sorgu atmak yerine `15-60 dakika` araligi mantiklidir.
- Amazon uzun sure `503` dondururse linki tarayicida acip calisip calismadigini kontrol et.
- Pushover anahtarlari ve gercek takip listesi GitHub'a konmamalidir.

## Yedekten Yeniden Kurulum

Yeniden kurulum icin ana rehber:

```txt
YEDEKTEN_YENIDEN_KURULUM.md
```

Yedek stratejisi:

- Kodlar GitHub reposunda tutulur.
- Pushover anahtarlari ve gercek takip listesi ayri, guvenli bir `configuration-backup.yaml` dosyasinda saklanir.
- Yeni Home Assistant kurulumunda once add-on GitHub'dan kurulur, sonra configuration yedegi yapistirilir.

## Yerel Test

Add-on icindeki Python dosyasini sozdizimi acisindan test etmek icin:

```bash
python3 -m py_compile ha-addon/app/main.py
```
