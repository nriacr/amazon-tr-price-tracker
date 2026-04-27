# Amazon.com.tr Fiyat Takibi

Bu proje, `amazon.com.tr` urun sayfalarini veya filtreli arama sonuc sayfalarini belirli araliklarla kontrol edip hedef fiyatin altina inildiginde `Pushover` uzerinden bildirim gonderen Home Assistant add-on'udur.

Ana hedef ortam `Home Assistant OS` yuklu Raspberry Pi'dir. Kodlar GitHub'da saklanabilir, Home Assistant'a add-on repository olarak eklenebilir veya local add-on olarak kurulabilir.

## Ne yapıyor?

- Amazon Turkiye urun sayfasini duzenli araliklarla indirir
- Filtreli arama sonuc sayfasindaki urun kartlarini tarayabilir
- Sayfadan urun adi ve fiyat cikarmaya calisir
- Fiyat hedef degerin altina inerse Pushover bildirimi yollar
- Ayni fiyat icin gereksiz tekrar bildirimini engeller
- Log satirlarini yerel saatle yazar
- Durumu `/data/state.json` icinde saklar

## Klasörler

- `ha-addon/`: Home Assistant add-on dosyaları
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
  - name: "Kulaklık"
    url: "https://www.amazon.com.tr/dp/B0YYYYYYYY"
    target_price: 1299
search_watches:
  - name: "iPad arama takibi"
    search_url: "https://www.amazon.com.tr/s?..."
    product_name: "ipad air 128"
    target_price: 22000
    max_items_to_scan: 24
```

`search_watches` modu su sekilde calisir:

- `search_url`: Amazon'da filtreledigin arama veya kategori linki
- `product_name`: Sonuclarda aranacak metin
- `target_price`: Bu fiyat ve altindaki eslesmeler icin bildirim
- `name`: Configuration ekraninda liste satirlarini ayirt etmek icin zorunlu kisa ad
- `max_items_to_scan`: Ilk kac urun kartinin taranacagi

Home Assistant Configuration ekraninda liste satirlarini daha kolay ayirt etmek icin `name` alani zorunludur ve her urun/arama kaydinda en uste yazilmalidir.

## Notlar

- Amazon zaman zaman bot korumasi, bolgesel farkliliklar veya HTML degisiklikleri uygulayabilir. Bu durumda secicileri guncellemek gerekebilir.
- Cok sik sorgu atmak yerine `15-60 dakika` araligi mantiklidir.
- Arama sonucu takibinde urun karti HTML'i degisirse secicilerde guncelleme gerekebilir.
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

Add-on içindeki Python dosyasını sözdizimi açısından test etmek için:

```bash
python3 -m py_compile ha-addon/app/main.py
```
