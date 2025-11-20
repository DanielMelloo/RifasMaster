# Lista de Correções
Utilize este arquivo para listar correções que devem ser feitas na aplicação.
O assistente verificará Este arquivo a cada interação.

## Concluídas ✅

- [x] corrigir o admin, tem algum erro que ta bugando o timestamp, olha o erro dado pelo flask
- [x] Corrigir DeprecationWarning do conversor de timestamp do SQLite (Python 3.12+)
- [x] as promoções iniciadas no admin não estão sendo aplicadas
- [x] Centralizar box da rifa na landing page e na rifa selecionada
- [x] No checkout da fazendinha, em vez de listar o nome da rifa, listar apenas a quantidade selecionada
- [x] Botão "Deletar" não estava aparecendo no admin panel (corrigido adicionando tickets_count)
- [x] Botão "Adicionar Promoção" estava apenas no modal de edição (movido para coluna Ações)

## Conclu ídas Hoje (20/11) - Ciclo #2 ✅

- [x] **CRÍTICO:** Em meus bilhetes, ao checar da rifa iphone, o vencedor é o 44, e um dos bilhetes comprados é o 44 (tem coroa), mas exibe "O sorteio foi realizado. Número vencedor: 44. Infelizmente você não ganhou desta vez." - **CORRIGIDO** usando Jinja2 namespace para resolver problema de escopo de variável

- [x] No checkout, mostre o valor unitário de cada bilhete e o total em baixo - **IMPLEMENTADO** linha "Preço unitário: R$ X.XX" adicionada

- [x] Dados do admin Daniel verificados - admin válido, usuário ID 1

## Concluídas Hoje (20/11) - Ciclo #3 ✅

- [x] Ha locais que estão com status "active" troca pra ativa e encerrado - **IMPLEMENTADO** mapeamento de tradução no backend

- [x] ESC para fechar modais - **IMPLEMENTADO** event listener global

## Concluídas Hoje (20/11) - Ciclo #4 (Refatoração Fazendinha) ✅

- [x] **CRÍTICO:** A lógica de compra de bilhetes do tipo fazendinha gera os bilhetes antes do pagamento, mostrando IDs na URL. **RESOLVIDO** - Implementado session storage, tickets criados apenas após pagamento

## Pendentes ⏳

- [x] corrige os detalhes do sorteio, para o usuário Daniel, não está mostrando nada pois dá erro, testa no web browser e veja para corrigir **(CORRIGIDO: Adicionado tratamento de erro no dashboard e verificado)**

- [x] corrige a ação detalhes do vencedor, não esta mostrando os dados do vencedor, e agora cada usuario tem os dados, e caso não informado, mostra que não foi informado pelo usuário **(CORRIGIDO: Modal atualizado para mostrar todos os dados do perfil)**

- [] corrige a ação detalhes do vencedor, não esta mostrando os dados do vencedor, e agora cada usuario tem os dados, e caso não informado, mostra que não foi informado pelo usuário, testa no web browser e veja para corrigir