<template>
  <div class="publish">
    <h1>Publish Messages</h1>

    <el-card header="Select Platform">
      <el-radio-group v-model="selectedPlatform">
        <el-radio-button label="webhook">Webhook</el-radio-button>
        <el-radio-button label="telegram_channel">Telegram Channel</el-radio-button>
        <el-radio-button label="email">Email</el-radio-button>
      </el-radio-group>

      <div class="platform-config" v-if="selectedPlatform">
        <!-- Webhook Config -->
        <template v-if="selectedPlatform === 'webhook'">
          <el-form-item label="Webhook URL">
            <el-input v-model="platformConfig.webhook_url" placeholder="https://example.com/webhook" />
          </el-form-item>
        </template>

        <!-- Telegram Config -->
        <template v-if="selectedPlatform === 'telegram_channel'">
          <el-form-item label="Channel ID">
            <el-input v-model="platformConfig.channel_id" placeholder="@channel or -1001234567890" />
          </el-form-item>
        </template>

        <!-- Email Config -->
        <template v-if="selectedPlatform === 'email'">
          <el-form-item label="Recipients">
            <el-select
              v-model="platformConfig.recipients"
              multiple
              filterable
              allow-create
              placeholder="Add email addresses"
              style="width: 100%"
            />
          </el-form-item>
        </template>
      </div>
    </el-card>

    <el-card header="Messages to Publish" style="margin-top: 20px">
      <el-table :data="selectedMessages" style="width: 100%">
        <el-table-column prop="title" label="Title" min-width="200">
          <template #default="{ row }">
            {{ row.title || truncate(row.content, 50) }}
          </template>
        </el-table-column>
        <el-table-column prop="author" label="Author" width="120" />
        <el-table-column prop="status" label="Status" width="100" />
        <el-table-column label="Actions" width="100">
          <template #default="{ $index }">
            <el-button size="small" type="danger" @click="removeMessage($index)">
              Remove
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="selectedMessages.length === 0" description="No messages selected" />

      <div class="add-messages" style="margin-top: 20px">
        <el-button @click="showMessageSelector = true">
          <el-icon><Plus /></el-icon>
          Add Messages
        </el-button>
      </div>
    </el-card>

    <div class="actions" style="margin-top: 20px">
      <el-button type="primary" size="large" @click="publishMessages" :loading="publishing">
        <el-icon><Upload /></el-icon>
        Publish {{ selectedMessages.length }} Messages
      </el-button>
    </div>

    <el-card header="Publish History" style="margin-top: 20px">
      <el-table :data="publishRecords" style="width: 100%">
        <el-table-column prop="message_id" label="Message ID" width="100" />
        <el-table-column prop="platform" label="Platform" width="120" />
        <el-table-column prop="status" label="Status" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target_url" label="Target URL" min-width="200" />
        <el-table-column prop="published_at" label="Published At" width="150">
          <template #default="{ row }">
            {{ row.published_at ? formatDate(row.published_at) : '-' }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Message Selector Dialog -->
    <el-dialog v-model="showMessageSelector" title="Select Messages" width="800px">
      <el-table
        :data="availableMessages"
        style="width: 100%"
        @selection-change="handleMessageSelection"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column prop="title" label="Title" min-width="200">
          <template #default="{ row }">
            {{ row.title || truncate(row.content, 50) }}
          </template>
        </el-table-column>
        <el-table-column prop="author" label="Author" width="120" />
        <el-table-column prop="created_at" label="Created" width="150">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="showMessageSelector = false">Cancel</el-button>
        <el-button type="primary" @click="addSelectedMessages">
          Add Selected ({{ tempSelectedMessages.length }})
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'

const route = useRoute()
const publishing = ref(false)
const selectedPlatform = ref('webhook')
const platformConfig = ref({
  webhook_url: '',
  channel_id: '',
  recipients: []
})

const selectedMessages = ref([])
const availableMessages = ref([])
const publishRecords = ref([])
const showMessageSelector = ref(false)
const tempSelectedMessages = ref([])

const truncate = (text, length) => {
  if (!text) return ''
  return text.length > length ? text.substring(0, length) + '...' : text
}

const formatDate = (date) => {
  if (!date) return ''
  return new Date(date).toLocaleString()
}

const getStatusType = (status) => {
  const types = {
    pending: 'warning',
    published: 'success',
    failed: 'danger'
  }
  return types[status] || ''
}

const handleMessageSelection = (selection) => {
  tempSelectedMessages.value = selection
}

const addSelectedMessages = () => {
  const existingIds = new Set(selectedMessages.value.map(m => m.id))
  const newMessages = tempSelectedMessages.value.filter(m => !existingIds.has(m.id))
  selectedMessages.value.push(...newMessages)
  showMessageSelector.value = false
  tempSelectedMessages.value = []
}

const removeMessage = (index) => {
  selectedMessages.value.splice(index, 1)
}

const publishMessages = async () => {
  if (selectedMessages.value.length === 0) {
    ElMessage.warning('Please select messages to publish')
    return
  }

  publishing.value = true
  try {
    const messageIds = selectedMessages.value.map(m => m.id)
    const res = await api.post('/publish', {
      message_ids: messageIds,
      target_platform: selectedPlatform.value,
      options: platformConfig.value
    })

    ElMessage.success(res.data.message)
    selectedMessages.value = []
    fetchPublishRecords()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || 'Failed to publish messages')
  } finally {
    publishing.value = false
  }
}

const fetchAvailableMessages = async () => {
  try {
    const res = await api.get('/messages', { params: { page_size: 50 } })
    availableMessages.value = res.data.items
  } catch (error) {
    console.error('Failed to fetch messages:', error)
  }
}

const fetchPublishRecords = async () => {
  try {
    const res = await api.get('/publish/records')
    publishRecords.value = res.data
  } catch (error) {
    console.error('Failed to fetch publish records:', error)
  }
}

onMounted(async () => {
  await fetchAvailableMessages()
  await fetchPublishRecords()

  // Check for pre-selected messages from query params
  if (route.query.ids) {
    const ids = route.query.ids.split(',').map(Number)
    const res = await api.get('/messages', { params: { page_size: 100 } })
    selectedMessages.value = res.data.items.filter(m => ids.includes(m.id))
  }
})
</script>

<style scoped>
.publish h1 {
  margin-bottom: 20px;
}

.platform-config {
  margin-top: 20px;
}

.actions {
  display: flex;
  justify-content: center;
}
</style>
