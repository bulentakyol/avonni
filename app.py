import streamlit as st
import pandas as pd
import math
import re

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(
    page_title="Avonni Ürün Analiz",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

SHEET_ID = "1F_kdWWEPL6GnlCzk3B9Ji1OoE-juZkCSZegyqbgFg1o"

# --- STİL TANIMLAMALARI (MOBİL UYUMLU HALE GETİRİLDİ) ---
st.markdown("""
    <style>
    .stApp { background-color: #1e1e1e; color: #ffffff; }

    div[data-baseweb="select"] * {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: 800 !important;
    }
    div[data-baseweb="input"] * {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: 800 !important;
    }

    label { color: #3498db !important; font-size: 11px !important; font-weight: bold !important; }
    div[data-testid="stMetricValue"] { font-size: 16px !important; font-weight: bold; }

    h1 { font-size: 20px !important; margin-bottom: 0px !important; padding-bottom: 2px !important; }
    h3 { font-size: 14px !important; margin-bottom: 0px !important; padding-bottom: 2px !important; color: #f1c40f !important; }

    .search-container {
        background-color: #141414;
        border: 1px solid #2c3e50;
        border-radius: 6px;
        padding: 10px;
        margin-bottom: 10px;
    }

    /* Görsel kutusu artık sabit piksel değil, oranla büyüyüp küçülüyor */
    .img-container {
        display: flex;
        justify-content: center;
        align-items: center;
        background-color: #141414;
        padding: 5px;
        border: 1px solid #2c3e50;
        border-radius: 5px;
        width: 100%;
        max-width: 380px;
        margin: 0 auto 10px auto;
    }
    .img-container img {
        width: 100%;
        height: auto;
        max-height: 540px;
        object-fit: contain;
        cursor: pointer;
    }

    /* Genel taşma önleyici: hiçbir eleman ekran genişliğini aşmasın */
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }
    div, span, p { max-width: 100%; word-wrap: break-word; }

    /* ------------------------------------------------------------ */
    /* MOBİL EKRAN (768px altı) İÇİN ÖZEL DÜZENLEMELER               */
    /* ------------------------------------------------------------ */
    @media (max-width: 768px) {
        /* Streamlit'in yan yana kolonlarını alt alta yığ */
        div[data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
        }
        div[data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }

        .img-container {
            max-width: 100% !important;
        }
        .img-container img {
            max-height: 320px !important;
        }

        h1 { font-size: 17px !important; }
        h3 { font-size: 13px !important; }
        label { font-size: 12px !important; }

        div[data-testid="stMetricValue"] { font-size: 15px !important; }

        /* Arama kutuları (Ürün Kodu / Multikod / Barkod / Tedarikçi) mobilde alt alta */
        div[data-testid="stSelectbox"] { margin-bottom: 6px; }
    }

    @media (max-width: 480px) {
        .img-container img {
            max-height: 260px !important;
        }
        span[style*="font-size: 18px"], span[style*="font-size:18px"] {
            font-size: 15px !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# SÜTUN İNDEKSLERİ
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
HARF_GORSEL_LINK = harf_to_indeks("BH")

KARGO_HARF_DESI = harf_to_indeks("A")
KARGO_HARF_DHL = harf_to_indeks("C")
KARGO_HARF_HJ = harf_to_indeks("D")
KARGO_HARF_HJXL = harf_to_indeks("K")

# --- YARDIMCI FONKSİYONLAR ---
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
        return float(s) * 1.0
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

def safe_str(val):
    if pd.isna(val) or val is None: return ""
    s = str(val).strip()
    if s.lower() in ["nan", "none", "nat", ""]: return ""
    if "." in s and not "http" in s:
        try:
            f = float(s)
            if f.is_integer():
                s = str(int(f))
        except:
            pass
    if s.endswith(".0"):
        s = s[:-2]
    return s

# --- VERİ VE KARGO SÖZLÜĞÜ YÜKLEME ---
@st.cache_data(ttl=30)
def load_data():
    url_genel = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=GENEL"
    url_kargo = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=KARGO"

    df_genel = pd.read_csv(url_genel, header=None, dtype=str)
    df_kargo = pd.read_csv(url_kargo, header=None, dtype=str)

    kargo_dict = {}
    for idx, row in df_kargo.iterrows():
        try:
            desi_raw = str(row[KARGO_HARF_DESI]).replace(",", ".").strip()
            desi_val = float(desi_raw)
            if desi_val > 0:
                kargo_dict[int(round(desi_val))] = {
                    'DHL': row[KARGO_HARF_DHL],
                    'HJ': row[KARGO_HARF_HJ],
                    'HJXL': row[KARGO_HARF_HJXL]
                }
        except:
            continue

    return df_genel, kargo_dict

st.markdown("<h1>💡 Avonni Ürün Analiz</h1>", unsafe_allow_html=True)

try:
    df_genel, kargo_dict = load_data()
except Exception as e:
    st.error(f"Google Sheets erişim hatası: {e}")
    st.stop()

# --- 1. BÖLÜM: ARAMA PANELİ ---
st.markdown("<div class='search-container'>", unsafe_allow_html=True)
st.markdown("<h3>🔍 Ürün Arama</h3>", unsafe_allow_html=True)

if 'sel_b' not in st.session_state: st.session_state.sel_b = ""
if 'sel_c' not in st.session_state: st.session_state.sel_c = ""
if 'sel_d' not in st.session_state: st.session_state.sel_d = ""
if 'sel_g' not in st.session_state: st.session_state.sel_g = ""

def clear_others(changed_key):
    for key in ['sel_b', 'sel_c', 'sel_d', 'sel_g']:
        if key != changed_key:
            st.session_state[key] = ""

c1, c2, c3, c4 = st.columns(4)

list_b = sorted([safe_str(x) for x in df_genel[HARF_ANA_KOD].unique() if safe_str(x)])
list_c = sorted([safe_str(x) for x in df_genel[HARF_MULTI_KOD].unique() if safe_str(x)])
list_d = sorted([safe_str(x) for x in df_genel[HARF_BARKOD].unique() if safe_str(x)])
list_g = sorted([safe_str(x) for x in df_genel[HARF_TEDARIKCI].unique() if safe_str(x)])

with c1: st.selectbox("Ürün Kodu", [""] + list_b, key="sel_b", on_change=clear_others, args=("sel_b",))
with c2: st.selectbox("Multikod", [""] + list_c, key="sel_c", on_change=clear_others, args=("sel_c",))
with c3: st.selectbox("Barkod", [""] + list_d, key="sel_d", on_change=clear_others, args=("sel_d",))
with c4: st.selectbox("Tedarikçi Kd", [""] + list_g, key="sel_g", on_change=clear_others, args=("sel_g",))
st.markdown("</div>", unsafe_allow_html=True)

selected_row = None
if st.session_state.sel_b: selected_row = df_genel[df_genel[HARF_ANA_KOD].apply(safe_str) == st.session_state.sel_b]
elif st.session_state.sel_c: selected_row = df_genel[df_genel[HARF_MULTI_KOD].apply(safe_str) == st.session_state.sel_c]
elif st.session_state.sel_d: selected_row = df_genel[df_genel[HARF_BARKOD].apply(safe_str) == st.session_state.sel_d]
elif st.session_state.sel_g: selected_row = df_genel[df_genel[HARF_TEDARIKCI].apply(safe_str) == st.session_state.sel_g]

if selected_row is not None and not selected_row.empty:
    row = selected_row.iloc[0]

    v_kod = safe_str(row[HARF_ANA_KOD])
    v_barkod = safe_str(row[HARF_BARKOD])
    v_ty = safe_str(row[HARF_TY_ID])
    v_hb = safe_str(row[HARF_HB_SKU])
    v_ted_adi = safe_str(row[HARF_SAGLAYICI])
    v_ted_kd = safe_str(row[HARF_TEDARIKCI])

    v_fiyat = row[HARF_FIYAT]
    v_kargo = row[HARF_KARGO]
    v_maliyet = row[HARF_MALIYET]
    v_termin = safe_str(row[HARF_TERMIN])
    v_stok = safe_str(row[HARF_STOK])
    v_katalog = "X" if "X" in str(row[HARF_KATALOG]).upper() else ""
    v_gorsel_link = safe_str(row[HARF_GORSEL_LINK])

    koli_l = safe_str(row[HARF_KOLI_L])
    koli_w = safe_str(row[HARF_KOLI_W])
    koli_h = safe_str(row[HARF_KOLI_H])
    v_koli = f"{koli_l} x {koli_w} x {koli_h}" if (koli_l and koli_w and koli_h) else "--"
    v_desi = safe_str(row[HARF_DESI]) or "--"

    v_olcu_h = safe_str(row[HARF_OLCU_H]) or "--"
    v_olcu_w = safe_str(row[HARF_OLCU_W]) or "--"
    v_olcu_d = safe_str(row[HARF_OLCU_D]) or "--"
    v_olcu_cap = safe_str(row[HARF_OLCU_CAP]) or "--"

    current_maliyet_raw = clean_float(v_maliyet)
    current_kargo_raw = clean_float(v_kargo)
    current_fiyat_raw = clean_float(v_fiyat)

    # --- 2. BÖLÜM: GÖRSEL VE YAN YANA DETAYLAR ---
    col_img, col_detay = st.columns([1, 1.5])

    with col_img:
        if v_gorsel_link.startswith("http"):
            st.markdown(f"""
                <div class="img-container">
                    <a href="{v_gorsel_link}" target="_blank">
                        <img src="{v_gorsel_link}" alt="Ürün Görseli">
                    </a>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="img-container" style="min-height: 200px;">
                    <p style="color: #7f8c8d; font-weight: bold;">Görsel Linki Yok</p>
                </div>
            """, unsafe_allow_html=True)

    with col_detay:
        def render_native_card(label, val):
            st.markdown(f"""
                <div style="background-color: #f1f2f6; border: 1px solid #2c3e50; border-radius: 4px; padding: 6px 8px; margin-bottom: 4px;">
                    <span style="color: #2980b9; font-size: 10px; font-weight: bold; text-transform: uppercase; display: block;">{label}</span>
                    <span style="color: #000000; font-size: 12px; font-weight: 800; word-break: break-all;">{val}</span>
                </div>
            """, unsafe_allow_html=True)

        d1, d2 = st.columns(2)
        with d1: render_native_card("Kod", v_kod)
        with d2: render_native_card("Barkod", v_barkod)

        d3, d4 = st.columns(2)
        with d3: render_native_card("TY ID", v_ty)
        with d4: render_native_card("HB SKU", v_hb)

        d5, d6 = st.columns(2)
        with d5: render_native_card("Ted Adı", v_ted_adi)
        with d6: render_native_card("Ted Kd", v_ted_kd)

        d7, d8 = st.columns(2)
        with d7: render_native_card("Fiyat", format_money(v_fiyat))
        with d8: render_native_card("Kargo Fiyatı", format_money(v_kargo))

        d9, d10 = st.columns(2)
        with d9: render_native_card("Maliyet", format_money(v_maliyet))
        with d10: render_native_card("Termin", v_termin)

        d11, d12 = st.columns(2)
        with d11: render_native_card("Koli Ölçüleri", v_koli)
        with d12: render_native_card("Desi", v_desi)

        d13, d14 = st.columns(2)
        with d13: render_native_card("Stok", v_stok)
        with d14: render_native_card("Katalog", v_katalog)

        o1, o2, o3, o4 = st.columns(4)
        with o1: render_native_card("H", v_olcu_h)
        with o2: render_native_card("W", v_olcu_w)
        with o3: render_native_card("D", v_olcu_d)
        with o4: render_native_card("Ø", v_olcu_cap)

    st.divider()

    # --- 3. BÖLÜM: PY KÂR ANALİZ İSTASYONU ---
    st.markdown("<h3>📊 PY Kâr Analiz İstasyonu</h3>", unsafe_allow_html=True)
    pk1, pk2 = st.columns([1, 2])

    with pk1:
        kom_oran = st.number_input("Komisyon (%)", value=23.5, step=0.1)
        satis_fiyati_kdvli = st.number_input("Satış Fiyatı (KDV'li)", value=float(current_fiyat_raw) if current_fiyat_raw > 0 else 0.0, step=10.0)

        payda = (1.0 / 1.20) - (kom_oran / 120.0)
        if (current_maliyet_raw > 0 or current_kargo_raw > 0) and payda > 0:
            min_satis = (current_maliyet_raw + current_kargo_raw) / payda
            st.markdown(f"**Min. Satış Fiyatı:** <span style='color:#3498db; font-size:15px; font-weight:bold;'>{min_satis:.2f} TL</span>", unsafe_allow_html=True)
        elif payda <= 0:
            st.markdown("**Min. Satış Fiyatı:** <span style='color:#e74c3c; font-size:13px; font-weight:bold;'>Komisyon oranı çok yüksek, hesaplanamıyor</span>", unsafe_allow_html=True)
        else:
            st.markdown("**Min. Satış Fiyatı:** <span style='color:#3498db; font-size:15px; font-weight:bold;'>0.00 TL</span>", unsafe_allow_html=True)

    with pk2:
        if satis_fiyati_kdvli > 0:
            satis_kdv_haric = satis_fiyati_kdvli / 1.20
            kom_kesintisi_brut = satis_fiyati_kdvli * (kom_oran / 100.0)
            kom_kesintisi_net = kom_kesintisi_brut / 1.20
            toplam_gider_kdv_haric = current_maliyet_raw + current_kargo_raw + kom_kesintisi_net
            net_kar_kdv_haric = satis_kdv_haric - toplam_gider_kdv_haric

            m1, m2, m3 = st.columns(3)
            m1.markdown(f"<p style='color:#7f8c8d; font-size:11px; font-weight:bold;'>PY Kom. Gideri (KDV'siz)</p><p style='color:#e67e22; font-size:16px; font-weight:bold;'>{format_money(kom_kesintisi_net)}</p>", unsafe_allow_html=True)
            m2.markdown(f"<p style='color:#7f8c8d; font-size:11px; font-weight:bold;'>Maliyet+Kargo+Kom(Net)</p><p style='color:#e74c3c; font-size:16px; font-weight:bold;'>{format_money(toplam_gider_kdv_haric)}</p>", unsafe_allow_html=True)

            kar_renk = "#e74c3c" if net_kar_kdv_haric < 0 else "#2ecc71"
            m3.markdown(f"<p style='color:{kar_renk}; font-size:11px; font-weight:bold;'>Net Kâr (KDV Hariç)</p><p style='color:{kar_renk}; font-size:18px; font-weight:bold;'>{format_money(net_kar_kdv_haric)}</p>", unsafe_allow_html=True)
        else:
            m1, m2, m3 = st.columns(3)
            m1.markdown(f"<p style='color:#7f8c8d; font-size:11px; font-weight:bold;'>PY Kom. Gideri (KDV'siz)</p><p style='color:#e67e22; font-size:16px; font-weight:bold;'>-- TL</p>", unsafe_allow_html=True)
            m2.markdown(f"<p style='color:#7f8c8d; font-size:11px; font-weight:bold;'>Maliyet+Kargo+Kom(Net)</p><p style='color:#e74c3c; font-size:16px; font-weight:bold;'>-- TL</p>", unsafe_allow_html=True)
            m3.markdown(f"<p style='color:#2ecc71; font-size:11px; font-weight:bold;'>Net Kâr (KDV Hariç)</p><p style='color:#2ecc71; font-size:18px; font-weight:bold;'>-- TL</p>", unsafe_allow_html=True)

    st.divider()

    st.markdown("<h3>📦 Canlı Desi & Kargo Fiyatları</h3>", unsafe_allow_html=True)
    d1, d2, d3, d4 = st.columns(4)

    init_en = clean_float(koli_w) if koli_w else 0.0
    init_boy = clean_float(koli_l) if koli_l else 0.0
    init_yuk = clean_float(koli_h) if koli_h else 0.0

    c_en = d1.number_input("En", value=init_en)
    c_boy = d2.number_input("Boy", value=init_boy)
    c_yuk = d3.number_input("Yükseklik", value=init_yuk)

    calc_desi = (c_en * c_boy * c_yuk) / 3000.0 if (c_en > 0 and c_boy > 0 and c_yuk > 0) else 0.0
    d4.markdown(f"<p style='color:#7f8c8d; font-size:11px; font-weight:bold;'>Sonuç Desi</p><p style='color:#3498db; font-size:18px; font-weight:bold;'>{calc_desi:.2f}</p>", unsafe_allow_html=True)

    # --- KARGO FİYATLARINI BASMA MOTORU ---
    if calc_desi > 0 and kargo_dict:
        desi_hedef = math.ceil(calc_desi)
        try:
            matched_key = None
            if desi_hedef in kargo_dict:
                matched_key = desi_hedef
            else:
                available_desis = sorted(kargo_dict.keys())
                for d in available_desis:
                    if d >= desi_hedef:
                        matched_key = d
                        break
                if not matched_key and available_desis:
                    matched_key = available_desis[-1]

            if matched_key and matched_key in kargo_dict:
                prices = kargo_dict[matched_key]
                dhl_val = prices['DHL']
                hj_val = prices['HJ']
                hjxl_val = prices['HJXL']

                kf1, kf2, kf3 = st.columns(3)
                kf1.markdown(f"<p style='color:#7f8c8d; font-size:11px; font-weight:bold;'>DHL:</p><p style='color:#e67e22; font-size:16px; font-weight:bold;'>{format_money(dhl_val)}</p>", unsafe_allow_html=True)
                kf2.markdown(f"<p style='color:#7f8c8d; font-size:11px; font-weight:bold;'>HJ:</p><p style='color:#9b59b6; font-size:16px; font-weight:bold;'>{format_money(hj_val)}</p>", unsafe_allow_html=True)
                kf3.markdown(f"<p style='color:#7f8c8d; font-size:11px; font-weight:bold;'>HJXL:</p><p style='color:#e74c3c; font-size:16px; font-weight:bold;'>{format_money(hjxl_val)}</p>", unsafe_allow_html=True)
            else:
                st.warning(f"{desi_hedef} desi için kargo fiyatı bulunamadı.")
        except Exception as ex:
            st.error(f"Kargo hesaplama hatası: {ex}")
else:
    st.info("Arama yapmak için yukarıdaki arama panelinden bir ürün seçiniz.")
