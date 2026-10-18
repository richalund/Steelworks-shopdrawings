"""Ritningsspråk: fasta texter på ritningarna (materiallista, allmänna noteringar, titelblockets rubriker,
detaljblad, A3-bladens noter) på svenska (sv), engelska (en) eller kinesiska (zh).

  import sprak
  T = sprak.oversattare("en")
  T("STYCKLIT.")                      -> "PART MARK"
  T("ALLA HÅL ÄR %s mm OM EJ ANNAT ANGES", 22) -> "ALL HOLES ARE 22 mm UNLESS OTHERWISE STATED"
  sprak.mall(svgtext, "zh")           -> mallens fasta rubriker utbytta

Noterna som användaren eller konstruktionsskriptet skriver (RITNING["noter"], --not) översätts inte: skriv dem på
ritningens språk. Kinesiska kräver ett typsnitt med kinesiska tecken (installera_linux.sh installerar
WenQuanYi Zen Hei); Qt byter typsnitt tecken för tecken, så mallens Arial/osifont fungerar ändå.
Saknas en text i tabellen används den svenska: lägg till raden här (alla tre språken) i stället för att
skriva texten direkt i ett skript.
"""

SPRAK = ("sv", "en", "zh")

# svensk nyckel: (engelska, kinesiska). %s ersätts med argumenten.
TEXTER = {
    # materiallistan och allmänna noteringar (sammanställning)
    "ALLMÄNNA NOTERINGAR:": ("GENERAL NOTES:", "一般说明："),
    "ALLA HÅL ÄR %s mm OM EJ ANNAT ANGES": ("ALL HOLES ARE %s mm UNLESS NOTED", "除另有注明外，所有孔径均为 %s mm"),
    "ALLA SVETSAR ÄR %s mm OM EJ ANNAT ANGES": ("ALL WELDS ARE a%s mm UNLESS NOTED", "除另有注明外，所有焊缝均为 a%s mm"),
    "MATERIALLISTA FÖR ETT GODS MÄRKT:": ("MATERIAL LIST FOR ASSEMBLY:", "构件材料表，构件编号："),
    "%s st. TILLVERKAS": ("%s pcs TO BE MADE", "制作数量 %s 件"),
    "STYCKLIT.": ("PART MARK", "零件号"),
    "PROFIL": ("PROFILE", "型材"),
    "MATERIAL": ("MATERIAL", "材料"),
    "ANT.": ("QTY", "数量"),
    "LÄNGD": ("LENGTH", "长度"),
    "AREA/st": ("AREA/pc", "面积/件"),
    "VIKT/st": ("WT/pc", "重量/件"),
    "TOTALT": ("TOTAL", "合计"),
    "KÄLLA": ("SOURCE", "来源"),
    # noteringarnas rubriker (noter.py) och noteringsbladet
    "UNDERLAG OCH ANTAGANDEN": ("BASIS AND ASSUMPTIONS", "依据与假设"),
    "UTFÖRANDE": ("EXECUTION", "做法"),
    "MONTAGE OCH INFÄSTNING": ("INSTALLATION AND FIXING", "安装与固定"),
    "SVETS": ("WELDING", "焊接"),
    "YTBEHANDLING": ("SURFACE TREATMENT", "表面处理"),
    "MATERIAL OCH KÄLLOR": ("MATERIALS AND SOURCES", "材料与来源"),
    "INKÖPTA KOMPONENTER": ("PURCHASED COMPONENTS", "外购件"),
    "KONTROLL": ("CHECKS", "检查"),
    "%s (FORTS.)": ("%s (CONT.)", "%s（续）"),
    "ALLMÄNNA NOTERINGAR SE BLAD %s": ("GENERAL NOTES SEE SHEET %s", "一般说明见图纸 %s"),
    "ALLMÄNNA NOTERINGAR %s": ("GENERAL NOTES %s", "一般说明 %s"),
    "GEMENSAMMA NOTERINGAR SE RITNING %s": ("COMMON NOTES SEE DRAWING %s", "通用说明见图纸 %s"),
    "GEMENSAMMA NOTERINGAR %s": ("COMMON NOTES %s", "通用说明 %s"),
    # detaljblad och översikt
    "DETALJ D%s  %s": ("DETAIL D%s  %s", "详图 D%s  %s"),
    "DETALJER %s – DETALJERNAS LÄGEN D1 ... VISAS I BLAD %s.1": ("DETAILS %s – LOCATION OF DETAILS D1 ... SHOWN ON SHEET %s.1",
                                                                "详图 %s – 详图 D1 ... 的位置见图纸 %s.1"),
    "VY %s  %s": ("VIEW %s  %s", "视图 %s  %s"),
    "REGELKONTROLL %s: %s": ("RULE CHECK %s: %s", "规则检查 %s：%s"),
    # titelblockets fasta rubriker (mallar/A2.svg)
    "UPPDRAG NR": ("JOB NO", "项目编号"),
    "RITAD/KONSTR AV": ("DRAWN/DESIGNED BY", "制图/设计"),
    "DATUM": ("DATE", "日期"),
    "HANDLÄGGARE": ("HANDLED BY", "经办人"),
    "ANSVARIG": ("RESPONSIBLE", "负责人"),
    "SKALA": ("SCALE", "比例"),
    "NUMMER": ("NUMBER", "图号"),
    "BET": ("REV", "版本"),
    "ANT": ("QTY", "数量"),
    "ÄNDRINGEN AVSER": ("DESCRIPTION OF CHANGE", "修改内容"),
    "SIGN": ("SIGN", "签名"),
    "PLACERING I STOMNÄT": ("LOCATION IN GRID", "轴网位置"),
    "SYSTEMLINJE": ("GRID LINE", "轴线"),
    "ETAPP": ("STAGE", "阶段"),
    "ANTAL": ("QTY", "数量"),
    # A3-bladen (ritning.py)
    "Material: %s": ("Material: %s", "材料：%s"),
    "Plåttjocklek %s mm, bockradie (inre) %s mm": ("Sheet thickness %s mm, inner bend radius %s mm", "板厚 %s mm，内折弯半径 %s mm"),
    "Utbredd plåt ca %s x %s mm, se blad 2": ("Flat blank approx. %s x %s mm, see sheet 2", "展开尺寸约 %s x %s mm，见第 2 页"),
    "Vikt ca %s kg": ("Weight approx. %s kg", "重量约 %s kg"),
    "Hörnradier R%s (4 st)": ("Corner radii R%s (4 pcs)", "圆角 R%s（4 处）"),
    "Mått i mm. Skala %s (isometri %s), blad 2 %s.": ("Dimensions in mm. Scale %s (isometric %s), sheet 2 %s.", "尺寸单位 mm。比例 %s（轴测图 %s），第 2 页 %s。"),
    "Utbredning %s, plåt %s mm. Utbredd storlek ca %s x %s mm.": ("Flat pattern %s, sheet %s mm. Blank size approx. %s x %s mm.",
                                                                  "展开图 %s，板厚 %s mm。展开尺寸约 %s x %s mm。"),
    "Bockradie inre %s mm. Bocknoter: riktning och vinkel vid varje bocklinje (NED streckad).": (
        "Inner bend radius %s mm. Bend notes: direction and angle at each bend line (DOWN dashed).",
        "内折弯半径 %s mm。折弯说明：每条折弯线标注方向和角度（向下为虚线）。"),
    "DXF för laser: %s, för bockning: %s": ("DXF for laser: %s, for bending: %s", "激光切割 DXF：%s，折弯 DXF：%s"),
    "Tillverkningsgranskning: %s, se %s": ("Manufacturability check: %s, see %s", "可制造性检查：%s，见 %s"),
    "Plåttjocklek %s mm. Kontur för laser: %s": ("Plate thickness %s mm. Contour for laser: %s", "板厚 %s mm。激光切割轮廓：%s"),
    "Fasade kanter %s mm": ("Chamfered edges %s mm", "倒角 %s mm"),
    "Gängade hål %s (gängan inte ritad)": ("Threaded holes %s (thread not drawn)", "螺纹孔 %s（螺纹未画出）"),
    "Vikt ca %s kg (stål)": ("Weight approx. %s kg (steel)", "重量约 %s kg（钢）"),
    "Mått i mm. Skala %s%s. Projektionsmetod E.": ("Dimensions in mm. Scale %s%s. First angle projection.", "尺寸单位 mm。比例 %s%s。第一角投影法。"),
    " (isometri %s)": (" (isometric %s)", "（轴测图 %s）"),
    "Ytbehandling enligt beställning.": ("Surface treatment as ordered.", "表面处理按订单要求。"),
    "UPP": ("UP", "向上"),
    "NED": ("DOWN", "向下"),
}


def oversattare(sprak="sv"):
    """Funktion T(svensk_text, *argument) för språket (sv, en, zh)."""
    if sprak not in SPRAK:
        raise ValueError("Okänt språk %s, finns: %s" % (sprak, ", ".join(SPRAK)))
    i = SPRAK.index(sprak) - 1

    def T(s, *arg):
        mall = s if i < 0 or s not in TEXTER else TEXTER[s][i]
        return mall % arg if arg else mall
    return T


def mall(svgtext, sprak="sv"):
    """Mallens fasta rubriker (<tspan>UPPDRAG NR</tspan> ...) på språket. Redigerbara fält ändras inte."""
    if sprak == "sv":
        return svgtext
    T = oversattare(sprak)
    for sv in sorted((k for k in TEXTER if k.isupper() and "%" not in k), key=len, reverse=True):
        svgtext = svgtext.replace(">%s</tspan>" % sv, ">%s</tspan>" % T(sv))
    return svgtext


def mallfil(mallsokvag, sprak, ut_mapp):
    """Kopia av mallfilen på språket i ut_mapp (eller mallen själv för svenska)."""
    import os
    if sprak == "sv":
        return mallsokvag
    with open(mallsokvag, encoding="utf-8") as f:
        text = mall(f.read(), sprak)
    ut = os.path.join(ut_mapp, "%s_%s.svg" % (os.path.splitext(os.path.basename(mallsokvag))[0], sprak))
    with open(ut, "w", encoding="utf-8") as f:
        f.write(text)
    return ut
