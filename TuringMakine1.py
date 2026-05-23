class TuringMachine:
    def __init__(self, num1: str, num2: str):
        buf = (len(num1) + 1) * len(num2) * 2 + 30
        self.tape = list(f"{num1}*{num2}=") + ['_'] * buf
        self.head = 0
        self.state = 'q0'
        self.step_count = 0

        self.target_sum = ''
        self.sum_index = 0
        self.after_add_shift = False
        self.last_bit_was_last = False 

    def _tape_str(self) -> str:
        return "".join(self.tape)

    def print_step(self, read_sym, write_sym, move_dir, state):
        tape_str = self._tape_str().rstrip('_')
        if self.head >= len(tape_str):
            tape_str = tape_str.ljust(self.head + 1, '_')
        display = (
            tape_str[:self.head]
            + "[" + tape_str[self.head] + "]"
            + tape_str[self.head + 1:]
        )
        print(
            f"Durum: {state:<22} | "
            f"Okunan: {read_sym} | "
            f"Yazılan: {write_sym} | "
            f"Hareket: {move_dir} | "
            f"Bant: {display}"
        )

    def read(self):
        while self.head >= len(self.tape):
            self.tape.append('_')
        return self.tape[self.head]

    def write(self, sym):
        while self.head >= len(self.tape):
            self.tape.append('_')
        self.tape[self.head] = sym

    def move(self, d):
        if d == 'R':
            self.head += 1
        elif d == 'L':
            self.head = max(0, self.head - 1)

    # banttan çarpılan ve sonucu oku
    def _get_multiplicand(self):
        ts = self._tape_str()
        raw = ts.split('*')[0]
        clean = ''.join(c for c in raw if c in '01')
        return clean if clean else '0'

    def _get_result(self):
        ts = self._tape_str()
        parts = ts.split('=')
        raw = parts[1] if len(parts) > 1 else ''
        clean = ''.join(c for c in raw if c in '01')
        return clean if clean else '0'

    # çarpılanı bantın başına 1 bit sola kaydırarak yaz
    def _shift_multiplicand_left(self):
        """Çarpılanı (bant[0..*) kısmını) 1 bit sola kaydır (sona 0 ekle)."""
        ts = self._tape_str()
        star_pos = ts.index('*')
        current = ''.join(c for c in ts[:star_pos] if c in '01')
        shifted = (current + '0').lstrip('0') or '0'
        # Yeni çarpılanı star_pos uzunluğuna sığdır (başa 0 ekle)
        padded = shifted.zfill(star_pos)
        if len(padded) > star_pos:
            # Alan yetmez: bandı genişlet (shift karakterleri ilerlet)
            extra = len(padded) - star_pos
            self.tape = list(' ' * extra) + self.tape
            self.head += extra
            # Yıldız pozisyonunu yeniden bul
            ts2 = "".join(self.tape)
            star_pos = ts2.index('*')
            padded = padded  # aynı uzunluk
        for i, ch in enumerate(padded):
            self.tape[i] = ch

    # Ana döngü
    def run(self):
        print("Turing Makinesi Simülasyonu Başlıyor...\n")
        MAX = 20000

        while self.step_count < MAX:
            sym = self.read()
            wsym = sym
            mov = 'S'
            st = self.state

            if self.state in ('q_kabul', 'q_red'):
                self.print_step(sym, wsym, 'S', st)
                break

            elif self.state == 'q0':
                if sym in ('0', '1'):
                    mov = 'R'
                elif sym == '*':
                    self.state = 'q1'; mov = 'R'
                else:
                    self.state = 'q_red'

            elif self.state == 'q1':
                if sym in ('0', '1'):
                    mov = 'R'
                elif sym == '=':
                    self.state = 'q2'; mov = 'L'
                else:
                    self.state = 'q_red'

            # q2: '='in solundan sola giderek ilk işlenmemiş biti bul
            elif self.state == 'q2':
                if sym in ('X', 'Y'):
                    mov = 'L'   # işlenmiş, atla

                elif sym == '0':
                    wsym = 'Y'
                    is_last = (self.tape[self.head - 1] == '*')
                    self.last_bit_was_last = is_last
                    if is_last:
                        # Son bit sıfır: ekleme yok, kaydırma da yok, temizle
                        self.state = 'q_temizle_start'
                    else:
                        self.state = 'q_go_eq_shift'
                    mov = 'L'

                elif sym == '1':
                    wsym = 'X'
                    is_last = (self.tape[self.head - 1] == '*')
                    self.last_bit_was_last = is_last

                    # Toplam hesapla
                    mult = self._get_multiplicand()
                    res  = self._get_result()
                    new_val = int(mult, 2) + int(res, 2)
                    self.target_sum = bin(new_val)[2:]
                    self.sum_index = 0

                    self.state = 'q_go_eq_add'
                    mov = 'R'

                elif sym == '*':
                    # Çarpan tamamen işlendi (hepsi 0'dı)
                    self.state = 'q_temizle_start'; mov = 'L'

                else:
                    self.state = 'q_red'

            # Toplama: '=' bul
            elif self.state == 'q_go_eq_add':
                if sym != '=':
                    mov = 'R'
                else:
                    self.state = 'q_add_writing'; mov = 'R'

            # Toplama: yaz
            elif self.state == 'q_add_writing':
                if self.sum_index < len(self.target_sum):
                    wsym = self.target_sum[self.sum_index]
                    self.sum_index += 1
                    mov = 'R'
                else:
                    self.state = 'q_add_return'; mov = 'L'

            # Toplama: '=' e geri dön
            # Son bit değilse kaydırmaya geç; son bitse doğrudan temizle
            elif self.state == 'q_add_return':
                if sym != '=':
                    mov = 'L'
                else:
                    if self.last_bit_was_last:
                        # Son bit: kaydırma yapma, temizliğe git
                        self.state = 'q_temizle_start'
                    else:
                        self.state = 'q_go_eq_shift'
                    mov = 'L'

            # Kaydırma: '=' e git (sağa), orada kaydır
            elif self.state == 'q_go_eq_shift':
                if sym != '=':
                    mov = 'R'
                else:
                    # Çarpılanı kaydır
                    self._shift_multiplicand_left()
                    # Son bit mi?
                    if self.last_bit_was_last:
                        self.state = 'q_temizle_start'
                    else:
                        self.state = 'q2'
                    mov = 'L'

            # Temizlik: '*' bul
            elif self.state == 'q_temizle_start':
                if sym != '*':
                    mov = 'L'
                else:
                    self.state = 'q_temizle'; mov = 'R'

            # Temizlik: X→1, Y→0
            elif self.state == 'q_temizle':
                if sym == 'X':
                    wsym = '1'; mov = 'R'
                elif sym == 'Y':
                    wsym = '0'; mov = 'R'
                elif sym == '=':
                    self.state = 'q_kabul'; mov = 'S'
                else:
                    mov = 'R'

            else:
                self.state = 'q_red'

            # --- güncelle & yazdır ---
            self.write(wsym)
            self.print_step(sym, wsym, mov, st)
            self.move(mov)
            self.step_count += 1

        else:
            print(f"\nHATA: {MAX} adım aşıldı, durduruldu!")


# ----------------------------------------------------------------------
def main():
    print("=" * 65)
    print("      Turing Makinesi ile Binary Çarpma Hesaplayıcı")
    print("=" * 65)

    num1 = input("Birinci sayıyı (Binary) girin: ").strip()
    num2 = input("İkinci sayıyı (Binary) girin:  ").strip()

    if not num1 or not num2:
        print("Hata: Boş girdi!"); return
    if not all(c in '01' for c in num1) or not all(c in '01' for c in num2):
        print("Hata: Lütfen sadece binary (0 ve 1) sayılar girin!"); return

    expected = int(num1, 2) * int(num2, 2)
    print(f"\nBant başlangıcı : {num1}*{num2}=")
    print(f"Beklenen sonuç  : {expected} ({bin(expected)[2:]})\n")

    tm = TuringMachine(num1, num2)
    tm.run()

    # Sonucu banttan oku
    tape_str = "".join(tm.tape).rstrip('_')
    parts = tape_str.split('=')
    result_raw = parts[1] if len(parts) > 1 else ''
    result_binary = ''.join(c for c in result_raw if c in '01')
    if not result_binary:
        result_binary = '0'

    result_dec = int(result_binary, 2)
    correct = result_dec == expected

    print("\n" + "=" * 65)
    print("İŞLEM TAMAMLANDI")
    print("=" * 65)
    print(f"Bant Son Durumu : {tape_str}")
    print(f"Toplam Adım     : {tm.step_count}")
    print(f"Sonuç (Binary)  : {result_binary}")
    print(f"Sonuç (Decimal) : {result_dec}")
    print(f"Doğrulama       : {int(num1,2)} × {int(num2,2)} = {expected}")


if __name__ == "__main__":
    main()