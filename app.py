import streamlit as st
import pandas as pd
import math

# --- SAYFA VE ARAYÜZ YAPILANDIRMASI ---
st.set_page_page_config(
    page_title="Avonni Stok & Kâr İstasyonu",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- DRIVE VE SHEETS ADRESLERİ ---
SHEET_ID = "1F_kdWWEPL6GnlCzk3B9Ji1OoE-juZkCSZegyqbgFg1o"
DRIVE_FOLDER_ID = "1meshrbBNQqyE0qXRbZ338ndBDnbDl56T"

# --- VERİ YÜKLEME FONKSİYONLARI ---
@st.cache_data(ttl=300)  # Veriyi 5 dakikada bir otomatik yeniler
def load_sheets_data():
    try:
        url_genel = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=GENEL"
        url_kargo = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=KARGO"
        
        df_genel = pd.read_csv(url_genel, header=None)
        df_kargo = pd.read_csv(url_kargo, header=None, skiprows=1)
        return df_genel, df_kargo
    except Exception as e:
        st.error(f"Google Sheets verisi okunamadı. İzinleri ve internet bağlantınızı kontrol edin: {e}")
        return None, None

def harf_to_indeks(harf):
    indeks = 0
    for char in harf.upper():
        indeks = indeks * 26 + (ord(char) - ord('A') + 1)
    return indeks - 1

def format_money(val):
    try:
        num = float(val)
        if num.is_integer():
            return f"{int(num):,}".replace(",", ".") + " TL"
        else:
            p_str = f"{num:,.2f}"
            main_p, dec_p = p_str.split(".")
            return main_p.replace(",", ".") + "," + dec_p + " TL"
    except:
        return str(val) + " TL" if pd.notna(val) else "-- TL"

def text_clean(val):
    if pd.isna(val): return ""
    s = str(val).replace(".0", "").strip()
    return "" if s.lower() == "nan" else s

# Google Drive klasöründeki resmi doğrudan göstermek için URL üretici
def get_drive_image_url(filename):
    # Drive görsellerini doğrudan yayınlamak için kütüphane/proxy kullanımı
    return f"https://lh3.googleusercontent.com/d/{DRIVE_FOLDER_ID}" # Not: Doğrudan erişim için bulut servisinde dosya adı eşleştirmesi kullanılır.

# --- VERİ SÜTUN İNDEKSLERİ ---
HARF_ANA_KOD = harf_to_indeks("B")
HARF_MULTI_KOD = harf_to_indeks("C")
HARF_BARKOD = harf_to_indeks("D")
HARF_SAGLAYICI = harf_to_indeks("F")
HARF_TEDARIKCI = harf_to_indeks("G")
HARF_TY_ID = harf_to_indeks("H")
HARF_HB_SKU = harf_to_indeks("I")
HARF_FIYAT = harf_to_indeks("M")
HARF_MALIYET = harf_to_indeks("N")
HARF_KARGO = harf_to_indeks("P")
HARF_STOK = harf_to_indeks("U")
HARF_KATALOG = harf_to_indeks("X")
HARF_TERMIN = harf_to_indeks("AF")

HARF_KOLI_L = harf_to_indeks("AL")
HARF_KOLI_W = harf_to_indeks("AM")
HARF_KOLI_H = harf_to_indeks("AN")
HARF_DESI = harf_to_indeks("BU")

HARF_OLCU_H = harf_to_indeks("AG")
HARF_OLCU_W = harf_to_indeks("AH")
HARF_OLCU_D = harf_to_indeks("AI")
HARF_OLCU_CAP = harf_to_indeks("AJ")

KARGO_HARF_DESI = harf_to_indeks("A")
KARGO_HARF_DHL = harf_to_indeks("C")
KARGO_HARF_HJ = harf_to_indeks("D")
KARGO_HARF_HJXL = harf_to_indeks("K")

# --- UYGULAMA BAŞLIĞI ---
st.title("💡 Avonni Arama & Kâr Analiz İstasyonu")

df_genel, df_kargo = load_sheets_data()

if df_genel is not None:
    # --- ÜST ARAMA PANELİ ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ara_kod = st.text_input("Ürün Kodu Ara", "").strip().lower()
    with col2:
        ara_multi = st.text_input("Multikod Ara", "").strip().lower()
    with col3:
        ara_bar = st.text_input("Barkod Ara", "").strip().lower()
    with col4:
        ara_ted = st.text_input("Tedarikçi Kd Ara", "").strip().lower()

    # Filtreleme Mantığı
    sonuc = pd.DataFrame()
    if ara_kod and len(ara_kod) >= 2:
        mask = df_genel[HARF_ANA_KOD].astype(str).str.lower().str.contains(ara_kod, na=False)
        sonuc = df_genel[mask]
    elif ara_multi and len(ara_multi) >= 2:
        mask = df_genel[HARF_MULTI_KOD].astype(str).str.lower().str.contains(ara_multi, na=False)
        sonuc = df_genel[mask]
    elif ara_bar and len(ara_bar) >= 2:
        mask = df_genel[HARF_BARKOD].astype(str).str.lower().str.contains(ara_bar, na=False)
        sonuc = df_genel[mask]
    elif ara_ted and len(ara_ted) >= 2:
        mask = df_genel[HARF_TEDARIKCI].astype(str).str.lower().str.contains(ara_ted, na=False)
        sonuc = df_genel[mask]

    # --- ANA İÇERİK ---
    if not sonuc.empty:
        ilk_satir = sonuc.iloc[0]
        
        # Değerleri Ayıkla
        u_kod = text_clean(ilk_satir[HARF_ANA_KOD])
        u_barkod = text_clean(ilk_satir[HARF_BARKOD])
        u_ty = text_clean(ilk_satir[HARF_TY_ID])
        u_hb = text_clean(ilk_satir[HARF_HB_SKU])
        u_ted_adi = text_clean(ilk_satir[HARF_SAGLAYICI])
        u_ted_kd = text_clean(ilk_satir[HARF_TEDARIKCI])
        u_fiyat_raw = ilk_satir[HARF_FIYAT]
        u_kargo_raw = ilk_satir[HARF_KARGO]
        u_maliyet_raw = ilk_satir[HARF_MALIYET]
        u_termin = text_clean(ilk_satir[HARF_TERMIN])
        u_stok = text_clean(ilk_satir[HARF_STOK])
        u_katalog = "X" if "X" in str(ilk_satir[HARF_KATALOG]).upper() else ""
        
        koli_l = text_clean(ilk_satir[HARF_KOLI_L])
        koli_w = text_clean(ilk_satir[HARF_KOLI_W])
        koli_h = text_clean(ilk_satir[HARF_KOLI_H])
        u_koli = f"{koli_l} x {koli_w} x {koli_h}" if koli_l and koli_w and koli_h else "--"
        u_desi = text_clean(ilk_satir[HARF_DESI]) or "--"

        u_olcu_h = text_clean(ilk_satir[HARF_OLCU_H]) or "--"
        u_olcu_w = text_clean(ilk_satir[HARF_OLCU_W]) or "--"
        u_olcu_d = text_clean(ilk_satir[HARF_OLCU_D]) or "--"
        u_olcu_cap = text_clean(ilk_satir[HARF_OLCU_CAP]) or "--"

        try: current_maliyet_raw = float(u_maliyet_raw)
        except: current_maliyet_raw = 0.0

        try: current_kargo_raw = float(u_kargo_raw)
        except: current_kargo_raw = 0.0

        # SOL PANELLER & SAĞ GÖRSEL DÜZENİ
        left_col, right_col = st.columns([2, 1])

        with left_col:
            st.subheader("📌 Ürün Bilgileri")
            b_col1, b_col2 = st.columns(2)
            with b_col1:
                st.text_input("Kod", u_kod, disabled=True)
                st.text_input("TY ID", u_ty, disabled=True)
                st.text_input("Ted Adı", u_ted_adi, disabled=True)
                st.text_input("Fiyat", format_money(u_fiyat_raw), disabled=True)
                st.text_input("Maliyet", format_money(u_maliyet_raw), disabled=True)
                st.text_input("Koli Ölçüleri", u_koli, disabled=True)
                st.text_input("Stok", u_stok, disabled=True)
            with b_col2:
                st.text_input("Barkod", u_barkod, disabled=True)
                st.text_input("HB SKU", u_hb, disabled=True)
                st.text_input("Ted Kd", u_ted_kd, disabled=True)
                st.text_input("Kargo Fiyatı", format_money(u_kargo_raw), disabled=True)
                st.text_input("Termin", u_termin, disabled=True)
                st.text_input("Desi", u_desi, disabled=True)
                st.text_input("Katalog Durumu", u_katalog, disabled=True)

            # ÜRÜN ÖLÇÜLERİ (H, W, D, Ø) - 4 PX / 8 PX DÜZENİ
            st.caption("📐 Ürün Ölçüleri")
            o1, o2, o3, o4 = st.columns(4)
            with o1: st.text_input("H", u_olcu_h, disabled=True)
            with o2: st.text_input("W", u_olcu_w, disabled=True)
            with o3: st.text_input("D", u_olcu_d, disabled=True)
            with o4: st.text_input("Ø", u_olcu_cap, disabled=True)

        with right_col:
            st.subheader("🖼️ Ürün Görseli")
            # Google Drive'dan Görsel Yükleme Simülasyonu
            st.info(f"Ürün Kodu: {u_kod}")
            img_url = f"https://drive.google.com/thumbnail?id={DRIVE_FOLDER_ID}&sz=w800"
            st.image("https://via.placeholder.com/300x450.png?text=Avonni+Aydinlatma", caption=f"{u_kod}.jpg", use_column_width=True)

        st.divider()

        # --- ALT SÜRÜCÜ: CANLI PAZARYERİ KÂR ANALİZ İSTASYONU ---
        st.subheader("📊 Canlı Pazaryeri Kâr Analiz İstasyonu (KDV Hariç Net Kâr)")
        
        pk1, pk2 = st.columns([1, 2])
        with pk1:
            kom_oran = st.number_input("Komisyon (%)", value=23.5, step=0.5)
            satis_fiyati_kdvli = st.number_input("Satış Fiyatı (KDV'li)", value=0.0, step=10.0)
            
            payda = (1.0 / 1.20) - (kom_oran / 120.0)
            if (current_maliyet_raw > 0 or current_kargo_raw > 0) and payda > 0:
                min_satis = (current_maliyet_raw + current_kargo_raw) / payda
                st.info(f"**Min. Satış Fiyatı:** {min_satis:.2f} TL")
            else:
                st.info("**Min. Satış Fiyatı:** 0.00 TL")

        with pk2:
            if satis_fiyati_kdvli > 0:
                satis_kdv_haric = satis_fiyati_kdvli / 1.20
                kom_kesintisi_brut = satis_fiyati_kdvli * (kom_oran / 100.0)
                kom_kesintisi_net = kom_kesintisi_brut / 1.20
                toplam_gider_kdv_haric = current_maliyet_raw + current_kargo_raw + kom_kesintisi_net
                net_kar_kdv_haric = satis_kdv_haric - toplam_gider_kdv_haric

                st.metric("PY Kom. Gideri (KDV'siz)", format_money(kom_kesintisi_net))
                st.metric("Maliyet + Kargo + Kom (Net)", format_money(toplam_gider_kdv_haric))
                st.metric("Net Kâr (KDV Hariç)", format_money(net_kar_kdv_haric), delta=f"{net_kar_kdv_haric:.2f} TL")
            else:
                st.write("Hesaplama için satış fiyatı giriniz.")

        st.divider()

        # --- ALT SÜRÜCÜ: CANLI DESİ HESAPLAMA İSTASYONU ---
        st.subheader("📦 Canlı Desi & Kargo Firma Fiyatları")
        d1, d2, d3, d4 = st.columns(4)
        with d1: c_en = st.number_input("En (cm)", value=0.0)
        with d2: c_boy = st.number_input("Boy (cm)", value=0.0)
        with d3: c_yuk = st.number_input("Yükseklik (cm)", value=0.0)
        
        calc_desi = 0.0
        if c_en > 0 and c_boy > 0 and c_yuk > 0:
            calc_desi = (c_en * c_boy * c_yuk) / 3000.0
        
        with d4:
            st.metric("Sonuç Desi", f"{calc_desi:.2f}")

        # Kargo Fiyatı Eşleşmesi
        if calc_desi > 0 and df_kargo is not None:
            desi_tam = math.ceil(calc_desi)
            try:
                mask_kargo = df_kargo[KARGO_HARF_DESI].astype(float) == float(desi_tam)
                kargo_satir = df_kargo[mask_kargo]
                if not kargo_satir.empty:
                    dhl_fiyat = kargo_satir.iloc[0][KARGO_HARF_DHL]
                    hj_fiyat = kargo_satir.iloc[0][KARGO_HARF_HJ]
                    hjxl_fiyat = kargo_satir.iloc[0][KARGO_HARF_HJXL]
                    
                    kf1, kf2, kf3 = st.columns(3)
                    kf1.metric("DHL Fiyatı", format_money(dhl_fiyat))
                    kf2.metric("HJ Fiyatı", format_money(hj_fiyat))
                    kf3.metric("HJXL Fiyatı", format_money(hjxl_fiyat))
            except Exception as e:
                st.caption("Kargo tablosundan fiyat okunamadı.")
    else:
        st.info("Aramak için yukarısındaki kutucuklardan en az 2 karakter giriniz.")