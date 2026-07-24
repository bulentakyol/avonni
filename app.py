import streamlit as st
import pandas as pd
import math
import re

# --- SAYFA VE ARAYÜZ YAPILANDIRMASI ---
st.set_page_config(
    page_title="Avonni 4'lü Arama ve Kâr Analiz İstasyonu",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- GOOGLE SHEETS & DRIVE ADRESLERİ ---
SHEET_ID = "1F_kdWWEPL6GnlCzk3B9Ji1OoE-juZkCSZegyqbgFg1o"
DRIVE_FOLDER_ID = "1meshrbBNQqyE0qXRbZ338ndBDnbDl56T"

# MASAÜSTÜ KODUNDAKİ VİZON / KOYU ANTRASİT TEMASI VE RENK PALETİ
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    div[data-baseweb="input"] { background-color: #141414 !important; border: 1px solid #2c3e50 !important; border-radius: 4px; }
    input { color: #ffffff !important; font-weight: 600 !important; -webkit-text-fill-color: #ffffff !important; }
    label { color: #3498db !important; font-size: 11px !important; font-weight: bold !important; }
    div[data-testid="stMetricValue"] { font-size: 20px !important; font-weight: bold; }
    
    /* Vizon / Koyu Antrasit Çerçeve Kart Kutuları */
    .vizon-box {
        background-color: #1e1e1e;
        border: 1px solid #2c3e50;
        border-radius: 6px;
        padding: 12px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# SÜTUN HARF TANIMLAMALARI (Masaüstü Mantığı Birebir)
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

# --- HASSAS SAYI DÖNÜŞTÜRÜCÜ & FORMATLAYICI ---
def clean_float(val):
    if pd.isna(val) or val is None: return 0.0
    s = str(val).strip()
    if not s or s == "--": return 0.0
    s = re.sub(r"[^\d,\.]", "", s)
    if not s: return 0.0
    
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    elif "." in s:
        parts = s.split(".")
        if len(parts) == 2 and len(parts[1]) == 3:
            s = s.replace(".", "")
    try:
        return float(s)
    except:
        return 0.0

def format_money(val):
    num = clean_float(val)
    if num == 0.0 and (pd.isna(val) or str(val).strip() in ["", "--"]):
        return "-- TL"
    if num.is_integer():
        return f"{int(num):,}".replace(",", ".") + " TL"
    else:
        p_str = f"{num:,.2f}"
        main_p, dec_p = p_str.split(".")
        return main_p.replace(",", ".") + "," + dec_p + " TL"

def text_clean(val):
    if pd.isna(val) or val is None: return ""
    s = str(val).replace(".0", "").strip()
    return "" if s.lower() == "nan" else s

# --- VERİ YÜKLEME (KARGO SEKME 'skiprows=1' MASAÜSTÜ MANTIĞI) ---
@st.cache_data(ttl=30)
def load_data():
    url_genel = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=GENEL"
    url_kargo = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=KARGO"
    
    df_genel = pd.read_csv(url_genel, header=None, dtype=str)
    # Masaüstü kodundaki kargo_sekmesini_yukle mantığı: skiprows=1 ile başlığı atlıyoruz
    df_kargo = pd.read_csv(url_kargo, header=None, skiprows=1, dtype=str)
    return df_genel, df_kargo

st.title("💡 Avonni 4'lü Arama ve Kâr Analiz İstasyonu")

try:
    df_genel, df_kargo = load_data()
except Exception as e:
    st.error(f"Google Sheets erişim hatası: {e}")
    st.stop()

# --- 1. ÜST PANEL: YAN YANA 4 ARAMA KUTUSU ---
st.subheader("🔍 Ürün Arama")
c1, c2, c3, c4 = st.columns(4)

list_b = sorted([str(x).strip() for x in df_genel[HARF_ANA_KOD].dropna().unique() if str(x).strip() not in ["", "nan"]])
list_c = sorted([str(x).strip() for x in df_genel[HARF_MULTI_KOD].dropna().unique() if str(x).strip() not in ["", "nan"]])
list_d = sorted([str(x).strip() for x in df_genel[HARF_BARKOD].dropna().unique() if str(x).strip() not in ["", "nan"]])
list_g = sorted([str(x).strip() for x in df_genel[HARF_TEDARIKCI].dropna().unique() if str(x).strip() not in ["", "nan"]])

with c1: sel_b = st.selectbox("Ürün Kodu", [""] + list_b, index=0)
with c2: sel_c = st.selectbox("Multikod", [""] + list_c, index=0)
with c3: sel_d = st.selectbox("Barkod", [""] + list_d, index=0)
with c4: sel_g = st.selectbox("Tedarikçi Kd", [""] + list_g, index=0)

selected_row = None
if sel_b: selected_row = df_genel[df_genel[HARF_ANA_KOD].astype(str).str.strip() == sel_b]
elif sel_c: selected_row = df_genel[df_genel[HARF_MULTI_KOD].astype(str).str.strip() == sel_c]
elif sel_d: selected_row = df_genel[df_genel[HARF_BARKOD].astype(str).str.strip() == sel_d]
elif sel_g: selected_row = df_genel[df_genel[HARF_TEDARIKCI].astype(str).str.strip() == sel_g]

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

    current_maliyet_raw = clean_float(v_maliyet)
    current_kargo_raw = clean_float(v_kargo)
    current_fiyat_raw = clean_float(v_fiyat)

    # --- 2. ORTA PANEL: BİLGİ VE GÖRSEL PANELİ ---
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

        # 8. Satır Ürün Ölçüleri (H, W, D, Ø)
        st.caption("📐 Ürün Ölçüleri (H / W / D / Ø)")
        o1, o2, o3, o4 = st.columns(4)
        o1.text_input("H:", v_olcu_h, disabled=True)
        o2.text_input("W:", v_olcu_w, disabled=True)
        o3.text_input("D:", v_olcu_d, disabled=True)
        o4.text_input("Ø:", v_olcu_cap, disabled=True)

    with col_right:
        st.subheader("🖼️ Ürün Görseli")
        # Masaüstü Gorsel_getir mantığı: Ürün koduna göre doğrudan resmi çağırma
        st.markdown(f"**Aranan Ürün Kodu:** `{v_kod}`")
        drive_thumb_url = f"https://drive.google.com/thumbnail?id={DRIVE_FOLDER_ID}&sz=w1000"
        st.image(drive_thumb_url, caption=f"{v_kod}.jpg", use_column_width=True)

    st.divider()

    # --- 3. ALT SÜRÜCÜ 1: CANLI PAZARYERİ KÂR ANALİZ İSTASYONU ---
    st.subheader("📊 Canlı Pazaryeri Kâr Analiz İstasyonu (KDV Hariç Net Kâr)")
    pk1, pk2 = st.columns([1, 2])

    with pk1:
        kom_oran = st.number_input("Komisyon (%)", value=23.5, step=0.1)
        satis_fiyati_kdvli = st.number_input("Satış Fiyatı (KDV'li)", value=float(current_fiyat_raw) if current_fiyat_raw > 0 else 0.0, step=10.0)
        
        payda = (1.0 / 1.20) - (kom_oran / 120.0)
        if (current_maliyet_raw > 0 or current_kargo_raw > 0) and payda > 0:
            min_satis = (current_maliyet_raw + current_kargo_raw) / payda
            st.markdown(f"**Min. Satış Fiyatı:** <span style='color:#3498db; font-weight:bold;'>{min_satis:.2f} TL</span>", unsafe_allow_html=True)
        else:
            st.markdown("**Min. Satış Fiyatı:** <span style='color:#3498db; font-weight:bold;'>0.00 TL</span>", unsafe_allow_html=True)

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
            
            # Masaüstü kodundaki net kâr negatifse kırmızı (#e74c3c), pozitifse yeşil (#2ecc71) mantığı
            kar_renk = "#e74c3c" if net_kar_kdv_haric < 0 else "#2ecc71"
            m3.markdown(f"<p style='color:{kar_renk}; font-size:14px; font-weight:bold; margin-bottom:2px;'>Net Kâr (KDV Hariç)</p><p style='color:{kar_renk}; font-size:22px; font-weight:bold;'>{format_money(net_kar_kdv_haric)}</p>", unsafe_allow_html=True)
        else:
            m1, m2, m3 = st.columns(3)
            m1.metric("PY Kom. Gideri (KDV'siz)", "-- TL")
            m2.metric("Maliyet+Kargo+Kom(Net)", "-- TL")
            m3.metric("Net Kâr (KDV Hariç)", "-- TL")

    st.divider()

    # --- 4. ALT SÜRÜCÜ 2: CANLI DESİ HESAPLA & KARGO FİRMA FİYATLARI ---
    st.subheader("📦 Canlı Desi Hesapla & Kargo Firma Fiyatları")
    d1, d2, d3, d4 = st.columns(4)
    
    init_en = clean_float(koli_w) if koli_w else 0.0
    init_boy = clean_float(koli_l) if koli_l else 0.0
    init_yuk = clean_float(koli_h) if koli_h else 0.0

    c_en = d1.number_input("En", value=init_en)
    c_boy = d2.number_input("Boy", value=init_boy)
    c_yuk = d3.number_input("Yükseklik", value=init_yuk)

    calc_desi = (c_en * c_boy * c_yuk) / 3000.0 if (c_en > 0 and c_boy > 0 and c_yuk > 0) else 0.0
    d4.metric("Sonuc Desi", f"{calc_desi:.2f}")

    # MASAÜSTÜ KARGO EŞLEŞTİRME MOTORU (astype(float) == float(desi_tam))
    if calc_desi > 0 and df_kargo is not None:
        desi_tam = math.ceil(calc_desi)
        try:
            df_kargo_clean = df_kargo.copy()
            # Masaüstü kodu: idx_desi = self.harf_to_indeks(KARGO_HARF_DESI)
            df_kargo_clean["DESI_NUM"] = df_kargo_clean[KARGO_HARF_DESI].apply(clean_float)
            
            # Masaüstündeki birebir tam eşleştirme maskesi
            mask_kargo = df_kargo_clean["DESI_NUM"].astype(float) == float(desi_tam)
            kargo_satir = df_kargo_clean[mask_kargo]

            if not kargo_satir.empty:
                dhl_val = kargo_satir.iloc[0][KARGO_HARF_DHL]
                hj_val = kargo_satir.iloc[0][KARGO_HARF_HJ]
                hjxl_val = kargo_satir.iloc[0][KARGO_HARF_HJXL]

                kf1, kf2, kf3 = st.columns(3)
                kf1.markdown(f"<p style='color:#7f8c8d; font-size:12px; font-weight:bold;'>DHL:</p><p style='color:#e67e22; font-size:20px; font-weight:bold;'>{format_money(dhl_val)}</p>", unsafe_allow_html=True)
                kf2.markdown(f"<p style='color:#7f8c8d; font-size:12px; font-weight:bold;'>HJ:</p><p style='color:#9b59b6; font-size:20px; font-weight:bold;'>{format_money(hj_val)}</p>", unsafe_allow_html=True)
                kf3.markdown(f"<p style='color:#7f8c8d; font-size:12px; font-weight:bold;'>HJXL:</p><p style='color:#e74c3c; font-size:20px; font-weight:bold;'>{format_money(hjxl_val)}</p>", unsafe_allow_html=True)
            else:
                st.warning(f"{desi_tam} desi için kargo tablosunda fiyat bulunamadı.")
        except Exception as ex:
            st.error(f"Kargo tablosu okunurken hata: {ex}")
else:
    st.info("Arama yapmak için yukarıdaki kutucuklardan bir ürün seçiniz.")
