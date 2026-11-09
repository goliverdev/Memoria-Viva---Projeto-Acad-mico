# emocao.py
# -*- coding: utf-8 -*-
import re

# ------------------------------------------------------------------
# Normalização
# ------------------------------------------------------------------

_ACENTOS = {
    "á": "a", "à": "a", "ã": "a", "â": "a", "ä": "a",
    "é": "e", "ê": "e", "è": "e", "ë": "e",
    "í": "i", "ì": "i", "î": "i", "ï": "i",
    "ó": "o", "ò": "o", "õ": "o", "ô": "o", "ö": "o",
    "ú": "u", "ù": "u", "û": "u", "ü": "u",
    "ç": "c",
}


def _normalizar(texto: str) -> str:
    """Minúsculas + remove acentuação (facilita o casamento de palavras)."""
    texto = (texto or "").lower()
    for origem, destino in _ACENTOS.items():
        texto = texto.replace(origem, destino)
    return texto


NEGACOES = ["nao", "nunca", "jamais", "nem", "sem"]
INTENSIFICADORES = [
    "muito", "muitissimo", "demais", "extremamente", "completamente",
    "totalmente", "tanto", "imensamente", "profundamente", "tao",
    "absurdamente", "bastante",
]
ATENUADORES = [
    "um pouco", "meio", "levemente", "ligeiramente", "meio que",
    "as vezes", "de vez em quando",
]


def _ocorrencias(padrao_normalizado: str, texto_normalizado: str):
    """Retorna os índices (start) de cada ocorrência de uma palavra/expressão
    inteira (respeitando limites de palavra) dentro do texto."""
    regex = r"\b" + re.escape(padrao_normalizado) + r"\b"
    return [m.start() for m in re.finditer(regex, texto_normalizado)]


def _tem_negacao_perto(texto_normalizado: str, indice: int, janela: int = 18) -> bool:
    trecho_anterior = texto_normalizado[max(0, indice - janela):indice]
    palavras_antes = trecho_anterior.split()
    return any(p in NEGACOES for p in palavras_antes[-3:])


def _tem_intensificador_perto(texto_normalizado: str, indice: int, janela: int = 18) -> bool:
    trecho_anterior = texto_normalizado[max(0, indice - janela):indice]
    palavras_antes = trecho_anterior.split()
    return any(p in INTENSIFICADORES for p in palavras_antes[-3:])


def _tem_atenuador_perto(texto_normalizado: str, indice: int, janela: int = 22) -> bool:
    trecho_anterior = texto_normalizado[max(0, indice - janela):indice]
    return any(atenuador in trecho_anterior for atenuador in ATENUADORES)



PALAVRAS_EMOCAO = {
    "alegria": [
        ("feliz", 2), ("felicidade", 2), ("alegre", 2), ("alegria", 2),
        ("sorrir", 1), ("sorriso", 1), ("contente", 1), ("animado", 1),
        ("animada", 1), ("empolgado", 2), ("empolgada", 2), ("adorei", 2),
        ("otimo", 1), ("otima", 1), ("maravilhoso", 2), ("maravilhosa", 2),
        ("incrivel", 1), ("divertido", 1), ("divertida", 1), ("diversao", 1),
        ("amei", 2), ("sucesso", 1), ("comemorar", 1), ("festa", 1),
        ("riso", 1), ("gargalhada", 2), ("radiante", 2), ("emocionado de alegria", 2),
    ],
    "tristeza": [
        ("triste", 2), ("tristeza", 2), ("chorar", 2), ("chorei", 2),
        ("choro", 1), ("sozinho", 1), ("sozinha", 1), ("sofrimento", 2),
        ("sofri", 2), ("vazio", 1), ("vazia", 1), ("deprimido", 2),
        ("deprimida", 2), ("desanimado", 1), ("desanimada", 1),
        ("chateado", 1), ("chateada", 1), ("lagrima", 1), ("lagrimas", 1),
        ("perda", 1), ("perdi", 1), ("magoado", 2), ("magoada", 2),
        ("desolado", 2), ("desolada", 2), ("abatido", 1), ("abatida", 1),
    ],
    "raiva": [
        ("raiva", 2), ("irritado", 1), ("irritada", 1), ("furioso", 2),
        ("furiosa", 2), ("bravo", 1), ("brava", 1), ("odio", 2),
        ("odiei", 2), ("revoltado", 2), ("revoltada", 2), ("injusto", 1),
        ("injustica", 1), ("briga", 1), ("discussao", 1), ("estressado", 1),
        ("estressada", 1), ("indignado", 1), ("indignada", 1),
    ],
    "medo": [
        ("medo", 2), ("assustado", 2), ("assustada", 2), ("pavor", 2),
        ("terror", 2), ("receio", 1), ("temer", 1), ("temeroso", 1),
        ("temerosa", 1), ("panico", 2), ("apavorado", 2), ("apavorada", 2),
        ("inseguro", 1), ("insegura", 1),
    ],
    "nojo": [
        ("nojo", 2), ("nojento", 1), ("nojenta", 1), ("repugnante", 2),
        ("asco", 2), ("enjoado", 1), ("enjoada", 1), ("repulsa", 2),
    ],
    "ansiedade": [
        ("ansioso", 2), ("ansiosa", 2), ("ansiedade", 2), ("nervoso", 1),
        ("nervosa", 1), ("preocupado", 1), ("preocupada", 1), ("tenso", 1),
        ("tensa", 1), ("aflito", 1), ("aflita", 1), ("apreensivo", 1),
        ("apreensiva", 1), ("inquieto", 1), ("inquieta", 1),
    ],
    "inveja": [
        ("inveja", 2), ("invejoso", 1), ("invejosa", 1), ("cobica", 1),
    ],
    "tedio": [
        ("tedio", 2), ("entediado", 2), ("entediada", 2), ("monotono", 1),
        ("monotona", 1), ("chato", 1), ("chata", 1),
    ],
    "vergonha": [
        ("vergonha", 2), ("envergonhado", 2), ("envergonhada", 2),
        ("constrangido", 2), ("constrangida", 2), ("humilhado", 2),
        ("humilhada", 2), ("encabulado", 1), ("encabulada", 1),
    ],
    "nostalgia": [
        ("saudade", 2), ("saudades", 2), ("nostalgia", 2), ("lembranca", 1),
        ("lembrancas", 1), ("antigamente", 1), ("aquela epoca", 1),
        ("recordar", 1), ("relembrar", 1), ("infancia", 1),
    ],
    "orgulho": [
        ("orgulho", 2), ("orgulhoso", 2), ("orgulhosa", 2), ("conquistei", 2),
        ("consegui", 1), ("realizei", 1), ("vencer", 1), ("venci", 1),
    ],
    "gratidao": [
        ("gratidao", 2), ("grato", 1), ("grata", 1), ("agradecido", 2),
        ("agradecida", 2), ("sortudo", 1), ("sortuda", 1), ("abencoado", 1),
        ("abencoada", 1),
    ],
}

FRASES_EMOCAO = {
    "alegria": "alegria",
    "tristeza": "tristeza",
    "raiva": "raiva",
    "medo": "medo",
    "nojo": "desconforto",
    "ansiedade": "ansiedade",
    "inveja": "inveja",
    "tedio": "tédio",
    "vergonha": "vergonha",
    "nostalgia": "saudade",
    "orgulho": "orgulho",
    "gratidao": "gratidão",
}

EMOCAO_PADRAO = "nostalgia"

# ------------------------------------------------------------------
# Palavras-chave de categoria
# ------------------------------------------------------------------

PALAVRAS_CATEGORIA = {
    "Família": [
        "familia", "mae", "pai", "avo", "avos", "irmao", "irma", "filho",
        "filha", "tio", "tia", "primo", "prima", "sobrinho", "sobrinha",
        "marido", "esposa", "parentes",
    ],
    "Viagem": [
        "viagem", "viajei", "viajar", "praia", "hotel", "passeio",
        "turismo", "mala", "aeroporto", "estrada", "exterior",
        "passaporte", "hospedagem", "excursao", "roteiro", "destino",
    ],
    "Infância": [
        "infancia", "crianca", "brincar", "brinquedo", "parquinho",
        "recreio",
    ],
    "Escola": [
        "escola", "faculdade", "prova", "aula", "professor", "professora",
        "estudar", "estudos", "universidade", "colegio", "formatura",
        "vestibular", "boletim", "diploma", "materia", "trabalho escolar",
        "monitoria", "estagio academico",
    ],
    "Trabalho": [
        "trabalho", "emprego", "chefe", "reuniao", "projeto", "escritorio",
        "entrevista de emprego", "demissao", "promocao", "carreira",
        "salario", "cliente", "colega de trabalho",
    ],
    "Amigos": [
        "amigo", "amiga", "amigos", "amizade", "turma",
    ],
    "Conquistas": [
        "conquista", "conquistei", "sucesso", "vitoria", "ganhei",
        "premio", "formei", "passei no", "aprovado", "aprovada", "meta",
        "objetivo alcancado", "realizei",
    ],
    "Perdas": [
        "perda", "perdi", "morreu", "falecimento", "luto", "despedida",
        "faleceu",
    ],
    "Saúde": [
        "saude", "hospital", "medico", "medica", "doenca", "cirurgia",
        "internado", "internada", "recuperacao", "tratamento",
    ],
    "Relacionamento": [
        "namorado", "namorada", "noivo", "noiva", "casamento", "casei",
        "namoro", "relacionamento", "paixao", "beijo", "ficamos juntos",
    ],
}


CATEGORIA_POR_EMOCAO = {
    "tristeza": "Perdas",
    "orgulho": "Conquistas",
    "nostalgia": "Infância",
    "gratidao": "Momentos especiais",
}

CATEGORIA_PADRAO = "Momentos especiais"


# ------------------------------------------------------------------
# Pontuação (com peso de título, negação e intensidade)
# ------------------------------------------------------------------

def _pontuar_emocoes(titulo_norm: str, texto_norm: str):
    """Retorna (pontuacao_por_emocao, intensidade_por_emocao, palavras_encontradas_por_emocao)."""
    pontuacao = {emo: 0.0 for emo in PALAVRAS_EMOCAO}
    intensidade = {emo: 0 for emo in PALAVRAS_EMOCAO}
    encontradas = {emo: [] for emo in PALAVRAS_EMOCAO}

    for emo, palavras in PALAVRAS_EMOCAO.items():
        for palavra, peso in palavras:
            for fonte_texto, multiplicador in ((titulo_norm, 2.0), (texto_norm, 1.0)):
                for idx in _ocorrencias(palavra, fonte_texto):
                    if _tem_negacao_perto(fonte_texto, idx):
                        continue  # negado: não conta
                    peso_efetivo = peso * multiplicador
                    if _tem_atenuador_perto(fonte_texto, idx):
                        peso_efetivo *= 0.5  # "um pouco de raiva" pesa menos que "muita raiva"
                    pontuacao[emo] += peso_efetivo
                    if _tem_intensificador_perto(fonte_texto, idx):
                        intensidade[emo] += 1
                    if palavra not in encontradas[emo]:
                        encontradas[emo].append(palavra)
    return pontuacao, intensidade, encontradas


def _pontuar_categorias(titulo_norm: str, texto_norm: str):
    pontuacao = {cat: 0.0 for cat in PALAVRAS_CATEGORIA}
    encontradas = {cat: [] for cat in PALAVRAS_CATEGORIA}
    for cat, palavras in PALAVRAS_CATEGORIA.items():
        for palavra in palavras:
            for fonte_texto, multiplicador in ((titulo_norm, 2.0), (texto_norm, 1.0)):
                qtd = len(_ocorrencias(palavra, fonte_texto))
                if qtd:
                    pontuacao[cat] += multiplicador * qtd
                    if palavra not in encontradas[cat]:
                        encontradas[cat].append(palavra)
    return pontuacao, encontradas




_ABERTURA_CATEGORIA = {
    "Família": "Momentos em família como esse ficam marcados.",
    "Viagem": "Viajar e viver algo novo sempre deixa marca.",
    "Infância": "Essas lembranças de infância têm um valor especial.",
    "Escola": "Trajetórias de estudo raramente são lineares.",
    "Trabalho": "O ambiente de trabalho mexe mesmo com a gente.",
    "Amigos": "Amizade é desses vínculos que valem a pena guardar.",
    "Conquistas": "Toda conquista carrega o esforço que ninguém viu.",
    "Perdas": "Perder alguém ou algo importante dói de verdade.",
    "Saúde": "Questões de saúde pedem paciência com o próprio corpo.",
    "Relacionamento": "Relações importantes moldam boa parte de quem somos.",
    "Momentos especiais": "Nem todo momento marcante precisa de um motivo grande.",
}

_FECHO_CATEGORIA = {
    "Família": "Vale voltar a essa lembrança sempre que precisar de raiz.",
    "Viagem": "Guarde esse registro para revisitar quando bater vontade de viajar de novo.",
    "Infância": "Faz bem revisitar quem você foi antes de virar quem você é.",
    "Escola": "Persistência importa mais do que perfeição — continue tentando.",
    "Trabalho": "Um passo de cada vez também é progresso.",
    "Amigos": "Poucas coisas sustentam a gente como uma boa amizade.",
    "Conquistas": "Reconheça o que você conquistou — você trabalhou por isso.",
    "Perdas": "Não precisa atravessar isso rápido, nem sozinho(a).",
    "Saúde": "Cuidar de si também é uma forma de conquista.",
    "Relacionamento": "Vínculos assim merecem ser cuidados com atenção.",
    "Momentos especiais": "Guardar isso por escrito já é uma forma de valorizar o momento.",
}

_RECONHECIMENTO_EMOCAO = {
    "alegria": "Dá para sentir a alegria genuína nas suas palavras",
    "tristeza": "Dá para perceber que isso pesou de verdade",
    "raiva": "É justo sentir raiva diante disso",
    "medo": "É compreensível sentir medo nessa situação",
    "nojo": "É normal sentir desconforto com algo assim",
    "ansiedade": "Dá para notar a ansiedade por trás do que você escreveu",
    "inveja": "Comparar-se é humano, mas sua caminhada é sua",
    "tedio": "Às vezes a rotina realmente pede um respiro",
    "vergonha": "Seja gentil consigo mesmo(a) — todo mundo passa por isso",
    "nostalgia": "Dá para sentir a saudade em cada palavra",
    "orgulho": "O orgulho que aparece aqui é bem merecido",
    "gratidao": "Essa gratidão que você registrou vale a pena guardar",
}


def _extrair_tema(titulo: str, texto: str) -> str:
    """Extrai um pequeno trecho do próprio conteúdo do usuário para dar
    contexto à frase (não é um dado inventado — vem do que a pessoa
    escreveu)."""
    base = (titulo or "").strip()
    if not base:
        palavras = (texto or "").strip().split()
        base = " ".join(palavras[:8])
    if len(base) > 60:
        base = base[:57].rstrip() + "..."
    return base


def _gerar_frase(emocao: str, categoria: str, intensidade_nivel: str,
                  emocao_secundaria: str, titulo: str, texto: str) -> str:
    tema = _extrair_tema(titulo, texto)

    abertura = _ABERTURA_CATEGORIA.get(categoria, _ABERTURA_CATEGORIA[CATEGORIA_PADRAO])
    reconhecimento = _RECONHECIMENTO_EMOCAO.get(emocao, "Dá para perceber o que você sentiu ao escrever isso")
    fecho = _FECHO_CATEGORIA.get(categoria, _FECHO_CATEGORIA[CATEGORIA_PADRAO])

    partes = [abertura]

    if tema:
        partes.append(f'Em "{tema}", {reconhecimento[0].lower()}{reconhecimento[1:]}.')
    else:
        partes.append(f"{reconhecimento}.")

    if intensidade_nivel == "alta":
        partes.append(f"E dá para sentir que essa {FRASES_EMOCAO.get(emocao, emocao)} veio com bastante intensidade.")

    if emocao_secundaria:
        partes.append(f"Junto com isso, também parece haver um pouco de {FRASES_EMOCAO.get(emocao_secundaria, emocao_secundaria)}.")

    partes.append(fecho)

    return " ".join(partes)


# ------------------------------------------------------------------
# Função principal
# ------------------------------------------------------------------

def _gerar_explicacao(emocao: str, categoria: str, emocao_secundaria,
                       palavras_emo: list, palavras_cat: list,
                       confianca_emo: str, confianca_cat: str) -> str:
    """Monta um texto curto explicando o raciocínio por trás da emoção e
    da categoria identificadas, citando as palavras/expressões reais do
    texto que levaram a essa conclusão."""
    partes = []

    label_emo = FRASES_EMOCAO.get(emocao, emocao)
    if confianca_emo == "baixa" or not palavras_emo:
        partes.append(
            f'Não encontrei palavras muito claras de sentimento no texto, então "{label_emo}" foi usada como estimativa geral.'
        )
    else:
        amostra = ", ".join(f'"{p}"' for p in palavras_emo[:3])
        partes.append(
            f'A emoção "{label_emo}" foi identificada porque o texto usa expressões como {amostra}.'
        )

    if emocao_secundaria:
        partes.append(f'Também percebi sinais de "{FRASES_EMOCAO.get(emocao_secundaria, emocao_secundaria)}" junto com isso.')

    if confianca_cat == "baixa" or not palavras_cat:
        partes.append(
            f'Não achei palavras específicas de categoria, então "{categoria}" foi escolhida com base na emoção identificada e no contexto geral.'
        )
    else:
        amostra_cat = ", ".join(f'"{p}"' for p in palavras_cat[:3])
        partes.append(
            f'A categoria "{categoria}" veio de termos como {amostra_cat}.'
        )

    return " ".join(partes)


def analisar_texto(titulo: str, texto: str) -> dict:
    """
    Analisa título + texto de uma memória e retorna um dicionário com:
      - categoria (str)
      - emocao (str)
      - emocao_secundaria (str ou None)
      - intensidade ("baixa" | "média" | "alta")
      - frase_motivadora (str)
      - explicacao (str) — por que essa emoção/categoria foi escolhida
      - confianca ("baixa" | "média" | "alta")

    Sempre retorna essa estrutura (com valores padrão seguros), mesmo para
    texto vazio, muito curto ou ambíguo — nunca lança exceção para a
    interface.
    """
    titulo = titulo or ""
    texto = texto or ""

    total_palavras = len((titulo + " " + texto).split())

    if total_palavras < 4:
        return {
            "categoria": "Indefinida",
            "emocao": "indefinida",
            "emocao_secundaria": None,
            "intensidade": "baixa",
            "confianca": "baixa",
            "frase_motivadora": "Escreva um pouco mais sobre esse momento para que a análise consiga captar melhor o que você sentiu.",
            "explicacao": "O texto é curto demais para uma análise segura — foram encontradas menos de 4 palavras no total.",
        }

    titulo_norm = _normalizar(titulo)
    texto_norm = _normalizar(texto)

    pontuacao_emo, intensidade_emo, palavras_emo_todas = _pontuar_emocoes(titulo_norm, texto_norm)
    pontuacao_cat, palavras_cat_todas = _pontuar_categorias(titulo_norm, texto_norm)

    # --- Emoção principal e secundária ---
    ranking_emo = sorted(pontuacao_emo.items(), key=lambda x: x[1], reverse=True)
    top_emo, top_score = ranking_emo[0]

    if top_score <= 0:
        emocao = EMOCAO_PADRAO
        emocao_secundaria = None
        confianca_emo = "baixa"
    else:
        emocao = top_emo
        confianca_emo = "alta" if top_score >= 3 else "média"
        segundo_emo, segundo_score = ranking_emo[1] if len(ranking_emo) > 1 else (None, 0)
        if segundo_emo and segundo_score > 0 and segundo_score >= top_score * 0.5:
            emocao_secundaria = segundo_emo
        else:
            emocao_secundaria = None

    # --- Intensidade ---
    hits_intensidade = intensidade_emo.get(emocao, 0)
    if hits_intensidade >= 2:
        intensidade_nivel = "alta"
    elif hits_intensidade == 1:
        intensidade_nivel = "média"
    else:
        intensidade_nivel = "baixa"

    # --- Categoria (com fallback via emoção quando não há palavras-chave) ---
    ranking_cat = sorted(pontuacao_cat.items(), key=lambda x: x[1], reverse=True)
    top_cat, top_cat_score = ranking_cat[0]

    if top_cat_score > 0:
        categoria = top_cat
        confianca_cat = "alta" if top_cat_score >= 3 else "média"
    else:
        categoria = CATEGORIA_POR_EMOCAO.get(emocao, CATEGORIA_PADRAO)
        confianca_cat = "baixa"

    confianca = "baixa" if "baixa" in (confianca_emo, confianca_cat) else (
        "alta" if confianca_emo == confianca_cat == "alta" else "média"
    )

    frase = _gerar_frase(emocao, categoria, intensidade_nivel, emocao_secundaria, titulo, texto)
    explicacao = _gerar_explicacao(
        emocao, categoria, emocao_secundaria,
        palavras_emo_todas.get(emocao, []), palavras_cat_todas.get(categoria, []),
        confianca_emo, confianca_cat,
    )

    return {
        "categoria": categoria,
        "emocao": emocao,
        "emocao_secundaria": emocao_secundaria,
        "intensidade": intensidade_nivel,
        "confianca": confianca,
        "frase_motivadora": frase,
        "explicacao": explicacao,
    }




def analisar_emocao(texto: str):
    """Compatibilidade: retorna (emocao, frase_motivadora) a partir só do
    texto (sem título). Prefira usar analisar_texto(titulo, texto)."""
    resultado = analisar_texto("", texto)
    return resultado["emocao"], resultado["frase_motivadora"]


def analisar_categoria(texto: str) -> str:
    """Compatibilidade: retorna só a categoria a partir do texto."""
    resultado = analisar_texto("", texto)
    return resultado["categoria"]


if __name__ == "__main__":
    testes = [
        ("Dia incrível", "Hoje foi um dia muito feliz, me diverti muito com meus amigos!"),
        ("Sinto tanta falta", "Estou com muita saudade da minha infância e daqueles tempos."),
        ("Que injustiça", "Fiquei com tanta raiva daquela injustiça que discuti com todos."),
        ("Vestibular", "Estudei muito para a prova e fiquei ansioso, mas no fim consegui passar e fiquei muito orgulhoso."),
        ("", "Não fiquei feliz com o que aconteceu, foi bem ruim pra mim, senti uma tristeza intensa e adorei ter meus amigos por perto depois."),
        ("oi", "tudo bem"),
    ]
    for titulo, texto in testes:
        r = analisar_texto(titulo, texto)
        print(f"\nTÍTULO: {titulo!r}\nTEXTO: {texto!r}")
        for k, v in r.items():
            print(f"  {k}: {v}")
