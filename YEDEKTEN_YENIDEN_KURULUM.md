# Amazon TR Price Tracker - Yedekten Yeniden Kurulum Rehberi

Bu rehber, Home Assistant bozulursa veya yeni bir cihaza temiz Home Assistant kurman gerekirse Amazon fiyat takip botunu tekrar ayağa kaldırmak içindir.

## Yedeklenmesi Gerekenler

Mutlaka saklanacak klasör:

```txt
/addons/local/amazon_tr_price_tracker
```

Bu klasörün içinde şunlar olmalı:

```txt
config.yaml
Dockerfile
run.sh
app/requirements.txt
app/main.py
```

Mutlaka ayrıca saklanacak ayar:

```txt
Amazon TR Price Tracker add-on Configuration içeriği
```

Bu ayarın içinde Pushover anahtarları, takip edilen ürün linkleri, arama linkleri, keyword değerleri ve hedef fiyatlar bulunur.

Not: Arama takibi, Amazon'un her kontrolde degisebilen arama sonuc linklerini sabit urun linkine cevirir. Bu sayede ayni urun hedef fiyat altinda kaldigi surece her kontrolde tekrar bildirim gondermez; fiyat daha da duserse tekrar bildirir.

## Önerilen Yedek Paketi

Bir klasör oluşturup içine şunları koy:

```txt
amazon-tr-price-tracker-backup/
  ha-addon/
    config.yaml
    Dockerfile
    run.sh
    app/
      requirements.txt
      main.py
  configuration-backup.yaml
  YEDEKTEN_YENIDEN_KURULUM.md
```

`configuration-backup.yaml`, Home Assistant add-on Configuration sekmesindeki ayarların kopyasıdır. Bu dosyada gizli Pushover bilgileri olacağı için güvenli bir yerde sakla.

## Örnek Configuration Yedeği

Aşağıdaki yapı örnektir. Kendi Pushover bilgilerini ve takiplerini bunun yerine koymalısın.

```yaml
interval_minutes: 30
request_timeout_seconds: 20
pushover_user_key: "PUSHOVER_USER_KEY"
pushover_api_token: "PUSHOVER_API_TOKEN"

products:
  - name: "Tek urun takibi"
    url: "https://www.amazon.com.tr/dp/B0XXXXXXXX"
    target_price: 25000

search_watches:
  - name: "iPad Air 13 arama takibi"
    search_url: "https://www.amazon.com.tr/s?..."
    product_name: "ipad air 13"
    target_price: 35000
    max_items_to_scan: 24
```

Sadece arama modu kullanıyorsan:

```yaml
interval_minutes: 30
request_timeout_seconds: 20
pushover_user_key: "PUSHOVER_USER_KEY"
pushover_api_token: "PUSHOVER_API_TOKEN"

products: []

search_watches:
  - name: "iPad Air 13 arama takibi"
    search_url: "https://www.amazon.com.tr/s?..."
    product_name: "ipad air 13"
    target_price: 35000
    max_items_to_scan: 24
```

## Yeni Home Assistant'a Geri Kurulum

En kolay yol, GitHub reposunu Home Assistant add-on repository olarak eklemektir.

GitHub repo:

```txt
https://github.com/nriacr/amazon-tr-price-tracker
```

Not: Home Assistant'ın add-on repository alanı private GitHub repolarını her zaman doğrudan okuyamaz. En kolay yöntem için bu repoyu public yapmak yeterlidir, çünkü bu repoda Pushover anahtarları ve gerçek takip listen yoktur. Repo private kalacaksa aşağıdaki "Private Repo Kalacaksa" bölümünü kullan.

## GitHub Uzerinden Kolay Kurulum

1. Yeni Home Assistant OS kurulumunu tamamla.
2. Home Assistant arayüzünde `Settings > Add-ons > Add-on Store` ekranını aç.
3. Sağ üstteki üç nokta menüsünden `Repositories` bölümünü aç.
4. Şu repo adresini ekle:

```txt
https://github.com/nriacr/amazon-tr-price-tracker
```

5. `Add` veya `Save` ile kaydet.
6. Add-on Store ekranını yenile.
7. `Amazon TR Price Tracker` add-on'unu bul.
8. `Install` yap.
9. `Configuration` sekmesine güvenli yerde sakladığın configuration yedeğini yapıştır.
10. `Save` yap.
11. `Start` yap.
12. `Log` sekmesinde şu satırı gör:

```txt
Servis basladi. Kontrol araligi: 30 dakika
```

Bu yöntem için repoda şu dosyalar bulunmalıdır:

```txt
repository.yaml
ha-addon/config.yaml
ha-addon/Dockerfile
ha-addon/run.sh
ha-addon/app/requirements.txt
ha-addon/app/main.py
```

## Private Repo Kalacaksa

Repo private kalırsa Home Assistant add-on store'a URL eklemek başarısız olabilir. Bu durumda güvenli yöntem:

1. GitHub'a giriş yap.
2. `https://github.com/nriacr/amazon-tr-price-tracker` reposunu aç.
3. `Code > Download ZIP` ile dosyaları indir.
4. ZIP içindeki `ha-addon` klasörünü Home Assistant'ta şu konuma koy:

```txt
/addons/local/amazon_tr_price_tracker
```

5. Home Assistant'ı yeniden başlat veya Add-on Store ekranını yenile.
6. `Amazon TR Price Tracker` add-on'unu kur.
7. Configuration yedeğini yapıştır.
8. `Start` yap.

## Manuel Geri Kurulum

1. Yeni Home Assistant OS kurulumunu tamamla.
2. `Settings > Add-ons` bölümünden terminal/SSH eklentisi kur.
3. Terminali aç.
4. Add-on klasörünü oluştur:

```sh
mkdir -p /addons/local/amazon_tr_price_tracker/app
```

5. Yedekteki dosyaları aynı konuma geri koy:

```txt
/addons/local/amazon_tr_price_tracker/config.yaml
/addons/local/amazon_tr_price_tracker/Dockerfile
/addons/local/amazon_tr_price_tracker/run.sh
/addons/local/amazon_tr_price_tracker/app/requirements.txt
/addons/local/amazon_tr_price_tracker/app/main.py
```

6. Home Assistant arayüzünde `Settings > Add-ons` ekranına dön.
7. Sayfayı yenile veya Home Assistant'ı yeniden başlat.
8. `Amazon TR Price Tracker` add-on'unu bul.
9. `Install` yap.
10. `Configuration` sekmesine yedeklediğin `configuration-backup.yaml` içeriğini yapıştır.
11. `Save` yap.
12. `Start` yap.
13. `Log` sekmesinde şu satırı gör:

```txt
Servis basladi. Kontrol araligi: 30 dakika
```

## Çalıştığını Test Etme

Arama modu için test:

1. `target_price` değerini geçici olarak çok yüksek yap.
2. Örnek:

```yaml
target_price: 999999
```

3. `Save` yap.
4. Add-on'u `Restart` et.
5. Pushover bildirimi gelirse sistem çalışıyor demektir.
6. Test bitince gerçek hedef fiyatı geri yaz.

## Log Saati Notu

Bu sürümde log satırları yerel saatle yazılır.

Örnek:

```txt
[2026-04-27T12:30:00+03:00] Servis basladi.
```

Eğer loglar 3 saat geriden görünürse `main.py` içinde şu satır kontrol edilmeli:

```python
now = datetime.now().astimezone().isoformat()
```

## Sorun Giderme

Add-on görünmüyorsa:

```sh
ls -la /addons/local/amazon_tr_price_tracker
```

`config.yaml` dosyasının bu klasörde olduğundan emin ol.

Yeni alanlar Configuration ekranında görünmüyorsa:

1. Add-on'u `Uninstall` yap.
2. Tekrar `Install` yap.
3. Configuration ekranını tekrar aç.

Kod değiştiği halde davranış değişmiyorsa:

1. Add-on'u `Stop` yap.
2. `Uninstall` yap.
3. Tekrar `Install` yap.
4. Configuration yedeğini tekrar yapıştır.
5. `Start` yap.

Arama sayfası okunamıyorsa logda şuna benzer hata çıkar:

```txt
Arama sonuc sayfasinda okunabilir urun bulunamadi.
```

Bu durumda Amazon sayfa yapısını değiştirmiş olabilir veya bot koruması farklı içerik döndürüyor olabilir. Aynı filtre linkini tarayıcıda açıp hala ürün görünüp görünmediğini kontrol et.

## Güvenlik Notu

`configuration-backup.yaml` içinde Pushover `user_key` ve `api_token` bulunur. Bu dosyayı herkese açık GitHub deposuna koyma.
