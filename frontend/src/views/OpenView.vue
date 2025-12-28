

<template>
    <div class="hero-section">
        <!-- TODO: 展示平台宣传文本 -->
        <h1 class="hero-title">AlCORO: Your group meeting slacking-off gadget! </h1>
    </div>
</template>

<script setup>

const props = defineProps({
    title: {
        type: String,
        required: true
    }
})
</script>

<style scoped>
/* 主区域背景，使界面更美观 */
.hero-section {
  /* width: 50%;
  height: 250px;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #4b79a1, #283e51);
  color: #ffffff;
  text-align: center;
  margin-top: 300px;
  margin-left: 200px;
  margin-right: 200px;
  border-radius: 12px;
  box-shadow: 0 8px 18px rgba(0, 0, 0, 0.2); */
  display: flex;
  border-radius: 12px;
  justify-content: center;
  margin-top: 300px;
  background: linear-gradient(135deg, #4b79a1, #283e51);
  color: #ffffff;
  margin-left: 200px;
  margin-right: 200px;
  height: 250px;
  align-items: center;
}

/* 宣传标语文字 */
.hero-title {
  font-size: 45px;
  font-weight: 700;
  letter-spacing: 1px;
  text-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}
</style>