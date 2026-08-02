<script setup>
defineProps({ eyebrow: String, title: { type: String, required: true }, description: String })
</script>
<template><header class="common-page-header"><div><p class="view-eyebrow">{{ eyebrow }}</p><h2>{{ title }}</h2><p v-if="description">{{ description }}</p></div><slot name="actions" /></header></template>
