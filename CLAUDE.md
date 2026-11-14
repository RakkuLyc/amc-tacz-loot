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
- Armas/munição/attachments em `building` e `building_large`; **a delegacia recebe mais armas**: o AMC ganhou o tema `police_station` (commit `27ae583` do AMC, 13 Nov 2026).
- Cura: farmácia bastante; casas, oficinas e postos um pouco; oficinas também com pouca munição.
- **Vasos (`pot`) não recebem nada** (ver fatos).
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
  Itens elegíveis = os que têm receita na mesa de armeiro do pacote padrão (`craftable` no catálogo: 70 armas, 25 munições,
  104 de 128 attachments; ficam de fora `oem_*`, `*_default` e variantes embutidas). Critério objetivo, não pelo nome.
  Os JSON de dados do jar têm comentários `/* */` (o parser do catálogo trata); `minigun` não tem `ammo_amount`.
  **Não verificado:** se uma arma só com `GunId`+`GunFireMode` (sem `GunCurrentAmmoCount`) atira e recarrega no jogo.
- LesRaisins: itens de cura são `lrtactical:consumable` com `custom_data.ConsumableId = "lrtactical:<id>"`.
  Cura > 0 (`docs/lr_catalog.json`): `ai2`, `amoxycillin`, `blood_pack`, `carfak`, `cms`, `goldenstar`, `ibuprofen`, `surv12`,
  `vaseline`; `condensed_milk` só dá fome (fora do loot de cura). Os com durabilidade (`max_durability` > 0) saem 1 por vez.
- First Aid: itens normais `firstaid:` `plaster`, `bandage`, `painkillers`, `morphine`, `morphine_injector`,
  `adrenaline_injector`, `defibrillator`.
- Item de mod opcional: a **tabela** e o **GLM** que o citam precisam de `"neoforge:conditions":[{"type":"neoforge:mod_loaded","modid":"firstaid"}]`;
  sem o First Aid o servidor sobe normalmente (testado).
- Sorte (bytecode do Minecraft 1.21.1): peso efetivo = `floor(weight + quality*Sorte)`; rolagens = `rolls + floor(bonus_rolls*Sorte)`.
  `bonus_rolls` < 1 não faz nada na Sorte I; `quality` é a alavanca que responde já na Sorte I. O AMC usa `setLootTable(chave, seed)`
  (carregamento preguiçoso: lê `player.getLuck()` ao abrir baús e barris). `random_chance` ignora Sorte: não usar para decidir
  se há loot; usar `minecraft:empty` com `quality` negativo. O `/loot` do console **não aplica Sorte** (`LootCommand` não a usa):
  testes por RCON são sempre com Sorte 0; Sorte > 0 só por conta analítica e no jogo (`/effect give @s minecraft:luck`).
- **Vasos**: `DecoratedPotBlockEntity.getTheItem()` chama `unpackLootTable(null)` (sem jogador, **sem Sorte**), e quando a tabela
  gera mais itens que espaços o Minecraft não preenche nada (`"Tried to over-fill a container"`): num vaso (1 espaço) isso
  esvaziaria também o item do AMC. Por isso o mod não injeta em vasos.
- Entrada aninhada `minecraft:loot_table` com `value` = id de tabela ou tabela inline funciona (testado; é como a arma vem
  com sua munição). Entradas compostas (group etc.) não têm peso.
- A delegacia (63 containers) tem o tema próprio `police_station` no AMC (mesmas tabelas vanilla de `building`). Containers por
  estrutura e tipo medidos no jogo: `docs/containers.json` (`tools/measure_containers.py`; confere com o total do AMC).

## Como testar
- Build: `JAVA_HOME=/usr/lib/jvm/java-21-openjdk ./gradlew build -Dorg.gradle.java.installations.paths=$JAVA_HOME`
  (o Java padrão do sistema é o 27, novo demais para o Gradle).
- Servidor de teste: copiar para `run/mods/` os jars de `../AbandonedModernCity/libs` (TACZ, First Aid, LesRaisins) e o
  jar do AMC; `run/server.properties` com RCON (porta 25575, senha `teste`); `./gradlew runServer` (mesmas opções);
  `python3 -I tools/rcon.py "setblock 0 100 0 minecraft:chest" "loot insert 0 100 0 loot <tabela>" "data get block 0 100 0 Items"`;
  `... tools/rcon.py stop`. (`run/` não é versionado.)

## Gerador (`tools/gen_loot.py`)
- `python3 -I tools/gen_loot.py` imprime a **prévia** (esperado por estrutura, Sorte 0 a 3; chance de um baú ter algo do mod);
  `--write` apaga e reescreve `src/main/resources/data/amctaczloot` e `global_loot_modifiers.json` e roda as verificações
  de consistência. **Todos os números ficam no bloco do topo do script** (chances em ‰ por tema/tier, Sorte, raridade das armas).
- Estrutura gerada: `<tema>/<tier>_core.json` (arma+munição, munição solta, attachment, cura LesRaisins; TACZ+LesRaisins) e
  `<tema>/<tier>_firstaid.json` (cura First Aid, com `neoforge:mod_loaded`); tabelas de escolha em `pick/`; um GLM
  `neoforge:add_table` por tabela, filtrado por `neoforge:loot_table_id`. Temas: building, building_large, police_station,
  pharmacy, house, workshop, gas_station; tiers chest, chest_hard, barrel, barrel_hard (sem pot).
- Validação (13 Nov 2026): servidor real com AMC+TACZ+LesRaisins+First Aid, `tools/sample_loot.py <tema> <tier> [N]` amostra
  centenas de baús: médias observadas batem com a prévia (Sorte 0). Dados: `tools/tacz_catalog.py`, `tools/lr_catalog.py`.
