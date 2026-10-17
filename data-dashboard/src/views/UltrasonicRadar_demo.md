# 超声波雷达演示代码 - 分段版本

> 演示时间：约 70 秒
> 每段代码可以单独复制粘贴到 `drawRadar()` 函数中

---

## 第 1 段：基础画布（30秒）

**讲解要点**：初始化 Canvas，画雷达网格背景

```javascript
const drawRadar = () => {
  const ctx = canvasCtx
  const canvas = radarCanvas.value
  const centerX = canvas.width / 2
  const centerY = canvas.height / 2
  const maxRadius = Math.min(centerX, centerY) - 40
  
  // 1. 清空画布 - 深色背景
  ctx.fillStyle = '#0a101f'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  
  // 2. 画4个同心圆 - 雷达网格
  ctx.strokeStyle = 'rgba(0, 229, 255, 0.2)'
  for (let i = 1; i <= 4; i++) {
    ctx.beginPath()
    ctx.arc(centerX, centerY, maxRadius * i / 4, 0, Math.PI * 2)
    ctx.stroke()
  }
  
  // 先写到这里，运行看效果！
}
```

**预期效果**：看到蓝色同心圆

---

## 第 2 段：传感器扇形（30秒）

**讲解要点**：根据数据画扇形，距离近变红色

```javascript
  // 3. 画传感器扇形 - 左、前、右三个方向
  sensors.value.forEach((sensor, i) => {
    if (sensor.distance > 0) {
      // 距离映射到半径
      const radius = (sensor.distance / 500) * maxRadius
      // 三个传感器的角度：左(PI)、前(-PI/2)、右(0)
      const angles = [Math.PI, -Math.PI / 2, 0]
      
      ctx.beginPath()
      ctx.moveTo(centerX, centerY)
      // 画扇形：从中心点出发的弧形
      ctx.arc(centerX, centerY, radius, angles[i] - Math.PI/6, angles[i] + Math.PI/6)
      ctx.closePath()
      
      // 距离小于500mm变红色警告，否则青色
      ctx.fillStyle = sensor.distance < 500 
        ? 'rgba(255, 51, 102, 0.6)' 
        : 'rgba(0, 229, 255, 0.4)'
      ctx.fill()
    }
  })
  
  // 写到这里，运行看效果！
```

**预期效果**：看到三个方向的扇形，随数据变色

---

## 第 3 段：动画循环（10秒）

**讲解要点**：让雷达动起来

```javascript
  // 4. 画中心点
  ctx.beginPath()
  ctx.arc(centerX, centerY, 10, 0, Math.PI * 2)
  ctx.fillStyle = '#00E5FF'
  ctx.fill()
  
  // 5. 循环绘制 - 实现动画效果
  requestAnimationFrame(drawRadar)
}
```

**预期效果**：完整的动态雷达图

---

## 演示流程

| 顺序 | 时间 | 操作 | 观众看到 |
|:---|:---|:---|:---|
| 1 | 30秒 | 打第1段 | 蓝色同心圆 |
| 2 | 30秒 | 打第2段 | 出现三个扇形 |
| 3 | 10秒 | 打第3段 | 中心点 + 动画 |

**总计：70秒**

---

## 备用：完整合并版（如果分段时间不够）

```javascript
const drawRadar = () => {
  const ctx = canvasCtx
  const canvas = radarCanvas.value
  const centerX = canvas.width / 2
  const centerY = canvas.height / 2
  const maxRadius = Math.min(centerX, centerY) - 40
  
  // 清空画布
  ctx.fillStyle = '#0a101f'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  
  // 画同心圆
  ctx.strokeStyle = 'rgba(0, 229, 255, 0.2)'
  for (let i = 1; i <= 4; i++) {
    ctx.beginPath()
    ctx.arc(centerX, centerY, maxRadius * i / 4, 0, Math.PI * 2)
    ctx.stroke()
  }
  
  // 画传感器扇形
  sensors.value.forEach((sensor, i) => {
    if (sensor.distance > 0) {
      const radius = (sensor.distance / 500) * maxRadius
      const angles = [Math.PI, -Math.PI / 2, 0]
      
      ctx.beginPath()
      ctx.moveTo(centerX, centerY)
      ctx.arc(centerX, centerY, radius, angles[i] - Math.PI/6, angles[i] + Math.PI/6)
      ctx.closePath()
      
      ctx.fillStyle = sensor.distance < 500 
        ? 'rgba(255, 51, 102, 0.6)' 
        : 'rgba(0, 229, 255, 0.4)'
      ctx.fill()
    }
  })
  
  // 画中心点 + 动画
  ctx.beginPath()
  ctx.arc(centerX, centerY, 10, 0, Math.PI * 2)
  ctx.fillStyle = '#00E5FF'
  ctx.fill()
  
  requestAnimationFrame(drawRadar)
}
```
