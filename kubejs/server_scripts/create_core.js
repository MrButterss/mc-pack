ServerEvents.recipes(event => {
  event.custom({
    type: 'create:mixing',
    heat_requirement: 'heated',
    ingredients: [
      { item: 'minecraft:glass_bottle' },
      { type: 'neoforge:single', amount: 250, fluid: 'minecraft:water' }
    ],
    results: [{ id: 'toughasnails:purified_water_bottle' }]
  }).id('mcpack:create/purified_water')

  const juices = {
    apple: 'minecraft:apple',
    melon: 'minecraft:melon_slice',
    sweet_berry: 'minecraft:sweet_berries',
    pumpkin: 'minecraft:pumpkin',
    cactus: 'minecraft:cactus',
    glow_berry: 'minecraft:glow_berries',
    chorus_fruit: 'minecraft:chorus_fruit'
  }
  Object.entries(juices).forEach(([name, fruit]) => {
    event.custom({
      type: 'create:mixing',
      ingredients: [
        { item: 'toughasnails:purified_water_bottle' },
        { item: 'minecraft:sugar' },
        { item: fruit }
      ],
      results: [{ id: `toughasnails:${name}_juice` }]
    }).id(`mcpack:create/${name}_juice`)
  })

  event.custom({
    type: 'create:item_application',
    ingredients: [{ item: 'sereneseasons:calendar' }, { item: 'minecraft:quartz' }],
    results: [{ id: 'sereneseasons:season_sensor' }]
  }).id('mcpack:create/season_sensor')

  event.custom({
    type: 'create:item_application',
    ingredients: [{ tag: 'c:chests' }, { item: 'structurize:sceptergold' }],
    results: [{ id: 'minecolonies:blockhutwarehouse' }]
  }).id('mcpack:create/warehouse_hut')

  event.custom({
    type: 'create:item_application',
    ingredients: [{ item: 'minecraft:smoker' }, { item: 'structurize:sceptergold' }],
    results: [{ id: 'minecolonies:blockhutkitchen' }]
  }).id('mcpack:create/kitchen_hut')
})
