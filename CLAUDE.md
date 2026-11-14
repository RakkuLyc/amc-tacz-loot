# AMC TACZ Loot — regras de trabalho (obrigatórias)

Seguem as regras do projeto Abandoned Modern City, por escolha do usuário (13 Nov 2026):
1. **Perguntar ao longo do caminho**: decisões de design, números e estilo são do usuário; com mais de uma solução, apresentar opções.
2. **Gerar o `.jar` a cada mudança pequena/média** (`./gradlew build` → `build/libs/`) e dizer o que mudou nele.
3. **GitHub** (`gh`): commits frequentes e claros; atualizar o repositório a cada jar testável.
4. **Iterativo**: etapas pequenas e testáveis; ao fim de cada uma, resumo + próximo passo recomendado.
5. **Não passar à próxima etapa antes de o usuário testar e aprovar a atual.**
6. **Documentação sempre atualizada** (este arquivo, `README.md`) no mesmo commit da mudança.

## O que é
Mod **só de dados** (NeoForge 1.21.1, `modLoader="lowcodefml"`, sem Java) que injeta loot nas tabelas do AMC
(`abandonedmoderncity:chests/<tema>/<chest|barrel|pot>[_hard]`): armas, munições e attachments do TACZ, itens de cura do
First Aid e da LesRaisins. Mod id `amctaczloot`. Recomeçado do zero em 13 Nov 2026 (a versão anterior foi apagada).

## Decisões do usuário (13 Nov 2026)
- Só o pacote padrão do TACZ (70 armas); o Gunpowder Revolution (`hamster`) fica de fora por ora.
- Armas/munição/attachments em `building` e `building_large`; **a delegacia recebe mais armas** (ver pendência).
- TACZ, LesRaisins e AMC são obrigatórios; **só o First Aid é opcional** (`neoforge:mod_loaded`).
- Loot generoso, mas sem abundância. Toda tabela com `weight`, `quality` e `rolls`/`bonus_rolls` para a Sorte funcionar.
- Repositório: mesmo nome (`RakkuLyc/amc-tacz-loot`), novo e vazio.

## Fatos verificados (nos jars/log, não de memória)
- Injeção: GLM nativo `neoforge:add_table` + condição `neoforge:loot_table_id` (campo `loot_table_id`); registrado em
  `data/neoforge/loot_modifiers/global_loot_modifiers.json` (`replace:false`). Funciona (teste de 13 Nov 2026).
- TACZ: itens genéricos `tacz:modern_kinetic_gun` / `tacz:ammo` / `tacz:attachment`; o ID fica em
  `minecraft:custom_data` (`GunId`, `AmmoId`, `AttachmentId`, valores `tacz:<id>`). Ao criar uma arma o próprio TACZ
  (`GunItemBuilder`) grava `GunId`, `GunFireMode` (nome do enum em maiúsculas: `SEMI`/`AUTO`/`BURST`),
  `GunCurrentAmmoCount`, `HasBulletInBarrel` e `HeatAmount`. Catálogo (70 armas com tipo, munição e modos de tiro;
  25 munições; 128 attachments) em `docs/tacz_catalog.json`, gerado por `tools/tacz_catalog.py`.
  Excluir do loot os attachments `oem_*` e `*_default` (equipamento de fábrica; **hipótese** pelo nome, não testado).
  Os JSON de dados do jar têm comentários `/* */` (o parser do catálogo trata); `minigun` não tem `ammo_amount`.
  **Não verificado:** se uma arma só com `GunId`+`GunFireMode` (sem `GunCurrentAmmoCount`) atira e recarrega no jogo.
- LesRaisins: itens de cura são `lrtactical:consumable` com `custom_data.ConsumableId = "lrtactical:<id>"`
  (`blood_pack`, `ibuprofen`, `condensed_milk`, `vaseline`, `surv12`, `goldenstar`, `cms`, `carfak`, `amoxycillin`, `ai2`).
- First Aid: itens normais `firstaid:` `plaster`, `bandage`, `painkillers`, `morphine`, `morphine_injector`,
  `adrenaline_injector`, `defibrillator`.
- Item de mod opcional: a **tabela** e o **GLM** que o citam precisam de `"neoforge:conditions":[{"type":"neoforge:mod_loaded","modid":"firstaid"}]`;
  sem o First Aid o servidor sobe normalmente (testado).
- Sorte: o AMC usa `setLootTable(chave, seed)` (carregamento preguiçoso, lê `player.getLuck()` ao abrir); vaso
  (`DecoratedPotBlockEntity`) também é `RandomizableContainer`. `random_chance` ignora Sorte: não usar para decidir
  se há loot. O comando `/loot` do console **não aplica Sorte** (`LootCommand` não a usa; confirmado no bytecode): testes por RCON são sempre com Sorte 0. Usar entrada `minecraft:empty` com `quality` negativo e itens com `quality` positivo + `bonus_rolls`.
- A delegacia (63 containers) usa o tema `building`, igual a outros prédios; **não existe tema `police_station`** no AMC.

## Como testar
- Build: `JAVA_HOME=/usr/lib/jvm/java-21-openjdk ./gradlew build -Dorg.gradle.java.installations.paths=$JAVA_HOME`
  (o Java padrão do sistema é o 27, novo demais para o Gradle).
- Servidor de teste: copiar para `run/mods/` os jars de `../AbandonedModernCity/libs` (TACZ, First Aid, LesRaisins) e o
  jar do AMC; `run/server.properties` com RCON (porta 25575, senha `teste`); `./gradlew runServer` (mesmas opções);
  `python3 -I tools/rcon.py "setblock 0 100 0 minecraft:chest" "loot insert 0 100 0 loot <tabela>" "data get block 0 100 0 Items"`;
  `... tools/rcon.py stop`. (`run/` não é versionado.)
