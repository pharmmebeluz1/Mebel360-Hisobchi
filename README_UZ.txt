MEBEL360° ↔ 2D-PLACE — 4 USTUNLI ENG ISHONCHLI V5

NIMA TUZATILDI
- 2D-PLACE uchun asosiy fayl endi aynan 4 ustun:
  SHIFR<TAB>UZUNLIK<TAB>ENI<TAB>SONI
- Detal shifrida probel, apostrof va maxsus harf bo‘lmaydi.
- Fayl Windows CRLF va oddiy ASCII formatida yaratiladi.
- Har safar topish oson bo‘lgan OXIRGI_KROY_IMPORT.txt fayli yaratiladi.
- TEST_2DPLACE_IMPORT.txt sinov fayli qo‘shildi.
- Mahsulot soni yozilganda detallar, kroy, list, furnitura va narx umumiy songa ko‘payadi.
- 2D va 3D chizmada bir xil shkaflar bitta umumiy maydonda ko‘rsatiladi.

ISHGA TUSHIRISH
1. ZIP faylni to‘liq chiqarib oling.
2. start.bat ni ikki marta bosing.
3. Brauzerda Mebel360 ochiladi.
4. Razmer va “Bir xil mahsulot soni”ni yozib, Hisoblash ni bosing.
5. Kroy bo‘limida birinchi marta “2D-PLACE yo‘lini sozlash” ni bosing.
6. “Kroy TXT tayyorlash” ni bosing.

2D-PLACE ICHIDA FAQAT SHU YO‘L BILAN KIRITING
1. Yuqoridagi “База деталей” menyusini bosing.
2. “Импорт” ustiga boring.
3. “... из файла с разделителями табуляциями” ni bosing.
4. OXIRGI_KROY_IMPORT.txt ni tanlang.
5. Materialni tanlab tasdiqlang.

JUDA MUHIM
TXT faylni “Открыть” tugmasi bilan ochmang.
“Открыть” TXT uchun emas. U bosilsa:
“Ошибка чтения группы деталей! Не найден файл данных”
xatosi chiqadi.

SINOV
Avval “Sinov TXT ochish” tugmasini bosib TEST_2DPLACE_IMPORT.txt ni yuqoridagi Import yo‘li bilan kiriting.
Sinovda 2 qator chiqishi kerak:
TEST_BAKA  1998 x 600  soni 2
TEST_POLKA 568 x 550   soni 6

V6 TUZATISH:
- LXDF orqa panel endi standart holatda bitta butun chiqarilmaydi.
- "LXDF orqa panelni chiqarish" tanlovida "Har bir bo‘limga alohida" standart qilib qo‘yildi.
- Masalan, 3 bo‘limli shkafda 3 ta alohida LXDF detal chiqadi.
- Mahsulot soni 6 bo‘lsa, har bir bo‘lim detali 6 tadan kroyga yuboriladi.
- Zarur bo‘lsa "Bitta butun panel" rejimini tanlash mumkin.

V7 — LXDF ORQA FORMULASI (ZUHRIDDIN AKA TAKLIFI)
- Shkafda LXDF balandligi: umumiy balandlik - sokol.
  Misol: 2200 - 70 = 2130 mm.
- Ichki bo‘lim eni: (umumiy eni - (bo‘lim soni + 1) × 16 mm) ÷ bo‘lim soni.
  Misol: (1900 - 64) ÷ 3 = 612 mm.
- Birinchi va oxirgi LXDF: ichki eni + 22 mm.
  Misol: 612 + 22 = 634 mm — 2 ta.
- O‘rtadagi LXDF: ichki eni + 14 mm.
  Misol: 612 + 14 = 626 mm — 1 ta.
- Natija: 2130 × 634 mm — 2 ta; 2130 × 626 mm — 1 ta.
- Mahsulot soni ko‘paytirilsa, har bir LXDF detalining soni ham shu miqdorga ko‘payadi.


YANGI: Mebel360 AI YORDAMCHI
- Hozirgi hisobni tushuntiradi.
- Ichki bo‘limlarni teng yoki erkin hisoblash rejimiga o‘tkazadi.
- Narx tarkibi, kroy, chiqindi, petla va furnitura bo‘yicha yordam beradi.
- Mijoz va usta rejimlari orasida o‘tkazadi.
- Ushbu versiya internet talab qilmaydigan dastur ichidagi aqlli yordamchi sifatida ishlaydi.

PROFESSIONAL MARKAZ — YANGI VERSIYA
- Buyurtma kodi, mijoz ismi, telefon, muddat, mas'ul xodim, holat va izoh maydonlari qo'shildi.
- Loyihani brauzerning lokal xotirasiga saqlash, qayta ochish, o'chirish, JSON eksport/import qilish mumkin.
- Erkin ichki konstruktor: har bir bo'limning eni, turi, tokcha soni, tortma soni, shapka polka va vishilka sozlamalari alohida beriladi.
- Materiallar katalogi: LMDF, MDF, akril, fanera va LXDF o'lchami/narxi saqlanadi; tanlanganda hisobga qo'llanadi.
- Furnitura katalogi: petla, mexanizm, tutqich, oyoqcha va vishilka narxlari saqlanadi.
- Qoldiq listlar ombori: material, eni, bo'yi, qalinligi va soni bilan qoldiq bo'laklarni saqlash mumkin.
- Detal QR etiketkalari: buyurtma kodi, detal nomi, razmeri, material va kromka ma'lumoti bilan A4 chop etiladi.
- Mijoz uchun taklif: 2D/3D rasm, narx, muddat, loyiha QR va mijoz ma'lumotlari bilan chop/PDF qilinadi.
- Ishlab chiqarish paketi: 2D, 3D, detallar, kroy, teshik xaritasi va umumiy hisob bitta A4 paketda chiqariladi.
- Mebel360 JSON paketi: loyiha ma'lumotlarini asosiy tizimga ulash uchun eksport qiladi.
- Lokal ishlab chiqarish navbati: loyiha "Konstruktor ko'rigida" holati bilan navbatga qo'yiladi.
- AI oddiy gapdan razmerlarni kiritadi. Masalan:
  "Balandligi 2200, uzunasi 1900, chuqurligi 600, o'rtasi vishilka, chap va o'ng 5 ta tokcha".

MUHIM
- Loyihalar, kataloglar va qoldiq ombori shu brauzer/kompyuterning lokal xotirasida saqlanadi.
- Brauzer ma'lumotlari tozalansa, lokal yozuvlar o'chishi mumkin. Vaqti-vaqti bilan JSON eksport qilib zaxira oling.
- Onlayn Mebel360 serveriga avtomatik yuborish uchun keyinchalik server API manzili va foydalanuvchi ruxsati kerak bo'ladi. Ushbu versiyada JSON eksport va lokal navbat ishlaydi.

=== 2026-08-02 YANGI VERSIYA ===
- Yangi ichki tuzilish: "Ikki cheti vishilkali, o‘rtasi polkali".
- Chap va o‘ng vishilka bo‘limi eni alohida kiritiladi, o‘rta polkali bo‘lim avtomatik hisoblanadi.
- O‘rta bo‘lim tokcha soni alohida sozlanadi.
- 2D va 3D chizmada ikkita vishilka va o‘rta tokchalar ko‘rsatiladi.
- Detallar, kromka, vishilka soni, teshik xaritasi va narx qayta hisoblanadi.
- UZ / RU / EN til tanlash tugmasi qo‘shildi.

YANGI — YUQORI/PASTKI 3 TILDA
- UZ tanlansa: Yuqori / Pastki; 2D-PLACE shifri: Yuqori_detal / Pastki_detal.
- RU tanlansa: Верхняя деталь / Нижняя деталь; eski 2D-PLACE uchun ASCII shifr: Verhnyaya_detal / Nizhnyaya_detal.
- EN tanlansa: Top panel / Bottom panel; 2D-PLACE shifri: Top_panel / Bottom_panel.
- Til almashtirilganda 2D-PLACE eksport nomlari ham darhol yangilanadi.

=== YANGI: HAQIQIY ONLAYN SUN’IY INTELLEKT ===
- Mebel360 AI oynasida “Onlayn AI sozlamasi” tugmasi qo‘shildi.
- OpenAI API kaliti kiritilsa, AI hozirgi loyiha o‘lchami, ichki tuzilishi, narxi, kroyi, chiqindisi va furniturasini chuqur tahlil qiladi.
- API kaliti HTML fayl ichiga yozilmaydi; faqat shu kompyuterdagi lokal ai_config.json faylida saqlanadi.
- Kalit bo‘lmasa, avvalgi internet talab qilmaydigan ichki aqlli yordamchi ishlashda davom etadi.
- Dasturiy buyruqlar (teng bo‘lim, erkin bo‘lim, loyihani saqlash, chop etish) internet bo‘lmasa ham ishlaydi.

ONLAYN AI NI YOQISH
1. ZIP faylni to‘liq chiqarib oling.
2. start.bat orqali dasturni oching. index.html ni yolg‘iz ochsangiz onlayn AI ishlamaydi.
3. “Mebel360 AI” tugmasini bosing.
4. “Onlayn AI sozlamasi”ni oching.
5. OpenAI API kalitini kiriting va modelni tanlab “Saqlash”ni bosing.
6. Yashil “Onlayn AI tayyor” holati chiqqach, loyihani erkin gap bilan tahlil qildiring.

XAVFSIZLIK
- ai_config.json faylini boshqa odamlarga yubormang: unda API kaliti bo‘lishi mumkin.
- ZIP tayyorlanganda ai_config.json avtomatik qo‘shilmaydi; foydalanuvchi o‘z kompyuterida kalitni o‘zi kiritadi.
- Har bir onlayn AI so‘rovi API hisobingizdan foydalanadi va xarajat keltirishi mumkin.



=== PRO KONSTRUKTOR MODULI ===
Qo‘shildi: pro_konstruktor.html
Ochish: dastur ishga tushgach yuqoridagi “Pro Konstruktor” tugmasini bosing.
Modul: 3D ko‘rinish, detallar/raskroy, furnitura va 2D Place TXT eksporti.
3D ko‘rinish Three.js CDN orqali yuklanadi, shuning uchun 3D uchun internet kerak bo‘lishi mumkin.
Hisob va jadvallar internet bo‘lmasa ham ishlaydi.


=== 2026-08-22 QO‘SHILDI ===
Yuborilgan app.py funksiyalari asosiy bridge_app.py serveriga birlashtirildi:
- GET /api/config
- POST /api/export-2dplace
Pro Konstruktor endi shu eksport endpointi bilan ishlaydi.
Asl yuborilgan kod app_simple_original.py nomi bilan ham saqlandi.


=== STUDIO 3D MODULI ===
Yangi studio_3d.html qo‘shildi.
Asosiy sahifadagi “Studio 3D” tugmasi orqali ochiladi.
Studio 3D: realistik tekstura, eshik/tortma animatsiyasi, X-Ray, detallar/furnitura jadvallari va 2D Place eksportini o‘z ichiga oladi.
