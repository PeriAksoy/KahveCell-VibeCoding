import { MILK_TYPES, SIZES, SUGAR_LEVELS } from '../constants/menu'

// "Büyük (L) · Yulaf sütü · 2 şeker · +1 shot"
export function describeOptions(order) {
  const size = SIZES.find((s) => s.value === order.size)
  const milk = MILK_TYPES.find((m) => m.value === (order.milk_type ?? ''))
  const sugar = SUGAR_LEVELS.find((s) => s.value === order.sugar_level)

  const parts = [
    size ? `${size.label} (${size.hint})` : order.size,
    milk?.label ?? order.milk_type,
    sugar?.label ?? `${order.sugar_level} şeker`,
  ]
  if (order.extra_shots > 0) parts.push(`+${order.extra_shots} shot`)
  return parts.join(' · ')
}
