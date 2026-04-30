# Amazon.com.tr Fiyat Takibi

Bu proje, `amazon.com.tr` urun sayfalarini veya filtreli arama sonuc sayfalarini belirli araliklarla kontrol edip hedef fiyatin altina inildiginde `Pushover` uzerinden bildirim gonderen Home Assistant add-on'udur.

Ana hedef ortam `Home Assistant OS` yuklu Raspberry Pi'dir. Kodlar GitHub'da saklanir ve Home Assistant'a add-on repository olarak eklenerek guncellenebilir.

## Guncel Surum

```txt
0.2.0
```

Bu surumde `search_watches` yapisi bastan kurgulandi. Artik tek bir arama linki altinda birden fazla urun hedefi takip edilebilir. Eski `search_watches` kayitlari bu surumde yeniden yeni formata gore girilmelidir.

## Ne yapıyor?

- Amazon Turkiye urun sayfasini duzenli araliklarla indirir.
- Filtreli arama sonuc sayfasindaki urun kartlarini tarayabilir.
- Tek bir arama sayfasinda birden fazla urun hedefi ve hedef fiyat kontrol edebilir.
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
search_watches:
  - name: "iPad ikinci el arama"
    search_url: "https://www.amazon.com.tr/s?k=ipad&i=warehouse-deals"
    max_items_to_scan: 40
    notify_once: true
    targets:
      - name: "iPad Air 13 M4"
        product_name: "ipad air 13"
        target_price: 35000
      - name: "iPad Pro 13 M5 256"
        product_name: "ipad pro 13 256"
        target_price: 60000
      - name: "iPad mini"
        product_name: "ipad mini"
        target_price: 20000
```

`search_watches` modu su sekilde calisir:

- `name`: Bu arama sayfasinin kisa adi. Configuration ekraninda bu isimle ayirt edilir.
- `search_url`: Amazon'da filtreledigin arama veya kategori linki.
- `max_items_to_scan`: O arama sayfasinda ilk kac urun kartinin taranacagi.
- `notify_once`: `true` ise ayni hedef urun bir kez bildirildikten sonra tekrar bildirilmez.
- `targets`: Ayni arama linki icinde takip edilecek urun hedefleri.

`targets` icindeki alanlar:

- `name`: Bu hedefin kisa adi. Bildirimlerde gorunur.
- `product_name`: Amazon sonuc basliginda aranacak metin.
- `target_price`: Bu fiyat ve altindaki eslesmeler icin bildirim.

Bu yeni yapida ayni Amazon arama linkini her urun icin tekrar yazmana gerek yoktur. Bir kere arama linkini girersin, altina istedigin kadar urun hedefi eklersin.

Arama modu varsayilan olarak `notify_once: true` calisir. Ayni hedef altinda ayni urun bir kez bildirildikten sonra kalici `notified_items` listesine eklenir; indirim devam ettigi surece her kontrolde tekrar bildirim gonderilmez. Fiyat daha da dustugunde de bildirim almak istersen ilgili arama kaydinda `notify_once: false` yapabilirsin.

## Arama Hata Bildirimleri

Arama takiplerinden biri hata verirse bot Pushover'a `Amazon arama hatasi` baslikli ayri bir bildirim yollar.

Bildirimde sunlar bulunur:

- Hangi arama kaydinda hata oldugu
- O arama altindaki hedeflerin adlari
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
