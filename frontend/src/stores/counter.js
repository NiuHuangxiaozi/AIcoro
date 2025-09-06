import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
// 这里确实就是理解了pinia的作用了
export const useCounterStore = defineStore('counter', () => {
  const count = ref(0)
  const doubleCount = computed(() => count.value * 2)
  function increment() {
    count.value++
  }

  return { count, doubleCount, increment }
})
