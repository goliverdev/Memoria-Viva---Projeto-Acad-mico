# Memória Viva

## Informações do projeto

**Nome:** Memória Viva\
**Tipo:** Projeto acadêmico\
**Descrição:** Aplicação para registro, organização e consulta de
memórias pessoais, com análise textual baseada em regras para
identificação de emoções e categorias.

## Visão geral

O **Memória Viva** é uma aplicação desktop desenvolvida em Python que
permite registrar, organizar e consultar memórias pessoais. O sistema
utiliza uma interface construída com Flet e armazena os dados localmente
em um banco SQLite.

Além do registro das lembranças, a aplicação realiza uma análise textual
do título e do conteúdo de cada memória para identificar emoções e
categorias relacionadas ao texto. Com base nessa análise, o sistema
também apresenta uma explicação e uma frase associada à emoção
identificada.

O projeto foi desenvolvido em contexto acadêmico e reúne conceitos de
desenvolvimento de interfaces, persistência de dados e processamento
textual baseado em regras.

## Funcionalidades

-   **Cadastro e autenticação:** criação de contas com nome, endereço de
    e-mail, senha e avatar.
-   **Registro de memórias:** criação de registros com título, categoria
    e descrição.
-   **Análise emocional:** identificação de uma emoção predominante e,
    quando aplicável, de uma emoção secundária.
-   **Classificação por categorias:** identificação de temas
    relacionados ao conteúdo da memória.
-   **Análise textual complementar:** consideração de negações,
    intensificadores e atenuadores na pontuação das palavras
    identificadas.
-   **Geração de conteúdo:** apresentação de uma explicação sobre a
    análise e de uma frase motivadora.
-   **Gerenciamento de memórias:** consulta, pesquisa, edição e exclusão
    de registros.
-   **Comunidade:** visualização de memórias que seus autores optaram
    por tornar públicas.
-   **Configurações de perfil:** edição de informações pessoais e
    personalização da aparência da aplicação.
-   **Privacidade:** possibilidade de definir a visibilidade de uma
    memória como pública ou privada.

## Tecnologias utilizadas

  -----------------------------------------------------------------------
  Tecnologia                          Finalidade
  ----------------------------------- -----------------------------------
  Python                              Linguagem utilizada no
                                      desenvolvimento da aplicação.

  Flet                                Construção da interface gráfica e
                                      gerenciamento da interação com o
                                      usuário.

  SQLite                              Armazenamento local dos dados de
                                      usuários e memórias.
  -----------------------------------------------------------------------

O SQLite é disponibilizado pela biblioteca padrão do Python e não requer
instalação independente.

## Estrutura do projeto

``` text
memoria-viva/
├── main.py          # Interface gráfica, telas e navegação
├── emocao.py        # Análise textual e identificação de emoções
├── database.py      # Criação e operações do banco de dados
├── memoria_viva.db  # Banco de dados SQLite
└── README.md        # Documentação do projeto
```

O arquivo `memoria_viva.db` é criado automaticamente durante a
inicialização da aplicação, caso ainda não exista. O módulo
`database.py` também verifica a estrutura do banco e adiciona colunas
ausentes quando necessário, preservando os registros existentes.

## Instalação e execução

### Pré-requisitos

-   Python instalado no computador.
-   `pip` disponível no terminal.
-   Os arquivos `main.py`, `emocao.py` e `database.py` localizados no
    mesmo diretório.

### 1. Instalar a dependência

Abra um terminal no diretório do projeto e execute:

``` bash
python -m pip install flet==0.28.3
```

### 2. Executar a aplicação

Após a instalação, execute:

``` bash
python main.py
```

A aplicação será iniciada por meio do Flet.

## Funcionamento da análise emocional

O módulo `emocao.py` realiza uma análise textual baseada em regras e
conjuntos de palavras associados a emoções e categorias. O procedimento
não depende de um modelo de aprendizado de máquina treinado.

De maneira geral, a análise segue estas etapas:

1.  **Normalização:** o texto é preparado para facilitar a comparação de
    palavras, considerando diferenças de acentuação e capitalização.
2.  **Identificação de termos:** são localizadas palavras e expressões
    associadas às emoções e às categorias previstas pelo sistema.
3.  **Análise de contexto:** o algoritmo considera termos de negação,
    intensificação e atenuação próximos às palavras identificadas.
4.  **Pontuação:** são calculadas pontuações para determinar as emoções
    e categorias mais relacionadas ao conteúdo.
5.  **Geração de resposta:** o módulo organiza os resultados e produz
    uma explicação e uma frase associadas à análise.

As emoções contempladas incluem alegria, tristeza, raiva, medo, nojo,
ansiedade, inveja, tédio, vergonha, nostalgia, orgulho e gratidão.

**Limitação:** por ser uma abordagem baseada em palavras-chave e regras
predefinidas, a análise pode não compreender adequadamente ironias,
ambiguidades, contextos complexos ou significados implícitos. Os
resultados são indicativos e não constituem avaliação psicológica ou
diagnóstico.

## Banco de dados

A persistência das informações é realizada pelo SQLite, por meio do
módulo `database.py`.

O banco contém duas tabelas principais:

-   **`usuarios`:** armazena o identificador do usuário, nome, endereço
    de e-mail, senha, avatar e data de cadastro.
-   **`memorias`:** armazena o usuário responsável pelo registro,
    título, categoria, texto, emoção identificada, data, frase
    motivadora, explicação e configuração de visibilidade.

Os dados permanecem armazenados após o encerramento da aplicação. Para
preservar os registros, mantenha uma cópia do arquivo `memoria_viva.db`.

### Considerações de segurança

Na implementação atual, as senhas são armazenadas em texto simples no
banco de dados, sem aplicação de hash. Por esse motivo, esta versão deve
ser utilizada em ambiente acadêmico, de demonstração ou desenvolvimento,
e não para armazenar credenciais reais ou informações pessoais
sensíveis.

Antes de disponibilizar a aplicação em um ambiente de produção, é
necessário implementar armazenamento seguro de senhas, revisar os
mecanismos de autenticação e autorização e avaliar a proteção dos dados
pessoais e das memórias compartilhadas.

## Conta de demonstração

A aplicação disponibiliza um usuário de demonstração criado
automaticamente durante a inicialização:

  Campo    Credencial
  -------- ---------------------------
  E-mail   `gabriel@memoriaviva.app`
  Senha    `123456`

Também é possível criar uma nova conta pela tela de cadastro.

## Observações

-   Execute `main.py` a partir do diretório do projeto para que o banco
    de dados seja criado ou localizado no caminho esperado.
-   Não exclua o arquivo `memoria_viva.db` caso deseje preservar os
    usuários e as memórias cadastradas.
-   Evite compartilhar o banco de dados, pois ele pode conter
    informações pessoais.
-   A aplicação depende do Flet. Caso ocorram problemas de
    compatibilidade, verifique a versão instalada e a utilizada no
    ambiente de desenvolvimento.