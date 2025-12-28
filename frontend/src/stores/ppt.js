import { defineStore } from 'pinia'
import { pptgenAPI } from '@/api'
import { ref } from 'vue'

export const usePptStore = defineStore('ppt', () => {

  const PPTGen = async (pptxFile, pdfFile, topic, numberOfPages) => {
    try {
      const response = await pptgenAPI.generatePPT(pptxFile, pdfFile, topic, numberOfPages)
      console.log("PPT生成任务创建成功:", response)
      return response.task_id
    } catch (error) {
        console.error('PPT生成失败:', error)
        throw error
    }
  }
  const getDownloadLink = async (taskId) => {
    try {
      const response = await pptgenAPI.getDownloadLink_api(taskId)
      console.log("下载链接:", response)
      return response
    } catch (error) {
      console.error('下载链接获取失败:', error)
      throw error
    }
  }
  return {
    PPTGen,
    getDownloadLink
  }
})