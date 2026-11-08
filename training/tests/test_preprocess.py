import pytest

from locknet.preprocess import on_isle


@pytest.mark.parametrize(
    "girdi,beklenen",
    [
        ("İSTANBUL'da IŞIK", "istanbulda ışık"),
        ("@USER g3rizek4lisin sen https://t.co/x", "@user gerizekalisin sen url"),
        ("a p t a l herif", "aptal herif"),
        ("çoooook güzeeel!!!", "çook güzeel"),
        ("s.ktir git a.q", "sktir git aq"),
        ("15temmuz 2023te 3 gün", "15temmuz 2023te 3 gün"),
        ("s@lak mısın", "salak mısın"),
        ("o bir salak", "o bir salak"),
        ("4pt4l m1s1n nes1n", "aptal misin nesin"),
        ("Kızlar 😂😂 aranızda", "kızlar aranızda"),
        ("pic.twitter.com/HaUlMku8UO", "url"),
        ("Ali’nin evi", "alinin evi"),
        ("", ""),
        ("   \n\t ", ""),
    ],
)
def test_kurallar(girdi, beklenen):
    assert on_isle(girdi) == beklenen


def test_turkce_buyuk_harf_sozluk_gibi_davranir():
    # Eski eklentideki hata: JS toLowerCase() "I" harfini "i" yapıyordu.
    assert on_isle("IRMAK") == "ırmak"
    assert on_isle("İZMİR") == "izmir"
