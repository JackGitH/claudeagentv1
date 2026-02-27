<template>
  <div class="notifications">
    <h1>Notification Settings</h1>

    <el-card header="Notification Channels">
      <el-form :model="settings" label-width="150px">
        <!-- Telegram Settings -->
        <el-divider content-position="left">Telegram</el-divider>
        <el-form-item label="Enable Telegram">
          <el-switch v-model="settings.telegram_enabled" />
        </el-form-item>
        <el-form-item label="Chat ID" v-if="settings.telegram_enabled">
          <el-input v-model="settings.telegram_chat_id" placeholder="Your Telegram chat ID" />
          <el-text size="small" type="info">
            Start a chat with your bot and use @userinfobot to get your chat ID
          </el-text>
        </el-form-item>
        <el-form-item v-if="settings.telegram_enabled">
          <el-button @click="testTelegram" :loading="testingTelegram">
            Test Telegram
          </el-button>
        </el-form-item>

        <!-- Email Settings -->
        <el-divider content-position="left">Email</el-divider>
        <el-form-item label="Enable Email">
          <el-switch v-model="settings.email_enabled" />
        </el-form-item>
        <el-form-item label="Email Address" v-if="settings.email_enabled">
          <el-input v-model="settings.email_address" placeholder="your@email.com" />
        </el-form-item>
        <el-form-item v-if="settings.email_enabled">
          <el-button @click="testEmail" :loading="testingEmail">
            Test Email
          </el-button>
        </el-form-item>

        <!-- Notification Preferences -->
        <el-divider content-position="left">Preferences</el-divider>
        <el-form-item label="Notify on New">
          <el-switch v-model="settings.notify_on_new" />
          <el-text size="small" type="info">Receive notifications for new messages</el-text>
        </el-form-item>
        <el-form-item label="Notify on Keyword">
          <el-switch v-model="settings.notify_on_keyword" />
          <el-text size="small" type="info">Receive notifications for keyword matches</el-text>
        </el-form-item>

        <!-- Quiet Hours -->
        <el-divider content-position="left">Quiet Hours</el-divider>
        <el-form-item label="Start Time">
          <el-time-select
            v-model="settings.quiet_hours_start"
            start="00:00"
            step="01:00"
            end="23:00"
            placeholder="Start time"
          />
        </el-form-item>
        <el-form-item label="End Time">
          <el-time-select
            v-model="settings.quiet_hours_end"
            start="00:00"
            step="01:00"
            end="23:00"
            placeholder="End time"
          />
        </el-form-item>
        <el-text size="small" type="info">
          Notifications will be paused during quiet hours
        </el-text>

        <el-form-item style="margin-top: 20px">
          <el-button type="primary" @click="saveSettings" :loading="saving">
            Save Settings
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card header="Notification History" style="margin-top: 20px">
      <el-table :data="records" style="width: 100%">
        <el-table-column prop="channel" label="Channel" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.channel }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="Status" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message_id" label="Message ID" width="100" />
        <el-table-column prop="error_message" label="Error" min-width="200">
          <template #default="{ row }">
            <el-text v-if="row.error_message" type="danger">{{ row.error_message }}</el-text>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="sent_at" label="Sent At" width="150">
          <template #default="{ row }">
            {{ row.sent_at ? formatDate(row.sent_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="Created" width="150">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const saving = ref(false)
const testingTelegram = ref(false)
const testingEmail = ref(false)

const settings = reactive({
  telegram_enabled: false,
  telegram_chat_id: '',
  email_enabled: false,
  email_address: '',
  notify_on_new: true,
  notify_on_keyword: true,
  quiet_hours_start: '22:00',
  quiet_hours_end: '08:00',
  filters: {}
})

const records = ref([])

const formatDate = (date) => {
  if (!date) return ''
  return new Date(date).toLocaleString()
}

const getStatusType = (status) => {
  const types = {
    pending: 'warning',
    sent: 'success',
    failed: 'danger'
  }
  return types[status] || ''
}

const fetchSettings = async () => {
  try {
    const res = await api.get('/notifications/settings')
    Object.assign(settings, res.data)
  } catch (error) {
    console.error('Failed to fetch settings:', error)
  }
}

const saveSettings = async () => {
  saving.value = true
  try {
    await api.put('/notifications/settings', settings)
    ElMessage.success('Settings saved')
  } catch (error) {
    ElMessage.error('Failed to save settings')
  } finally {
    saving.value = false
  }
}

const testTelegram = async () => {
  if (!settings.telegram_chat_id) {
    ElMessage.warning('Please enter a chat ID')
    return
  }

  testingTelegram.value = true
  try {
    await api.post('/notifications/telegram/test')
    ElMessage.success('Test message sent to Telegram')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || 'Failed to send test message')
  } finally {
    testingTelegram.value = false
  }
}

const testEmail = async () => {
  if (!settings.email_address) {
    ElMessage.warning('Please enter an email address')
    return
  }

  testingEmail.value = true
  try {
    await api.post('/notifications/email/test')
    ElMessage.success('Test email sent')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || 'Failed to send test email')
  } finally {
    testingEmail.value = false
  }
}

const fetchRecords = async () => {
  try {
    const res = await api.get('/notifications/records')
    records.value = res.data
  } catch (error) {
    console.error('Failed to fetch records:', error)
  }
}

onMounted(() => {
  fetchSettings()
  fetchRecords()
})
</script>

<style scoped>
.notifications h1 {
  margin-bottom: 20px;
}
</style>
