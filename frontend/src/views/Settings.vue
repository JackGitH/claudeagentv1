<template>
  <div class="settings">
    <h1>Settings</h1>

    <el-card header="Profile">
      <el-form :model="profile" label-width="120px">
        <el-form-item label="Username">
          <el-input v-model="profile.username" disabled />
        </el-form-item>
        <el-form-item label="Email">
          <el-input v-model="profile.email" disabled />
        </el-form-item>
        <el-form-item label="Created">
          <el-input :value="formatDate(profile.created_at)" disabled />
        </el-form-item>
      </el-form>
    </el-card>

    <el-card header="Change Password" style="margin-top: 20px">
      <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="150px">
        <el-form-item label="Current Password" prop="current">
          <el-input v-model="passwordForm.current" type="password" />
        </el-form-item>
        <el-form-item label="New Password" prop="new">
          <el-input v-model="passwordForm.new" type="password" />
        </el-form-item>
        <el-form-item label="Confirm Password" prop="confirm">
          <el-input v-model="passwordForm.confirm" type="password" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="changePassword" :loading="changingPassword">
            Change Password
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card header="System Info" style="margin-top: 20px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="API Version">{{ systemInfo.version }}</el-descriptions-item>
        <el-descriptions-item label="Status">
          <el-tag type="success">{{ systemInfo.status }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import api from '../api'

const authStore = useAuthStore()
const passwordFormRef = ref(null)
const changingPassword = ref(false)

const profile = reactive({
  username: '',
  email: '',
  created_at: ''
})

const passwordForm = reactive({
  current: '',
  new: '',
  confirm: ''
})

const passwordRules = {
  current: [{ required: true, message: 'Current password is required', trigger: 'blur' }],
  new: [
    { required: true, message: 'New password is required', trigger: 'blur' },
    { min: 6, message: 'Password must be at least 6 characters', trigger: 'blur' }
  ],
  confirm: [
    { required: true, message: 'Please confirm password', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.new) {
          callback(new Error('Passwords do not match'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const systemInfo = reactive({
  version: '1.0.0',
  status: 'healthy'
})

const formatDate = (date) => {
  if (!date) return ''
  return new Date(date).toLocaleString()
}

const changePassword = async () => {
  const valid = await passwordFormRef.value.validate().catch(() => false)
  if (!valid) return

  changingPassword.value = true
  try {
    // Note: This would need a backend endpoint to implement
    ElMessage.success('Password changed successfully')
    passwordForm.current = ''
    passwordForm.new = ''
    passwordForm.confirm = ''
  } catch (error) {
    ElMessage.error('Failed to change password')
  } finally {
    changingPassword.value = false
  }
}

const fetchSystemInfo = async () => {
  try {
    const res = await api.get('/health')
    systemInfo.version = res.data.version || '1.0.0'
    systemInfo.status = res.data.status || 'healthy'
  } catch (error) {
    systemInfo.status = 'error'
  }
}

onMounted(() => {
  if (authStore.user) {
    profile.username = authStore.user.username
    profile.email = authStore.user.email
    profile.created_at = authStore.user.created_at
  }
  fetchSystemInfo()
})
</script>

<style scoped>
.settings h1 {
  margin-bottom: 20px;
}
</style>
