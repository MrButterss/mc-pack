const meadowCheese = ['cheese', 'sheep_cheese', 'grain_cheese', 'amethyst_cheese', 'buffalo_cheese', 'goat_cheese', 'warped_cheese'].map(c => `meadow:${c}_slice`)
const wedges = ['brewinandchewin:flaxen_cheese_wedge', 'brewinandchewin:scarlet_cheese_wedge', 'culturaldelights:cheese_wedge']

ServerEvents.tags('item', event => {
  event.add('c:cheese', wedges)
  event.add('brewinandchewin:foods/cheese_wedge', meadowCheese)
  event.add('c:crops/coffee', 'herbalbrews:coffee_beans')
  event.add('c:crops/coffee_beans', 'herbalbrews:coffee_beans')
})

ServerEvents.recipes(event => {
  event.replaceInput({ mod: 'herbalbrews' }, 'herbalbrews:coffee_beans', '#c:crops/coffee_beans')
})
