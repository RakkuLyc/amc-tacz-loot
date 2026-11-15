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
- Armas/munição/attachments em `building` (o tema `building_large` foi removido do AMC em 14 Nov 2026, commit `72d07b3`); **a delegacia recebe mais armas**: o AMC ganhou o tema `police_station` (commit `27ae583` do AMC, 13 Nov 2026).
- Cura: farmácia bastante; casas, oficinas e postos um pouco; oficinas também com pouca munição.
- **Vasos (`pot`) não recebem nada** (ver fatos).
- **Sem itens vanilla úteis (14 Nov 2026):** as tabelas do mod nunca tiveram item vanilla; os vanilla dos containers vinham das tabelas
  do próprio AMC (94 tipos). O mod agora **sobrescreve as 42 tabelas do AMC** (mesmos caminhos, `data/abandonedmoderncity/loot_table/chests/`)
  só com **sucata**, a mesma lista em todos os temas: stick, wheat/beetroot/melon/pumpkin seeds, rotten_flesh, bone, paper, bowl,
  glass_bottle, spider_eye. Quantidade (bloco `JUNK_SHAPE` do gerador): baú 2–4 pilhas, barril/vaso 30% de ter 1–2 (vaso 1); tiers
  `_hard` iguais (o prêmio vem do mod). Sem efeito de Sorte. Escolha do usuário entre mudar o AMC, sobrescrever pelo mod ou deixar.
- TACZ, LesRaisins e AMC são obrigatórios; **só o First Aid é opcional** (`neoforge:mod_loaded`).
- Loot generoso, mas sem abundância. Toda tabela com `weight`, `quality` e `rolls`/`bonus_rolls` para a Sorte funcionar.
- Repositório: mesmo nome (`RakkuLyc/amc-tacz-loot`), novo e vazio (antigo apagado e recriado em 14 Nov 2026).

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
  **Verificado pelo usuário no jogo (13 Nov 2026):** uma arma só com `GunId`+`GunFireMode` atira e a munição/attachment/cura funcionam.
  **Não verificado:** as armas geradas agora também levam `GunCurrentAmmoCount: 0` e `HasBulletInBarrel: false`; recarregar com a munição que vem junto está por testar.
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

## Números aprovados pelo usuário (13 Nov 2026, "Aprovo")
- (Os totais por estrutura aprovados em 13 Nov foram substituídos pela mudança de 14 Nov, abaixo; as raridades e a Sorte continuam.)
- Raridade das armas por tipo (peso): padrão pistol 10, smg 6, shotgun 6, rifle 4, dmr 2, sniper 1,5, mg 1, rpg 0,3; delegacia
  pistol 8, smg 8, shotgun 8, rifle 6, dmr 2,5, sniper 1,5, mg 1, rpg 0,3 (rpg7, m320 e minigun entram, bem raros; munição
  .50 BMG, 40mm e foguete ×0,15–0,4). A arma vem **descarregada**, com 1 a 2 pentes do calibre junto.
- Cura: comuns (ibuprofen, blood_pack, vaseline; plaster, bandage) saem mais que as raras (ai2, carfak; defibrillator).
- Sorte: `quality` = 25% da chance base por nível (×1,25 / ×1,5 / ×1,75 nas Sortes I/II/III); `bonus_rolls` só nos baús
  difíceis (0,34: Sorte III) e comuns (0,2: Sorte V). Delegacia 5,7 → 7,1 → 8,3 → 11,9 armas.
- Todos esses valores (inclusive a sucata) estão no bloco do topo de `tools/gen_loot.py`; mudar um número = editar a linha, `--write`, build.

## Como testar
- **Sorte de verdade só no jogo, abrindo containers reais** (o `/loot` nem o console aplicam Sorte): `/amcs spawn police_station
  abandoned_police_station` duas vezes, longe uma da outra; abrir os baús de uma sem efeito e os da outra com
  `/effect give @s minecraft:luck infinite 2`; comparar com a prévia (ruído grande numa só estrutura: procura-se diferença clara).
- Chunks gerados antes de uma mudança no AMC guardam os ids antigos das tabelas (o id é gravado ao colocar o container);
  containers já abertos não têm mais tabela. Testar em mundo novo ou com `/amcs spawn`.
- O jar do AMC precisa ser o reconstruído com o tema `police_station` (mesmo número de versão 0.1.0 do antigo: substituir).
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
  `neoforge:add_table` por tabela, filtrado por `neoforge:loot_table_id`. Temas: building, police_station,
  pharmacy, house, workshop, gas_station; tiers chest, chest_hard, barrel, barrel_hard (sem pot).
- Validação (13 Nov 2026): servidor real com AMC+TACZ+LesRaisins+First Aid, `tools/sample_loot.py <tema> <tier> [N]` amostra
  centenas de baús: médias observadas batem com a prévia (Sorte 0). Dados: `tools/tacz_catalog.py`, `tools/lr_catalog.py`.
- Sobrescrita das tabelas do AMC: `mods.toml` declara `ordering="AFTER"` para o AMC (o mod carrega depois, então os seus arquivos de
  mesmo caminho prevalecem). **Testado (14 Nov 2026):** com o jar do AMC original (tabelas vanilla antigas) na pasta `mods`, 1.680
  amostras de baús/barris dos 7 temas deram só sucata + itens do mod. **Não testado:** sem o `ordering` (não sei se é necessário) e
  os vasos (arquivos gerados, não amostrados). A ordem entre mods não é uma garantia do Minecraft: se outro mod também sobrescrever
  essas tabelas, o resultado depende da ordem de carga. As verificações do gerador falham se surgir qualquer item vanilla fora da lista de sucata.

## Mudança de 14 Nov 2026 (pedido do usuário): mais armas, e o AMC mudou
- O AMC removeu `building_large` (72d07b3), tirou 70% dos barris dos prédios e converteu o resto em baús (68e2d7c) e criou
  containers difíceis em subsolos/terraços/sótãos (a783d70). **`docs/containers.json` foi medido de novo** com o AMC atual
  (a crash building foi de 201 para 94 containers; prédios são quase só baús; a rampa ainda tem 242 barris).
- Pedido: prédios **1 arma a cada 3–7 baús**; delegacia **1 arma a cada 3–4 baús "de forma garantida"**.
  Implementado (Sorte 0, por baú; barris continuam raros): `building` baú 200‰ (1 em 5), baú difícil 333‰ (1 em 3);
  `police_station` baú 250‰ (1 em 4), baú difícil 333‰ (1 em 3). Resultado: prédios 1 arma a cada **5,0** baús, delegacia a cada **3,6**.
  Amostragem no servidor: baú de prédio 0,191 (esp. 0,200), difícil 0,332 (0,333); delegacia 0,259 (0,250), difícil 0,323 (0,333).
- "Garantida": loot table é sorteio independente por container; **não existe garantia exata por estrutura** em mod só de dados.
  O mais próximo é a probabilidade: na delegacia (Sorte 0) chance de pelo menos 4 armas 99%, 5: 98%, 6: 94%, 8: 76%.
- Consequência (a vigiar): o total por prédio subiu muito (brutalista ~46 armas, rampa ~33, torre ~14, apartamentos ~2),
  porque os prédios têm centenas de baús. Se for demais, baixar `gun` em `RATES["building"]` (1 em 7 = 143‰).
