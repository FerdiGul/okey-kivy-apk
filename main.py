from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.properties import StringProperty

# -------------------- Oyuncu İsimleri Ekranı --------------------
class OyuncuIsimleriEkrani(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'oyuncu_isimleri'
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.inputs = []
        for i in range(4):
            ti = TextInput(
                hint_text=f"Oyuncu {i+1} İsmi",
                multiline=False,
                size_hint_y=None,
                height=40
            )
            self.inputs.append(ti)
            layout.add_widget(ti)
        self.devam_button = Button(text="Devam", size_hint_y=None, height=40)
        self.devam_button.bind(on_press=self.devam)
        layout.add_widget(self.devam_button)
        self.add_widget(layout)

    def devam(self, instance):
        names = [inp.text.strip() for inp in self.inputs]
        if any(not name for name in names):
            popup = Popup(title="Hata", 
                          content=Label(text="Lütfen tüm oyuncu isimlerini girin."),
                          size_hint=(None, None), size=(400, 200))
            popup.open()
            return
        app = App.get_running_app()
        app.oyun_ekrani.set_player_names(names)
        self.manager.current = 'puan_hesaplama'

# -------------------- Puan Hesaplama Ekranı (Eşli Mod Turnuva) --------------------
class OyunEkrani(Screen):
    # Turnuva: 3 tur, her tur 8 el (bölüm)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'puan_hesaplama'
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.add_widget(self.layout)

        # Turnuva ayarları
        self.total_rounds = 3
        self.games_per_round = 8
        self.current_round = 1
        self.current_game = 0  # Mevcut turun el sayısı (0-index)
        self.current_round_scores = [0, 0]  # Her turdaki toplam skorlar (Takım 1, Takım 2)
        self.round_wins = [0, 0]            # Her takımın tur kazancı
        self.hand_results = []              # Her elin sonuçlarını tablo şeklinde saklar (list of tuples)

        # Eşli mod: 2 takım
        self.competitor_count = 2  
        self.player_names = []      # 4 oyuncu ismi
        self.team_names = []        # Takım 1 ve Takım 2 otomatik oluşturulacak

        # UI referansları
        self.info_label = None  # Gösterir: "Tur: X/Y | El: Z/W"
        self.skor_inputs = []   # Her takım için el skoru girilecek alanlar
        self.penalty_checkboxes = []  # 3 satır x 2 sütun (ek ceza)
        self.result_label = None      # Bu elin hesaplanmış sonucunu gösterir
        self.table_label = None       # Geçmiş el sonuçlarını gösteren tablo

    def set_player_names(self, names):
        self.player_names = names
        self.team_names = [
            f"Takım 1 ({self.player_names[0]} - {self.player_names[1]})",
            f"Takım 2 ({self.player_names[2]} - {self.player_names[3]})"
        ]

    def on_pre_enter(self):
        self.layout.clear_widgets()
        # Turnuva başlangıç bilgileri
        self.current_round = 1
        self.current_game = 0
        self.current_round_scores = [0, 0]
        self.round_wins = [0, 0]
        self.hand_results = []

        self.info_label = Label(text=f"Tur: {self.current_round}/{self.total_rounds} | El: {self.current_game+1}/{self.games_per_round}",
                                size_hint_y=None, height=40)
        self.layout.add_widget(self.info_label)

        # Skor giriş alanları (2 adet)
        self.skor_inputs = []
        for i in range(self.competitor_count):
            hint = f"{self.team_names[i]} El Skoru (örn. 92, -5, 104)"
            ti = TextInput(hint_text=hint, multiline=False, size_hint_y=None, height=40, input_filter='int')
            ti.bind(text=self.check_score_inputs)
            self.skor_inputs.append(ti)
            self.layout.add_widget(ti)

        # Ek ceza check-box'ları: 3 adet, her biri +101 ekleyecek
        penalty_names = ["Okey Kaldı (101)", "İşlek Attı (101)", "Yanlış Açtı (101)"]
        self.penalty_checkboxes = []
        grid = GridLayout(cols=self.competitor_count+1, size_hint_y=None, height=(len(penalty_names)+1)*40)
        grid.add_widget(Label(text=""))
        for i in range(self.competitor_count):
            grid.add_widget(Label(text=self.team_names[i], size_hint_y=None, height=40))
        for pen in penalty_names:
            grid.add_widget(Label(text=pen, size_hint_y=None, height=40))
            row = []
            for i in range(self.competitor_count):
                cb = CheckBox(active=False, size_hint=(None, None), size=(40,40))
                row.append(cb)
                grid.add_widget(cb)
            self.penalty_checkboxes.append(row)
        self.layout.add_widget(Label(text="Ek Cezalar (+101)", size_hint_y=None, height=30))
        self.layout.add_widget(grid)

        # Hesapla butonu – başlangıçta skor alanları boş olduğundan devre dışı:
        self.hesapla_button = Button(text="Hesapla", size_hint_y=None, height=40)
        self.hesapla_button.bind(on_press=self.hesapla_skor)
        self.hesapla_button.disabled = True
        self.layout.add_widget(self.hesapla_button)

        # Yeni El butonu – başlangıçta devre dışı; yalnızca hesaplama yapıldıktan sonra aktif olacak
        self.yeni_el_button = Button(text="Yeni El", size_hint_y=None, height=40)
        self.yeni_el_button.bind(on_press=self.yeni_el)
        self.yeni_el_button.disabled = True
        self.layout.add_widget(self.yeni_el_button)

        # Sonuç etiketleri
        self.result_label = Label(text="", size_hint_y=None, height=80)
        self.layout.add_widget(self.result_label)

        # El sonuçlarını tablo şeklinde gösteren label
        self.table_label = Label(text="El Sonuçları:\nEl | Takım 1 | Takım 2", size_hint_y=None, height=120)
        self.layout.add_widget(self.table_label)

        # Tur özetini gösteren label
        self.round_summary_label = Label(text="", size_hint_y=None, height=80)
        self.layout.add_widget(self.round_summary_label)

    def check_score_inputs(self, instance, value):
        # Hesapla butonunu ancak her iki skor girişi doluysa aktif yap
        all_filled = all(ti.text.strip() != "" for ti in self.skor_inputs)
        self.hesapla_button.disabled = not all_filled

    def hesapla_skor(self, instance):
        # "Hesapla" butonuna basıldığında, yalnızca bu elin skoru hesaplanır.
        try:
            game_scores = []
            for i in range(self.competitor_count):
                base_str = self.skor_inputs[i].text.strip()
                base_val = int(base_str) if base_str else 0
                penalty = 0
                for row in self.penalty_checkboxes:
                    if row[i].active:
                        penalty += 101
                final_score = base_val + penalty
                game_scores.append(final_score)
        except ValueError:
            self.show_popup("Hata", "Lütfen geçerli sayısal değer girin.")
            return

        # Bu elin sonucu hesaplandı, ekranda göster
        self.last_hand_scores = game_scores  # Bu elin skoru hafızaya alındı
        display_text = "Bu elin sonucu:\n"
        for i in range(self.competitor_count):
            display_text += f"{self.team_names[i]}: {game_scores[i]}\n"
        self.result_label.text = display_text

        # Hesapla butonu artık devre dışı, ve "Yeni El" butonu aktif hale gelsin
        self.hesapla_button.disabled = True
        self.yeni_el_button.disabled = False

        # Not: Hesapla butonuna basınca mevcut el sayısı artmasın, yalnızca "Yeni El" ile geçiş olsun.
        self.info_label.text = f"Tur: {self.current_round}/{self.total_rounds} | El: {self.current_game+1}/{self.games_per_round}"

    def yeni_el(self, instance):
        # "Yeni El" butonuna basılınca, eğer hesaplama yapılmışsa, mevcut elin sonucu hafızaya kaydedilsin.
        if hasattr(self, "last_hand_scores"):
            for i in range(self.competitor_count):
                self.current_round_scores[i] += self.last_hand_scores[i]
            hand_number = self.current_game + 1
            self.hand_results.append((hand_number, self.last_hand_scores[0], self.last_hand_scores[1]))
            self.update_table_display()
            del self.last_hand_scores

        # Mevcut el tamamlandıktan sonra, el sayısını artır.
        self.current_game += 1

        # Temizle: skor giriş alanlarını ve ceza kutularını sıfırla.
        for ti in self.skor_inputs:
            ti.text = ""
        for row in self.penalty_checkboxes:
            for cb in row:
                cb.active = False

        # Hesapla butonunu tekrar devre dışı bırak (girişler boş olduğu için)
        self.hesapla_button.disabled = True
        # Yeni El butonunu yeniden devre dışı bırak; sadece hesapla alanları dolduğunda aktif olacak.
        self.yeni_el_button.disabled = True

        # Eğer bu turdaki el sayısı tamamlanmadıysa, sadece el numarasını güncelle.
        if self.current_game < self.games_per_round:
            self.info_label.text = f"Tur: {self.current_round}/{self.total_rounds} | El: {self.current_game+1}/{self.games_per_round}"
        else:
            # Tur tamamlandı: Tur kazananı belirlensin.
            min_score = min(self.current_round_scores)
            winners = [self.team_names[i] for i in range(self.competitor_count) if self.current_round_scores[i] == min_score]
            if len(winners) == 1:
                for i in range(self.competitor_count):
                    if self.current_round_scores[i] == min_score:
                        self.round_wins[i] += 1
            else:
                for i in range(self.competitor_count):
                    if self.current_round_scores[i] == min_score:
                        self.round_wins[i] += 0.5
            round_text = f"Tur {self.current_round} Sonu:\n"
            for i in range(self.competitor_count):
                round_text += f"{self.team_names[i]}: {self.current_round_scores[i]} puan\n"
            round_text += "Tur Kazananı: " + ", ".join(winners)
            self.round_summary_label.text = round_text

            self.current_round += 1
            self.current_game = 0
            self.current_round_scores = [0] * self.competitor_count
            self.hand_results = []  # Yeni tur için tablo sıfırlansın

            if self.current_round <= self.total_rounds:
                self.info_label.text = f"Tur: {self.current_round}/{self.total_rounds} | El: 1/{self.games_per_round}"
            else:
                # Turnuva bitmiş
                if self.round_wins[0] > self.round_wins[1]:
                    overall_winner = self.team_names[0]
                elif self.round_wins[1] > self.round_wins[0]:
                    overall_winner = self.team_names[1]
                else:
                    overall_winner = "Berabere"
                final_text = (f"Turnuva Sonu:\n"
                              f"{self.team_names[0]} Tur Kazancı: {self.round_wins[0]}\n"
                              f"{self.team_names[1]} Tur Kazancı: {self.round_wins[1]}\n"
                              f"Turnuva Kazananı: {overall_winner}")
                self.result_label.text = final_text
                self.info_label.text = "Turnuva Bitti."
                self.hesapla_button.disabled = True
                return

    def update_table_display(self):
        table_text = "El Sonuçları:\nEl | Takım 1 | Takım 2\n"
        for hand, s1, s2 in self.hand_results:
            table_text += f"{hand} | {s1} | {s2}\n"
        self.table_label.text = table_text

    def show_popup(self, title, content):
        popup = Popup(title=title,
                      content=Label(text=content),
                      size_hint=(None, None),
                      size=(400, 200))
        popup.open()

# -------------------- Kurallar Ekranı --------------------
class KurallarEkrani(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'kurallar'
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        kurallar_text = (
            "EŞLİ 101 TURNUVASI OYUN KURALLARI\n\n"
            "III. OYUNA İLİŞKİN GENEL KURALLAR:\n"
            "- Oyunda 12-13-1 şeklinde per yapılamaz.\n"
            "- Gösterge fonksiyonu yoktur.\n"
            "- Gösterge çift olarak kullanılamaz.\n"
            "- Açarken yanlış per açarsanız, hatalı olan oyuncunun takımına 101 ceza puanı verilir.\n"
            "- 101 oyununda açılan perlerin toplam değeri 101 olmalıdır.\n"
            "- Yandan taş aldığınızda el açmak zorundasınız; aldığınız taşı el açarken kullanmalısınız.\n"
            "- Yana atılan taşlar birbirinin üzerine, önceki atılan taşlar görünmeyecek şekilde atılır.\n"
            "- Elinizde 1 taş kaldığında bu taşı göstergenin üzerine bırakarak veya yan tarafa kapalı olarak atarak oyunu bitirebilirsiniz.\n"
            "- Elden bitme, okey atma, çift açma gibi durumlarda ceza oranları uygulanır:\n"
            "    * Normal bitiş: -101\n"
            "    * Çift bitiş: -202\n"
            "    * Elden Bitme: -202\n"
            "    * Elden Okey Bitme: -404\n"
            "- Eşlerden biri biterse diğerinin cezası iptal edilir.\n"
            "(Detaylar PDF’de mevcuttur.)"
        )
        layout.add_widget(Label(text=kurallar_text, halign='left'))
        self.add_widget(layout)

# -------------------- Oyun Sonu Ekranı --------------------
class OyunSonuEkrani(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'oyun_sonu'
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.add_widget(self.layout)

    def puanlari_goster(self, round_wins):
        self.layout.clear_widgets()
        result_text = "Turnuva Sonu Skorları (Tur Kazanımları):\n"
        result_text += f"Takım 1: {round_wins[0]} tur\n"
        result_text += f"Takım 2: {round_wins[1]} tur\n"
        if round_wins[0] > round_wins[1]:
            result_text += "\nTurnuva Kazananı: Takım 1"
        elif round_wins[1] > round_wins[0]:
            result_text += "\nTurnuva Kazananı: Takım 2"
        else:
            result_text += "\nTurnuva Berabere bitti."
        self.layout.add_widget(Label(text=result_text, halign='center'))

# -------------------- Ana Uygulama Sınıfı --------------------
class Okey101YardimciApp(App):
    def build(self):
        sm = ScreenManager()
        self.oyuncu_isimleri = OyuncuIsimleriEkrani(name='oyuncu_isimleri')
        self.oyun_ekrani = OyunEkrani(name='puan_hesaplama')
        self.kurallar = KurallarEkrani(name='kurallar')
        self.oyun_sonu = OyunSonuEkrani(name='oyun_sonu')

        sm.add_widget(self.oyuncu_isimleri)
        sm.add_widget(self.oyun_ekrani)
        sm.add_widget(self.kurallar)
        sm.add_widget(self.oyun_sonu)

        sm.current = 'oyuncu_isimleri'
        return sm

if __name__ == '__main__':
    Okey101YardimciApp().run()
