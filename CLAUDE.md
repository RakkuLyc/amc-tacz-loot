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

## ESTADO ATUAL (15 Nov 2026) — o que está valendo; as seções abaixo desta são HISTÓRICO e podem citar números já substituídos
- **Armas** (chance por baú comum / difícil, Sorte 0): prédio 12,0% / 20,0% (1 a cada 8,3 / 5 baús), barris 0,4% / 0,7%; delegacia 25,0% / 33,3%
  (1 a cada 4 / 3), barris 3,0% / 6,0%. Tipos: pistola 10, smg 6, escopeta 6, fuzil 4, dmr 2, sniper 1,5, mg 1, rpg 0,3 (delegacia: smg/escopeta 8, fuzil 6).
  Arma cai **com 50% do pente cheio** (`GunCurrentAmmoCount` = ammo_amount x 0,5 arredondado para cima: 17 -> 9, pente de 1 -> 1; `HasBulletInBarrel` = false), **exceto a minigun** (sem pente definido, nasce com 0).
- **Attachments** (aprovado em 16 Nov 2026): a chance de QUALQUER attachment por container é **0,8 da chance de arma** do mesmo tema/tipo (`ATT_FRACTION_OF_GUN`): prédio baú 9,6%, difícil 16%,
  barris 0,3% / 0,6%; delegacia 20% / 26,6% / 2,4% / 4,8%. Qual sai: peso por **classe** (Comum 8, Incomum 4, Raro 2, Épico 1) sobre os 104 attachments fabricáveis, classes em
  `docs/attachments_rarity.json` (gerado por `tools/att_rarity.py <tacz.jar>`: 50% quantas armas aceitam o attachment (peso real do loot) + 50% atributos (zoom, recuo, precisão, nível do pente,
  dano/perfuração, silenciador), comparados dentro de cada tipo; corte 40/30/20/10%). Chance de cada item por baú de prédio: Comum 0,150%, Incomum 0,075%, Raro 0,037%, Épico 0,019%. Miras = 35% dos sorteios.
- **Munição** (pool próprio): baú de prédio 52,0%, difícil 86,6%, barris 6,2% / 11,4%; delegacia baú 80,0%, difícil 100,0% (teto), barris 20,0% / 36,0%.
  Calibre: metade igual para os 23 calibres com arma + metade pela popularidade das armas (ex. prédio: 12g 11,9%, 9mm 10,8%, .45 ACP 9,3%; mais raros ~2,4%).
  **Cada acerto de munição dá 1 a 3 pilhas de calibres sorteados** (o mesmo calibre pode repetir), com balas por pilha proporcionais à pilha máxima, **no
  tamanho original** (9mm 24–50 com pilha 60; 12g 14–30; .308 19–40; 22wmr 26–53; 40mm e foguete 2–5). `AMMO_STACKS = (1, 3)`, `AMMO_SIZE = 1.0`.
  **Total de balas por baú de prédio ~31 (dobro da versão de 1 pilha); delegacia ~48.**
- **Cura LesRaisins** (chance de CADA item por container, independente; mesma em todos os temas exceto farmácia; "raridade dobrada" em 16 Nov = chances x0,5): Comuns vaseline,
  ibuprofen, amoxicillin, golden star **4,6% cada**; Incomuns blood pack **2,3%**, CAR **2,1%**; **Raros** AI-2 e CMS **1,0%**; **Épico** SURV12 **0,5%**.
  **Farmácia = valores congelados "como estava"** (`HEAL_PHARMACY_FIXED`): comuns 9,2%, blood pack 9,0%, CAR 8,5%, AI-2 8,0%, CMS 7,0%, SURV12 4,0%.
- **Comida**: leite condensado 8% por container em todos os temas (2–4 unidades); pão 20% só em casas (4–12). Itens de cura First Aid e comida **não** mudaram com o ×0,5.
- **Equipamento LesRaisins** (chance de CADA item por container, independente; todos os temas **exceto farmácia**; **na delegacia as chances dos throwable dobram**): M67 Grenade 9,2% (**3 a 5**; delegacia 18,4%),
  RGN Grenade 4,1% (**2 a 4**; delegacia 8,2%), C4 Sticky Bomb 3,0% (1; delegacia 6,0%), Dagger / Karambit / Baseball Bat 2,0% cada (1, durabilidade cheia). Itens: `lrtactical:throwable` (`ThrowableId`) e
  `lrtactical:melee` (`MeleeWeaponId`). O detonator **não** entra no loot (o C4 o entrega ao ser arremessado, confirmado pelo usuário). smoke/flash/molotov/flash shield de fora.
- **First Aid** (opcional, tabela própria com `neoforge:mod_loaded`; chance de CADA item por container, independente, mesma em todos os temas exceto farmácia; x0,5 em 16 Nov):
  plaster **7,5%** (4–14 un., "Muito comum"); bandage, adrenaline injector, painkillers **4,6%** (Comuns; bandage 2–10); defibrillator **2,1%** (Incomum); **Raro** morphine **1,0%**;
  **Épico** morphine injector **0,5%**. **Farmácia congelada**: plaster 15%, comuns 9,2%, morphine 8,2%, defibrillator 8,2%, injector 4,0%. `FA_CHANCE`, `FA_CLASS`, `FA_COUNT`.
  Classes (mais comum -> mais rara): Muito comum, Comum, Incomum, Raro, **Épico** (nova, 16 Nov). Raro = base 4,0% e Épico = 2,0% LR (e 2,0% / 1,0% FA) antes de x0,5: valores meus.
- **Sucata** vanilla (stick, 4 sementes, carne podre, osso, papel, tigela, garrafa, olho de aranha) nas 36 tabelas do AMC sobrescritas; sem itens vanilla úteis (única exceção: pão).
- **Vasos** não recebem nada do mod. Temas: building, police_station, pharmacy, house, workshop, gas_station (o AMC removeu `building_large`).
- **Ferramentas**: `gen_loot.py` (prévia / `--write`), `sample_items.py` (chance por item num servidor de teste; use este), `sample_loot.py` (categorias de arma/munição;
  a coluna `lr` conta o leite como LesRaisins e **não bate** com `expected()["lr"]`: dá falso desvio), `measure_containers.py`, `tacz_catalog.py`, `lr_catalog.py`.

## HISTÓRICO — Decisões do usuário (13 Nov 2026)
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
  .50 BMG, 40mm e foguete ×0,15–0,4). A arma vem **descarregada**, e **sem** munição junto (mudou em 14 Nov, abaixo).
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
- Para medir chance por item, use `python3 -I tools/sample_items.py <tema/tier> [N] [filtro]` (o `sample_loot.py` só serve para arma/munição).
- Servidor de teste: copiar para `run/mods/` os jars de `../AbandonedModernCity/libs` (TACZ, First Aid, LesRaisins) e o
  jar do AMC; `run/server.properties` com RCON (porta 25575, senha `teste`); `./gradlew runServer` (mesmas opções);
  `python3 -I tools/rcon.py "setblock 0 100 0 minecraft:chest" "loot insert 0 100 0 loot <tabela>" "data get block 0 100 0 Items"`;
  `... tools/rcon.py stop`. (`run/` não é versionado.)

## Gerador (`tools/gen_loot.py`)
- `python3 -I tools/gen_loot.py` imprime a **prévia** (esperado por estrutura, Sorte 0 a 3; chance de um baú ter algo do mod);
  `--write` apaga e reescreve `src/main/resources/data/amctaczloot` e `global_loot_modifiers.json` e roda as verificações
  de consistência. **Todos os números ficam no bloco do topo do script** (chances em ‰ por tema/tier, Sorte, raridade das armas).
- Estrutura gerada: `<tema>/<tier>_core.json` (2 pools independentes: arma/attachment/cura LesRaisins e munição; TACZ+LesRaisins) e
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

## Munição (opção B, escolhida pelo usuário em 14 Nov 2026)
- Pedido: a munição **não** vem mais junto da arma; é aleatória, com raridade por calibre conforme as armas que o usam.
  Implementado: a tabela do núcleo tem **2 pools independentes** (arma/attachment/cura LR; e munição). `pick/gun_*` agora só tem armas.
- Calibre: peso = soma das raridades (por tipo de arma) das armas que usam o calibre, com redutor extra em .50 BMG/.338/.45-70/.500
  mag (×0,4–0,5) e 40mm/foguete (×0,15) — `ammo_weights()`. Mais comuns: 12g ~20%, 9mm ~18%, .45 ACP ~15% (prédio).
- Quantidade = **o mesmo total de munição de antes** (solta + a que vinha com a arma): baú de prédio 26%, difícil 43,3%;
  delegacia 40% / 58,3%; barris de prédio 3,1% / 5,7%, de delegacia 10% / 18%; oficina inalterada (4% / 7%, barril 1,5% / 3%).
  Pilha: de 1/6 a 1/2 da pilha cheia do calibre (ex. 9mm 10–30 balas). Sorte: `quality` como as demais categorias.
- Validado no servidor (3.000 baús de prédio): 0,270 pilhas/baú (esp. 0,260); calibres batem com a fatia esperada; dos baús
  com arma só 26% têm alguma munição (= a chance geral) e só 3% a do calibre da arma (antes 100%).
- Referência: a munição do Apocalypse Loot (Lost Cities) é ~8–14× maior por baú e tem faixa de raridade 14:1 (a nossa é ~270:1);
  o usuário escolheu manter a nossa opção B. Simulação de 20 baús em `run/tmp/simulate_ammo.py` (não versionada).

## Proposta C aplicada (15 Nov 2026) — substitui a raridade/quantidade de munição e as taxas de arma dos prédios
- Feedback do usuário (screenshot da green tower: 14 armas, ~10 pilhas visíveis): armas ok, pouca munição. O inventário **funde pilhas
  iguais**, então a contagem de pilhas na tela engana (9mm 55 > máx 50 de uma pilha).
- **Raridade da munição igual** para todos os calibres que têm arma (23; `7.62x25` e `6.8x51 Fury` não têm arma e ficam fora).
  **Quantidade por pilha** proporcional à pilha máxima, 9mm de referência 24–50 (`AMMO_REF`): pilha 60 → 24–50; 64 → 26–53; 50 → 20–42;
  48 → 19–40; 42 → 17–35; 36 → 14–30; 30 → 12–25; 6 (40mm, foguete) → 2–5. Uma só tabela `pick/ammo` (sem perfil de arma).
- **Armas dos prédios −40%** (baú comum 12% = 1 a cada 8,3; difícil 20% = 1 a cada 5; barris 0,4% / 0,7%). **Delegacia inalterada nas
  armas** (25% / 33,3%, barris 3% / 6%). **Munição ×2** em prédio e delegacia: prédio baú 52%, difícil 86,6%, barris 6,2% / 11,4%;
  delegacia baú 80%, **difícil 100% (teto, sem entrada `empty`: peso 0 não é válido)**, barris 20% / 36%. Oficina e demais temas inalterados.
- Interpretação assumida: "deixe a quantidade de balas úteis como está" = manter os tamanhos de pilha definidos; os fatores −40% / ×2 foram
  proposta minha (aprovada). Antes: green tower 18,1 armas / 408 balas / 16,7 úteis por arma; agora (esperado) 10,9 armas / 47,3 pilhas /
  ~1.350 balas / ~40 úteis por arma; delegacia 9,4 armas, 33,3 pilhas.
- Validado no servidor (Sorte 0): armas e munição por baú batem (prédio 0,120 e 0,542; delegacia 0,244 e 0,811; difícil 1,000); 23 calibres,
  fatias 3,6–5,0% (esperado 4,35%); balas por pilha dentro dos intervalos acima. A seção "Munição (opção B)" acima ficou superada neste ponto.

## Calibre misto, opção 2 (15 Nov 2026) — substitui "raridade igual" da proposta C
- Feedback (crash building, ~66 baús, 3 armas, ~33 pilhas): munição como projetado (34,3 esperadas), mas **3 armas** (chance de ≤3: 3,6%) e,
  com calibres todos iguais, só ~24% da munição serve às armas achadas (poucas armas cobrem poucos dos 23 calibres). Antes eu mostrara só a
  média de "balas úteis por arma"; **a variação é grande e deve ser mostrada**.
- Decisão do usuário (opção 2): a chance de cada calibre é **metade igual para todos e metade pela popularidade das armas** que o usam
  (`AMMO_MIX_UNIFORM = 0.5`; popularidade = soma do peso por tipo das armas do tema). Tabelas `pick/ammo_default` e `pick/ammo_police`
  (a delegacia usa os pesos de armas dela). Mais comuns (prédio): 12g 11,9%, 9mm 10,8%, .45 ACP 9,3%, 5.56 5,9%; mais raros ~2,4%
  (40mm, foguete, .45-70, 7.92x57). Taxas de arma/munição e tamanhos de pilha da proposta C **inalterados**.
- Validado no servidor: 100 rodadas de 66 baús (crash building): 7,5 armas, 34,8 pilhas, ~416 balas úteis, mediana 58 úteis/arma (antes 33),
  38% da munição serve (antes 24%), 3% das rodadas com <20 úteis/arma (antes 16%). Calibres batem com o esperado (12g em prédio saiu 14,6%
  contra 11,9% — ~3σ, pesos do arquivo conferidos; na delegacia saiu abaixo; tratado como ruído).

## Cura LesRaisins e comida (15 Nov 2026) — substitui os pesos/fatias de cura anteriores
- **Chance de cada item POR CONTAINER, independente dos outros** (não é fatia): vaseline 19,5%, ibuprofen 19%, amoxicillin 18%, golden star 17%
  (Comuns); blood pack 9%, CAR 8,5%, AI-2 8%, CMS 7% (Incomuns); SURV12 **4%** (Raro; o usuário pediu 3% e depois "diminuir levemente a
  raridade" — interpretado como um pouco mais comum). Soma 110% = ~1 item de cura LesRaisins por container (antes ~4%).
  A mesma chance em todos os temas e tipos de container; `HEAL_LR`, `HEAL_CLASS`, `PHARMACY_MULT` no bloco do topo de `gen_loot.py`.
- **Farmácia**: multiplicador **×2 só nos Incomuns e no Raro** (blood pack 18%, CAR 17%, AI-2 16%, CMS 14%, SURV12 8%); Comuns inalterados.
  O ×2 é escolha minha (o usuário pediu um multiplicador sem valor).
- **Comida**: leite condensado 8% por container, 2–4 unidades, em todos os temas (incluindo farmácia: suposição minha); **pão (vanilla,
  exceção explícita do usuário) 20%, 4–12 unidades, só em casas**. O leite já restaura 6 de fome, saturação 1,6 e aplica o efeito Saturação
  (2 s) no próprio item da LesRaisins (conferido no JSON). First Aid inalterado (continua por categoria, `fa`).
- Implementação: cada item tem o seu próprio pool (item com `weight` = chance em ‰ e `quality` = 25% por nível de Sorte; entrada `empty` com o
  resto); a tabela `pick/lr` deixou de existir. A verificação do gerador passou a aceitar `minecraft:bread` além da sucata.
- Validado no servidor (Sorte 0): prédio (2.500 baús) vaseline 20,2%, SURV12 3,6%, leite 7,0% (2–4); casa (2.000) pão 20,1% (4–12, média 7,9);
  farmácia (2.000) incomuns 13–18%, SURV12 7,3%; barril de oficina e baú difícil da delegacia com as mesmas chances do prédio; pão ausente em prédio.
- Monte Carlo (Sorte 0): green tower ~100 curas LR (comuns 67 / incomuns 30 / SURV12 3,6), 7,3 pilhas de leite; rampa 439; casa 63 curas e
  ~91 unidades de pão; farmácia grande 33,6. **Escala ~27× a anterior (3,6 curas na green tower)**; risco de estouro de container só em
  dispenser/dropper (9 espaços): ~1 em 125.000–250.000 containers (o container fica vazio se estourar).

## Opção C: cura LesRaisins x0,5 (15 Nov 2026)
- Feedback: uma farmácia grande deu ~34 itens de cura (previsto ~41 com LR+First Aid+leite; não foi azar). Escolha do usuário: **tudo x0,5**
  nas chances de cura LesRaisins (`HEAL_SCALE = 0.5`, aplicado por cima do multiplicador da farmácia; arredondado em ‰).
- Chances por container agora: vaseline 9,8%, ibuprofen 9,5%, amoxicillin 9,0%, golden star 8,5% (Comuns); blood pack 4,5%, CAR 4,3%, AI-2 4,0%,
  CMS 3,5% (Incomuns); SURV12 2,0% (Raro). Soma 0,55 por container. **Farmácia**: Incomuns e Raro com o ×2 antigo, então voltam aos valores
  anteriores ao x0,5: blood pack 9,0%, CAR 8,5%, AI-2 8,0%, CMS 7,0%, SURV12 4,0%; Comuns como nos outros lugares (soma 0,733). Leite 8%, pão
  20% (só casas) e First Aid **inalterados**.
- Validado no servidor: prédio (3.000 baús) vaseline 9,7%, SURV12 1,9%; farmácia (2.500) incomuns 6,8–9,1%, SURV12 4,4%; casa pão 20,6%.
- Monte Carlo (Sorte 0), curas LesRaisins: green tower 50 (39–62); brutalista 126; rampa 220; delegacia 35; casa 31; oficina 34; posto 17;
  farmácia grande 16,9 (11–24); farmácia pequena 12,4 (7–18). Antes da mudança de 15 Nov eram 3,6 na green tower e 3,6 na farmácia grande.

## Comuns da LesRaisins com a mesma chance (15 Nov 2026)
- Pedido: "todos os itens comuns do LesRaisins com o mesmo peso". Os 4 Comuns (vaseline, ibuprofen, amoxicillin, golden star) agora têm 184‰ (18,4%)
  antes do x0,5 = **9,2% por container** (média dos antigos 19,5/19/18/17; total dos Comuns inalterado em 36,8%). Incomuns, Raro, farmácia, leite,
  pão e First Aid inalterados. Valor 18,4% escolhido por mim (o usuário não deu número).
- Validado no servidor (Sorte 0): prédio (4.000 baús) comuns 8,8–9,9%; farmácia (3.000) 9,2–10,5%. Lição: **sempre mandar `tools/rcon.py stop` ao
  fim de um teste**; um servidor esquecido faz o próximo falhar com "FAILED TO BIND TO PORT" e o amostrador mede o servidor antigo sem aviso
  (aconteceu uma vez; o teste foi refeito). Para ver se há servidor aberto use `pgrep -f '[b]ootstraplauncher'` (o `pgrep` simples conta o próprio comando).

## Munição em 1 a 3 pilhas de calibres diferentes (opção C, 15 Nov 2026)
- Descoberta: no baú **real** o Minecraft já divide cada pilha em vários pedaços espalhados em slots aleatórios (`shuffleAndSplitItems`, só
  quando há slots livres); o `/loot insert` dos testes NÃO faz isso. Antes da mudança um baú com munição tinha **1 calibre só em ~5 pedaços**
  (~6 balas cada). Então "balas soltas espalhadas" já existia; o que faltava era mais de um calibre por baú.
- Apocalypse Loot (referência): pool próprio de munição, cada rolagem = 1 pilha de um calibre por peso, 1–3 rolagens (2–5 nas tabelas mais ricas),
  `bonus_rolls` 1,0, calibre pode repetir, pilhas grandes (9mm 21–57), sem truque de pilhas pequenas (conta com a divisão do Minecraft).
- Escolha do usuário: **opção C** = a chance de o container ter munição não mudou (prédio baú 52% etc.), mas cada acerto sorteia calibres de
  `pick/ammo_*` com `rolls` uniforme **1 a 3** (primeiro 2–3, depois o usuário pediu 1–3), pilhas a **50%** do tamanho para manter o total de balas
  (2,0 pilhas x 0,5 = 1; com 2–3 pilhas seria 0,4). A escolha dos 50% foi minha (manter o total); se o usuário preferir 40% o total cai ~20%.
- Validado no baú real (preenchimento real forçado com `execute if items`, 800 baús de prédio): 54% com munição; calibres diferentes por baú
  com munição: 1 (37%), 2 (34%), 3 (29%), média 1,9; ~8 pedaços por baú; 16,4 balas por baú (esperado 15,7). Delegacia (500): 80% com munição,
  22,9 balas (esperado 24,0). Risco de container de 9 espaços estourar (dispenser/dropper): 1 em 77.000 a 500.000.
- Para testar o preenchimento real: `setblock ... chest{LootTable:"...",LootTableSeed:1L}` + `execute if items block ... container.0 minecraft:stone`
  + `data get block ... Items`. **O Minecraft do Prism Launcher do usuário aparece como `bootstraplauncher` no `pgrep`: nunca matar; para saber se o
  servidor de teste está aberto, use a porta 25575 (`ss -ltn`).**

## Tamanho das pilhas de volta ao original (15 Nov 2026)
- Pedido: "o tamanho das pilhas deve ser igual ao valor anterior, sem mudar" → `AMMO_SIZE = 1.0` (9mm 24–50 etc.), com 1 a 3 pilhas por acerto.
- **Consequência (avisada ao usuário):** o total de balas por container dobrou (média 2,0 pilhas x tamanho cheio): baú de prédio 15,6 → ~31, delegacia
  ~24 → ~48; green tower ~2.800 balas (antes ~1.400). Para voltar ao total antigo bastaria baixar a chance de munição em `RATES` ×0,5 (não aplicado).
- Validado: tamanhos observados iguais aos esperados (9mm 24–50, 308 19–40, 22wmr 26–53, 338 12–25, 40mm 2–5; o 12g chegou a 36 por fusão de duas
  pilhas no `/loot insert`, pilha cheia = 36); baú real (800 de prédio): 54% com munição, calibres 1/2/3 = 37/34/29%, 33,0 balas por baú (esperado 31,2);
  delegacia (500): 80%, 46,4 balas (esperado 47,9).

## First Aid por item e quantidades grandes (16 Nov 2026)
- Classes pedidas pelo usuário: Muito comum = plaster; Comum (mesma categoria LesRaisins) = bandage, adrenaline injector, painkillers; Incomum = morphine,
  defibrillator; Raro = morphine injector. Depois: "aumente drasticamente a quantidade da pilha": plaster **4–14**, bandage **2–10** (pilha máxima de ambos no
  First Aid = 16, `stacksTo(16)` no registro; defibrillator tem durabilidade). O usuário não aprovou/ajustou os números de chance que propus; aplicados mesmo assim.
- O sistema antigo (taxa por categoria `fa` + `pick/fa` com pesos) foi removido: o First Aid agora é um pool por item (como as curas LR). `fa` saiu de `RATES`.
- Validado (Sorte 0): prédio (3.000 baús) plaster 13,5% (4–14), bandage 8,9% (2–10), comuns ~9%; farmácia incomuns 7,4–9,0%, injector 3,6%; barril de oficina igual
  ao prédio; **sem o jar do First Aid o servidor sobe sem erros, sem itens `firstaid:` e com o resto do mod normal**.
- Monte Carlo (unidades de First Aid): green tower ~199 (plaster 123, bandage 50), rampa ~872, casa ~125, delegacia ~138, farmácia grande ~52, pequena ~39.
  **Escala ~38x a anterior (5 na green tower).** Risco de estourar um dispenser/dropper (9 espaços): ~1 em 5.000 (barril difícil da delegacia), 1 em 12.000
  (barril da delegacia), 1 em 38.000 (barril de prédio); o container fica vazio se estourar.

## Granadas, C4 e armas brancas da LesRaisins (16 Nov 2026)
- Classificação do usuário: Comum = M67; Incomum = RGN; meio-termo (entre incomum e raro) = C4; Raro = Dagger, Karambit, Baseball Bat. Pedido final: "se baseie nos valores de
  chance de cura do LesRaisins", M67 "sempre de 3 a 5" e RGN "no mínimo 2, no máximo 4". Valores: M67 9,2% (= comuns de cura), RGN 4,1% (média dos incomuns de cura),
  C4 3,0% (ponto médio incomum-raro, escolha minha), raros 2,0% (= SURV12). Config: `GEAR`, `GEAR_EXCLUDED_THEMES`.
- Pilha máxima das granadas = 3 (`stack_size` no JSON do item): o excedente de um sorteio de 5 vira outra pilha (stack splitter do loot). No baú real as unidades aparecem em pedaços de 1–2
  espalhados pelos slots (total por baú continua 3–5 / 2–4).
- Padrões de amostragem corrigidos: `sample_items.py` agora reconhece `ThrowableId` e `MeleeWeaponId`. Lição: **regex com id específico + `.*?` com `re.S` pega a contagem do item errado**; casar o item
  genérico `\{count: N, Slot: Xb, ... id: "..."\}` e só depois filtrar.
- Validado (prédio, 4.000 baús): M67 8,7% (3–5), RGN 4,6% (2–4), C4 3,0%, armas brancas 1,8–2,2%; farmácia 0 itens; 0 erros de carga.
- Monte Carlo (Sorte 0): 100 baús ≈ 37 M67 (18–57), 12 RGN, 3 C4, 2 de cada arma branca (65% de chance de conseguir as 3); green tower ≈ 34 M67, 11 RGN, 2,7 C4, 5,5 armas brancas; rampa ≈ 147 M67.
  Risco de estourar dispenser/dropper (9 espaços): ~1 em 1.200 no barril difícil da delegacia, 1 em 2.500 no barril da delegacia, 1 em 8.800 no barril de prédio.

## Delegacia com throwable ×2 (16 Nov 2026)
- Pedido: "na delegacia, dobre as chances dos throwable" (M67, RGN, C4; `GEAR_THEME_MULT = {"police_station": {"throwable": 2.0}}`) e "coloque itens melee nas casas também".
  **As armas brancas já saíam nas casas** (regra: todos os temas menos a farmácia, 2% cada); nada foi alterado nelas, o usuário foi avisado e recebeu uma tabela de multiplicadores.
- Validado (3.000 baús): delegacia M67 17,8%, RGN 8,9%, C4 6,1%, armas brancas 1,7–2,1%; casa e prédio inalterados; 0 erros de carga. Delegacia inteira (63 containers): ~46 M67, ~15,5 RGN, ~3,8 C4.
- Risco de estourar dispenser/dropper (9 espaços) na delegacia: ~1 em 1.200 (barril) e 1 em 610 (barril difícil).

## Raridade dobrada das curas e nova classe Épico (16 Nov 2026)
- Pedido: "duplique a raridade dos itens de cura, mantenha a farmácia como está" (interpretado: itens 2x mais raros = chances x0,5, LesRaisins e First Aid, farmácia com os mesmos números de antes);
  CMS, AI-2 e Morphine -> Raro; SURV12 e Morphine Injector -> nova classe **Épico**. Os números de Raro/Épico foram escolhas minhas. Leite, pão, equipamento e munição inalterados.
- Config: `HEAL_RARITY_SCALE = 0.5`, `HEAL_PHARMACY_FIXED` (a antiga `PHARMACY_MULT` foi removida).
- Validado (prédio, 8.000 baús): plaster 7,8%, comuns 4,2–5,3%, blood pack 2,2%, CAR 2,1%, AI-2 e CMS 0,9%, SURV12 0,6%, defibrillator 2,3%, morphine 1,1%, injector 0,5%; farmácia (3.000) idêntica
  à anterior (CMS 6,8%, SURV12 4,0%, plaster 15,1%). 0 erros de carga.
- Resultado esperado: green tower ~23 curas LesRaisins e ~98 unidades de First Aid (antes 50 e 199); 100 baús ~133 itens de cura no total; chance de 1+ item Épico em 100 baús 39% cada, Raro 63% cada.

## Attachments por classe de raridade (16 Nov 2026)
- Ideia do usuário: "ligeiramente mais raros que as armas", baseada no tipo de arma que o attachment aceita e nos seus atributos. Proposta (tabela) aprovada e aplicada sem mudanças.
  Antes: att = 4% (baú de prédio, 1/3 da arma) e 1,2% nos barris (3x a arma), tipo com peso fixo e uniforme dentro do tipo. Agora: 9,6% e 0,3%.
- Fatos: compatibilidade vem de `tacz_tags/attachments/allow_attachments/<arma>.json` (tags `#tacz:...` resolvidas recursivamente); atributos de `data/attachments/<id>_data.json` e zoom de
  `assets/tacz/display/attachments/<id>_display.json`. 67 das 71 armas têm lista (`m320`, `minigun`, `rpg7`, `taurus943` não aceitam nenhum attachment); `sight_infitac_fmp13` não tem arquivo de dados.
  As munições especiais (fmj, he, hp, i, slug...) são do tipo `extended_mag` no TACZ. Épicos: scope_mk5hd, scope_xl50, scope_mk4ert, scope_1873_6x, scope_1866_4x, muzzle_silencer_vulture,
  muzzle_brake_timeless50, laser_peq6, stock_heavy_spas_12, stock_tactical_spas_12. Os pesos dos atributos e os cortes 40/30/20/10 são julgamento meu (aprovados pelo usuário).
- Validado no servidor: prédio (8.000 baús) 9,6% com attachment, classes 67,8/22,2/8,1/1,9% (esperado 65,6/24,2/8,2/2,0); por item 0,155/0,069/0,037/0,019%; delegacia (3.000) 19,9%
  (Épicos saíram abaixo do esperado, amostra pequena). Se o catálogo do TACZ mudar, rode `tools/att_rarity.py` (o gerador falha se as classes estiverem desatualizadas).

## Armas nascem com 50% do pente (16 Nov 2026)
- Pedido: "todas as armas, com exceção da minigun, passam a já spawnar com 50% do pente cheio". `GUN_SPAWN_AMMO_FRACTION = 0.5`, `GUN_SPAWN_AMMO_EXCLUDED = ("minigun",)`, `gun_spawn_ammo()`.
  Pente = `ammo_amount` do TACZ (`docs/tacz_catalog.json`); só a minigun não tem. Arredondamento para CIMA (escolha minha): 22 armas têm pente ímpar; 4 têm pente de 1
  (lonetrail, m320, rpg7, springfield1873) e nascem carregadas com 1. A bala na câmara (`HasBulletInBarrel`) continua false.
- Validado no servidor: 1.280 armas amostradas (as 70 apareceram), todas com a contagem esperada; minigun 0; 0 erros de carga. **Não testado no jogo:** se o TACZ aceita atirar com o pente a 50% sem bala na câmara.
- Isso interage com o pool de munição: a arma já traz balas, mas a munição de reserva continua sorteada à parte.
