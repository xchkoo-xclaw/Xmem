<template>
  <div class="inline-flex bg-surface rounded-full p-1 shadow-float w-fit border border-border">
    <button
      v-for="tab in tabs"
      :key="tab.value"
      :data-onboarding="`tab-${tab.value}`"
      :class="[
        'px-3 md:px-4 py-2 text-sm font-semibold rounded-full transition-all duration-200 whitespace-nowrap',
        modelValue === tab.value ? 'bg-accent text-on-accent shadow' : 'text-muted hover:text-text'
      ]"
      @click="$emit('update:modelValue', tab.value)"
    >
      {{ tab.label }}
    </button>
  </div>
  <slot />
</template>

<script setup lang="ts">
defineProps<{
  tabs: { label: string; value: string }[];
  modelValue: string;
}>();
defineEmits<{
  (e: "update:modelValue", value: string): void;
}>();
</script>

