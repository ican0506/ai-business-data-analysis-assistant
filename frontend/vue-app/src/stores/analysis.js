import { defineStore } from 'pinia'

import { getDatasetMetrics, getFieldMapping, replaceFieldMapping } from '../api/datasets'
import { resolveDomainDisplay } from '../utils/domainDisplay'

export const useAnalysisStore = defineStore('analysis', {
  state: () => ({
    datasetId: null,
    metrics: null,
    fieldMapping: null,
    loading: false,
    savingMapping: false,
    mappingDialogVisible: false,
    error: '',
  }),
  getters: {
    selectedModule: (state) => state.metrics?.selected_module || { id: 'generic', name: '通用数据分析' },
    domain() { return resolveDomainDisplay(this.selectedModule) },
    overrides: (state) => state.fieldMapping?.overrides || {},
  },
  actions: {
    async load(datasetId) {
      if (!datasetId) return
      this.datasetId = Number(datasetId)
      this.loading = true
      this.error = ''
      try {
        const [fieldMapping, metrics] = await Promise.all([
          getFieldMapping(this.datasetId),
          getDatasetMetrics(this.datasetId),
        ])
        this.fieldMapping = fieldMapping
        this.metrics = metrics
      } catch (error) {
        this.error = error.message || '加载数据集分析结果失败，请重试。'
        throw error
      } finally {
        this.loading = false
      }
    },
    async saveOverrides(overrides) {
      if (!this.datasetId) return
      this.savingMapping = true
      this.error = ''
      try {
        await replaceFieldMapping(this.datasetId, overrides)
        await this.load(this.datasetId)
      } catch (error) {
        this.error = error.message || '字段映射保存失败，请检查后端提示。'
        throw error
      } finally {
        this.savingMapping = false
      }
    },
  },
})
