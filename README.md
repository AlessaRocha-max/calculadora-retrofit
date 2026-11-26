# Calculadora Retrofit de Iluminação — Casa

Projeto AB2 da disciplina **Eficiência e Gestão Energética**.

A calculadora mostra se vale a pena trocar a iluminação de uma casa por LED (retrofit). Ela faz as contas cômodo por cômodo e diz quanto se economiza por ano e em quanto tempo o dinheiro investido volta.

## Abrir a calculadora

- **No navegador:** https://alessarocha-max.github.io/calculadora-retrofit/
- **No computador:** baixe o arquivo `retrofit_visual.html` e abra com dois cliques.
- **Versão em Python:** `python calculadora_retrofit.py` (apertando só ENTER em todas as perguntas, ele calcula a mesma casa de exemplo da página).

## O que ela calcula

1. **Quantidade de lâmpadas** em cada cômodo pelo Método dos Lúmens, conferindo se a luz fica dentro do recomendado para cada uso.
2. **Gasto de energia** hoje e depois da troca, com a Tarifa Branca (horário de ponta, intermediário e fora de ponta).
3. **Troca de lâmpadas ao longo do tempo**, levando em conta quanto cada tipo de lâmpada dura.
4. **Sensores e controles:** sensor de presença, temporizador e dimmer.
5. **Se vale a pena:** payback simples e descontado, VPL e TIR.
6. **Diagnóstico** final em linguagem simples.

## Arquivos

| Arquivo | O que é |
|---|---|
| `retrofit_visual.html` | Calculadora completa, com gráficos (abre no navegador) |
| `calculadora_retrofit.py` | A mesma calculadora em Python, no terminal |
| `index.html` | Atalho que abre a calculadora no GitHub Pages |
