<template>
  <div class="subscriptions">
    <div class="header">
      <h1>Subscriptions</h1>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        Add Subscription
      </el-button>
    </div>

    <el-table :data="subscriptions" style="width: 100%" v-loading="loading">
      <el-table-column prop="name" label="Name" min-width="150" />
      <el-table-column prop="source_type" label="Type" width="100">
        <template #default="{ row }">
          <el-tag :type="getSourceType(row.source_type)">
            {{ row.source_type }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="source_config" label="Config" min-width="200">
        <template #default="{ row }">
          <span>{{ formatConfig(row.source_config) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="enabled" label="Status" width="100">
        <template #default="{ row }">
          <el-switch
            v-model="row.enabled"
            @change="toggleSubscription(row)"
          />
        </template>
      </el-table-column>
      <el-table-column prop="last_checked_at" label="Last Checked" width="150">
        <template #default="{ row }">
          {{ row.last_checked_at ? formatDate(row.last_checked_at) : 'Never' }}
        </template>
      </el-table-column>
      <el-table-column label="Actions" width="150">
        <template #default="{ row }">
          <el-button size="small" @click="editSubscription(row)">Edit</el-button>
          <el-button size="small" type="danger" @click="deleteSubscription(row)">Delete</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingSubscription ? 'Edit Subscription' : 'New Subscription'"
      width="500px"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="Name" prop="name">
          <el-input v-model="form.name" placeholder="Subscription name" />
        </el-form-item>
        <el-form-item label="Source Type" prop="source_type">
          <el-select v-model="form.source_type" placeholder="Select type" style="width: 100%">
            <el-option label="Twitter" value="twitter" />
            <el-option label="RSS" value="rss" />
            <el-option label="Webhook" value="webhook" />
            <el-option label="Keyword" value="keyword" />
          </el-select>
        </el-form-item>

        <!-- Twitter Config -->
        <template v-if="form.source_type === 'twitter'">
          <el-form-item label="Usernames">
            <el-select
              v-model="form.source_config.usernames"
              multiple
              filterable
              allow-create
              placeholder="Add usernames"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="Keywords">
            <el-select
              v-model="form.source_config.keywords"
              multiple
              filterable
              allow-create
              placeholder="Add keywords"
              style="width: 100%"
            />
          </el-form-item>
        </template>

        <!-- RSS Config -->
        <template v-if="form.source_type === 'rss'">
          <el-form-item label="RSS URL">
            <el-input v-model="form.source_config.url" placeholder="https://example.com/feed.xml" />
          </el-form-item>
        </template>

        <!-- Webhook Config -->
        <template v-if="form.source_type === 'webhook'">
          <el-form-item label="Source Name">
            <el-input v-model="form.source_config.source" placeholder="my-app" />
          </el-form-item>
          <el-form-item label="Secret (Optional)">
            <el-input v-model="form.source_config.secret" placeholder="Webhook secret" />
          </el-form-item>
        </template>

        <!-- Keyword Config -->
        <template v-if="form.source_type === 'keyword'">
          <el-form-item label="Keywords">
            <el-select
              v-model="form.source_config.keywords"
              multiple
              filterable
              allow-create
              placeholder="Add keywords"
              style="width: 100%"
            />
          </el-form-item>
        </template>

        <el-form-item label="Enabled">
          <el-switch v-model="form.enabled" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">Cancel</el-button>
        <el-button type="primary" @click="saveSubscription" :loading="saving">Save</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const loading = ref(false)
const saving = ref(false)
const subscriptions = ref([])
const showCreateDialog = ref(false)
const editingSubscription = ref(null)
const formRef = ref(null)

const form = reactive({
  name: '',
  source_type: 'rss',
  source_config: {},
  enabled: true
})

const rules = {
  name: [{ required: true, message: 'Name is required', trigger: 'blur' }],
  source_type: [{ required: true, message: 'Source type is required', trigger: 'change' }]
}

const getSourceType = (type) => {
  const types = {
    twitter: 'primary',
    rss: 'success',
    webhook: 'warning',
    keyword: 'info'
  }
  return types[type] || ''
}

const formatConfig = (config) => {
  if (!config) return ''
  if (config.url) return config.url
  if (config.usernames?.length) return `@${config.usernames.join(', @')}`
  if (config.keywords?.length) return config.keywords.join(', ')
  if (config.source) return config.source
  return JSON.stringify(config)
}

const formatDate = (date) => {
  if (!date) return ''
  return new Date(date).toLocaleString()
}

const resetForm = () => {
  form.name = ''
  form.source_type = 'rss'
  form.source_config = {}
  form.enabled = true
  editingSubscription.value = null
}

const editSubscription = (sub) => {
  editingSubscription.value = sub
  form.name = sub.name
  form.source_type = sub.source_type
  form.source_config = { ...sub.source_config }
  form.enabled = sub.enabled
  showCreateDialog.value = true
}

const saveSubscription = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    if (editingSubscription.value) {
      await api.put(`/subscriptions/${editingSubscription.value.id}`, form)
      ElMessage.success('Subscription updated')
    } else {
      await api.post('/subscriptions', form)
      ElMessage.success('Subscription created')
    }
    showCreateDialog.value = false
    resetForm()
    fetchSubscriptions()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || 'Failed to save subscription')
  } finally {
    saving.value = false
  }
}

const toggleSubscription = async (sub) => {
  try {
    await api.put(`/subscriptions/${sub.id}`, { enabled: sub.enabled })
    ElMessage.success(sub.enabled ? 'Subscription enabled' : 'Subscription disabled')
  } catch (error) {
    sub.enabled = !sub.enabled
    ElMessage.error('Failed to update subscription')
  }
}

const deleteSubscription = async (sub) => {
  try {
    await ElMessageBox.confirm('Are you sure you want to delete this subscription?', 'Confirm Delete')
    await api.delete(`/subscriptions/${sub.id}`)
    ElMessage.success('Subscription deleted')
    fetchSubscriptions()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('Failed to delete subscription')
    }
  }
}

const fetchSubscriptions = async () => {
  loading.value = true
  try {
    const res = await api.get('/subscriptions')
    subscriptions.value = res.data
  } catch (error) {
    ElMessage.error('Failed to fetch subscriptions')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchSubscriptions()
})
</script>

<style scoped>
.subscriptions .header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.subscriptions h1 {
  margin: 0;
}
</style>
