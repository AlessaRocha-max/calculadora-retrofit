"""
Calculadora de Retrofit de Iluminação - Casa
AB2 - Eficiência e Gestão Energética

Retrofit não é só trocar a lâmpada que queimou: é refazer a iluminação de
cada cômodo. O programa dimensiona cômodo por cômodo (Método dos Lúmens),
confere a luz recomendada para cada uso (faixas de referência para casas,
seção 4.2 do trabalho escrito; NBR ISO/CIE 8995-1 para o escritório), soma o gasto com reposição de lâmpadas (ciclo de
vida) e o efeito de sensores (presença, temporizador, dimmer), e calcula a
economia e o retorno (payback, VPL e TIR) do retrofit da casa toda para LED.

Execução:  python calculadora_retrofit.py
Dica: pressione ENTER para aceitar o valor padrão mostrado entre colchetes.
      Só com ENTER, o programa calcula a casa de exemplo (igual à da página HTML).
"""

import math
import sys
import textwrap

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---------------------------------------------------------------------------
# Luz mínima por uso: nome, Em (lux), UGR máx. (0 = não se aplica), Ra mín.
# Casas: valor dentro das faixas de referência do trabalho escrito (seção 4.2),
# iluminação geral; a NBR ISO/CIE 8995-1 não traz valores para residências.
# Escritório: NBR ISO/CIE 8995-1.
# ---------------------------------------------------------------------------
AMBIENTES = {
    1: ("Sala de estar / jantar", 150, 0, 80),
    2: ("Cozinha", 150, 0, 80),
    3: ("Quarto", 150, 0, 80),
    4: ("Banheiro", 200, 0, 80),
    5: ("Corredor, hall ou escada", 100, 0, 80),
    6: ("Garagem, despensa ou área de serviço", 100, 0, 80),
    7: ("Escritório em casa (home office)", 500, 19, 80),
}

# Lâmpadas de hoje: nome, potência (W), luz (lm), reator (W), vida (h), preço de reposição (R$)
LAMP_HOJE = {
    "inc60": ("Incandescente 60 W", 60, 800, 0, 1000, 6),
    "hal42": ("Halógena 42 W", 42, 630, 0, 2000, 12),
    "fc15": ("Fluorescente compacta 15 W", 15, 850, 0, 6000, 12),
    "fc25": ("Fluorescente compacta 25 W", 25, 1500, 0, 8000, 18),
    "ft20": ("Fluorescente tubular 20 W", 20, 1050, 5, 7500, 10),
    "ft40": ("Fluorescente tubular 40 W", 40, 2700, 8, 7500, 12),
}
# LEDs: nome, potência (W), luz (lm), vida (h), preço (R$)
LAMP_LED = {
    "b9": ("Bulbo LED 9 W", 9, 850, 15000, 10),
    "b12": ("Bulbo LED 12 W", 12, 1100, 15000, 14),
    "b15": ("Bulbo LED 15 W", 15, 1500, 15000, 20),
    "t9": ("Tubo LED 9 W (60 cm)", 9, 900, 25000, 18),
    "t18": ("Tubo LED 18 W (120 cm)", 18, 2000, 25000, 35),
    "p18": ("Plafon LED 18 W", 18, 1650, 25000, 45),
}
# Cômodos que já têm LED: as mesmas lâmpadas da lista de LEDs, com a chave "l" + chave do LED.
# Nesses cômodos as lâmpadas ficam; só se acrescentam LEDs se faltar luz.
for _k, (_n, _p, _f, _vida, _preco) in LAMP_LED.items():
    LAMP_HOJE["l" + _k] = (_n, _p, _f, 0, _vida, _preco)
HOJE_LED = {"l" + k for k in LAMP_LED}

# Casa de exemplo: casa hipotética pequena para o estudo de caso (igual à da página HTML)
EXEMPLO = [
    dict(nome="Sala de estar", amb=1, comp=3.5, larg=3.0, pd=2.6, qa=2, tipoA="inc60", tipoL="b15",
         hd=6.0, hp=3.0, hi=1.0, pres=0.0, tmr=0.0, dim=0.0, cctrl=0.0),
    dict(nome="Sala de jantar", amb=1, comp=3.0, larg=2.8, pd=2.6, qa=2, tipoA="inc60", tipoL="b15",
         hd=3.0, hp=2.0, hi=1.0, pres=0.0, tmr=0.0, dim=0.0, cctrl=0.0),
    dict(nome="Cozinha", amb=2, comp=3.0, larg=2.5, pd=2.6, qa=1, tipoA="ft40", tipoL="t18",
         hd=5.0, hp=2.0, hi=1.0, pres=0.0, tmr=0.0, dim=0.0, cctrl=0.0),
    dict(nome="Área de serviço", amb=6, comp=2.0, larg=1.5, pd=2.6, qa=1, tipoA="inc60", tipoL="b9",
         hd=3.0, hp=0.5, hi=0.5, pres=0.0, tmr=1.5, dim=0.0, cctrl=60.0),
    dict(nome="Quarto 1 – suíte", amb=3, comp=3.5, larg=3.0, pd=2.6, qa=2, tipoA="fc25", tipoL="b15",
         hd=4.0, hp=2.0, hi=1.0, pres=0.0, tmr=0.0, dim=0.0, cctrl=0.0),
    dict(nome="Banheiro da suíte", amb=4, comp=2.0, larg=1.5, pd=2.5, qa=1, tipoA="inc60", tipoL="b12",
         hd=2.0, hp=1.0, hi=0.5, pres=0.0, tmr=0.0, dim=0.0, cctrl=0.0),
    dict(nome="Quarto 2", amb=3, comp=3.0, larg=2.8, pd=2.6, qa=1, tipoA="lb9", tipoL="b9",
         hd=4.0, hp=2.0, hi=1.0, pres=0.0, tmr=0.0, dim=0.0, cctrl=0.0),
    dict(nome="Banheiro social", amb=4, comp=2.2, larg=1.5, pd=2.5, qa=1, tipoA="inc60", tipoL="b12",
         hd=2.0, hp=1.0, hi=0.5, pres=30.0, tmr=0.0, dim=0.0, cctrl=90.0),
]
NOVO = dict(nome="Novo cômodo", amb=3, comp=3.0, larg=3.0, pd=2.7, qa=1, tipoA="inc60", tipoL="b12",
            hd=3.0, hp=1.0, hi=1.0, pres=0.0, tmr=0.0, dim=0.0, cctrl=0.0)

# Fator de utilização estimado em função do índice do recinto K
# (luminária de distribuição direta, refletâncias teto/parede/piso ≈ 70/50/20 %)
TABELA_FU = [
    (0.60, 0.40), (0.80, 0.48), (1.00, 0.53), (1.25, 0.59), (1.50, 0.63),
    (2.00, 0.69), (2.50, 0.73), (3.00, 0.76), (4.00, 0.80), (5.00, 0.82),
]

# Fator médio de emissão do SIN (kg CO2/kWh) - ajuste conforme o ano no MCTI
FATOR_EMISSAO = 0.0385
# Tarifa Branca: fração dos dias com ponta e intermediário (≈ 252 dias úteis por ano)
DIAS_UTEIS = 252 / 365


# ---------------------------------------------------------------------------
# Entrada de dados
# ---------------------------------------------------------------------------
def ler_numero(pergunta, padrao=None, minimo=0.0, inteiro=False, maximo=None):
    sufixo = f" [{fmt_padrao(padrao)}]" if padrao is not None else ""
    while True:
        texto = input(f"  {pergunta}{sufixo}: ").strip().replace(",", ".")
        if not texto and padrao is not None:
            valor = padrao
        else:
            try:
                valor = int(texto) if inteiro else float(texto)
            except ValueError:
                print("    ! Valor inválido. Digite um número.")
                continue
        if valor < minimo:
            print(f"    ! O valor deve ser maior ou igual a {fmt_padrao(minimo)}.")
            continue
        if maximo is not None and valor > maximo:
            print(f"    ! O valor deve ser no máximo {fmt_padrao(maximo)}.")
            continue
        return valor


def fmt_padrao(v):
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return str(v).replace(".", ",")


def dica(texto):
    print(f"    ({texto})")


def perguntar_sim(pergunta, padrao=False):
    resp = input(f"  {pergunta} [{'S/n' if padrao else 's/N'}]: ").strip().lower()
    if not resp:
        return padrao
    return resp in ("s", "sim")


def titulo(texto):
    print("\n" + "=" * 72)
    print(f"  {texto}")
    print("=" * 72)


def subtitulo(texto):
    print(f"\n  --- {texto} ---")


def moeda(valor):
    s = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def moeda_s(valor):
    return ("-" if valor <= -0.005 else "") + moeda(abs(valor))


def num(valor, casas=1):
    s = f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s


def pct(valor):
    return f"{num(valor, 0 if float(valor).is_integer() else 1)} %"


def lista(nomes):
    if len(nomes) <= 1:
        return "".join(nomes)
    return ", ".join(nomes[:-1]) + " e " + nomes[-1]


def escolher(titulo_menu, opcoes, padrao):
    """Menu numerado. opcoes = lista de (chave, rótulo); 0 = Outra."""
    print(f"\n  {titulo_menu}")
    for i, (_, rotulo) in enumerate(opcoes, 1):
        print(f"  {i:>2} - {rotulo}")
    print(f"  {0:>2} - Outra (informar os números)")
    chaves = [c for c, _ in opcoes]
    padrao_n = chaves.index(padrao) + 1 if padrao in chaves else 0
    n = ler_numero("Digite o número da opção", padrao_n, 0, inteiro=True, maximo=len(opcoes))
    return "x" if n == 0 else chaves[n - 1]


# ---------------------------------------------------------------------------
# Cálculos luminotécnicos
# ---------------------------------------------------------------------------
def indice_recinto(comprimento, largura, h_util):
    return (comprimento * largura) / (h_util * (comprimento + largura))


def fator_utilizacao(k):
    if k <= TABELA_FU[0][0]:
        return TABELA_FU[0][1]
    if k >= TABELA_FU[-1][0]:
        return TABELA_FU[-1][1]
    for (k1, f1), (k2, f2) in zip(TABELA_FU, TABELA_FU[1:]):
        if k1 <= k <= k2:
            return f1 + (f2 - f1) * (k - k1) / (k2 - k1)


def iluminancia(qtd, fluxo, fu, fm, area):
    return qtd * fluxo * fu * fm / area


def qtd_necessaria(em, area, fluxo, fu, fm):
    return math.ceil(em * area / (fluxo * fu * fm))


def verificar(valor, referencia, maior_melhor=True):
    ok = valor >= referencia if maior_melhor else valor <= referencia
    return "ATENDE" if ok else "NÃO ATENDE"


# ---------------------------------------------------------------------------
# Análise de viabilidade
# ---------------------------------------------------------------------------
def tir(investimento, economia, n):
    """Taxa que zera o VPL (busca por bisseção)."""
    if investimento <= 0 or economia <= 0 or economia * n <= investimento:
        return None

    def vpl(r):
        return -investimento + economia * (1 - (1 + r) ** -n) / r

    lo, hi = 1e-9, 1.0
    while vpl(hi) > 0 and hi < 1e4:
        hi *= 2
    for _ in range(200):
        meio = (lo + hi) / 2
        if vpl(meio) > 0:
            lo = meio
        else:
            hi = meio
    return (lo + hi) / 2


def viabilidade(investimento, economia, k, n):
    """Fluxo de caixa: ano 0 = investimento, anos 1..n = economia na conta."""
    saldo = saldo_d = vpl = -investimento
    pb_desc = None
    anos = [(0, -investimento, -investimento, saldo, saldo_d)]
    for t in range(1, n + 1):
        fd = economia / (1 + k) ** t
        if pb_desc is None and economia > 0 and saldo_d < 0 <= saldo_d + fd:
            pb_desc = t - 1 + (-saldo_d) / fd
        saldo += economia
        saldo_d += fd
        vpl += fd
        anos.append((t, economia, fd, saldo, saldo_d))
    if investimento == 0 and economia > 0:
        pb_desc = 0.0
    return {"anos": anos, "vpl": vpl, "pb_desc": pb_desc,
            "tir": tir(investimento, economia, n)}


# ---------------------------------------------------------------------------
# Cálculo de um cômodo e da casa
# ---------------------------------------------------------------------------
def calc_comodo(v, g):
    r = dict(v)
    r["area"] = v["comp"] * v["larg"]
    r["h"] = v["pd"] - g["plano"]
    r["k"] = indice_recinto(v["comp"], v["larg"], r["h"])
    r["fu"] = round(fator_utilizacao(r["k"]) * 100) / 100
    r["eA"] = iluminancia(v["qa"], v["fa"], r["fu"], g["fm"], r["area"])
    r["atA"] = r["eA"] >= v["em"]
    r["led"] = bool(v.get("led"))
    if r["led"]:
        # Já é LED: as lâmpadas de hoje ficam e só entram LEDs novos se faltar luz
        r["mant"] = v["qa"]
        falta = v["em"] * r["area"] / (r["fu"] * g["fm"]) - v["qa"] * v["fa"]
        r["novos"] = 0 if r["atA"] else max(0, math.ceil(falta / v["fl"] - 1e-9))
    else:
        r["mant"] = 0
        r["novos"] = qtd_necessaria(v["em"], r["area"], v["fl"], r["fu"], g["fm"])
    r["ql"] = r["mant"] + r["novos"]
    r["eL"] = (r["mant"] * v["fa"] + r["novos"] * v["fl"]) * r["fu"] * g["fm"] / r["area"]
    r["atL"] = r["eL"] >= v["em"]
    # Potência de hoje inclui o reator; o LED não usa reator
    r["potA"] = v["qa"] * (v["pa"] + v["reat"])
    r["potL"] = r["mant"] * (v["pa"] + v["reat"]) + r["novos"] * v["pl"]
    # Sensores: cortam horas acesas (presença, temporizador) e potência (dimmer)
    if not g["ctrl"]:
        r.update(pres=0.0, tmr=0.0, dim=0.0, cctrl=0.0)
    r["temCtrl"] = r["pres"] > 0 or r["tmr"] > 0 or r["dim"] > 0
    r["fH"] = (v["hd"] - r["tmr"]) / v["hd"] * (1 - r["pres"] / 100)
    r["fP"] = 1 - r["dim"] / 100
    r["potC"] = r["potL"] * r["fP"]
    r["horas"] = v["hd"] * g["da"]
    r["horasC"] = r["horas"] * r["fH"]
    r["kwhA"] = r["potA"] * r["horas"] / 1000
    r["kwhS"] = r["potL"] * r["horas"] / 1000
    r["kwhL"] = r["potC"] * r["horasC"] / 1000

    def custo(p_w, f):
        """Custo anual. Na Tarifa Branca separa ponta, intermediário e fora de
        ponta; só os dias úteis têm ponta e intermediário."""
        tot = p_w * r["horas"] * f / 1000
        if not g["th"]:
            return {"c": tot * g["tar"]}
        p = p_w * v["hp"] * g["da"] * DIAS_UTEIS * f / 1000
        i = p_w * v["hi"] * g["da"] * DIAS_UTEIS * f / 1000
        fo = tot - p - i
        return {"p": p, "i": i, "f": fo, "c": p * g["tp"] + i * g["ti"] + fo * g["tf"]}

    c_a, c_s, c_l = custo(r["potA"], 1), custo(r["potL"], 1), custo(r["potC"], r["fH"])
    r["custoA"], r["custoS"], r["custoL"] = c_a["c"], c_s["c"], c_l["c"]
    if g["th"]:
        r.update(pA=c_a["p"], iA=c_a["i"], fA=c_a["f"], pL=c_l["p"], iL=c_l["i"], fL=c_l["f"])
    # Manutenção: lâmpadas que queimam por ano × (preço da lâmpada + mão de obra)
    # (num cômodo que já é LED, as lâmpadas mantidas seguem com a vida e o preço de hoje)
    q_h = r["mant"] / v["vidaA"] + r["novos"] / v["vidaL"]
    c_h = (r["mant"] / v["vidaA"] * (v["rep"] + g["inst"])
           + r["novos"] / v["vidaL"] * (v["preco"] + g["inst"]))
    r["trocA"] = v["qa"] * r["horas"] / v["vidaA"]
    r["trocS"] = q_h * r["horas"]
    r["trocL"] = q_h * r["horasC"]
    r["manA"] = r["trocA"] * (v["rep"] + g["inst"])
    r["manS"] = c_h * r["horas"]
    r["manL"] = c_h * r["horasC"]
    r["econE"] = r["custoA"] - r["custoL"]
    r["econM"] = r["manA"] - r["manL"]
    r["econ"] = r["econE"] + r["econM"]
    r["econS"] = (r["custoA"] - r["custoS"]) + (r["manA"] - r["manS"])
    r["econCtrl"] = r["econ"] - r["econS"]
    r["invLed"] = r["novos"] * (v["preco"] + g["inst"])
    r["inv"] = r["invLed"] + r["cctrl"]
    # Já é LED, tem luz suficiente e não tem sensor: não há nada a fazer
    r["nada"] = r["led"] and r["novos"] == 0 and r["inv"] == 0 and not r["temCtrl"]
    r["payback"] = r["inv"] / r["econ"] if r["econ"] > 0 else None
    r["pbCtrl"] = (r["cctrl"] / r["econCtrl"]
                   if r["temCtrl"] and r["econCtrl"] > 0 and r["cctrl"] > 0 else None)
    r["kwhE"] = r["kwhA"] - r["kwhL"]
    vidas = ([v["vidaL"]] if r["novos"] else []) + ([v["vidaA"]] if r["mant"] else [])
    r["vida"] = min(vidas or [v["vidaL"]]) / r["horasC"]
    r["vidaAnosA"] = v["vidaA"] / r["horas"]
    # Troca direta: uma LED no lugar de cada lâmpada de hoje, sem sensores
    # (num cômodo que já é LED, nada muda)
    if r["led"]:
        r.update(qD=v["qa"], eD=r["eA"], potD=r["potA"], kwhD=r["kwhA"],
                 custoD=r["custoA"], manD=r["manA"], invD=0.0)
    else:
        r["qD"] = v["qa"]
        r["eD"] = v["qa"] * v["fl"] * r["fu"] * g["fm"] / r["area"]
        r["potD"] = v["qa"] * v["pl"]
        r["kwhD"] = r["potD"] * r["horas"] / 1000
        r["custoD"] = custo(r["potD"], 1)["c"]
        r["manD"] = v["qa"] / v["vidaL"] * (v["preco"] + g["inst"]) * r["horas"]
        r["invD"] = v["qa"] * (v["preco"] + g["inst"])
    r["atD"] = r["eD"] >= v["em"]
    r["econD"] = (r["custoA"] - r["custoD"]) + (r["manA"] - r["manD"])
    return r


SOMA = ["area", "qa", "ql", "novos","potA", "potL", "potC", "kwhA", "kwhS", "kwhL", "custoA", "custoS",
        "custoL", "trocA", "trocS", "trocL", "manA", "manS", "manL", "econE", "econM", "econ",
        "econS", "econCtrl", "invLed", "cctrl", "inv", "pA", "iA", "fA", "pL", "iL", "fL",
        "qD", "potD", "kwhD", "custoD", "manD", "invD", "econD"]


def totais(rs, g):
    t = {k: sum(r.get(k, 0) for r in rs) for k in SOMA}
    t["N"] = len(rs)
    t["nAtA"] = sum(1 for r in rs if r["atA"])
    t["nAtL"] = sum(1 for r in rs if r["atL"])
    t["nAtD"] = sum(1 for r in rs if r["atD"])
    t["pbD"] = t["invD"] / t["econD"] if t["econD"] > 0 else None
    t["kwhE"] = t["kwhA"] - t["kwhL"]
    t["reducao"] = t["kwhE"] / t["kwhA"] * 100 if t["kwhA"] else 0
    t["reducaoS"] = (t["kwhA"] - t["kwhS"]) / t["kwhA"] * 100 if t["kwhA"] else 0
    t["co2"] = t["kwhE"] * FATOR_EMISSAO
    t["payback"] = t["inv"] / t["econ"] if t["econ"] > 0 else None
    t["pbS"] = t["invLed"] / t["econS"] if t["econS"] > 0 else None
    t["temCtrl"] = any(r["temCtrl"] for r in rs)
    t["pbCtrl"] = (t["cctrl"] / t["econCtrl"]
                   if t["temCtrl"] and t["econCtrl"] > 0 and t["cctrl"] > 0 else None)
    t["vf"] = viabilidade(t["inv"], t["econ"], g["tma"] / 100, g["n"])
    t["vidaMin"] = min(r["vida"] for r in rs)
    t["vidaMax"] = max(r["vida"] for r in rs)
    t["vidaAMin"] = min(r["vidaAnosA"] for r in rs)
    t["vidaAMax"] = max(r["vidaAnosA"] for r in rs)
    return t


def ordem_prioridade(rs):
    com = sorted((r for r in rs if r["payback"] is not None), key=lambda r: r["payback"])
    sem = sorted((r for r in rs if r["payback"] is None and not r["nada"]), key=lambda r: -r["econ"])
    return com + sem + [r for r in rs if r["nada"]]


# ---------------------------------------------------------------------------
# Perguntas
# ---------------------------------------------------------------------------
def ler_comodo(i, d, g):
    titulo(f"CÔMODO {i}")
    v = {}
    v["nome"] = input(f"  Nome do cômodo [{d['nome']}]: ").strip() or d["nome"]
    print("\n  Para que o cômodo é usado?")
    for cod, (nome, em, _, _) in AMBIENTES.items():
        print(f"  {cod:>2} - {nome:<36} {em} lux")
    print(f"  {0:>2} - Outro uso (informar manualmente)")
    op = ler_numero("Digite o número da opção", d["amb"], 0, inteiro=True, maximo=len(AMBIENTES))
    if op == 0:
        v["uso"] = "uso informado"
        v["em"] = ler_numero("Luz recomendada (lux)", 150.0, 1)
        dica("use 80 se não souber")
        v["raN"] = ler_numero("Fidelidade de cor mínima (IRC)", 80.0, 1)
        dica("0 = não se aplica (casas)")
        v["ugrN"] = ler_numero("Ofuscamento máximo (UGR)", 0.0, 0)
    else:
        v["uso"], v["em"], v["ugrN"], v["raN"] = AMBIENTES[op]
    print(f"    -> a luz recomendada é de pelo menos {v['em']} lux neste cômodo")

    print()
    v["comp"] = ler_numero("Comprimento (m)", d["comp"], 0.1)
    v["larg"] = ler_numero("Largura (m)", d["larg"], 0.1)
    dica("em casas, cerca de 2,5 a 2,8 m")
    v["pd"] = ler_numero("Altura do chão até o teto (m)", d["pd"], g["plano"] + 0.3)

    print()
    dica("conte lâmpadas, não luminárias: uma calha pode ter 2 tubos")
    v["qa"] = ler_numero("Quantas lâmpadas tem hoje?", d["qa"], 0, inteiro=True)
    v["tipoA"] = escolher("Que lâmpada é?",
                          [(k, p[0] + (" (já é LED)" if k in HOJE_LED else ""))
                           for k, p in LAMP_HOJE.items()], d["tipoA"])
    if v["tipoA"] == "x":
        v["led"] = perguntar_sim("Essa lâmpada já é LED?")
        v["pa"] = ler_numero("Potência da lâmpada (W)", 9.0 if v["led"] else 60.0, 0.1)
        v["fa"] = ler_numero("Luz da lâmpada (lúmens)", 850.0 if v["led"] else 800.0, 1)
        v["reat"] = 0.0
        if not v["led"]:
            dica("só em tubo fluorescente; sem reator = 0")
            v["reat"] = ler_numero("Gasto do reator por lâmpada (W)", 0.0, 0)
        v["vidaA"] = ler_numero("Quanto dura (horas)", 15000.0 if v["led"] else 1000.0, 100)
        v["rep"] = ler_numero("Preço para repor (R$)", 10.0 if v["led"] else 6.0, 0)
    else:
        v["led"] = v["tipoA"] in HOJE_LED
        _, v["pa"], v["fa"], v["reat"], v["vidaA"], v["rep"] = LAMP_HOJE[v["tipoA"]]

    if v["led"]:
        print("    -> já é LED: estas lâmpadas ficam. Só entram LEDs novos se faltar luz.")
    # Num cômodo que já é LED, o LED sugerido para acrescentar é o mesmo modelo
    padrao_l = v["tipoA"][1:] if v["tipoA"] in HOJE_LED else d["tipoL"]
    v["tipoL"] = escolher("Se faltar luz, qual LED acrescentar?" if v["led"] else
                          "Qual LED vai entrar?",
                          [(k, p[0]) for k, p in LAMP_LED.items()], padrao_l)
    if v["tipoL"] == "x":
        v["pl"] = ler_numero("Potência do LED (W)", 12.0, 0.1)
        v["fl"] = ler_numero("Luz do LED (lúmens)", 1100.0, 1)
        v["vidaL"] = ler_numero("Quanto dura o LED (horas)", 15000.0, 100)
        v["preco"] = ler_numero("Preço de cada LED (R$)", 14.0, 0)
    else:
        _, v["pl"], v["fl"], v["vidaL"], v["preco"] = LAMP_LED[v["tipoL"]]

    print()
    dica("some todos os períodos do dia")
    v["hd"] = ler_numero("Horas acesas por dia", d["hd"], 0.1, maximo=24)
    v["hp"] = v["hi"] = 0.0
    if g["th"]:
        while True:
            dica("ponta: em geral das 18h às 21h")
            v["hp"] = ler_numero("Dessas, horas na ponta", d["hp"], 0, maximo=3)
            dica("intermediário: 1 h antes e 1 h depois da ponta")
            v["hi"] = ler_numero("Horas no intermediário", d["hi"], 0, maximo=2)
            if v["hp"] + v["hi"] <= v["hd"]:
                break
            print("    ! Ponta + intermediário não pode passar das horas acesas por dia.")

    v["pres"] = v["tmr"] = v["dim"] = v["cctrl"] = 0.0
    if g["ctrl"]:
        tem = d["pres"] > 0 or d["tmr"] > 0 or d["dim"] > 0
        if perguntar_sim("Usar sensores neste cômodo?", padrao=tem):
            dica("banheiro, corredor e garagem: 30 a 50 %; 0 = sem sensor")
            v["pres"] = ler_numero("Sensor de presença: tempo com a luz acesa e o cômodo "
                                   "vazio (%)", d["pres"], 0, maximo=90)
            dica("comum em área externa; 0 = sem temporizador")
            while True:
                v["tmr"] = ler_numero("Temporizador: horas por dia de luz esquecida acesa",
                                      d["tmr"], 0)
                if v["tmr"] < v["hd"]:
                    break
                print("    ! Precisa ser menor que as horas acesas por dia.")
            dica("sala e quarto: 15 a 30 %; 0 = sem dimmer")
            v["dim"] = ler_numero("Dimmer: quanto a luz fica mais fraca, em média (%)",
                                  d["dim"], 0, maximo=90)
            dica("sensor de presença ≈ R$ 60 a 120; dimmer ≈ R$ 80 a 150")
            v["cctrl"] = ler_numero("Custo dos sensores deste cômodo, com instalação (R$)",
                                    d["cctrl"], 0)
    return v


def main():
    titulo("CALCULADORA DE RETROFIT DE ILUMINAÇÃO DA CASA")
    print("  Retrofit não é só trocar a lâmpada que queimou: é refazer a")
    print("  iluminação de cada cômodo, com a luz recomendada, menos")
    print("  manutenção, sensores, e um investimento que se paga.\n")
    print("  Responda com os dados da sua casa. O número entre colchetes é um")
    print("  exemplo: pressione ENTER para usá-lo. Só com ENTER, o programa")
    print("  calcula a casa de exemplo (a mesma da página HTML).")

    g = {}
    # 1. A casa ---------------------------------------------------------------
    titulo("1. A CASA")
    dica("só para identificar a casa no relatório")
    g["local"] = input("  Qual é a casa? (nome ou endereço) [Casa hipotética (estudo de caso)]: ").strip() \
        or "Casa hipotética (estudo de caso)"
    dica("casa onde se mora: 365; casa de praia ou de fim de semana: bem menos")
    g["da"] = ler_numero("Dias de uso por ano", 365, 1, inteiro=True, maximo=366)

    # 2. Conta de luz ---------------------------------------------------------
    titulo("2. CONTA DE LUZ")
    g["th"] = perguntar_sim("A casa tem Tarifa Branca (preço muda com o horário)?")
    if g["th"]:
        print("  Nos dias úteis, o kWh custa mais no início da noite (ponta, 3 horas,")
        print("  em geral das 18h às 21h) e um pouco mais na hora antes e na hora")
        print("  depois (intermediário). No resto do dia, nos fins de semana e nos")
        print("  feriados vale o preço mais barato (fora de ponta).")
        dica("os três preços vêm na conta ou no site da distribuidora, com impostos")
        g["tp"] = ler_numero("Preço do kWh na ponta (R$)", 1.90, 0.01)
        g["ti"] = ler_numero("Preço do kWh no intermediário (R$)", 1.20, 0.01)
        g["tf"] = ler_numero("Preço do kWh fora de ponta (R$)", 0.80, 0.01)
    else:
        dica("na conta de luz: divida o valor total a pagar pelo consumo do mês em kWh")
        g["tar"] = ler_numero("Preço do kWh com impostos (R$)", 0.95, 0.01)

    # 3. Instalação, sensores e ajustes -----------------------------------------
    titulo("3. INSTALAÇÃO E SENSORES")
    dica("vale para a troca e para cada reposição; use 0 se você mesmo for trocar")
    g["inst"] = ler_numero("Mão de obra por lâmpada (R$)", 10.0, 0)
    g["ctrl"] = perguntar_sim("Usar sensores e controles nos cômodos?", padrao=True)
    g["plano"], g["fm"], g["ral"], g["ugrl"] = 0.75, 0.80, 80.0, 0.0
    if perguntar_sim("Deseja alterar os ajustes técnicos (altura medida, Fm, IRC, UGR)?"):
        dica("plano de trabalho: altura de uma mesa ou bancada")
        g["plano"] = ler_numero("Altura onde a luz é medida (m)", 0.75, 0, maximo=1.5)
        dica("Fm: perda de luz por sujeira e desgaste")
        g["fm"] = ler_numero("Fator de manutenção (Fm)", 0.80, 0.1, maximo=1)
        g["ral"] = ler_numero("Fidelidade de cor dos LEDs (IRC)", 80.0, 1)
        dica("só em catálogos; 0 = não sei; só conta no escritório")
        g["ugrl"] = ler_numero("Ofuscamento das luminárias (UGR)", 0.0, 0)

    # 4. Cômodos ----------------------------------------------------------------
    titulo("4. CÔMODOS")
    print("  Cada cômodo tem o tamanho, as lâmpadas de hoje, o LED que vai")
    print("  entrar e quantas horas a luz fica acesa.")
    n_com = ler_numero("Quantos cômodos?", len(EXEMPLO), 1, inteiro=True, maximo=40)
    lidos = []
    for i in range(n_com):
        padrao = EXEMPLO[i] if i < len(EXEMPLO) else NOVO
        lidos.append(ler_comodo(i + 1, padrao, g))

    # 5. Análise do investimento -------------------------------------------------
    titulo("5. ANÁLISE DO INVESTIMENTO")
    dica("taxa mínima de atratividade (TMA): rendimento de uma aplicação segura")
    g["tma"] = ler_numero("Quanto o dinheiro renderia aplicado (% ao ano)", 12.0, 0)
    g["n"] = ler_numero("Por quantos anos analisar", 10, 1, inteiro=True, maximo=50)

    rs = [calc_comodo(v, g) for v in lidos]
    t = totais(rs, g)
    relatorio(g, rs, t)
    titulo("DIAGNÓSTICO DA CASA")
    diagnostico(g, rs, t)
    print()


# ---------------------------------------------------------------------------
# Relatório
# ---------------------------------------------------------------------------
def tempo_txt(anos):
    meses = round(anos * 12)
    if anos < 1:
        return f"cerca de {meses} {'mês' if meses == 1 else 'meses'}"
    return f"{num(anos, 1)} anos (cerca de {meses} meses)"


def pb_txt(v):
    return "—" if v is None else f"{num(v, 2)} anos"


def relatorio(g, rs, t):
    vf = t["vf"]
    titulo("RESULTADOS DA CASA")
    print(f"  Casa: {g['local']}")
    print(f"  Cômodos: {t['N']}  |  Área iluminada: {num(t['area'], 1)} m²")
    print(f"  Nesse uso, os LEDs duram de {num(t['vidaMin'], 1)} a {num(t['vidaMax'], 1)} "
          "anos, conforme o cômodo.")

    subtitulo("Cômodo por cômodo: luz (hoje -> com LED)")
    print(f"  {'CÔMODO':<20}{'ÁREA m²':>8}{'MÍN. lux':>9}{'LUZ lux':>14}{'LÂMPADAS':>10}  LUZ OK?")
    for r in rs:
        luz = f"{num(r['eA'], 0)}->{num(r['eL'], 0)}"
        lamp = f"{r['qa']}->{r['ql']}"
        print(f"  {r['nome'][:19]:<20}{num(r['area'], 1):>8}{num(r['em'], 0):>9}{luz:>14}"
              f"{lamp:>10}  {verificar(r['eA'], r['em'])} -> {verificar(r['eL'], r['em'])}")

    subtitulo("Cômodo por cômodo: energia e dinheiro (hoje -> com LED)")
    print(f"  {'CÔMODO':<20}{'POTÊNCIA W':>13}{'kWh/ANO':>13}{'CONTA R$/ANO':>15}{'ECONOMIA/ANO':>15}")
    for r in rs:
        print(f"  {r['nome'][:19]:<20}{num(r['potA'], 0) + '->' + num(r['potL'], 0):>13}"
              f"{num(r['kwhA'], 0) + '->' + num(r['kwhL'], 0):>13}"
              f"{num(r['custoA'], 0) + '->' + num(r['custoL'], 0):>15}{moeda_s(r['econ']):>15}")
    print(f"  {'CASA TODA':<20}{num(t['potA'], 0) + '->' + num(t['potL'], 0):>13}"
          f"{num(t['kwhA'], 0) + '->' + num(t['kwhL'], 0):>13}"
          f"{num(t['custoA'], 0) + '->' + num(t['custoL'], 0):>15}{moeda_s(t['econ']):>15}")

    subtitulo("Por onde começar a troca (retorno mais rápido primeiro)")
    print(f"  {'CÔMODO':<22}{'INVESTIMENTO':>14}{'ECONOMIA/ANO':>15}  SE PAGA EM")
    for i, r in enumerate(ordem_prioridade(rs), 1):
        pb = ("já é LED: nada a trocar" if r["nada"] else
              "sem retorno" if r["payback"] is None else tempo_txt(r["payback"]))
        print(f"  {(str(i) + '. ' + r['nome'])[:21]:<22}{moeda(r['inv']):>14}"
              f"{moeda_s(r['econ']):>15}  {pb}")

    subtitulo("Casa toda: três caminhos comparados")
    print(f"  {'':<38}{'HOJE':>14}{'TROCA DIRETA':>14}{'OTIMIZADA':>14}")

    def pbc(pb, inv):
        return "-" if inv <= 0 else ("sem retorno" if pb is None else tempo_curto(pb))

    linhas = [
        ("Cômodos com a luz recomendada", f"{t['nAtA']} de {t['N']}",
         f"{t['nAtD']} de {t['N']}", f"{t['nAtL']} de {t['N']}"),
        ("Quantidade de lâmpadas", str(t["qa"]), str(t["qD"]), str(t["ql"])),
        ("Potência de todas as lâmpadas (W)", num(t["potA"], 0), num(t["potD"], 0), num(t["potL"], 0)),
        ("Potência por m² (W/m²)", num(t["potA"] / t["area"], 2), num(t["potD"] / t["area"], 2),
         num(t["potL"] / t["area"], 2)),
        ("Energia gasta (kWh por ano)", num(t["kwhA"], 0), num(t["kwhD"], 0), num(t["kwhL"], 0)),
        ("Conta de luz da iluminação (R$/ano)", moeda(t["custoA"]), moeda(t["custoD"]), moeda(t["custoL"])),
        ("Conta de luz da iluminação (R$/mês)", moeda(t["custoA"] / 12), moeda(t["custoD"] / 12),
         moeda(t["custoL"] / 12)),
        ("Reposição de lâmpadas (R$/ano)", moeda(t["manA"]), moeda(t["manD"]), moeda(t["manL"])),
        ("Gasto total (R$ por ano)", moeda(t["custoA"] + t["manA"]), moeda(t["custoD"] + t["manD"]),
         moeda(t["custoL"] + t["manL"])),
        ("Investimento (R$)", "-", moeda(t["invD"]), moeda(t["inv"])),
        ("Economia por ano (R$)", "-", moeda_s(t["econD"]), moeda_s(t["econ"])),
        ("Se paga em", "-", pbc(t["pbD"], t["invD"]), pbc(t["payback"], t["inv"])),
    ]
    for rot, a, b, c in linhas:
        print(f"  {rot:<38}{a:>14}{b:>14}{c:>14}")
    print("  Troca direta: uma LED no lugar de cada lâmpada de hoje, sem sensores.")
    print("  Otimizada: LEDs na quantidade certa para a luz recomendada"
          + (", com os sensores." if t["temCtrl"] else "."))
    ra_max = max(r["raN"] for r in rs)
    print(f"\n  Fidelidade de cor dos LEDs (IRC): {num(g['ral'], 0)} (mín. {num(ra_max, 0)}) -> "
          f"{verificar(g['ral'], ra_max)}")
    com_ugr = [r for r in rs if r["ugrN"] > 0]
    if com_ugr:
        ugr_min = min(r["ugrN"] for r in com_ugr)
        if g["ugrl"] > 0:
            print(f"  Ofuscamento no escritório (UGR): {num(g['ugrl'], 0)} (máx. {num(ugr_min, 0)}) -> "
                  f"{verificar(g['ugrl'], ugr_min, maior_melhor=False)}")
        else:
            print("  Ofuscamento no escritório (UGR): não informado (ver catálogo do fabricante)")
    if t["kwhE"] >= 0:
        print(f"\n  Energia economizada : {num(t['kwhE'], 0)} kWh por ano ({num(t['reducao'], 1)} %)")
    else:
        print(f"\n  Energia a mais      : {num(-t['kwhE'], 0)} kWh por ano "
              f"({num(-t['reducao'], 1)} %, porque haverá mais luz)")
    print(f"  Economia por ano    : {moeda(t['econ'])} ({moeda(t['econ'] / 12)} por mês)")
    print(f"                        conta de luz {moeda_s(t['econE'])} + "
          f"reposição {moeda_s(t['econM'])}")
    print(f"  CO2 evitado         : {num(t['co2'], 1)} kg por ano")

    def faixa(a, b):
        return num(a, 1) if abs(a - b) < 0.05 else f"{num(a, 1)} a {num(b, 1)}"

    subtitulo("Ciclo de vida: troca de lâmpadas queimadas (casa toda)")
    print(f"  {'':<38}{'HOJE':>14}{'COM LED':>14}")
    print(f"  {'Quanto cada lâmpada dura (anos)':<38}{faixa(t['vidaAMin'], t['vidaAMax']):>14}"
          f"{faixa(t['vidaMin'], t['vidaMax']):>14}")
    print(f"  {'Lâmpadas que queimam por ano':<38}{num(t['trocA'], 1):>14}{num(t['trocL'], 1):>14}")
    print(f"  {'Gasto com reposição (R$/ano)':<38}{moeda(t['manA']):>14}{moeda(t['manL']):>14}")

    subtitulo("Sensores e controles")
    com_ctrl = [r for r in rs if r["temCtrl"] or r["cctrl"] > 0]
    if not g["ctrl"]:
        print("  Não incluídos nesta simulação.")
    elif not com_ctrl:
        print("  Nenhum cômodo tem sensor.")
    else:
        print(f"  {'CÔMODO':<20}{'SENSORES':<26}{'kWh A MENOS':>12}{'R$/ANO':>12}{'CUSTO':>12}")
        for r in com_ctrl:
            it = []
            if r["pres"] > 0:
                it.append(f"presença {pct(r['pres'])}")
            if r["tmr"] > 0:
                it.append(f"temp. {num(r['tmr'], 1)} h")
            if r["dim"] > 0:
                it.append(f"dimmer {pct(r['dim'])}")
            print(f"  {r['nome'][:19]:<20}{', '.join(it)[:25]:<26}{num(r['kwhS'] - r['kwhL'], 0):>12}"
                  f"{moeda(r['econCtrl']):>12}{moeda(r['cctrl']):>12}")
        print(f"\n  {'Casa toda':<38}{'SÓ LED':>14}{'LED+SENSORES':>14}")
        print(f"  {'Energia gasta (kWh por ano)':<38}{num(t['kwhS'], 0):>14}{num(t['kwhL'], 0):>14}")
        print(f"  {'Economia de energia vs. hoje':<38}{num(t['reducaoS'], 1) + ' %':>14}"
              f"{num(t['reducao'], 1) + ' %':>14}")
        print(f"  {'Conta de luz (R$ por ano)':<38}{moeda(t['custoS']):>14}{moeda(t['custoL']):>14}")
        print(f"  {'Reposição de lâmpadas (R$/ano)':<38}{moeda(t['manS']):>14}{moeda(t['manL']):>14}")
        print(f"  {'Investimento':<38}{moeda(t['invLed']):>14}{moeda(t['inv']):>14}")
        print(f"  {'Se paga em':<38}{pb_txt(t['pbS']):>14}{pb_txt(t['payback']):>14}")
        if t["econCtrl"] > 0:
            print(f"\n  Os sensores somam {moeda(t['econCtrl'])} por ano à economia do LED"
                  + (f" e custam {moeda(t['cctrl'])}"
                     + (f": sozinhos, se pagam em {num(t['pbCtrl'], 2)} anos."
                        if t["pbCtrl"] is not None else ".")
                     if t["cctrl"] > 0 else ", sem custo extra."))

    subtitulo("Custo da troca")
    print(f"  Lâmpadas LED        : {moeda(t['invLed'])} ({t['novos']} lâmpadas novas, "
          "com mão de obra)")
    if t["cctrl"] > 0:
        print(f"  Sensores            : {moeda(t['cctrl'])}")
        print(f"  Investimento total  : {moeda(t['inv'])}")
    if t["payback"] is None:
        print("  Se paga em          : nunca (não há economia na conta nem na reposição)")
    else:
        print(f"  Se paga em          : {num(t['payback'], 2)} anos "
              f"(cerca de {round(t['payback'] * 12)} meses)")
        print(f"  {'Saldo em ' + str(g['n']) + ' anos':<20}: "
              f"{moeda_s(t['econ'] * g['n'] - t['inv'])} (já descontada a compra)")

    if g["th"]:
        subtitulo("Tarifa Branca: economia por horário (casa toda)")
        print(f"  {'':<26}{'HOJE':>10}{'COM LED':>10}{'ECONOMIA':>10}{'R$/ANO':>14}")
        for rotulo, a, b, preco in (
                ("Ponta (kWh por ano)", t["pA"], t["pL"], g["tp"]),
                ("Intermediário (kWh/ano)", t["iA"], t["iL"], g["ti"]),
                ("Fora de ponta (kWh/ano)", t["fA"], t["fL"], g["tf"])):
            print(f"  {rotulo:<26}{num(a, 0):>10}{num(b, 0):>10}"
                  f"{num(a - b, 0):>10}{moeda((a - b) * preco):>14}")
        print(f"  {'Total na conta (R$/ano)':<26}{'':>30}{moeda(t['econE']):>14}")

    subtitulo("Vale mais que deixar o dinheiro aplicado?")
    print(f"  Comparação com aplicar o mesmo dinheiro a {pct(g['tma'])} ao ano, por {g['n']} anos.")
    print("  Payback descontado  : "
          + (f"{num(vf['pb_desc'], 2)} anos" if vf["pb_desc"] is not None
             else f"não se paga em {g['n']} anos"))
    print(f"  {'VPL em ' + str(g['n']) + ' anos':<20}: {moeda_s(vf['vpl'])} "
          + ("(positivo: a troca rende mais que a aplicação)" if vf["vpl"] >= 0
             else "(negativo: a aplicação rende mais)"))
    print("  TIR                 : "
          + (f"{num(vf['tir'] * 100, 1)} % ao ano" if vf["tir"] is not None
             else "não existe (a troca não se paga no prazo)"))
    print(f"\n  {'ANO':>4}{'FLUXO':>16}{'DESCONTADO':>16}{'SALDO':>16}{'SALDO DESC.':>16}")
    for ano, f, fd, s, sd in vf["anos"]:
        print(f"  {ano:>4}{moeda_s(f):>16}{moeda_s(fd):>16}{moeda_s(s):>16}{moeda_s(sd):>16}")

    subtitulo("Memorial de cálculo por cômodo")
    for r in rs:
        print(f"\n  {r['nome']}")
        print(f"    K = {num(r['comp'], 2)}·{num(r['larg'], 2)} / [{num(r['h'], 2)}·({num(r['comp'], 2)}"
              f" + {num(r['larg'], 2)})] = {num(r['k'], 2)}  ->  Fu = {num(r['fu'], 2)}")
        print(f"    E hoje = {r['qa']}·{num(r['fa'], 0)}·{num(r['fu'], 2)}·{num(g['fm'], 2)} / "
              f"{num(r['area'], 2)} = {num(r['eA'], 1)} lx")
        if not r["led"]:
            print(f"    n LED = ⌈{num(r['em'], 0)}·{num(r['area'], 2)} / ({num(r['fl'], 0)}·"
                  f"{num(r['fu'], 2)}·{num(g['fm'], 2)})⌉ = {r['ql']}  ->  E LED = "
                  f"{num(r['eL'], 1)} lx")
            p_led = f"{r['ql']}·{num(r['pl'], 0)}"
        elif r["novos"] == 0:
            print(f"    Já é LED e E hoje ≥ {num(r['em'], 0)} lx: ficam as {r['qa']} lâmpadas, "
                  "nenhuma nova")
            p_led = f"{r['qa']}·{num(r['pa'], 0)}"
        else:
            print(f"    Já é LED: ficam {r['qa']}; novos = ⌈({num(r['em'], 0)}·{num(r['area'], 2)} / "
                  f"({num(r['fu'], 2)}·{num(g['fm'], 2)}) − {r['qa']}·{num(r['fa'], 0)}) / "
                  f"{num(r['fl'], 0)}⌉ = {r['novos']}  ->  E LED = {num(r['eL'], 1)} lx")
            p_led = f"{r['qa']}·{num(r['pa'], 0)} + {r['novos']}·{num(r['pl'], 0)}"
        print(f"    P hoje = {r['qa']}·({num(r['pa'], 0)} + {num(r['reat'], 0)}) = {num(r['potA'], 0)} W"
              f"  |  P LED = {p_led} = {num(r['potL'], 0)} W")
        print(f"    Energia: {num(r['kwhA'], 0)} kWh -> {num(r['kwhL'], 0)} kWh por ano"
              + (f" (sensores: horas x {num(r['fH'], 3)}, potência x {num(r['fP'], 2)})"
                 if r["temCtrl"] else ""))


# ---------------------------------------------------------------------------
# Diagnóstico em linguagem simples (mesmo texto da versão em HTML)
# ---------------------------------------------------------------------------
def paragrafo(texto, recuo="  ", recuo_seguinte=None):
    # Espaço inquebrável em "R$ " para o valor não ser separado do símbolo
    texto = texto.replace("R$ ", "R$ ")
    linhas = textwrap.fill(texto, width=70, initial_indent=recuo,
                           subsequent_indent=recuo_seguinte or recuo)
    print(linhas.replace(" ", " "))


def nome_lamp(tab, k, alt):
    if k not in tab:
        return alt
    nome = tab[k][0]
    return nome[0].lower() + nome[1:]


def tempo_curto(anos):
    meses = round(anos * 12)
    if meses < 24:
        return f"{meses} {'mês' if meses == 1 else 'meses'}"
    return f"{num(anos, 1)} anos"


def diagnostico(g, rs, t):
    vf = t["vf"]
    n_anos, tma = g["n"], g["tma"]
    at_a = t["nAtA"] == t["N"]
    faltam = [r for r in rs if not r["atA"]]
    dif = t["ql"] - t["qa"]
    if dif > 0:
        dif_txt = f"{dif} a mais que hoje"
    elif dif < 0:
        dif_txt = f"{-dif} a menos que hoje"
    else:
        dif_txt = "a mesma quantidade de hoje"

    # Veredito
    if t["payback"] is not None and t["payback"] > 5:
        problema = f"o dinheiro investido demora {tempo_txt(t['payback'])} para voltar"
    else:
        problema = (f"em {n_anos} anos a troca rende menos do que deixar o dinheiro "
                    f"aplicado a {pct(tma)} ao ano")
    if all(r["nada"] for r in rs):
        veredito = "NADA A TROCAR"
        motivo = ("Todos os cômodos já têm lâmpadas LED e a luz recomendada. "
                  "A iluminação da casa já está eficiente.")
    elif t["payback"] is None and not at_a:
        veredito = "TROCAR PARA TER LUZ SUFICIENTE"
        motivo = (f"Hoje falta luz em {len(faltam)} de {t['N']} cômodos. Para resolver é "
                  "preciso pôr mais lâmpadas, e a conta não diminui"
                  + (f" (sobe {moeda(-t['econ'])} por ano)" if t["econ"] < -0.005 else "")
                  + ": a troca não se paga, ela serve para ter a luz recomendada.")
    elif t["payback"] is None:
        veredito = "NÃO COMPENSA TROCAR"
        motivo = ("Com esses dados as lâmpadas LED não diminuem a conta de luz da casa, "
                  "então o dinheiro da troca nunca volta.")
    elif t["payback"] <= 5 and vf["vpl"] >= 0:
        veredito = "RECOMENDADO TROCAR PARA LED"
        motivo = (("Todos os cômodos já têm luz suficiente, mas a troca diminui a conta de luz"
                   if at_a else
                   f"A troca resolve a falta de luz em {len(faltam)} de {t['N']} cômodos e "
                   "ainda diminui a conta de luz")
                  + f". O dinheiro investido volta em {tempo_txt(t['payback'])}.")
    elif not at_a:
        veredito = "TROCAR PARA TER LUZ SUFICIENTE"
        motivo = (f"Hoje falta luz em {len(faltam)} de {t['N']} cômodos e a troca resolve "
                  f"isso, mas {problema}.")
    else:
        veredito = "TROCA POUCO VANTAJOSA"
        motivo = f"A casa já tem luz suficiente em todos os cômodos, e {problema}."
    print(f"  Casa analisada: {g['local']}\n")
    print(f"  >>> {veredito} <<<")
    paragrafo(motivo)

    print("\n  COMO ESTÁ HOJE")
    reat_txt = " (contando o gasto dos reatores)" if any(r["reat"] > 0 for r in rs) else ""
    if at_a:
        situacao = "Todos os cômodos já têm a luz recomendada."
    else:
        situacao = (f"Falta luz em {len(faltam)} de {t['N']} cômodos: "
                    + lista([f"{r['nome']} ({num(r['eA'], 0)} de {num(r['em'], 0)} lux)"
                             for r in faltam])
                    + ". Com pouca luz a vista cansa mais e fica difícil ler, cozinhar e "
                      "fazer tarefas.")
    ja_led = [r["nome"] for r in rs if r["led"]]
    if len(ja_led) == len(rs):
        situacao += " Todos os cômodos já usam LED."
    elif ja_led:
        situacao += (f" {'O cômodo' if len(ja_led) == 1 else 'Os cômodos'} {lista(ja_led)} "
                     f"{'já usa' if len(ja_led) == 1 else 'já usam'} LED.")
    paragrafo(f"A casa tem {t['N']} {'cômodo' if t['N'] == 1 else 'cômodos'} e {num(t['area'], 1)} m² iluminados. Hoje são "
              f"{t['qa']} lâmpadas, que somam {num(t['potA'], 0)} W{reat_txt}. {situacao} "
              f"Essas lâmpadas gastam {num(t['kwhA'], 0)} kWh por ano, o que dá cerca de "
              f"{moeda(t['custoA'])} na conta de luz ({moeda(t['custoA'] / 12)} por mês). "
              f"Por ano queimam cerca de {num(t['trocA'], 1)} lâmpadas, e repor custa "
              f"{moeda(t['manA'])}.")

    print("\n  O QUE MUDA COM LED")
    if all(r["nada"] for r in rs):
        intro = "Nenhuma lâmpada precisa ser trocada. Em cada cômodo:"
    else:
        intro = (
              f"Para ter a luz recomendada em todos os cômodos são necessárias "
              f"{t['ql']} lâmpadas LED ({dif_txt}). Só com a troca, o gasto da casa "
              + (f"cai para {num(t['kwhS'], 0)} kWh por ano ({moeda(t['custoS'])}), uma "
                 f"economia de {num(t['reducaoS'], 1)} %. "
                 if t["reducaoS"] >= 0 else
                 f"sobe para {num(t['kwhS'], 0)} kWh por ano ({moeda(t['custoS'])}), "
                 f"{num(-t['reducaoS'], 1)} % a mais, porque haverá mais luz. ")
              + ("O LED dura mais, então a reposição de lâmpadas queimadas cai para "
                 if t["manS"] < t["manA"] else "A reposição de lâmpadas queimadas fica em ")
              + f"{moeda(t['manS'])} por ano. Em cada cômodo:")
    paragrafo(intro)
    for r in rs:
        antes = f"{r['qa']} × {nome_lamp(LAMP_HOJE, r['tipoA'], 'lâmpada de ' + num(r['pa'], 0) + ' W')}"
        novo = nome_lamp(LAMP_LED, r["tipoL"], "LED de " + num(r["pl"], 0) + " W")
        if r["econ"] > 0.005:
            fim = f"Economia de {moeda(r['econ'])} por ano."
        elif r["econ"] < -0.005:
            fim = (f"A conta deste cômodo sobe {moeda(-r['econ'])} por ano, porque hoje falta "
                   "luz e serão necessárias mais lâmpadas.")
        else:
            fim = ""
        if r["led"] and r["novos"] == 0:
            texto = (f"{r['nome']}: já é LED ({antes}) e tem {num(r['eA'], 0)} lux, o "
                     "suficiente. Não precisa trocar"
                     + (". Só entram os sensores. " + fim if r["temCtrl"] else "."))
        elif r["led"]:
            ficam = ("fica a lâmpada de hoje" if r["qa"] == 1 else
                     f"ficam as {r['qa']} lâmpadas de hoje")
            texto = (f"{r['nome']}: já é LED; {ficam} e "
                     f"{'entra' if r['novos'] == 1 else 'entram'} mais {r['novos']} × {novo}; "
                     f"a luz vai de {num(r['eA'], 0)} para {num(r['eL'], 0)} lux. {fim}")
        else:
            texto = (f"{r['nome']}: {antes} -> {r['ql']} × {novo}; a luz vai de "
                     f"{num(r['eA'], 0)} para {num(r['eL'], 0)} lux. {fim}")
        paragrafo(texto.strip(), "  • ", "    ")

    if t["invD"] > 0:
        print("\n  E SE TROCAR SÓ LÂMPADA POR LÂMPADA?")
        falta_d = t["N"] - t["nAtD"]
        paragrafo(f"Na troca direta (uma LED no lugar de cada lâmpada, sem mexer na quantidade) "
                  f"a casa gastaria {num(t['kwhD'], 0)} kWh por ano, com investimento de "
                  f"{moeda(t['invD'])} e economia de {moeda(t['econD'])} por ano"
                  + (f", que se paga em {tempo_txt(t['pbD'])}" if t["pbD"] is not None else "")
                  + ". "
                  + ((f"Mas nenhum dos {t['N']} cômodos teria a luz recomendada: " if falta_d == t["N"] else
                      f"Mas {falta_d} de {t['N']} {'cômodo continuaria' if falta_d == 1 else 'cômodos continuariam'} "
                      "sem a luz recomendada: ")
                     + "gastar menos não basta, a luz também precisa ser suficiente. "
                     "Por isso o estudo recomenda a solução otimizada."
                     if falta_d > 0 else
                     "Todos os cômodos teriam a luz recomendada, então a troca direta também serve."))

    print("\n  SENSORES E CONTROLES")
    com_ctrl = [r for r in rs if r["temCtrl"]]
    if not g["ctrl"]:
        paragrafo("Não foram incluídos. Sensores de presença, temporizadores e dimmers "
                  "apagam ou diminuem a luz quando ela não é necessária. Responda 's' no "
                  "item 3 para simular.")
    elif not com_ctrl or t["econCtrl"] <= 0:
        paragrafo("Com os valores informados, os sensores não trazem economia além da "
                  "troca para LED.")
    else:
        def itens(r):
            it = []
            if r["pres"] > 0:
                it.append("presença")
            if r["tmr"] > 0:
                it.append("temporizador")
            if r["dim"] > 0:
                it.append("dimmer")
            return f"{r['nome']} ({', '.join(it)})"
        texto = (f"Foram incluídos sensores em {lista([itens(r) for r in com_ctrl])}. Com eles "
                 f"o gasto da casa cai de {num(t['kwhS'], 0)} para {num(t['kwhL'], 0)} kWh por "
                 f"ano, mais {moeda(t['econCtrl'])} de economia por ano")
        if t["cctrl"] > 0:
            texto += f". Os sensores custam {moeda(t['cctrl'])}"
            if t["pbCtrl"] is not None:
                texto += f" e se pagam sozinhos em {tempo_txt(t['pbCtrl'])}"
        texto += (f". No total, a economia de energia chega a {num(t['reducao'], 1)} %."
                  if t["reducao"] >= 0 else
                  f". No total, o gasto de energia fica {num(-t['reducao'], 1)} % maior que "
                  "hoje, porque haverá mais luz.")
        paragrafo(texto)

    print("\n  CUSTO E RETORNO")
    custo = (f"Comprar e instalar os LEDs custa {moeda(t['invLed'])}"
             + (f", mais {moeda(t['cctrl'])} dos sensores: total de {moeda(t['inv'])}"
                if t["cctrl"] > 0 else "")
             + ". ")
    if t["econ"] > 0:
        custo += (f"Por ano, a conta de luz fica {moeda(abs(t['econE']))} "
                  f"{'mais barata' if t['econE'] >= 0 else 'mais cara'} e o gasto com "
                  f"lâmpadas queimadas {'cai' if t['econM'] >= 0 else 'sobe'} "
                  f"{moeda(abs(t['econM']))}: economia total de {moeda(t['econ'])} por ano "
                  f"({moeda(t['econ'] / 12)} por mês). ")
        if g["th"]:
            custo += (f"Com a Tarifa Branca, essa economia vem da ponta "
                      f"({moeda((t['pA'] - t['pL']) * g['tp'])}), do intermediário "
                      f"({moeda((t['iA'] - t['iL']) * g['ti'])}) e do resto do dia "
                      f"({moeda((t['fA'] - t['fL']) * g['tf'])}). ")
        saldo = t["econ"] * n_anos - t["inv"]
        custo += (f"Com essa economia, o valor investido volta em "
                  f"{tempo_txt(t['payback'])}. Em {n_anos} anos, já descontada a compra, "
                  + (f"sobram {moeda(saldo)}. " if saldo >= 0
                     else f"ainda faltam {moeda(-saldo)}. ")
                  + f"A troca também evita {num(t['co2'], 1)} kg de CO2 por ano.")
    else:
        custo += ("Como a conta de luz e a manutenção não ficam mais baratas, não há "
                  "economia para pagar esse valor.")
    if t["inv"] == 0 and t["econ"] <= 0:
        custo = "Não há nada a comprar: a iluminação da casa fica como está."
    paragrafo(custo)

    print("\n  VALE MAIS QUE DEIXAR O DINHEIRO APLICADO?")
    if t["payback"] is None:
        paragrafo("Não há investimento para comparar." if t["inv"] == 0 else
                  "Sem economia na conta de luz, a troca não tem retorno.")
    else:
        aplicado = (f"Se o dinheiro ficasse aplicado, renderia {pct(tma)} ao ano. Levando "
                    "isso em conta, o payback descontado "
                    + (f"é de {tempo_txt(vf['pb_desc'])}" if vf["pb_desc"] is not None
                       else f"passa de {n_anos} anos")
                    + f". O VPL em {n_anos} anos é {moeda_s(vf['vpl'])}: "
                    + ("positivo, então a troca rende mais do que a aplicação."
                       if vf["vpl"] >= 0 else
                       "negativo, então a aplicação renderia mais do que a troca."))
        if vf["tir"] is not None:
            aplicado += (f" A TIR, que é quanto a troca rende por ano, é de "
                         f"{num(vf['tir'] * 100, 1)} %, "
                         f"{'acima' if vf['tir'] * 100 >= tma else 'abaixo'} dos "
                         f"{pct(tma)} da aplicação.")
        paragrafo(aplicado)

    print("\n  POR ONDE COMEÇAR")
    rapidos = [r for r in ordem_prioridade(rs) if r["payback"] is not None][:3]
    sem_ret = [r for r in rs if r["payback"] is None and not r["nada"]]
    nada = [r["nome"] for r in rs if r["nada"]]
    if rapidos:
        comecar = ("Os cômodos em que a troca se paga mais rápido são "
                   + lista([f"{r['nome']} ({tempo_curto(r['payback'])})" for r in rapidos])
                   + ". Se não der para trocar tudo de uma vez, comece por eles.")
    elif sem_ret:
        comecar = "Nenhum cômodo tem retorno com esses dados."
    else:
        comecar = ""
    if sem_ret:
        comecar += (f" Em {lista([r['nome'] for r in sem_ret])} a troca não diminui a conta"
                    + (": ali ela serve para ter a luz recomendada."
                       if any(not r["atA"] for r in sem_ret) else "."))
    if nada:
        comecar += (f" {lista(nada)} já {'tem' if len(nada) == 1 else 'têm'} LED e luz "
                    "suficiente: nada a trocar.")
    paragrafo(comecar.strip())

    print("\n  PONTOS DE ATENÇÃO")
    aten = []
    mais = [r for r in rs if r["ql"] > r["qa"]]
    if mais:
        aten.append("Precisam de mais pontos de luz: "
                    + lista([f"{r['nome']} (+{r['ql'] - r['qa']})" for r in mais])
                    + ". Confira com um eletricista se a instalação comporta.")
    sobra = [r for r in rs if r["novos"] > 0 and r["eL"] > r["em"] * 1.3]
    if sobra:
        aten.append(f"A luz com LED fica bem acima do mínimo em "
                    f"{lista([r['nome'] for r in sobra])}. Dá para usar lâmpadas mais fracas "
                    "e economizar ainda mais.")
    fracos = [r for r in rs if r["novos"] > 0 and r["fl"] / r["pl"] < 90]
    if fracos:
        aten.append(f"O LED escolhido para {lista([r['nome'] for r in fracos])} produz menos "
                    "de 90 lúmens por watt. Modelos comuns hoje passam de 100 lm/W: um LED "
                    "mais eficiente diminui a quantidade e o gasto.")
    if t["payback"] is not None and t["payback"] > 5:
        aten.append("O retorno é demorado. Vale pesquisar LEDs mais baratos ou mais "
                    "eficientes, ou trocar primeiro só os cômodos que se pagam rápido.")
    ra_max = max(r["raN"] for r in rs)
    if g["ral"] < ra_max:
        aten.append(f"Os LEDs mostram as cores pior do que o recomendado (IRC "
                    f"{num(g['ral'], 0)}, mínimo {num(ra_max, 0)}). Escolha modelos com IRC "
                    "maior.")
    for r in rs:
        if r["ugrN"] <= 0:
            continue
        if g["ugrl"] == 0:
            aten.append(f"No {r['nome']}, o ofuscamento (UGR) da luminária não foi informado. "
                        f"Confira no catálogo se ele é no máximo {num(r['ugrN'], 0)}, para a "
                        "luz não incomodar a vista.")
        elif g["ugrl"] > r["ugrN"]:
            aten.append(f"No {r['nome']}, a luminária ofusca mais do que a norma permite (UGR "
                        f"{num(g['ugrl'], 0)}, máximo {num(r['ugrN'], 0)}). Prefira uma com "
                        "difusor.")
    curtos = [r for r in rs if n_anos > r["vida"] and not r["nada"]]
    if curtos:
        aten.append(f"O prazo da análise ({n_anos} anos) passa da vida do LED em "
                    + lista([f"{r['nome']} ({num(r['vida'], 1)} anos)" for r in curtos])
                    + ". A conta já inclui, em média por ano, o custo de repor os LEDs que "
                      "queimarem.")
    dims = [r for r in rs if r["dim"] > 0]
    if dims:
        aten.append(f"Para usar dimmer em {lista([r['nome'] for r in dims])}, o LED precisa "
                    "ser dimerizável (vem escrito na embalagem). Confira antes de comprar.")
    if any(r["pres"] > 0 for r in rs):
        aten.append("Use sensor de presença com tempo de espera de alguns minutos, para a luz "
                    "não apagar com a pessoa parada. Em quartos e na sala ele costuma "
                    "incomodar; funciona melhor em banheiro, corredor e garagem.")
    fluo = [r for r in rs if r["tipoA"].startswith("f") or r["reat"] > 0]
    if fluo:
        aten.append(f"As lâmpadas fluorescentes retiradas ({lista([r['nome'] for r in fluo])}) "
                    "têm mercúrio: não jogue no lixo comum. Entregue num ponto de coleta "
                    "(logística reversa).")
    aten.append("Estes números são uma estimativa pelo Método dos Lúmens. Depois da troca, "
                "meça a luz com um luxímetro (há aplicativos de celular que dão uma ideia) "
                "para confirmar.")
    for item in aten:
        paragrafo(item, "  • ", "    ")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n\n  Programa encerrado pelo usuário.")
    if sys.stdin.isatty():
        input("  Pressione ENTER para sair...")
