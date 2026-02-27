<template>
  <el-config-provider :locale="zhCn">
    <el-container class="app-container">
      <el-header class="app-header">
        <div class="logo">
          <el-icon><Message /></el-icon>
          <span>Message Subscription System</span>
        </div>
        <div class="header-right">
          <el-dropdown v-if="authStore.isLoggedIn">
            <span class="user-info">
              <el-icon><User /></el-icon>
              {{ authStore.user?.username }}
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="router.push('/settings')">Settings</el-dropdown-item>
                <el-dropdown-item divided @click="logout">Logout</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button v-else type="primary" @click="router.push('/login')">Login</el-button>
        </div>
      </el-header>

      <el-container>
        <el-aside width="200px" class="app-aside">
          <el-menu
            :default-active="route.path"
            router
            class="side-menu"
          >
            <el-menu-item index="/dashboard">
              <el-icon><HomeFilled /></el-icon>
              <span>Dashboard</span>
            </el-menu-item>
            <el-menu-item index="/subscriptions">
              <el-icon><Collection /></el-icon>
              <span>Subscriptions</span>
            </el-menu-item>
            <el-menu-item index="/messages">
              <el-icon><ChatDotSquare /></el-icon>
              <span>Messages</span>
            </el-menu-item>
            <el-menu-item index="/publish">
              <el-icon><Upload /></el-icon>
              <span>Publish</span>
            </el-menu-item>
            <el-menu-item index="/notifications">
              <el-icon><Bell /></el-icon>
              <span>Notifications</span>
            </el-menu-item>
          </el-menu>
        </el-aside>

        <el-main class="app-main">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </el-config-provider>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const logout = async () => {
  await authStore.logout()
  router.push('/login')
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
}

.app-container {
  height: 100%;
}

.app-header {
  background: #409eff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: bold;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  color: white;
}

.app-aside {
  background: #f5f7fa;
}

.side-menu {
  border-right: none;
}

.app-main {
  background: #f0f2f5;
  padding: 20px;
}
</style>
