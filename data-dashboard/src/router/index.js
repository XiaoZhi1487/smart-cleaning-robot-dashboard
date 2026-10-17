import { createRouter, createWebHashHistory } from 'vue-router'

// 路由配置
const routes = [
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/views/Layout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Screen1.vue'),
        meta: { title: '数据大屏', icon: '📊' }
      },
      {
        path: 'ultrasonic-radar',
        name: 'UltrasonicRadar',
        component: () => import('@/views/UltrasonicRadar.vue'),
        meta: { title: '超声波传感器', icon: '📡' }
      },
      {
        path: 'depth-camera',
        name: 'DepthCamera',
        component: () => import('@/views/DepthCamera.vue'),
        meta: { title: '工业相机', icon: '📷' }
      },

    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    redirect: '/dashboard'
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

// 设置页面标题
router.beforeEach((to, from, next) => {
  if (to.meta.title) {
    document.title = `${to.meta.title} - 智能清洁机器人监控系统`
  }
  next()
})

// 路由错误处理
router.onError((error) => {
  console.error('Router Error:', error)
})

export default router
