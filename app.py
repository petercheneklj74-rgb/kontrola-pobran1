import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Kontrola pobrań",
    page_icon="📦",
    layout="wide"
)

st.title("📦 Dashboard – Kontrola przesyłek pobraniowych")

st.write(
    "System do weryfikacji przesyłek i rozliczeń między spółkami: INT, Lublin, Rzeszów."
)

st.divider()

# Opcja uniwersalna: Wybór formatu plików na górze
st.sidebar.header("⚙️ Ustawienia wczytywania")
separator = st.sidebar.selectbox(
    "Wybierz domyślny separator w plikach CSV:",
    options=["; (średnik - standard Excel PL)", ", (przecinek - standard EN)", "	 (tabulator / tsv)"],
    index=0
)

# Przypisanie separatora
if ";" in separator:
    sep_char = ";"
elif "," in separator:
    sep_char = ","
else:
    sep_char = "\t"

st.header("1. Pliki bazowe spółek")

col1, col2, col3 = st.columns(3)

with col1:
    plik_int = st.file_uploader(
        "INT – plik bazowy",
        type=["csv", "txt"],
        key="spolka_int"
    )

with col2:
    plik_lublin = st.file_uploader(
        "Lublin – plik bazowy",
        type=["csv", "txt"],
        key="spolka_lublin"
    )

with col3:
    plik_rzeszow = st.file_uploader(
        "Rzeszów – plik bazowy",
        type=["csv", "txt"],
        key="spolka_rzeszow"
    )

st.divider()

st.header("2. Plik do weryfikacji")

plik_kontrolny = st.file_uploader(
    "Wgraj plik z przesyłkami do sprawdzenia",
    type=["csv", "txt"],
    key="kontrolny"
)

st.divider()

if plik_int and plik_lublin and plik_rzeszow and plik_kontrolny:
    st.success("Wszystkie cztery pliki zostały wgrane!")

    # Uniwersalna funkcja bezpiecznego wczytywania
    def wczytaj_csv_bezpiecznie(plik):
        for sep_test in [sep_char, ',', ';', '\t']:
            for enc in ['utf-8', 'cp1250', 'latin2']:
                try:
                    plik.seek(0)
                    df = pd.read_csv(plik, sep=sep_test, encoding=enc, engine='python', on_bad_lines='skip')
                    if len(df.columns) > 1:
                        return df
                except Exception:
                    continue
        plik.seek(0)
        return pd.read_csv(plik, sep=None, encoding='utf-8', engine='python', errors='replace')

    try:
        df_int = wczytaj_csv_bezpiecznie(plik_int)
        df_lublin = wczytaj_csv_bezpiecznie(plik_lublin)
        df_rzeszow = wczytaj_csv_bezpiecznie(plik_rzeszow)
        df_kontrolny = wczytaj_csv_bezpiecznie(plik_kontrolny)
    except Exception as e:
        st.error(f"Błąd podczas wczytywania plików: {e}")
        st.stop()

    st.subheader("3. Konfiguracja kolumn dla każdego pliku")
    st.write("Wskaż, która kolumna zawiera numer listu przewozowego w poszczególnych plikach (domyślnie wybrano sugerowane):")

    # Pomocnicza funkcja do znajdowania indeksu domyślnej kolumny (szuka dokładnego lub częściowego dopasowania)
    def znajdz_indeks_domyslny(kolumny, szukana_nazwa):
        # 1. Próba dokładnego dopasowania
        for i, kol in enumerate(kolumny):
            if str(kol).strip().lower() == szukana_nazwa.lower():
                return i
        # 2. Próba dopasowania częściowego (np. zawiera szukaną frazę)
        for i, kol in enumerate(kolumny):
            if szukana_nazwa.lower() in str(kol).strip().lower():
                return i
        return 0 # Jeśli nie znajdzie, domyślnie pierwsza kolumna

    idx_int = znajdz_indeks_domyslny(df_int.columns.tolist(), "nrlistu")
    idx_lublin = znajdz_indeks_domyslny(df_lublin.columns.tolist(), "nrlistu")
    idx_rzeszow = znajdz_indeks_domyslny(df_rzeszow.columns.tolist(), "nrlistu")
    idx_kontrolny = znajdz_indeks_domyslny(df_kontrolny.columns.tolist(), "List przewozowy")

    col_conf_1, col_conf_2, col_conf_3, col_conf_4 = st.columns(4)

    with col_conf_1:
        kol_int = st.selectbox(
            "Kolumna: INT",
            options=df_int.columns.tolist(),
            index=idx_int,
            key="kol_int_sel"
        )

    with col_conf_2:
        kol_lublin = st.selectbox(
            "Kolumna: Lublin",
            options=df_lublin.columns.tolist(),
            index=idx_lublin,
            key="kol_lublin_sel"
        )

    with col_conf_3:
        kol_rzeszow = st.selectbox(
            "Kolumna: Rzeszów",
            options=df_rzeszow.columns.tolist(),
            index=idx_rzeszow,
            key="kol_rzeszow_sel"
        )

    with col_conf_4:
        kol_kontrolny = st.selectbox(
            "Kolumna: Plik Kontrolny",
            options=df_kontrolny.columns.tolist(),
            index=idx_kontrolny,
            key="kol_kontr_sel"
        )

    st.divider()

    if st.button("ANALIZUJ I DOPASUJ", type="primary"):
        with st.spinner("Trwa dopasowywanie przesyłek..."):
            # Pobranie zbiorów unikalnych numerów dla każdej spółki
            listy_int = set(df_int[kol_int].astype(str).str.strip())
            listy_lublin = set(df_lublin[kol_lublin].astype(str).str.strip())
            listy_rzeszow = set(df_rzeszow[kol_rzeszow].astype(str).str.strip())

            # Funkcja przypisująca spółkę
            def znajdz_spolke(numer):
                num_str = str(numer).strip()
                spolki = []
                if num_str in listy_int:
                    spolki.append("INT")
                if num_str in listy_lublin:
                    spolki.append("Lublin")
                if num_str in listy_rzeszow:
                    spolki.append("Rzeszów")
                
                if not spolki:
                    return "Brak w bazach"
                return ", ".join(spolki)

            # Aplikowanie logiki do pliku kontrolnego
            df_wynikowy = df_kontrolny.copy()
            df_wynikowy["Dopasowana Spółka"] = df_wynikowy[kol_kontrolny].apply(znajdz_spolke)

            st.session_state["wynik_analizy"] = df_wynikowy
            st.success("Analiza zakończona sukcesem!")

    # Jeśli wynik istnieje w pamięci sesji, pokaż go
    if "wynik_analizy" in st.session_state:
        st.divider()
        st.header("4. Wyniki dopasowania, wyszukiwanie i kolory")

        df_res = st.session_state["wynik_analizy"]
        
        # Czytelne podsumowanie liczbowe w metrykach
        total_rows = len(df_res)
        cnt_int = (df_res["Dopasowana Spółka"] == "INT").sum()
        cnt_lublin = (df_res["Dopasowana Spółka"] == "Lublin").sum()
        cnt_rzeszow = (df_res["Dopasowana Spółka"] == "Rzeszów").sum()
        cnt_brak = (df_res["Dopasowana Spółka"] == "Brak w bazach").sum()

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Wszystkie", total_rows)
        m2.metric("INT", cnt_int)
        m3.metric("Lublin", cnt_lublin)
        m4.metric("Rzeszów", cnt_rzeszow)
        m5.metric("Brak w bazach", cnt_brak)

        st.markdown("")

        # --- SEKCJA FILTRÓW, WYSZUKIWARKI I KOLOROWYCH PRZYCISKÓW ---
        st.subheader("Filtrowanie i wyszukiwanie")
        
        f_col1, f_col2, f_col3 = st.columns(3)

        with f_col1:
            wybrana_opcja_surowa = st.radio(
                "Wybierz widok dla spółki:",
                options=[
                    "⚪ Wszystkie", 
                    "🟢 INT (Zielony)", 
                    "🔵 Lublin (Niebieski)", 
                    "🔴 Rzeszów (Czerwony)", 
                    "⚫ Brak w bazach"
                ],
                horizontal=False
            )
            
            if "Wszystkie" in wybrana_opcja_surowa:
                wybrana_spolka_filtr = "Wszystkie"
            elif "INT" in wybrana_opcja_surowa:
                wybrana_spolka_filtr = "INT"
            elif "Lublin" in wybrana_opcja_surowa:
                wybrana_spolka_filtr = "Lublin"
            elif "Rzeszów" in wybrana_opcja_surowa:
                wybrana_spolka_filtr = "Rzeszów"
            else:
                wybrana_spolka_filtr = "Brak w bazach"

        with f_col2:
            szukany_tekst = st.text_input("🔍 Szukaj w tabeli (np. numer listu):", "")

        with f_col3:
            wszystkie_kolumny = df_res.columns.tolist()
            wybrane_kolumny = st.multiselect(
                "Wybierz kolumny do wyświetlenia i pobrania:",
                options=wszystkie_kolumny,
                default=wszystkie_kolumny
            )

        # 1. Filtrowanie po spółce
        if wybrana_spolka_filtr == "Wszystkie":
            df_filtered = df_res
        else:
            df_filtered = df_res[df_res["Dopasowana Spółka"] == wybrana_spolka_filtr]

        # 2. Filtrowanie po wyszukiwanym tekście
        if szukany_tekst:
            mask = df_filtered.astype(str).apply(lambda col: col.str.contains(szukany_tekst, case=False, na=False)).any(axis=1)
            df_filtered = df_filtered[mask]

        if not wybrane_kolumny:
            wybrane_kolumny = wszystkie_kolumny

        df_final_display = df_filtered[wybrane_kolumny]

        # --- FUNKCJA KOLORUJĄCA WIERSZE ---
        def koloruj_wiersze(row):
            if "Dopasowana Spółka" in row.index:
                spolka = str(row["Dopasowana Spółka"])
                if "INT" in spolka and "Lublin" not in spolka and "Rzeszów" not in spolka:
                    return ['background-color: #d4edda'] * len(row)  # Zielony dla INT
                elif "Lublin" in spolka and "INT" not in spolka and "Rzeszów" not in spolka:
                    return ['background-color: #cce5ff'] * len(row)  # Niebieski dla Lublina
                elif "Rzeszów" in spolka and "INT" not in spolka and "Lublin" not in spolka:
                    return ['background-color: #f8d7da'] * len(row)  # Czerwony/różowy dla Rzeszowa
            return [''] * len(row)

        st.markdown(f"**Wyświetlam wierszy:** {len(df_final_display)}")
        
        st.dataframe(df_final_display.style.apply(koloruj_wiersze, axis=1), use_container_width=True)

        csv_data = df_final_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Pobierz przefiltrowany wynik jako CSV",
            data=csv_data,
            file_name=f"wyniki_{wybrana_spolka_filtr.lower().replace(' ', '_')}.csv",
            mime="text/csv",
            type="primary"
        )

else:
    st.info("Wgraj trzy pliki bazowe (INT, Lublin, Rzeszów) oraz plik kontrolny, aby przejść do analizy.")

st.caption("System kontroli rozliczeń pobrań – wersja 3.3")