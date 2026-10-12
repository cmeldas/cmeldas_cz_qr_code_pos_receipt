# QR kód platby na účtence pokladny (`cmeldas_cz_qr_code_pos_receipt`)

Doplňuje pokladnu (POS) o QR kód platby převodem na účtence. Navazuje na modul
[`cz_qr_payment`](https://github.com/cmeldas/cz_qr_payment), který dodává metodu QR kódu
„QR Platba (CZ)“ (`qr_czk`, formát SPD).

## Co dělá

- **Zpráva pro příjemce**: QR v pokladně nese `Order <pos_reference> <tracking_number>`
  (např. `Order 26A-1-000042 A12`, v QR bez mezer). Jádro posílá `pos_order_id.name`, které
  je u nové objednávky v prohlížeči jen `/`, takže by v QR číslo objednávky chybělo.
  Podle zprávy páruje platby modul `fio_qr_payment_validation`.
- **QR na účtence**: obrázek QR z popupu se uloží k platbě (`pos.payment.qr_code`) a tiskne se
  na účtenku pod platbami, i při opakovaném tisku.
- **Záloha na serveru**: platba QR metodou, která QR z pokladny nedostala, ho dostane při uložení.

Jeden dotaz na server pro popup i účtenku (`pos.payment.method.get_qr_code_image`).

## Odoo 20

Port z větve `19.0`, verze `20.0.1.1.0`. Pro obsluhu se nic nemění: popup, zpráva i QR na účtence
jsou stejné jako v 19.

Co se změnilo v Odoo 20 a v modulu:

- **Účtenka** už není OWL šablona `point_of_sale.OrderReceipt`, ale šablona QWeb
  `point_of_sale.pos_order_receipt` (`ir.ui.view`), kterou vykresluje server i pokladna
  (převod `registerPythonTemplate`). Rozšíření je proto v `receipt/pos_order_receipt.xml`
  v `data` manifestu (ne v assets), data jsou slovníky (`payment.get('qr_code')`).
  QR je na stejném místě (před `before-footer`), šířka 75 % účtenky (účtenka má v 20 šířku 512 px).
- **Pole `pos.payment.qr_code`** má od 20 přímo `point_of_sale` (stejný sloupec), modul ho už
  nedefinuje. Jádro ho po zavření popupu maže; tento modul ho nechává kvůli účtence.
- **`showQR`**: Odoo 20 volá `get_qr_code_value` (surová hodnota SPD) a obrázek kreslí v prohlížeči
  jako SVG (přes 24 kB i u QR bez částky). Modul dál bere od serveru PNG (`get_qr_code_image`, stejné jako
  `get_qr_code` v 19, ~10 kB) se stejným řetězcem SPD. Popup dostává props jádra 20
  (`payment.getQrPopupProps()`), stav platby se nastavuje jako v jádře (`waiting`), takže funguje
  tlačítko „Show QR Code“ i zákaznický displej. Bez spojení se použije `default_qr` (v 20 surová
  hodnota) a obrázek vykreslí prohlížeč.
- Typ integrace platební metody `qr_code` je v 20 `bank_qr_code`.
- Práva: `security/ir.model.access.csv` → `security/ir.access.csv` (model `ir.access`, sloupec
  `operation`: uživatel pokladny `cru`, manažer `crud`). Jádro 20 už dává uživateli pokladny na
  `pos.payment` plná práva, takže soubor je jen zachování stavu z 19.
- Autor v manifestu sjednocený na Matouš Čmelík.
- `i18n/cs.po`: český překlad chyby z `get_qr_code_image` (špatně nastavená platební metoda).
  Python překlady se v Odoo 20 hledají podle modulu volajícího kódu, takže překlad stejné věty
  v `point_of_sale` se sem nepropíše.

### Migrace dat 19 → 20

`migrations/20.0.1.1.0/pre-migrate.py` (běží při `-u` z `19.0.1.1.0`, idempotentní):

1. Smaže z `ir_model_data` XML ID práv modulu, která pořád ukazují na `ir.model.access`/`ir.rule`
   (jinak načtení `ir.access.csv` spadne na „found record of different model“); nové záznamy
   `ir.access` vzniknou znovu. Pokud je rámec migrace převedl na `ir.access`, nedělá nic.
2. Převede `pos_payment_method.payment_method_type` z `qr_code` na `bank_qr_code` (na produkci
   metoda „QR“, id 8). Patří to do migrace `point_of_sale`, tady jen pro jistotu.

Uložené QR kódy plateb (`pos_payment.qr_code`, na produkci 2 036 PNG od 2024) převod nepotřebují,
Odoo 20 je čte ze stejného sloupce a stará účtenka je při opakovaném tisku vytiskne.

## Testy

```
odoo -d <db> -i cmeldas_cz_qr_code_pos_receipt --test-enable --test-tags /cmeldas_cz_qr_code_pos_receipt --stop-after-init
```

Testy ověřují obrázek a hodnotu QR, zálohu na serveru, zachování QR z pokladny a vykreslení
účtenky na serveru. Část v prohlížeči (patch `showQR`, šablona účtenky převedená do JS) testy
nepokrývají; 11. 10. 2026 ověřeno v pokladně Odoo 20 (headless Edge přes CDP): popup s PNG z
serveru, stav `waiting` a QR na zákaznickém displeji, po potvrzení QR zůstává u platby, účtenka
v prohlížeči i na serveru má blok „QR kód pro platbu“ se stejným obrázkem, uložená platba má
tentýž QR, offline záloha (`default_qr` → SVG) i nulová částka fungují, bez chyb v konzoli.

## Licence

LGPL-3, autor Matouš Čmelík.
