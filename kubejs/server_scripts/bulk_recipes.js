ServerEvents.recipes(event => {
  event.shaped('16x minecraft:stick', ['L', 'L'], { L: '#minecraft:logs' }).id('mcpack:sticks_from_logs')
  event.shaped('4x minecraft:chest', ['LLL', 'L L', 'LLL'], { L: '#minecraft:logs' }).id('mcpack:chests_from_logs')
})
