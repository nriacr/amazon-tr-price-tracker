# Amazon.com.tr Fiyat Takibi

Bu proje, `amazon.com.tr` urun sayfalarini veya filtreli arama sonuc sayfalarini belirli araliklarla kontrol edip hedef fiyatin altina inildiginde `Pushover` uzerinden bildirim gonderen kucuk bir bottur.

Ana hedef ortam `Home Assistant OS` yüklü Raspberry Pi'dir. Bu nedenle çözüm, Home Assistant'ta `local add-on` olarak çalıştırılabilecek şekilde paketlendi.

## Ne yapıyor?

- Amazon Turkiye urun sayfasini duzenli araliklarla indirir
- Filtreli arama sonuc sayfasindaki urun kartlarini tarayabilir
- Sayfadan urun adi ve fiyat cikarmaya calisir
- Fiyat hedef degerin altina inerse Pushover bildirimi yollar
- Ayni fiyat icin gereksiz tekrar bildirimini engeller
- Durumu `/data/state.json` icinde saklar

## Klasörler

- `ha-addon/`: Home Assistant add-on dosyaları

## Home Assistant OS Kurulumu

1. `ha-addon` klasörünün içeriğini Raspberry Pi üzerinde `/addons/local/amazon_tr_price_tracker` altına kopyala.
2. Home Assistant'ı yeniden başlat veya `Settings > Add-ons` ekranını yenile.
3. Add-on store içinde `Amazon TR Price Tracker` add-on'unu aç.
4. Yapılandırmayı aşağıdaki örneğe benzer şekilde gir.
5. Add-on'u başlat.

Alternatif olarak bu projeyi GitHub'a koyup ayrı bir add-on repository olarak da yayınlayabilirsin; ilk sürüm için buna gerek yok.

## Örnek Yapılandırma

```yaml
interval_minutes: 30
request_timeout_seconds: 20
pushover_user_key: "PUSHOVER_USER_KEY"
pushover_api_token: "PUSHOVER_APP_TOKEN"
products:
  - url: "https://www.amazon.com.tr/dp/B0XXXXXXXX"
    target_price: 24999.90
    name: "iPhone 16"
  - url: "https://www.amazon.com.tr/dp/B0YYYYYYYY"
    target_price: 1299
    name: "Kulaklık"
search_watches:
  - search_url: "https://www.amazon.com.tr/s?..."
    product_name: "ipad air 128"
    target_price: 22000
    name: "iPad arama takibi"
    max_items_to_scan: 24
```

`search_watches` modu su sekilde calisir:

- `search_url`: Amazon'da filtreledigin arama veya kategori linki
- `product_name`: Sonuclarda aranacak metin
- `target_price`: Bu fiyat ve altindaki eslesmeler icin bildirim
- `name`: Istege bagli, bildirimde gorunecek kisa ad
- `max_items_to_scan`: Ilk kac urun kartinin taranacagi

## Notlar

- Amazon zaman zaman bot korumasi, bolgesel farkliliklar veya HTML degisiklikleri uygulayabilir. Bu durumda secicileri guncellemek gerekebilir.
- Cok sik sorgu atmak yerine `15-60 dakika` araligi mantiklidir.
- Arama sonucu takibinde urun karti HTML'i degisirse secicilerde guncelleme gerekebilir.

## Yerel Test

Add-on içindeki Python dosyasını sözdizimi açısından test etmek için:

```bash
python3 -m py_compile ha-addon/app/main.py
```
