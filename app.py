import streamlit as st
import pandas as pd
import math

# --- SAYFA VE ARAYÜZ YAPILANDIRMASI ---
st.set_page_config(
    page_title="Avonni 4'lü Arama ve Kâr Analiz İstasyonu",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- GOOGLE SHEETS & DRIVE ADRESLERİ ---
SHEET_ID = "1F_kdWWEPL6GnlCzk3B9Ji1OoE-juZkCSZegyqbgFg1o"

# CSS İLE MASAÜSTÜ NİZAMI VE SIKIŞTIRILMIŞ TASARIM
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    div[data-baseweb="input"] { background-color: #141414 !important; border-color: #2b2b2b !important; }
    input { color: #ffffff !important; font-weight: bold; }
    div[data-testid="stMetricValue"] { font-size: 18px !important; }
    </style>
""", unsafe_allow_keywords=True)

# SÜTUN HARF TANIMLAMALARI
def harf_to_indeks(harf):
    indeks = 0
    for char in harf.upper():
        indeks = indeks * 26 + (ord(char) - ord('A') + 1)
    return indeks - 1

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

# --- VERİ MÖDÜLÜ ---
@st.cache_data(ttl=60)
def load_data():
    url_genel = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=GENEL"
    url_kargo = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=KARGO"
    
    df_genel = pd.read_csv(url_genel, header=None)
    df_kargo = pd.read_csv(url_kargo, header=None)
    return df_genel, df_kargo

def format_money(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return "-- TL"
        num = float(str(val).replace(".", "").replace(",", "."))
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

st.title("💡 Avonni 4'lü Arama ve Kâr Analiz İstasyonu")

try:
    df_genel, df_kargo = load_data()
except Exception as e:
    st.error(f"Veri yüklenemedi. İnternet/Sheets izinlerini kontrol edin: {e}")
    st.stop()

# --- 1. ÜST ARAMA PANELİ (4 KUTU - AÇILIR LİSTELİ) ---
st.subheader("🔍 Ürün Arama")
c1, c2, c3, c4 = st.columns(4)

list_b = sorted(df_genel[HARF_ANA_KOD].dropna().astype(str).unique().tolist())
list_c = sorted(df_genel[HARF_MULTI_KOD].dropna().astype(str).unique().tolist())
list_d = sorted(df_genel[HARF_BARKOD].dropna().astype(str).unique().tolist())
list_g = sorted(df_genel[HARF_TEDARIKCI].dropna().astype(str).unique().tolist())

with c1:
    sel_b = st.selectbox("Ürün Kodu", [""] + list_b, index=0)
with c2:
    sel_c = st.selectbox("Multikod", [""] + list_c, index=0)
with c3:
    sel_d = st.selectbox("Barkod", [""] + list_d, index=0)
with c4:
    sel_g = st.selectbox("Tedarikçi Kd", [""] + list_g, index=0)

# Seçilen Koda Göre Satırı Bul
selected_row = None
if sel_b:
    selected_row = df_genel[df_genel[HARF_ANA_KOD].astype(str) == sel_b]
elif sel_c:
    selected_row = df_genel[df_genel[HARF_MULTI_KOD].astype(str) == sel_c]
elif sel_d:
    selected_row = df_genel[df_genel[HARF_BARKOD].astype(str) == sel_d]
elif sel_g:
    selected_row = df_genel[df_genel[HARF_TEDARIKCI].astype(str) == sel_g]

if selected_row is not None and not selected_row.empty:
    row = selected_row.iloc[0]

    v_kod = text_clean(row[HARF_ANA_KOD])
    v_barkod = text_clean(row[HARF_BARKOD])
    v_ty = text_clean(row[HARF_TY_ID])
    v_hb = text_clean(row[HARF_HB_SKU])
    v_ted_adi = text_clean(row[HARF_SAGLAYICI])
    v_ted_kd = text_clean(row[HARF_TEDARIKCI])
    
    v_fiyat = row[HARF_FIYAT]
    v_kargo = row[HARF_KARGO]
    v_maliyet = row[HARF_MALIYET]
    v_termin = text_clean(row[HARF_TERMIN])
    v_stok = text_clean(row[HARF_STOK])
    v_katalog = "X" if "X" in str(row[HARF_KATALOG]).upper() else ""

    koli_l = text_clean(row[HARF_KOLI_L])
    koli_w = text_clean(row[HARF_KOLI_W])
    koli_h = text_clean(row[HARF_KOLI_H])
    v_koli = f"{koli_l} x {koli_w} x {koli_h}" if (koli_l and koli_w and koli_h) else "--"
    v_desi = text_clean(row[HARF_DESI]) or "--"

    v_olcu_h = text_clean(row[HARF_OLCU_H]) or "--"
    v_olcu_w = text_clean(row[HARF_OLCU_W]) or "--"
    v_olcu_d = text_clean(row[HARF_OLCU_D]) or "--"
    v_olcu_cap = text_clean(row[HARF_OLCU_CAP]) or "--"

    try: current_maliyet_raw = float(str(v_maliyet).replace(".", "").replace(",", "."))
    except: current_maliyet_raw = 0.0

    try: current_kargo_raw = float(str(v_kargo).replace(".", "").replace(",", "."))
    except: current_kargo_raw = 0.0

    # --- ORTA PANEL: BİLGİLER + GÖRSEL ---
    col_left, col_right = st.columns([2, 1])

    with col_left:
        r1_1, r1_2 = st.columns(2)
        r1_1.text_input("Kod:", v_kod, disabled=True)
        r1_2.text_input("Barkod:", v_barkod, disabled=True)

        r2_1, r2_2 = st.columns(2)
        r2_1.text_input("TY ID:", v_ty, disabled=True)
        r2_2.text_input("HB SKU:", v_hb, disabled=True)

        r3_1, r3_2 = st.columns(2)
        r3_1.text_input("Ted Adı:", v_ted_adi, disabled=True)
        r3_2.text_input("Ted Kd:", v_ted_kd, disabled=True)

        r4_1, r4_2 = st.columns(2)
        r4_1.text_input("Fiyat:", format_money(v_fiyat), disabled=True)
        r4_2.text_input("Kargo:", format_money(v_kargo), disabled=True)

        r5_1, r5_2 = st.columns(2)
        r5_1.text_input("Maliyet:", format_money(v_maliyet), disabled=True)
        r5_2.text_input("Termin:", v_termin, disabled=True)

        r6_1, r6_2 = st.columns(2)
        r6_1.text_input("Koli:", v_koli, disabled=True)
        r6_2.text_input("Desi:", v_desi, disabled=True)

        r7_1, r7_2 = st.columns(2)
        r7_1.text_input("Stok:", v_stok, disabled=True)
        r7_2.text_input("Katalog:", v_katalog, disabled=True)

        # 8. SATIR ÜRÜN ÖLÇÜLERİ (H, W, D, Ø)
        o1, o2, o3, o4 = st.columns(4)
        o1.text_input("H:", v_olcu_h, disabled=True)
        o2.text_input("W:", v_olcu_w, disabled=True)
        o3.text_input("D:", v_olcu_d, disabled=True)
        o4.text_input("Ø:", v_olcu_cap, disabled=True)

    with col_right:
        # GOOGLE DRIVE GÖRSEL ÇEKİCİ
        img_url = f"https://drive.google.com/thumbnail?id=1meshrbBNQqyE0qXRbZ338ndBDnbDl56T&sz=w1000"
        st.image(img_url, caption=f"{v_kod}.jpg", use_column_width=True)

    st.divider()

    # --- ALT SÜRÜCÜ 1: CANLI PAZARYERİ KÂR ANALİZ İSTASYONU ---
    st.subheader("📊 Canlı Pazaryeri Kâr Analiz İstasyonu (KDV Hariç Net Kâr)")
    pk1, pk2 = st.columns([1, 2])

    with pk1:
        kom_oran = st.number_input("Komisyon (%)", value=20.4, step=0.1)
        satis_fiyati_kdvli = st.number_input("Satış Fiyatı (KDV'li)", value=4295.0, step=10.0)
        
        payda = (1.0 / 1.20) - (kom_oran / 120.0)
        if (current_maliyet_raw > 0 or current_kargo_raw > 0) and payda > 0:
            min_satis = (current_maliyet_raw + current_kargo_raw) / payda
            st.markdown(f"**Min. Satış Fiyatı:** `{min_satis:.2f}`")
        else:
            st.markdown("**Min. Satış Fiyatı:** `0.00`")

    with pk2:
        if satis_fiyati_kdvli > 0:
            satis_kdv_haric = satis_fiyati_kdvli / 1.20
            kom_kesintisi_brut = satis_fiyati_kdvli * (kom_oran / 100.0)
            kom_kesintisi_net = kom_kesintisi_brut / 1.20
            toplam_gider_kdv_haric = current_maliyet_raw + current_kargo_raw + kom_kesintisi_net
            net_kar_kdv_haric = satis_kdv_haric - toplam_gider_kdv_haric

            m1, m2, m3 = st.columns(3)
            m1.metric("PY Kom. Gideri (KDV'siz)", format_money(kom_kesintisi_net))
            m2.metric("Maliyet+Kargo+Kom(Net)", format_money(toplam_gider_kdv_haric))
            m3.metric("Net Kâr (KDV Hariç)", format_money(net_kar_kdv_haric))

    st.divider()

    # --- ALT SÜRÜCÜ 2: CANLI DESİ & KARGO FİRMA FİYATLARI ---
    st.subheader("📦 Canlı Desi Hesapla & Kargo Firma Fiyatları")
    d1, d2, d3, d4 = st.columns(4)
    c_en = d1.number_input("En", value=57.0)
    c_boy = d2.number_input("Boy", value=57.0)
    c_yuk = d3.number_input("Yükseklik", value=35.0)

    calc_desi = (c_en * c_boy * c_yuk) / 3000.0 if (c_en > 0 and c_boy > 0 and c_yuk > 0) else 0.0
    d4.metric("Sonuç Desi", f"{calc_desi:.2f}")

    # KARGO FİRMA FİYATI EŞLEŞTİRME ENGINE
    if calc_desi > 0 and df_kargo is not None:
        desi_tam = math.ceil(calc_desi)
        try:
            # KARGO sekmesinde A sütunu desi, C=DHL, D=HJ, K=HJXL
            df_kargo_clean = df_kargo.iloc[1:].copy() # İlk satır başlık olduğu için kesiyoruz
            df_kargo_clean[KARGO_HARF_DESI] = pd.to_numeric(df_kargo_clean[KARGO_HARF_DESI], errors='coerce')
            
            mask_kargo = df_kargo_clean[KARGO_HARF_DESI] == float(desi_tam)
            kargo_satir = df_kargo_clean[mask_kargo]

            if not kargo_satir.empty:
                dhl_val = kargo_satir.iloc[0][KARGO_HARF_DHL]
                hj_val = kargo_satir.iloc[0][KARGO_HARF_HJ]
                hjxl_val = kargo_satir.iloc[0][KARGO_HARF_HJXL]

                kf1, kf2, kf3 = st.columns(3)
                kf1.metric("DHL", format_money(dhl_val))
                kf2.metric("HJ", format_money(hj_val))
                kf3.metric("HJXL", format_money(hjxl_val))
            else:
                st.warning("Bu desi için kargo fiyatı bulunamadı.")
        except Exception as ex:
            st.error(f"Kargo tablosu okunurken hata: {ex}")
else:
    st.info("Arama yapmak için yukarıdaki kutucuklardan bir ürün seçiniz.")
