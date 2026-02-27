<template>
  <div class="dashboard">
    <h1>Dashboard</h1>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="Total Subscriptions" :value="stats.totalSubscriptions">
            <template #prefix>
              <el-icon><Collection /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="Total Messages" :value="stats.totalMessages">
            <template #prefix>
              <el-icon><ChatDotSquare /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="New Messages" :value="stats.newMessages">
            <template #prefix>
              <el-icon><Bell /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="Published" :value="stats.published">
            <template #prefix>
              <el-icon><Upload /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="content-row">
      <el-col :span="16">
        <el-card header="Recent Messages">
          <el-table :data="recentMessages" style="width: 100%">
            <el-table-column prop="title" label="Title" min-width="200">
              <template #default="{ row }">
                <span>{{ row.title || truncate(row.content, 50) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="author" label="Author" width="120" />
            <el-table-column prop="category" label="Category" width="100" />
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
            <el-table-column prop="created_at" label="Created" width="150">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card header="Quick Actions">
          <el-space direction="vertical" style="width: 100%">
            <el-button type="primary" @click="$router.push('/subscriptions')">
              <el-icon><Plus /></el-icon>
              Add Subscription
            </el-button>
            <el-button @click="$router.push('/messages')">
              <el-icon><View /></el-icon>
              View All Messages
            </el-button>
            <el-button @click="$router.push('/publish')">
              <el-icon><Upload /></el-icon>
              Publish Messages
            </el-button>
            <el-button @click="$router.push('/notifications')">
              <el-icon><Setting /></el-icon>
              Notification Settings
            </el-button>
          </el-space>
        </el-card>

        <el-card header="Active Subscriptions" style="margin-top: 20px">
          <el-list>
            <el-list-item v-for="sub in activeSubscriptions" :key="sub.id">
              <el-list-item-meta
                :title="sub.name"
                :description="sub.source_type"
              />
              <template #extra>
                <el-tag :type="sub.enabled ? 'success' : 'info'" size="small">
                  {{ sub.enabled ? 'Active' : 'Paused' }}
                </el-tag>
              </template>
            </el-list-item>
          </el-list>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const stats = ref({
  totalSubscriptions: 0,
  totalMessages: 0,
  newMessages: 0,
  published: 0
})

const recentMessages = ref([])
const activeSubscriptions = ref([])

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

const fetchDashboard = async () => {
  try {
    // Fetch subscriptions
    const subsRes = await api.get('/subscriptions')
    activeSubscriptions.value = subsRes.data.slice(0, 5)
    stats.value.totalSubscriptions = subsRes.data.length

    // Fetch messages
    const msgRes = await api.get('/messages', { params: { page_size: 10 } })
    recentMessages.value = msgRes.data.items
    stats.value.totalMessages = msgRes.data.total
    stats.value.newMessages = msgRes.data.items.filter(m => m.status === 'new').length

    // Fetch publish records
    const pubRes = await api.get('/publish/records')
    stats.value.published = pubRes.data.filter(r => r.status === 'published').length
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error)
  }
}

onMounted(() => {
  fetchDashboard()
})
</script>

<style scoped>
.dashboard h1 {
  margin-bottom: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.content-row {
  margin-top: 20px;
}
</style>
