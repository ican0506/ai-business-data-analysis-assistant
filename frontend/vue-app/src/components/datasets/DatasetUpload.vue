<script setup>
import { ElMessage } from 'element-plus'
import { ref } from 'vue'

import { uploadDataset } from '../../api/datasets'

const emit = defineEmits(['uploaded'])
const inputRef = ref(null)
const selectedFile = ref(null)
const isUploading = ref(false)
const uploadProgress = ref(0)
const errorMessage = ref('')

function chooseFile() { inputRef.value?.click() }

function onFileChange(event) {
  const [file] = event.target.files
  errorMessage.value = ''
  if (!file) return
  if (!/\.(csv|xlsx)$/i.test(file.name)) {
    selectedFile.value = null
    errorMessage.value = '仅支持 CSV 或 XLSX 格式文件。'
    event.target.value = ''
    return
  }
  selectedFile.value = file
}

async function submitUpload() {
  if (!selectedFile.value || isUploading.value) return
  isUploading.value = true
  uploadProgress.value = 0
  errorMessage.value = ''
  try {
    const dataset = await uploadDataset(selectedFile.value, (progress) => { uploadProgress.value = progress })
    emit('uploaded', { dataset, file: selectedFile.value })
    ElMessage.success('文件上传并解析成功，已加入当前浏览器的展示记录。')
    selectedFile.value = null
    inputRef.value.value = ''
  } catch (error) {
    errorMessage.value = error.message || '上传失败，请稍后重试。'
  } finally {
    isUploading.value = false
  }
}
</script>

<template>
  <el-card class="dataset-upload-card" shadow="never">
    <div class="upload-copy"><p class="view-eyebrow">DATA INGESTION</p><h3>上传业务数据</h3><p>支持 CSV、XLSX 文件，上传后由现有后端完成解析与字段识别。</p></div>
    <input ref="inputRef" class="native-file-input" type="file" accept=".csv,.xlsx" @change="onFileChange" />
    <div class="upload-actions"><el-button plain @click="chooseFile">选择 Excel / CSV</el-button><el-button type="primary" :loading="isUploading" :disabled="!selectedFile" @click="submitUpload">{{ isUploading ? '正在上传' : '开始上传' }}</el-button></div>
    <p v-if="selectedFile" class="selected-file">已选择：{{ selectedFile.name }}（{{ (selectedFile.size / 1024).toFixed(1) }} KB）</p>
    <el-progress v-if="isUploading" :percentage="uploadProgress" :stroke-width="8" />
    <p v-if="errorMessage" class="form-error" role="alert">{{ errorMessage }}</p>
  </el-card>
</template>
