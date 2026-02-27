<template>
  <div class="messages">
    <div class="header">
      <h1>Messages</h1>
      <el-input
        v-model="search"
        placeholder="Search messages..."
        style="width: 300px"
        clearable
        @clear="fetchMessages"
        @keyup.enter="fetchMessages"
      >
        <template #append>
          <el-button @click="fetchMessages">
            <el-icon><Search /></el-icon>
          </el-button>
        </template>
      </el-input>
    </div>

    <el-table
      :data="messages"
      style="width: 100%"
      v-loading="loading"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="50" />
      <el-table-column prop="title" label="Title" min-width="200">
        <template #default="{ row }">
          <div class="message-title">
            <strong>{{ row.title || 'No Title' }}</strong>
            <small v-if="row.author">by {{ row.author }}</small>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="content" label="Content" min-width="300">
        <template #default="{ row }">
          <el-tooltip :content="row.content" placement="top" :disabled="row.content.length < 100">
            <span>{{ truncate(row.content, 100) }}</span>
          </el-tooltip>
        </template>
      </el-table-column>
      <el-table-column prop="category" label="Category" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.category" size="small">{{ row.category }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="sentiment" label="Sentiment" width="100">
        <template #default="{ row }">
          <el-tag
            v-if="row.sentiment"
            :type="getSentimentType(row.sentiment)"
            size="small"
          >
            {{ row.sentiment }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="Status" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)" size="small">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="Created" width="150">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="Actions" width="200">
        <template #default="{ row }">
          <el-button size="small" @click="viewMessage(row)">View</el-button>
          <el-button size="small" type="primary" @click="analyzeMessage(row)">
            Analyze
          </el-button>
          <el-button size="small" type="danger" @click="deleteMessage(row)">
            Delete
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next"
        @size-change="fetchMessages"
        @current-change="fetchMessages"
      />
    </div>

    <div class="batch-actions" v-if="selectedMessages.length > 0">
      <el-button type="primary" @click="publishSelected">
        Publish Selected ({{ selectedMessages.length }})
      </el-button>
    </div>

    <!-- Message Detail Dialog -->
    <el-dialog v-model="showDetailDialog" title="Message Detail" width="700px">
      <el-descriptions :column="1" border v-if="selectedMessage">
        <el-descriptions-item label="Title">{{ selectedMessage.title }}</el-descriptions-item>
        <el-descriptions-item label="Author">{{ selectedMessage.author }}</el-descriptions-item>
        <el-descriptions-item label="Source">
          <a :href="selectedMessage.source_url" target="_blank" v-if="selectedMessage.source_url">
            {{ selectedMessage.source_url }}
          </a>
        </el-descriptions-item>
        <el-descriptions-item label="Content">
          <div class="message-content">{{ selectedMessage.content }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="Summary" v-if="selectedMessage.summary">
          {{ selectedMessage.summary }}
        </el-descriptions-item>
        <el-descriptions-item label="Category">{{ selectedMessage.category }}</el-descriptions-item>
        <el-descriptions-item label="Sentiment">
          <el-tag v-if="selectedMessage.sentiment" :type="getSentimentType(selectedMessage.sentiment)">
            {{ selectedMessage.sentiment }} ({{ selectedMessage.sentiment_score }})
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Keywords" v-if="selectedMessage.keywords">
          {{ selectedMessage.keywords }}
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const router = useRouter()
const loading = ref(false)
const messages = ref([])
const selectedMessages = ref([])
const search = ref('')
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const showDetailDialog = ref(false)
const selectedMessage = ref(null)

const truncate = (text, length) => {
  if (!text) return ''
  return text.length > length ? text.substring(0, length) + '...' : text
}

const formatDate = (date) => {
  if (!date) return ''
  return new Date(date).toLocaleString()
}

const getSentimentType = (sentiment) => {
  const types = {
    positive: 'success',
    negative: 'danger',
    neutral: 'info'
  }
  return types[sentiment] || 'info'
}

const getStatusType = (status) => {
  const types = {
    new: 'primary',
    processing: 'warning',
    processed: 'success',
    published: 'info',
    failed: 'danger'
  }
  return types[status] || ''
}

const handleSelectionChange = (selection) => {
  selectedMessages.value = selection
}

const viewMessage = (message) => {
  selectedMessage.value = message
  showDetailDialog.value = true
}

const analyzeMessage = async (message) => {
  try {
    ElMessage.info('Analyzing message...')
    const res = await api.post(`/messages/${message.id}/analyze`)
    Object.assign(message, res.data)
    ElMessage.success('Analysis complete')
  } catch (error) {
    ElMessage.error('Failed to analyze message')
  }
}

const deleteMessage = async (message) => {
  try {
    await ElMessageBox.confirm('Are you sure you want to delete this message?', 'Confirm Delete')
    await api.delete(`/messages/${message.id}`)
    ElMessage.success('Message deleted')
    fetchMessages()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('Failed to delete message')
    }
  }
}

const publishSelected = () => {
  const ids = selectedMessages.value.map(m => m.id)
  router.push({ path: '/publish', query: { ids: ids.join(',') } })
}

const fetchMessages = async () => {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value
    }
    if (search.value) {
      params.search = search.value
    }

    const res = await api.get('/messages', { params })
    messages.value = res.data.items
    total.value = res.data.total
  } catch (error) {
    ElMessage.error('Failed to fetch messages')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchMessages()
})
</script>

<style scoped>
.messages .header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.messages h1 {
  margin: 0;
}

.message-title {
  display: flex;
  flex-direction: column;
}

.message-title small {
  color: #999;
  font-weight: normal;
}

.message-content {
  max-height: 300px;
  overflow-y: auto;
  white-space: pre-wrap;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.batch-actions {
  margin-top: 20px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}
</style>
