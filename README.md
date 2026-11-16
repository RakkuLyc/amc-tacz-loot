# AMC TACZ Loot

Mod só de dados para NeoForge 1.21.1: loot do TACZ (armas, munições, attachments), da LesRaisins Tactical (cura e comida) e
do First Aid nos containers do Abandoned Modern City (AMC).

**Versão 1.0.1** (16 Nov 2026; corrige o pente das armas da 1.0.0). **Estado:** etapa de balanceamento concluída e aprovada pelo usuário (armas, munição, curas, equipamento, First Aid, attachments e pente inicial).
Os valores em vigor estão no bloco "ESTADO ATUAL" do `CLAUDE.md`.

- As tabelas são geradas por `tools/gen_loot.py` (`python3 -I tools/gen_loot.py` mostra a prévia; `--write` grava os arquivos).
  Todo número fica no bloco do topo do script. Cada tabela usa `weight`, `quality` e `bonus_rolls` para a Sorte funcionar.
- O mod injeta itens nas tabelas do AMC (loot modifiers `neoforge:add_table`) e **sobrescreve as tabelas de loot do AMC** com
  sucata vanilla (stick, sementes, etc.); o valor vem do TACZ, da LesRaisins e do First Aid. Vasos não recebem nada.
- Requer: AMC (build recente, com o tema `police_station`), TACZ 1.2.0+, LesRaisins Tactical 0.4.3+. Opcional: First Aid 1.3.5+.
- Detalhes técnicos, decisões e como testar: `CLAUDE.md`.
