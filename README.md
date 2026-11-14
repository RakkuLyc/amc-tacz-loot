# AMC TACZ Loot

Mod só de dados para NeoForge 1.21.1: loot do TACZ (armas, munições, attachments), First Aid e LesRaisins nos
containers do Abandoned Modern City. **Estado: tabelas geradas e números aprovados (13 Nov 2026); aguardando teste no jogo.** `tools/gen_loot.py` gera as tabelas por tema e tipo de container
(sem vasos), com `weight`, `quality` e `bonus_rolls` para a Sorte funcionar.
Requer: AMC, TACZ 1.2.0+, LesRaisins Tactical 0.4.3+. Opcional: First Aid 1.3.5+.
Detalhes técnicos e decisões: `CLAUDE.md`.

O mod também **sobrescreve as tabelas de loot do AMC** para que só reste sucata vanilla (sticks, sementes, etc.); o valor vem do TACZ, LesRaisins e First Aid.
